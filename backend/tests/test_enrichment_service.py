"""
Tests for the AI-powered transaction enrichment service.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import date

from app.database import init_db, get_db
from app.services.enrichment_service import enrichment_service, _sanitize_for_ai
from app.models.enrichment import EnrichmentResult, EnrichmentTriggerRequest


@pytest.fixture(autouse=True)
def setup_db(tmp_path, monkeypatch):
    """Create a fresh DuckDB, initialize schema, and seed test data."""
    db_path = str(tmp_path / "test_enrichment.duckdb")
    monkeypatch.setattr("app.database.DATABASE_PATH", db_path)
    monkeypatch.setattr("app.database._connection", None)
    init_db()

    # DuckDB has a known bug where UPDATE on tables with PRIMARY KEY + FOREIGN KEY
    # constraints throws spurious "duplicate key" errors. Recreate the transactions
    # table without FK constraints so the enrichment UPDATE works.
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
        # Seed account
        conn.execute(
            "INSERT INTO accounts (id, name, type, is_asset) VALUES (?, ?, ?, ?)",
            ["acct-1", "Chase Checking", "Checking", True],
        )
        # Seed categories
        conn.execute(
            "INSERT INTO categories (id, name, group_name) VALUES (?, ?, ?)",
            ["cat-food", "Food & Drink", "Essential"],
        )
        conn.execute(
            "INSERT INTO categories (id, name, group_name) VALUES (?, ?, ?)",
            ["cat-income", "Income", "Income"],
        )
        # Seed transactions
        conn.execute(
            """INSERT INTO transactions (id, account_id, date, description,
               original_description, amount, category_id, reviewed, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
            ["tx-1", "acct-1", date(2026, 1, 15), "Starbucks", "SQ *STARBUCKS #1234", -450, "cat-food", False],
        )
        conn.execute(
            """INSERT INTO transactions (id, account_id, date, description,
               original_description, amount, category_id, reviewed, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
            ["tx-2", "acct-1", date(2026, 1, 14), "Netflix", "NETFLIX.COM", -1599, None, False],
        )
        conn.execute(
            """INSERT INTO transactions (id, account_id, date, description,
               original_description, amount, category_id, reviewed, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
            ["tx-3", "acct-1", date(2026, 1, 13), "Payroll", "DIRECT DEP ACME CORP", 500000, "cat-income", False],
        )

    yield

    import app.database
    if app.database._connection:
        app.database._connection.close()
        app.database._connection = None


class TestSanitizeForAI:
    def test_removes_card_numbers(self):
        result = _sanitize_for_ai("Payment 4111111111111111 received")
        assert "4111111111111111" not in result
        assert "[CARD]" in result

    def test_empty_string(self):
        assert _sanitize_for_ai("") == ""

    def test_no_sensitive_data(self):
        assert _sanitize_for_ai("STARBUCKS #1234") == "STARBUCKS #1234"


class TestGetUnenrichedTransactions:
    def test_returns_all_unenriched(self):
        txns = enrichment_service.get_unenriched_transactions()
        assert len(txns) == 3
        ids = {t["id"] for t in txns}
        assert ids == {"tx-1", "tx-2", "tx-3"}

    def test_returns_specific_ids(self):
        txns = enrichment_service.get_unenriched_transactions(
            transaction_ids=["tx-1", "tx-2"]
        )
        assert len(txns) == 2
        ids = {t["id"] for t in txns}
        assert ids == {"tx-1", "tx-2"}

    def test_respects_limit(self):
        txns = enrichment_service.get_unenriched_transactions(limit=1)
        assert len(txns) == 1

    def test_excludes_already_enriched(self):
        # Mark tx-1 as enriched
        with get_db() as conn:
            conn.execute(
                "UPDATE transactions SET enrichment_source = 'ai' WHERE id = 'tx-1'"
            )
        txns = enrichment_service.get_unenriched_transactions()
        ids = {t["id"] for t in txns}
        assert "tx-1" not in ids
        assert len(txns) == 2

    def test_includes_category_name(self):
        txns = enrichment_service.get_unenriched_transactions(
            transaction_ids=["tx-1"]
        )
        assert txns[0]["category_name"] == "Food & Drink"

    def test_null_category_name_for_uncategorized(self):
        txns = enrichment_service.get_unenriched_transactions(
            transaction_ids=["tx-2"]
        )
        assert txns[0]["category_name"] is None


class TestBuildEnrichmentPrompt:
    def test_prompt_contains_transaction_data(self):
        txns = [
            {
                "id": "tx-1",
                "description": "Starbucks",
                "original_description": "SQ *STARBUCKS #1234",
                "normalized_merchant": None,
                "amount": -450,
                "category_name": "Food & Drink",
            }
        ]
        prompt = enrichment_service.build_enrichment_prompt(txns)
        assert "tx-1" in prompt
        assert "SQ *STARBUCKS #1234" in prompt
        assert "normalized_merchant" in prompt
        assert "subcategory" in prompt
        assert "is_discretionary" in prompt

    def test_prompt_sanitizes_sensitive_data(self):
        txns = [
            {
                "id": "tx-1",
                "description": "Payment",
                "original_description": "PAYMENT 4111111111111111",
                "normalized_merchant": None,
                "amount": -1000,
                "category_name": None,
            }
        ]
        prompt = enrichment_service.build_enrichment_prompt(txns)
        assert "4111111111111111" not in prompt
        assert "[CARD]" in prompt


class TestApplyEnrichmentResults:
    def test_applies_results_to_db(self):
        results = [
            EnrichmentResult(
                transaction_id="tx-1",
                normalized_merchant="Starbucks",
                subcategory="Coffee Shop",
                is_discretionary=True,
            ),
        ]
        count = enrichment_service.apply_enrichment_results(results)
        assert count == 1

        # Verify DB
        with get_db() as conn:
            row = conn.execute(
                "SELECT normalized_merchant, subcategory, is_discretionary, enrichment_source FROM transactions WHERE id = 'tx-1'"
            ).fetchone()

        assert row[0] == "Starbucks"
        assert row[1] == "Coffee Shop"
        assert row[2] is True
        assert row[3] == "ai"

    def test_preserves_existing_merchant_when_null(self):
        # First set a normalized_merchant
        with get_db() as conn:
            conn.execute(
                "UPDATE transactions SET normalized_merchant = 'Original' WHERE id = 'tx-1'"
            )

        # Apply enrichment with null normalized_merchant
        results = [
            EnrichmentResult(
                transaction_id="tx-1",
                normalized_merchant=None,
                subcategory="Coffee Shop",
                is_discretionary=True,
            ),
        ]
        enrichment_service.apply_enrichment_results(results)

        with get_db() as conn:
            row = conn.execute(
                "SELECT normalized_merchant FROM transactions WHERE id = 'tx-1'"
            ).fetchone()
        assert row[0] == "Original"

    def test_multiple_results(self):
        results = [
            EnrichmentResult(
                transaction_id="tx-1",
                normalized_merchant="Starbucks",
                subcategory="Coffee Shop",
                is_discretionary=True,
            ),
            EnrichmentResult(
                transaction_id="tx-2",
                normalized_merchant="Netflix",
                subcategory="Streaming Service",
                is_discretionary=True,
            ),
            EnrichmentResult(
                transaction_id="tx-3",
                normalized_merchant="Acme Corp",
                subcategory="Payroll",
                is_discretionary=False,
            ),
        ]
        count = enrichment_service.apply_enrichment_results(results)
        assert count == 3


class TestEnrichBatch:
    @patch("app.services.enrichment_service.invoke_and_parse")
    def test_returns_results_on_success(self, mock_invoke):
        mock_invoke.return_value = [
            {
                "transaction_id": "tx-1",
                "normalized_merchant": "Starbucks",
                "subcategory": "Coffee Shop",
                "is_discretionary": True,
            },
        ]
        txns = enrichment_service.get_unenriched_transactions(transaction_ids=["tx-1"])
        results = enrichment_service.enrich_batch(txns)
        assert len(results) == 1
        assert results[0].transaction_id == "tx-1"
        assert results[0].normalized_merchant == "Starbucks"
        assert results[0].subcategory == "Coffee Shop"
        assert results[0].is_discretionary is True

    @patch("app.services.enrichment_service.invoke_and_parse")
    def test_returns_empty_on_ai_error(self, mock_invoke):
        from app.services.gemini_client import AIClientError
        mock_invoke.side_effect = AIClientError("API error")
        txns = enrichment_service.get_unenriched_transactions(transaction_ids=["tx-1"])
        results = enrichment_service.enrich_batch(txns)
        assert results == []

    def test_empty_transactions_returns_empty(self):
        results = enrichment_service.enrich_batch([])
        assert results == []

    @patch("app.services.enrichment_service.invoke_and_parse")
    def test_skips_items_without_transaction_id(self, mock_invoke):
        mock_invoke.return_value = [
            {"normalized_merchant": "Starbucks", "subcategory": "Coffee", "is_discretionary": True},
        ]
        txns = enrichment_service.get_unenriched_transactions(transaction_ids=["tx-1"])
        results = enrichment_service.enrich_batch(txns)
        assert results == []


class TestTriggerEnrichment:
    @patch("app.services.enrichment_service.invoke_and_parse")
    def test_end_to_end(self, mock_invoke):
        mock_invoke.return_value = [
            {"transaction_id": "tx-1", "normalized_merchant": "Starbucks", "subcategory": "Coffee Shop", "is_discretionary": True},
            {"transaction_id": "tx-2", "normalized_merchant": "Netflix", "subcategory": "Streaming", "is_discretionary": True},
            {"transaction_id": "tx-3", "normalized_merchant": "Acme Corp", "subcategory": "Payroll", "is_discretionary": False},
        ]

        response = enrichment_service.trigger_enrichment()
        assert response.total_count == 3
        assert response.success_count == 3
        assert response.failure_count == 0
        assert response.duration_ms >= 0

        # Verify DB was updated
        with get_db() as conn:
            row = conn.execute(
                "SELECT enrichment_source, subcategory FROM transactions WHERE id = 'tx-1'"
            ).fetchone()
        assert row[0] == "ai"
        assert row[1] == "Coffee Shop"

    @patch("app.services.enrichment_service.invoke_and_parse")
    def test_with_specific_ids(self, mock_invoke):
        mock_invoke.return_value = [
            {"transaction_id": "tx-1", "normalized_merchant": "Starbucks", "subcategory": "Coffee", "is_discretionary": True},
        ]

        request = EnrichmentTriggerRequest(transaction_ids=["tx-1"])
        response = enrichment_service.trigger_enrichment(request)
        assert response.total_count == 1
        assert response.success_count == 1

    def test_no_unenriched_transactions(self):
        # Mark all as enriched
        with get_db() as conn:
            conn.execute("UPDATE transactions SET enrichment_source = 'ai'")

        response = enrichment_service.trigger_enrichment()
        assert response.total_count == 0
        assert response.success_count == 0

    @patch("app.services.enrichment_service.invoke_and_parse")
    def test_idempotency(self, mock_invoke):
        """Re-enriching already-enriched transactions should skip them."""
        mock_invoke.return_value = [
            {"transaction_id": "tx-1", "normalized_merchant": "Starbucks", "subcategory": "Coffee", "is_discretionary": True},
        ]

        # First enrichment
        request = EnrichmentTriggerRequest(transaction_ids=["tx-1"])
        response1 = enrichment_service.trigger_enrichment(request)
        assert response1.success_count == 1

        # Second enrichment of same transaction — should find 0 unenriched
        response2 = enrichment_service.trigger_enrichment(request)
        assert response2.total_count == 0
        assert response2.success_count == 0
