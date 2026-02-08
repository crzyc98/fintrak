import os
import pytest
from fastapi.testclient import TestClient

# CRITICAL: Set test database BEFORE any app imports
# This prevents tests from accidentally using the production database
os.environ["DATABASE_PATH"] = ":memory:"

from app.main import app
import app.database as db_module


@pytest.fixture(autouse=True)
def setup_database():
    """Reset database connection and initialize fresh schema for each test."""
    # Force a fresh connection to the in-memory database
    db_module._connection = None
    db_module.DATABASE_PATH = ":memory:"

    db_module.init_db()
    yield

    # Clean up connection after test
    if db_module._connection is not None:
        try:
            db_module._connection.close()
        except Exception:
            pass
        db_module._connection = None


@pytest.fixture
def client():
    return TestClient(app)
