import os
import duckdb
from contextlib import contextmanager

DATABASE_PATH = os.getenv("DATABASE_PATH", "fintrak.duckdb")

_connection = None


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
            ai_match_count INTEGER NOT NULL DEFAULT 0,
            skipped_count INTEGER NOT NULL DEFAULT 0,
            duration_ms INTEGER,
            error_message TEXT,
            started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        )
    """)

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
