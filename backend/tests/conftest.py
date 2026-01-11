import os
import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_PATH"] = ":memory:"

from app.main import app
from app.database import init_db, get_connection


@pytest.fixture(autouse=True)
def setup_database():
    init_db()
    yield
    conn = get_connection()
    conn.execute("DROP TABLE IF EXISTS balance_snapshots")
    conn.execute("DROP TABLE IF EXISTS categories")
    conn.execute("DROP TABLE IF EXISTS accounts")


@pytest.fixture
def client():
    return TestClient(app)
