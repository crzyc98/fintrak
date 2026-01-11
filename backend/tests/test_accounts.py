import pytest


def test_create_account(client):
    response = client.post(
        "/api/accounts",
        json={"name": "My Checking", "type": "Checking", "institution": "Chase"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Checking"
    assert data["type"] == "Checking"
    assert data["institution"] == "Chase"
    assert data["is_asset"] is True
    assert "id" in data


def test_create_credit_account_is_not_asset(client):
    response = client.post(
        "/api/accounts",
        json={"name": "Credit Card", "type": "Credit"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["is_asset"] is False


def test_get_accounts(client):
    client.post("/api/accounts", json={"name": "Account 1", "type": "Checking"})
    client.post("/api/accounts", json={"name": "Account 2", "type": "Savings"})

    response = client.get("/api/accounts")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_account_by_id(client):
    create_response = client.post(
        "/api/accounts", json={"name": "Test Account", "type": "Checking"}
    )
    account_id = create_response.json()["id"]

    response = client.get(f"/api/accounts/{account_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Account"


def test_get_account_not_found(client):
    response = client.get("/api/accounts/nonexistent-id")
    assert response.status_code == 404


def test_update_account(client):
    create_response = client.post(
        "/api/accounts", json={"name": "Old Name", "type": "Checking"}
    )
    account_id = create_response.json()["id"]

    response = client.put(
        f"/api/accounts/{account_id}", json={"name": "New Name"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"


def test_delete_account(client):
    create_response = client.post(
        "/api/accounts", json={"name": "To Delete", "type": "Checking"}
    )
    account_id = create_response.json()["id"]

    response = client.delete(f"/api/accounts/{account_id}")
    assert response.status_code == 204

    get_response = client.get(f"/api/accounts/{account_id}")
    assert get_response.status_code == 404


def test_name_validation_too_long(client):
    response = client.post(
        "/api/accounts",
        json={"name": "A" * 101, "type": "Checking"},
    )
    assert response.status_code == 422


def test_account_type_validation(client):
    response = client.post(
        "/api/accounts",
        json={"name": "Test", "type": "InvalidType"},
    )
    assert response.status_code == 422
