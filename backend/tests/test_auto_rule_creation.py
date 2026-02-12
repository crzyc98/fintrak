"""
Integration tests for auto-rule creation from AI classification results.

Tests that high-confidence AI results automatically create categorization rules,
while low-confidence results, duplicates, and generic patterns are skipped.
"""
import uuid

import pytest

import app.database as db_module
from app.database import get_db, init_db
from app.models.categorization import UnifiedAIResult
from app.services.categorization_service import CategorizationService
from app.services.rule_service import rule_service
from app.services.desc_rule_service import desc_rule_service
from app.models.categorization import CategorizationRuleCreate, DescriptionPatternRuleCreate


# ── helpers ──────────────────────────────────────────────────────────────

def _insert_account(account_id: str, name: str = "Test Checking") -> str:
    with get_db() as conn:
        conn.execute(
            "INSERT INTO accounts (id, name, type, is_asset) VALUES (?, ?, ?, ?)",
            [account_id, name, "checking", True],
        )
    return account_id


def _insert_category(category_id: str, name: str, group_name: str = "Lifestyle") -> str:
    with get_db() as conn:
        conn.execute(
            "INSERT INTO categories (id, name, group_name) VALUES (?, ?, ?)",
            [category_id, name, group_name],
        )
    return category_id


def _insert_transaction(
    tx_id: str,
    account_id: str,
    description: str = "Test transaction",
    amount: int = -500,
    normalized_merchant: str | None = None,
    category_id: str | None = None,
) -> str:
    with get_db() as conn:
        conn.execute(
            """INSERT INTO transactions
               (id, account_id, date, description, original_description, amount,
                normalized_merchant, category_id, reviewed)
               VALUES (?, ?, '2026-01-15', ?, ?, ?, ?, ?, FALSE)""",
            [tx_id, account_id, description, description, amount,
             normalized_merchant, category_id],
        )
    return tx_id


# ── fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture
def service():
    return CategorizationService()


@pytest.fixture
def account_id():
    return _insert_account(str(uuid.uuid4()))


@pytest.fixture
def category_id():
    return _insert_category(str(uuid.uuid4()), "Dining Out")


@pytest.fixture
def category_id_b():
    return _insert_category(str(uuid.uuid4()), "Groceries", "Essential")


# ── T020: High-confidence AI result creates merchant rule ────────────────

class TestHighConfidenceCreatesRule:
    def test_merchant_rule_created(self, service, account_id, category_id):
        tx_id = _insert_transaction(
            str(uuid.uuid4()), account_id,
            description="STARBUCKS #1234",
            normalized_merchant="Starbucks",
        )

        transactions = [
            {"id": tx_id, "description": "STARBUCKS #1234",
             "account_id": account_id, "category_id": None,
             "normalized_merchant": "Starbucks"},
        ]
        results = [
            UnifiedAIResult(
                transaction_id=tx_id,
                category_name="Dining Out",
                category_group="Lifestyle",
                normalized_merchant="Starbucks",
                confidence=0.95,
            ),
        ]

        service.apply_unified_results(results, transactions)

        rule = rule_service.find_matching_rule("Starbucks")
        assert rule is not None
        assert rule.category_id == category_id
        assert rule.source == "ai"


# ── T021: Low-confidence AI result does NOT create rule ──────────────────

class TestLowConfidenceNoRule:
    def test_no_rule_below_threshold(self, service, account_id, category_id):
        tx_id = _insert_transaction(
            str(uuid.uuid4()), account_id,
            description="UNKNOWN MERCHANT",
            normalized_merchant="Unknown Shop",
        )

        transactions = [
            {"id": tx_id, "description": "UNKNOWN MERCHANT",
             "account_id": account_id, "category_id": None,
             "normalized_merchant": "Unknown Shop"},
        ]
        results = [
            UnifiedAIResult(
                transaction_id=tx_id,
                category_name="Dining Out",
                category_group="Lifestyle",
                normalized_merchant="Unknown Shop",
                confidence=0.75,
            ),
        ]

        service.apply_unified_results(results, transactions)

        rule = rule_service.find_matching_rule("Unknown Shop")
        assert rule is None


# ── T022: Existing rule prevents duplicate creation ──────────────────────

class TestExistingRuleNoDuplicate:
    def test_no_duplicate_when_rule_exists(self, service, account_id, category_id):
        # Pre-create a manual rule
        rule_service.create_rule(CategorizationRuleCreate(
            merchant_pattern="starbucks",
            category_id=category_id,
            source="manual",
        ))

        tx_id = _insert_transaction(
            str(uuid.uuid4()), account_id,
            description="STARBUCKS COFFEE",
            normalized_merchant="Starbucks",
        )

        transactions = [
            {"id": tx_id, "description": "STARBUCKS COFFEE",
             "account_id": account_id, "category_id": None,
             "normalized_merchant": "Starbucks"},
        ]
        results = [
            UnifiedAIResult(
                transaction_id=tx_id,
                category_name="Dining Out",
                category_group="Lifestyle",
                normalized_merchant="Starbucks",
                confidence=0.95,
            ),
        ]

        service.apply_unified_results(results, transactions)

        # Should still be exactly 1 rule, the manual one
        all_rules = rule_service.get_all_rules()
        starbucks_rules = [r for r in all_rules if r.merchant_pattern == "starbucks"]
        assert len(starbucks_rules) == 1
        assert starbucks_rules[0].source == "manual"


# ── T023: Same merchant in batch uses highest confidence ─────────────────

class TestBatchDeduplication:
    def test_highest_confidence_wins(self, service, account_id, category_id, category_id_b):
        tx_id_1 = _insert_transaction(
            str(uuid.uuid4()), account_id,
            description="STARBUCKS #1",
            normalized_merchant="Starbucks",
        )
        tx_id_2 = _insert_transaction(
            str(uuid.uuid4()), account_id,
            description="STARBUCKS #2",
            normalized_merchant="Starbucks",
        )

        transactions = [
            {"id": tx_id_1, "description": "STARBUCKS #1",
             "account_id": account_id, "category_id": None,
             "normalized_merchant": "Starbucks"},
            {"id": tx_id_2, "description": "STARBUCKS #2",
             "account_id": account_id, "category_id": None,
             "normalized_merchant": "Starbucks"},
        ]
        results = [
            UnifiedAIResult(
                transaction_id=tx_id_1,
                category_name="Groceries",
                category_group="Essential",
                normalized_merchant="Starbucks",
                confidence=0.91,
            ),
            UnifiedAIResult(
                transaction_id=tx_id_2,
                category_name="Dining Out",
                category_group="Lifestyle",
                normalized_merchant="Starbucks",
                confidence=0.97,
            ),
        ]

        service.apply_unified_results(results, transactions)

        rule = rule_service.find_matching_rule("Starbucks")
        assert rule is not None
        # Should pick "Dining Out" (0.97 > 0.91)
        assert rule.category_id == category_id


# ── T024: Description pattern rule created when no merchant ──────────────

class TestDescriptionPatternRule:
    def test_desc_rule_created_no_merchant(self, service, account_id, category_id):
        tx_id = _insert_transaction(
            str(uuid.uuid4()), account_id,
            description="TRANSFER TO SAVINGS ACCOUNT",
        )

        transactions = [
            {"id": tx_id, "description": "TRANSFER TO SAVINGS ACCOUNT",
             "account_id": account_id, "category_id": None,
             "normalized_merchant": None},
        ]
        results = [
            UnifiedAIResult(
                transaction_id=tx_id,
                category_name="Dining Out",
                category_group="Lifestyle",
                normalized_merchant=None,
                confidence=0.92,
            ),
        ]

        service.apply_unified_results(results, transactions)

        rule = desc_rule_service.find_matching_rule(
            "TRANSFER TO SAVINGS ACCOUNT", account_id
        )
        assert rule is not None
        assert rule.source == "ai"


# ── T025: Generic/empty pattern skipped ──────────────────────────────────

class TestGenericPatternSkipped:
    def test_generic_pattern_not_created(self, service, account_id, category_id):
        """A description that reduces to just '*' should not create a rule."""
        tx_id = _insert_transaction(
            str(uuid.uuid4()), account_id,
            description="12345678",
        )

        transactions = [
            {"id": tx_id, "description": "12345678",
             "account_id": account_id, "category_id": None,
             "normalized_merchant": None},
        ]
        results = [
            UnifiedAIResult(
                transaction_id=tx_id,
                category_name="Dining Out",
                category_group="Lifestyle",
                normalized_merchant=None,
                confidence=0.95,
            ),
        ]

        service.apply_unified_results(results, transactions)

        all_desc_rules = desc_rule_service.get_all_rules(account_id=account_id)
        assert len(all_desc_rules) == 0

    def test_short_pattern_not_created(self, service, account_id, category_id):
        """A description that reduces to a very short pattern should not create a rule."""
        tx_id = _insert_transaction(
            str(uuid.uuid4()), account_id,
            description="AB 123456",
        )

        transactions = [
            {"id": tx_id, "description": "AB 123456",
             "account_id": account_id, "category_id": None,
             "normalized_merchant": None},
        ]
        results = [
            UnifiedAIResult(
                transaction_id=tx_id,
                category_name="Dining Out",
                category_group="Lifestyle",
                normalized_merchant=None,
                confidence=0.95,
            ),
        ]

        service.apply_unified_results(results, transactions)

        all_desc_rules = desc_rule_service.get_all_rules(account_id=account_id)
        assert len(all_desc_rules) == 0
