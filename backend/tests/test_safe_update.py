"""Tests for safe_update_transaction() helper in database.py."""
import uuid
from datetime import date, datetime

import duckdb
import pytest

from app.database import TRANSACTION_COLUMNS, safe_update_transaction


@pytest.fixture()
def conn():
    """Create an in-memory DuckDB with the full transactions schema + all 7 indexes."""
    c = duckdb.connect(":memory:")

    # Parent tables needed for FK constraints
    c.execute("""
        CREATE TABLE accounts (
            id VARCHAR(36) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            type VARCHAR(20) NOT NULL,
            institution VARCHAR(200),
            is_asset BOOLEAN NOT NULL,
            csv_column_mapping JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE categories (
            id VARCHAR(36) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            emoji VARCHAR(10),
            parent_id VARCHAR(36),
            group_name VARCHAR(20) NOT NULL,
            budget_amount INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Transactions table matching production schema
    c.execute("""
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
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES accounts(id),
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    """)

    # All 6 secondary indexes (matching database.py)
    c.execute("CREATE INDEX idx_transactions_account_date ON transactions(account_id, date DESC)")
    c.execute("CREATE INDEX idx_transactions_category ON transactions(category_id)")
    c.execute("CREATE INDEX idx_transactions_reviewed ON transactions(reviewed)")
    c.execute("CREATE INDEX idx_transactions_normalized_merchant ON transactions(normalized_merchant)")
    c.execute("CREATE INDEX idx_transactions_categorization_source ON transactions(categorization_source)")
    c.execute("CREATE INDEX idx_transactions_enrichment_source ON transactions(enrichment_source)")

    # Seed parent data
    c.execute("INSERT INTO accounts VALUES (?, ?, ?, ?, ?, NULL, CURRENT_TIMESTAMP)",
              ["acct-1", "Checking", "checking", "Test Bank", True])
    c.execute("INSERT INTO categories VALUES (?, ?, ?, NULL, ?, NULL, CURRENT_TIMESTAMP)",
              ["cat-1", "Groceries", None, "essentials"])

    yield c
    c.close()


def _insert_transaction(conn, tx_id=None, **overrides):
    """Insert a test transaction and return the id."""
    tx_id = tx_id or str(uuid.uuid4())
    defaults = {
        "id": tx_id,
        "account_id": "acct-1",
        "date": date(2026, 1, 15),
        "description": "Test Store",
        "original_description": "TEST STORE #123",
        "amount": -5000,
        "category_id": "cat-1",
        "reviewed": False,
        "reviewed_at": None,
        "notes": None,
        "normalized_merchant": None,
        "confidence_score": None,
        "categorization_source": None,
        "subcategory": None,
        "is_discretionary": None,
        "enrichment_source": None,
        "created_at": datetime(2026, 1, 15, 12, 0, 0),
    }
    defaults.update(overrides)
    cols = ", ".join(TRANSACTION_COLUMNS)
    placeholders = ", ".join(["?"] * len(TRANSACTION_COLUMNS))
    conn.execute(
        f"INSERT INTO transactions ({cols}) VALUES ({placeholders})",
        [defaults[c] for c in TRANSACTION_COLUMNS],
    )
    return tx_id


def _fetch_row(conn, tx_id):
    """Fetch a transaction row as a dict."""
    cols_csv = ", ".join(TRANSACTION_COLUMNS)
    row = conn.execute(
        f"SELECT {cols_csv} FROM transactions WHERE id = ?", [tx_id]
    ).fetchone()
    if row is None:
        return None
    return dict(zip(TRANSACTION_COLUMNS, row))


class TestSafeUpdateTransaction:
    def test_updates_enrichment_columns(self, conn):
        tx_id = _insert_transaction(conn)

        result = safe_update_transaction(conn, tx_id, {
            "subcategory": "Coffee Shop",
            "is_discretionary": True,
            "enrichment_source": "ai",
            "normalized_merchant": "Starbucks",
        })

        assert result is True
        row = _fetch_row(conn, tx_id)
        assert row["subcategory"] == "Coffee Shop"
        assert row["is_discretionary"] is True
        assert row["enrichment_source"] == "ai"
        assert row["normalized_merchant"] == "Starbucks"

    def test_preserves_non_updated_columns(self, conn):
        tx_id = _insert_transaction(conn, notes="original note")

        safe_update_transaction(conn, tx_id, {"subcategory": "Fast Food"})

        row = _fetch_row(conn, tx_id)
        assert row["notes"] == "original note"
        assert row["description"] == "Test Store"
        assert row["amount"] == -5000
        assert row["account_id"] == "acct-1"
        assert row["category_id"] == "cat-1"

    def test_returns_false_for_missing_transaction(self, conn):
        result = safe_update_transaction(conn, "nonexistent-id", {"subcategory": "X"})
        assert result is False

    def test_multiple_updates_on_same_row(self, conn):
        tx_id = _insert_transaction(conn)

        safe_update_transaction(conn, tx_id, {"subcategory": "Coffee Shop"})
        safe_update_transaction(conn, tx_id, {"is_discretionary": True})
        safe_update_transaction(conn, tx_id, {"enrichment_source": "ai"})

        row = _fetch_row(conn, tx_id)
        assert row["subcategory"] == "Coffee Shop"
        assert row["is_discretionary"] is True
        assert row["enrichment_source"] == "ai"

    def test_updates_categorization_columns(self, conn):
        tx_id = _insert_transaction(conn)

        result = safe_update_transaction(conn, tx_id, {
            "category_id": "cat-1",
            "confidence_score": 0.95,
            "categorization_source": "ai",
        })

        assert result is True
        row = _fetch_row(conn, tx_id)
        assert row["category_id"] == "cat-1"
        assert float(row["confidence_score"]) == pytest.approx(0.95)
        assert row["categorization_source"] == "ai"

    def test_updates_review_columns(self, conn):
        tx_id = _insert_transaction(conn)
        reviewed_at = datetime(2026, 2, 10, 15, 30, 0)

        result = safe_update_transaction(conn, tx_id, {
            "reviewed": True,
            "reviewed_at": reviewed_at,
        })

        assert result is True
        row = _fetch_row(conn, tx_id)
        assert row["reviewed"] is True
        assert row["reviewed_at"] == reviewed_at
