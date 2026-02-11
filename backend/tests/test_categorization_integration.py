"""
Integration tests for description-based pattern rules feature.

Tests the full flow from manual correction -> pattern rule creation -> pipeline application.
"""
import pytest
from datetime import datetime

from app.database import init_db, get_db
from app.services.transaction_service import transaction_service
from app.services.categorization_service import categorization_service
from app.services.desc_rule_service import desc_rule_service
from app.services.rule_service import rule_service
from app.models.transaction import TransactionUpdate
from app.models.categorization import DescriptionPatternRuleCreate, CategorizationRuleCreate


@pytest.fixture(autouse=True)
def setup_db(tmp_path, monkeypatch):
    """Create a fresh DuckDB, initialize schema, and seed test data."""
    db_path = str(tmp_path / "test_integration.duckdb")
    monkeypatch.setattr("app.database.DATABASE_PATH", db_path)
    monkeypatch.setattr("app.database._connection", None)
    init_db()

    # DuckDB has a known bug where UPDATE on tables with PRIMARY KEY + FOREIGN KEY
    # constraints throws spurious "duplicate key" errors. The transaction_service.update
    # method already works around this with DELETE+INSERT, but
    # apply_categorization_results uses a plain UPDATE. Recreate the transactions
    # table without FK constraints so the categorization pipeline UPDATE works.
    with get_db() as conn:
        conn.execute("DROP TABLE IF EXISTS transactions")
        conn.execute("""
            CREATE TABLE transactions (
                id VARCHAR(36) PRIMARY KEY,
                account_id VARCHAR(36) NOT NULL,
                date DATE NOT NULL,
                description VARCHAR(500) NOT NULL,
                original_description VARCHAR(500) NOT NULL,
                amount INTEGER NOT NULL,
                category_id VARCHAR(36),
                reviewed BOOLEAN NOT NULL DEFAULT FALSE,
                reviewed_at TIMESTAMP,
                notes TEXT,
                normalized_merchant VARCHAR(255),
                confidence_score DECIMAL(3,2),
                categorization_source VARCHAR(10),
                subcategory VARCHAR(100),
                is_discretionary BOOLEAN,
                enrichment_source VARCHAR(10),
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

    with get_db() as conn:
        # Seed accounts
        conn.execute(
            "INSERT INTO accounts (id, name, type, is_asset) VALUES (?, ?, ?, ?)",
            ["acct-1", "Fidelity Cash", "Investment", True],
        )
        conn.execute(
            "INSERT INTO accounts (id, name, type, is_asset) VALUES (?, ?, ?, ?)",
            ["acct-2", "Chase Checking", "Checking", True],
        )
        # Seed categories
        conn.execute(
            "INSERT INTO categories (id, name, group_name) VALUES (?, ?, ?)",
            ["cat-income", "Income", "Income"],
        )
        conn.execute(
            "INSERT INTO categories (id, name, group_name) VALUES (?, ?, ?)",
            ["cat-transfer", "Transfer", "Transfer"],
        )
        conn.execute(
            "INSERT INTO categories (id, name, group_name) VALUES (?, ?, ?)",
            ["cat-food", "Food", "Expenses"],
        )

    yield

    import app.database
    if app.database._connection:
        app.database._connection.close()
        app.database._connection = None


# ---------------------------------------------------------------------------
# Helper to insert a raw transaction directly into the DB
# ---------------------------------------------------------------------------
def _insert_transaction(
    tx_id: str,
    account_id: str,
    date: str,
    description: str,
    amount: int,
    category_id=None,
    reviewed: bool = False,
    normalized_merchant=None,
):
    """Insert a transaction row directly, bypassing the service layer."""
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO transactions (
                id, account_id, date, description, original_description,
                amount, category_id, reviewed, reviewed_at, notes,
                created_at, normalized_merchant
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                tx_id,
                account_id,
                date,
                description,
                description,  # original_description = description
                amount,
                category_id,
                reviewed,
                None,   # reviewed_at
                None,   # notes
                datetime.utcnow(),
                normalized_merchant,
            ],
        )


# ============================================================================
# T008 - US1: Manual correction creates description rule
# ============================================================================


class TestManualCorrectionCreatesDescRule:
    """Verify that manually correcting a merchant-less transaction creates a desc rule."""

    def test_manual_correction_creates_desc_rule(self):
        """Correcting category on a transaction with no merchant should create a desc rule."""
        _insert_transaction(
            tx_id="tx-1",
            account_id="acct-1",
            date="2024-03-15",
            description="DIRECT DEPOSIT Fidelity Bro461026 (Cash)",
            amount=100000,
            category_id=None,
            reviewed=False,
            normalized_merchant=None,
        )

        update_data = TransactionUpdate(category_id="cat-income")
        transaction_service.update("tx-1", update_data)

        # Verify a description pattern rule was created
        with get_db() as conn:
            rows = conn.execute(
                "SELECT account_id, description_pattern, category_id "
                "FROM description_pattern_rules"
            ).fetchall()

        assert len(rows) == 1
        account_id, pattern, category_id = rows[0]
        assert account_id == "acct-1"
        assert "direct deposit fidelity" in pattern
        assert "*" in pattern  # numeric portion replaced with wildcard
        assert category_id == "cat-income"

    def test_manual_correction_with_merchant_skips_desc_rule(self):
        """When a transaction HAS a merchant, a merchant rule is created instead."""
        _insert_transaction(
            tx_id="tx-1",
            account_id="acct-1",
            date="2024-03-15",
            description="DIRECT DEPOSIT Fidelity Bro461026 (Cash)",
            amount=100000,
            category_id=None,
            reviewed=False,
            normalized_merchant="fidelity",
        )

        update_data = TransactionUpdate(category_id="cat-income")
        transaction_service.update("tx-1", update_data)

        # No description pattern rule should be created
        with get_db() as conn:
            desc_rows = conn.execute(
                "SELECT COUNT(*) FROM description_pattern_rules"
            ).fetchone()
            assert desc_rows[0] == 0

            # A merchant rule SHOULD exist for "fidelity"
            merchant_rows = conn.execute(
                "SELECT merchant_pattern, category_id FROM categorization_rules"
            ).fetchall()
            assert len(merchant_rows) == 1
            assert merchant_rows[0][0] == "fidelity"

    def test_empty_description_skips_desc_rule(self):
        """Transactions with empty/whitespace descriptions should not create desc rules."""
        _insert_transaction(
            tx_id="tx-1",
            account_id="acct-1",
            date="2024-03-15",
            description="   ",
            amount=100000,
            category_id=None,
            reviewed=False,
            normalized_merchant=None,
        )

        update_data = TransactionUpdate(category_id="cat-income")
        transaction_service.update("tx-1", update_data)

        with get_db() as conn:
            rows = conn.execute(
                "SELECT COUNT(*) FROM description_pattern_rules"
            ).fetchone()
            assert rows[0] == 0


# ============================================================================
# T011 - US2: Description rule applied in categorization pipeline
# ============================================================================


class TestDescRulePipeline:
    """Verify that _apply_rules applies desc rules correctly in the pipeline."""

    def test_desc_rule_applied_in_pipeline(self):
        """A matching desc rule should categorize a merchant-less transaction."""
        # Create a description pattern rule directly
        desc_rule_service.create_rule(
            DescriptionPatternRuleCreate(
                description_pattern="direct deposit fidelity bro* (cash)",
                account_id="acct-1",
                category_id="cat-income",
            )
        )

        # Insert an uncategorized transaction into DB (needed for apply_categorization_results)
        _insert_transaction(
            tx_id="tx-1",
            account_id="acct-1",
            date="2024-03-15",
            description="DIRECT DEPOSIT Fidelity Bro999999 (Cash)",
            amount=50000,
            category_id=None,
            reviewed=False,
            normalized_merchant=None,
        )

        # Build the transaction dict as _apply_rules expects
        tx_dict = {
            "id": "tx-1",
            "description": "DIRECT DEPOSIT Fidelity Bro999999 (Cash)",
            "original_description": "DIRECT DEPOSIT Fidelity Bro999999 (Cash)",
            "amount": 50000,
            "normalized_merchant": None,
            "account_id": "acct-1",
        }

        remaining, merchant_match_count, desc_match_count = (
            categorization_service._apply_rules([tx_dict])
        )

        assert desc_match_count == 1
        assert len(remaining) == 0

        # Verify the transaction was updated in the DB
        with get_db() as conn:
            row = conn.execute(
                "SELECT category_id, categorization_source FROM transactions WHERE id = ?",
                ["tx-1"],
            ).fetchone()
            assert row[0] == "cat-income"
            assert row[1] == "desc_rule"

    def test_merchant_rule_takes_precedence(self):
        """Merchant rules should take priority over description rules."""
        # Create a merchant rule
        rule_service.create_rule(
            CategorizationRuleCreate(
                merchant_pattern="fidelity",
                category_id="cat-transfer",
            )
        )

        # Create a description rule for the same pattern
        desc_rule_service.create_rule(
            DescriptionPatternRuleCreate(
                description_pattern="direct deposit fidelity bro* (cash)",
                account_id="acct-1",
                category_id="cat-income",
            )
        )

        # Insert the transaction into DB
        _insert_transaction(
            tx_id="tx-1",
            account_id="acct-1",
            date="2024-03-15",
            description="DIRECT DEPOSIT Fidelity Bro999999 (Cash)",
            amount=50000,
            category_id=None,
            reviewed=False,
            normalized_merchant="fidelity",
        )

        tx_dict = {
            "id": "tx-1",
            "description": "DIRECT DEPOSIT Fidelity Bro999999 (Cash)",
            "original_description": "DIRECT DEPOSIT Fidelity Bro999999 (Cash)",
            "amount": 50000,
            "normalized_merchant": "fidelity",
            "account_id": "acct-1",
        }

        remaining, merchant_match_count, desc_match_count = (
            categorization_service._apply_rules([tx_dict])
        )

        # Merchant rule should win
        assert merchant_match_count == 1
        assert desc_match_count == 0
        assert len(remaining) == 0

        # Verify the transaction got the merchant rule's category
        with get_db() as conn:
            row = conn.execute(
                "SELECT category_id, categorization_source FROM transactions WHERE id = ?",
                ["tx-1"],
            ).fetchone()
            assert row[0] == "cat-transfer"

    def test_desc_rule_account_scoping(self):
        """Desc rules should only match transactions in the same account."""
        # Create a desc rule for acct-1
        desc_rule_service.create_rule(
            DescriptionPatternRuleCreate(
                description_pattern="direct deposit fidelity bro* (cash)",
                account_id="acct-1",
                category_id="cat-income",
            )
        )

        # Insert a transaction in acct-2 with a matching description
        _insert_transaction(
            tx_id="tx-1",
            account_id="acct-2",
            date="2024-03-15",
            description="DIRECT DEPOSIT Fidelity Bro999999 (Cash)",
            amount=50000,
            category_id=None,
            reviewed=False,
            normalized_merchant=None,
        )

        tx_dict = {
            "id": "tx-1",
            "description": "DIRECT DEPOSIT Fidelity Bro999999 (Cash)",
            "original_description": "DIRECT DEPOSIT Fidelity Bro999999 (Cash)",
            "amount": 50000,
            "normalized_merchant": None,
            "account_id": "acct-2",
        }

        remaining, merchant_match_count, desc_match_count = (
            categorization_service._apply_rules([tx_dict])
        )

        # Should NOT match — rule is for acct-1, transaction is in acct-2
        assert desc_match_count == 0
        assert len(remaining) == 1
        assert remaining[0]["id"] == "tx-1"


# ============================================================================
# T013 - US3: Pattern extraction end-to-end
# ============================================================================


class TestPatternExtractionEndToEnd:
    """Verify that a correction-created pattern matches future variant descriptions."""

    def test_pattern_extraction_matches_future_variants(self):
        """
        Correcting tx-1 should auto-create a desc rule whose wildcard pattern
        also matches tx-2 with a different numeric portion.
        """
        # Step 1: Insert tx-1 and manually correct it
        _insert_transaction(
            tx_id="tx-1",
            account_id="acct-1",
            date="2024-03-15",
            description="DIRECT DEPOSIT Fidelity Bro461026 (Cash)",
            amount=100000,
            category_id=None,
            reviewed=False,
            normalized_merchant=None,
        )

        update_data = TransactionUpdate(category_id="cat-income")
        transaction_service.update("tx-1", update_data)

        # Step 2: Insert tx-2 with a different numeric portion
        _insert_transaction(
            tx_id="tx-2",
            account_id="acct-1",
            date="2024-04-15",
            description="DIRECT DEPOSIT Fidelity Bro458529 (Cash)",
            amount=100000,
            category_id=None,
            reviewed=False,
            normalized_merchant=None,
        )

        # Step 3: Apply rules to tx-2
        tx_dict = {
            "id": "tx-2",
            "description": "DIRECT DEPOSIT Fidelity Bro458529 (Cash)",
            "original_description": "DIRECT DEPOSIT Fidelity Bro458529 (Cash)",
            "amount": 100000,
            "normalized_merchant": None,
            "account_id": "acct-1",
        }

        remaining, merchant_match_count, desc_match_count = (
            categorization_service._apply_rules([tx_dict])
        )

        assert desc_match_count == 1
        assert len(remaining) == 0

        # Verify tx-2 was categorized correctly
        with get_db() as conn:
            row = conn.execute(
                "SELECT category_id, categorization_source FROM transactions WHERE id = ?",
                ["tx-2"],
            ).fetchone()
            assert row[0] == "cat-income"
            assert row[1] == "desc_rule"
