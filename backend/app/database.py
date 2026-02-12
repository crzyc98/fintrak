import os
import duckdb
import logging
from contextlib import contextmanager

DATABASE_PATH = os.getenv("DATABASE_PATH", "fintrak.duckdb")

_connection = None
logger = logging.getLogger(__name__)

# Canonical column list for the transactions table.
# Used by safe_update_transaction() to SELECT/INSERT full rows.
TRANSACTION_COLUMNS = [
    "id", "account_id", "date", "description", "original_description",
    "amount", "category_id", "reviewed", "reviewed_at", "notes",
    "normalized_merchant", "confidence_score", "categorization_source",
    "subcategory", "is_discretionary", "enrichment_source",
    "created_at",
]


def get_connection() -> duckdb.DuckDBPyConnection:
    global _connection
    if _connection is None:
        _connection = duckdb.connect(DATABASE_PATH)
    return _connection


@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
    finally:
        pass


def checkpoint():
    """Flush WAL to main database file. Call after bulk operations."""
    conn = get_connection()
    conn.execute("CHECKPOINT")
    logger.info("Database checkpoint completed")


def close_connection():
    """Properly close the database connection with a final checkpoint."""
    global _connection
    if _connection is not None:
        try:
            _connection.execute("CHECKPOINT")
            logger.info("Final checkpoint completed")
        except Exception as e:
            logger.warning(f"Checkpoint failed during shutdown: {e}")
        finally:
            try:
                _connection.close()
                logger.info("Database connection closed")
            except Exception as e:
                logger.warning(f"Error closing connection: {e}")
            _connection = None


def safe_update_transaction(conn, transaction_id: str, updates: dict) -> bool:
    """
    Safely update a transaction row using DELETE+INSERT to work around a
    DuckDB ART index limitation.

    DuckDB implements UPDATE as DELETE+INSERT internally.  On tables with
    multiple ART indexes (transactions has 7), this can trigger spurious
    "Duplicate key violates primary key constraint" errors.  The explicit
    DELETE followed by INSERT avoids the issue.

    Args:
        conn: Active DuckDB connection.
        transaction_id: The UUID of the transaction to update.
        updates: Dict mapping column names to new values.

    Returns:
        True if the row was updated, False if the transaction was not found.
    """
    cols_csv = ", ".join(TRANSACTION_COLUMNS)
    row = conn.execute(
        f"SELECT {cols_csv} FROM transactions WHERE id = ?",
        [transaction_id],
    ).fetchone()

    if row is None:
        return False

    row_dict = dict(zip(TRANSACTION_COLUMNS, row))
    row_dict.update(updates)

    conn.execute("DELETE FROM transactions WHERE id = ?", [transaction_id])
    conn.execute(
        f"INSERT INTO transactions ({cols_csv}) "
        f"VALUES ({', '.join(['?'] * len(TRANSACTION_COLUMNS))})",
        [row_dict[c] for c in TRANSACTION_COLUMNS],
    )
    return True


def init_db():
    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id VARCHAR(36) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            type VARCHAR(20) NOT NULL,
            institution VARCHAR(200),
            is_asset BOOLEAN NOT NULL,
            csv_column_mapping JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Migration: Add csv_column_mapping column if it doesn't exist (for existing databases)
    try:
        conn.execute("SELECT csv_column_mapping FROM accounts LIMIT 1")
    except duckdb.BinderException:
        conn.execute("ALTER TABLE accounts ADD COLUMN csv_column_mapping JSON")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id VARCHAR(36) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            emoji VARCHAR(10),
            parent_id VARCHAR(36),
            group_name VARCHAR(20) NOT NULL,
            budget_amount INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS balance_snapshots (
            id VARCHAR(36) PRIMARY KEY,
            account_id VARCHAR(36) NOT NULL,
            balance INTEGER NOT NULL,
            snapshot_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
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
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES accounts(id),
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    """)

    # Create indexes for common query patterns on transactions
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_transactions_account_date
        ON transactions(account_id, date DESC)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_transactions_category
        ON transactions(category_id)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_transactions_reviewed
        ON transactions(reviewed)
    """)

    # Categorization feature tables and indexes
    conn.execute("""
        CREATE TABLE IF NOT EXISTS categorization_rules (
            id VARCHAR(36) PRIMARY KEY,
            merchant_pattern VARCHAR(255) NOT NULL UNIQUE,
            category_id VARCHAR(36) NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS categorization_batches (
            id VARCHAR(36) PRIMARY KEY,
            import_id VARCHAR(36),
            transaction_count INTEGER NOT NULL,
            success_count INTEGER NOT NULL DEFAULT 0,
            failure_count INTEGER NOT NULL DEFAULT 0,
            rule_match_count INTEGER NOT NULL DEFAULT 0,
            desc_rule_match_count INTEGER NOT NULL DEFAULT 0,
            ai_match_count INTEGER NOT NULL DEFAULT 0,
            skipped_count INTEGER NOT NULL DEFAULT 0,
            duration_ms INTEGER,
            error_message TEXT,
            started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        )
    """)

    # Migration: Add desc_rule_match_count column if it doesn't exist (for existing databases)
    try:
        conn.execute("SELECT desc_rule_match_count FROM categorization_batches LIMIT 1")
    except duckdb.BinderException:
        conn.execute("ALTER TABLE categorization_batches ADD COLUMN desc_rule_match_count INTEGER DEFAULT 0")

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_transactions_normalized_merchant
        ON transactions(normalized_merchant)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_transactions_categorization_source
        ON transactions(categorization_source)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_categorization_rules_category
        ON categorization_rules(category_id)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_categorization_batches_started
        ON categorization_batches(started_at)
    """)

    # Description-based pattern rules for categorization fallback
    conn.execute("""
        CREATE TABLE IF NOT EXISTS description_pattern_rules (
            id VARCHAR(36) PRIMARY KEY,
            account_id VARCHAR(36) NOT NULL,
            description_pattern VARCHAR(500) NOT NULL,
            category_id VARCHAR(36) NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES accounts(id),
            FOREIGN KEY (category_id) REFERENCES categories(id),
            UNIQUE(account_id, description_pattern)
        )
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_desc_pattern_rules_account
        ON description_pattern_rules(account_id)
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_desc_pattern_rules_category
        ON description_pattern_rules(category_id)
    """)

    # Category mapping table for AI-suggested CSV import mappings
    conn.execute("""
        CREATE TABLE IF NOT EXISTS category_mappings (
            id VARCHAR(36) PRIMARY KEY,
            account_id VARCHAR(36),
            source_category VARCHAR(255) NOT NULL,
            target_category_id VARCHAR(36) NOT NULL,
            source VARCHAR(20) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_id) REFERENCES accounts(id),
            FOREIGN KEY (target_category_id) REFERENCES categories(id),
            UNIQUE(account_id, source_category)
        )
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_category_mappings_account
        ON category_mappings(account_id)
    """)

    # Enrichment feature: add columns for AI-powered transaction enrichment
    for col, col_type in [
        ("subcategory", "VARCHAR(100)"),
        ("is_discretionary", "BOOLEAN"),
        ("enrichment_source", "VARCHAR(10)"),
    ]:
        try:
            conn.execute(f"SELECT {col} FROM transactions LIMIT 1")
        except duckdb.BinderException:
            conn.execute(f"ALTER TABLE transactions ADD COLUMN {col} {col_type}")

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_transactions_enrichment_source
        ON transactions(enrichment_source)
    """)

    # Migration: Add source column to rule tables for tracking AI-created vs manual rules
    try:
        conn.execute("SELECT source FROM categorization_rules LIMIT 1")
    except duckdb.BinderException:
        conn.execute("ALTER TABLE categorization_rules ADD COLUMN source VARCHAR(10) DEFAULT 'manual'")

    try:
        conn.execute("SELECT source FROM description_pattern_rules LIMIT 1")
    except duckdb.BinderException:
        conn.execute("ALTER TABLE description_pattern_rules ADD COLUMN source VARCHAR(10) DEFAULT 'manual'")
