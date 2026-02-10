"""Unit tests for description pattern rule service."""
import pytest
import uuid
from app.database import init_db, get_db
from app.services.desc_rule_service import desc_rule_service
from app.models.categorization import DescriptionPatternRuleCreate


@pytest.fixture(autouse=True)
def setup_db(tmp_path, monkeypatch):
    """Set up a fresh in-memory database for each test."""
    db_path = str(tmp_path / "test.duckdb")
    monkeypatch.setattr("app.database.DATABASE_PATH", db_path)
    monkeypatch.setattr("app.database._connection", None)
    init_db()
    # Seed test account and category
    with get_db() as conn:
        conn.execute(
            "INSERT INTO accounts (id, name, type, is_asset) VALUES (?, ?, ?, ?)",
            ["acct-1", "Fidelity Cash", "Investment", True],
        )
        conn.execute(
            "INSERT INTO accounts (id, name, type, is_asset) VALUES (?, ?, ?, ?)",
            ["acct-2", "Chase Checking", "Checking", True],
        )
        conn.execute(
            "INSERT INTO categories (id, name, group_name) VALUES (?, ?, ?)",
            ["cat-income", "Income", "Income"],
        )
        conn.execute(
            "INSERT INTO categories (id, name, group_name) VALUES (?, ?, ?)",
            ["cat-transfer", "Transfer", "Transfer"],
        )
    yield
    # Cleanup
    import app.database
    if app.database._connection:
        app.database._connection.close()
        app.database._connection = None


class TestDescRuleServiceCreate:
    def test_create_rule(self):
        data = DescriptionPatternRuleCreate(
            description_pattern="direct deposit fidelity bro* (cash)",
            account_id="acct-1",
            category_id="cat-income",
        )
        rule = desc_rule_service.create_rule(data)
        assert rule.id is not None
        assert rule.description_pattern == "direct deposit fidelity bro* (cash)"
        assert rule.account_id == "acct-1"
        assert rule.category_id == "cat-income"
        assert rule.rule_type == "description"
        assert rule.account_name == "Fidelity Cash"
        assert rule.category_name == "Income"

    def test_upsert_same_pattern_updates_category(self):
        data1 = DescriptionPatternRuleCreate(
            description_pattern="direct deposit *",
            account_id="acct-1",
            category_id="cat-income",
        )
        rule1 = desc_rule_service.create_rule(data1)

        data2 = DescriptionPatternRuleCreate(
            description_pattern="direct deposit *",
            account_id="acct-1",
            category_id="cat-transfer",
        )
        rule2 = desc_rule_service.create_rule(data2)

        # Same rule ID, updated category
        assert rule2.id == rule1.id
        assert rule2.category_id == "cat-transfer"

    def test_same_pattern_different_accounts(self):
        """Same pattern in different accounts creates separate rules."""
        data1 = DescriptionPatternRuleCreate(
            description_pattern="direct deposit *",
            account_id="acct-1",
            category_id="cat-income",
        )
        data2 = DescriptionPatternRuleCreate(
            description_pattern="direct deposit *",
            account_id="acct-2",
            category_id="cat-transfer",
        )
        rule1 = desc_rule_service.create_rule(data1)
        rule2 = desc_rule_service.create_rule(data2)

        assert rule1.id != rule2.id
        assert rule1.category_id == "cat-income"
        assert rule2.category_id == "cat-transfer"

    def test_pattern_normalized_to_lowercase(self):
        data = DescriptionPatternRuleCreate(
            description_pattern="DIRECT DEPOSIT *",
            account_id="acct-1",
            category_id="cat-income",
        )
        rule = desc_rule_service.create_rule(data)
        assert rule.description_pattern == "direct deposit *"


class TestDescRuleServiceMatching:
    def test_find_matching_rule_wildcard(self):
        desc_rule_service.create_rule(DescriptionPatternRuleCreate(
            description_pattern="direct deposit fidelity bro* (cash)",
            account_id="acct-1",
            category_id="cat-income",
        ))

        rule = desc_rule_service.find_matching_rule(
            "DIRECT DEPOSIT Fidelity Bro458529 (Cash)", "acct-1"
        )
        assert rule is not None
        assert rule.category_id == "cat-income"

    def test_case_insensitive_matching(self):
        desc_rule_service.create_rule(DescriptionPatternRuleCreate(
            description_pattern="direct deposit *",
            account_id="acct-1",
            category_id="cat-income",
        ))

        rule = desc_rule_service.find_matching_rule(
            "DIRECT DEPOSIT 12345", "acct-1"
        )
        assert rule is not None

    def test_account_scoping(self):
        """Rule for account A should NOT match transactions in account B."""
        desc_rule_service.create_rule(DescriptionPatternRuleCreate(
            description_pattern="direct deposit *",
            account_id="acct-1",
            category_id="cat-income",
        ))

        rule = desc_rule_service.find_matching_rule(
            "DIRECT DEPOSIT 12345", "acct-2"
        )
        assert rule is None

    def test_most_recent_rule_wins(self):
        """When multiple rules match, the most recently created wins."""
        desc_rule_service.create_rule(DescriptionPatternRuleCreate(
            description_pattern="direct deposit *",
            account_id="acct-1",
            category_id="cat-income",
        ))
        desc_rule_service.create_rule(DescriptionPatternRuleCreate(
            description_pattern="direct deposit *",
            account_id="acct-1",
            category_id="cat-transfer",
        ))

        rule = desc_rule_service.find_matching_rule(
            "DIRECT DEPOSIT 12345", "acct-1"
        )
        assert rule is not None
        assert rule.category_id == "cat-transfer"

    def test_no_match_returns_none(self):
        desc_rule_service.create_rule(DescriptionPatternRuleCreate(
            description_pattern="direct deposit *",
            account_id="acct-1",
            category_id="cat-income",
        ))

        rule = desc_rule_service.find_matching_rule(
            "SOME OTHER DESCRIPTION", "acct-1"
        )
        assert rule is None

    def test_empty_description_returns_none(self):
        rule = desc_rule_service.find_matching_rule("", "acct-1")
        assert rule is None

    def test_exact_match_no_wildcard(self):
        desc_rule_service.create_rule(DescriptionPatternRuleCreate(
            description_pattern="atm",
            account_id="acct-1",
            category_id="cat-income",
        ))

        rule = desc_rule_service.find_matching_rule("ATM", "acct-1")
        assert rule is not None


class TestDescRuleServiceCRUD:
    def test_delete_rule(self):
        rule = desc_rule_service.create_rule(DescriptionPatternRuleCreate(
            description_pattern="test pattern *",
            account_id="acct-1",
            category_id="cat-income",
        ))

        assert desc_rule_service.delete_rule(rule.id) is True
        assert desc_rule_service.get_by_id(rule.id) is None

    def test_delete_nonexistent_returns_false(self):
        assert desc_rule_service.delete_rule("nonexistent-id") is False

    def test_get_by_id_missing(self):
        assert desc_rule_service.get_by_id("nonexistent-id") is None

    def test_get_all_rules_with_account_filter(self):
        desc_rule_service.create_rule(DescriptionPatternRuleCreate(
            description_pattern="pattern a *",
            account_id="acct-1",
            category_id="cat-income",
        ))
        desc_rule_service.create_rule(DescriptionPatternRuleCreate(
            description_pattern="pattern b *",
            account_id="acct-2",
            category_id="cat-transfer",
        ))

        rules = desc_rule_service.get_all_rules(account_id="acct-1")
        assert len(rules) == 1
        assert rules[0].account_id == "acct-1"

    def test_count_rules(self):
        desc_rule_service.create_rule(DescriptionPatternRuleCreate(
            description_pattern="pattern a *",
            account_id="acct-1",
            category_id="cat-income",
        ))
        desc_rule_service.create_rule(DescriptionPatternRuleCreate(
            description_pattern="pattern b *",
            account_id="acct-2",
            category_id="cat-transfer",
        ))

        assert desc_rule_service.count_rules() == 2
        assert desc_rule_service.count_rules(account_id="acct-1") == 1
