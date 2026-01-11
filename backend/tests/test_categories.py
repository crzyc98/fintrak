import pytest


def test_create_category(client):
    response = client.post(
        "/api/categories",
        json={
            "name": "Groceries",
            "emoji": "🛒",
            "group_name": "Essential",
            "budget_amount": 50000,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Groceries"
    assert data["emoji"] == "🛒"
    assert data["group_name"] == "Essential"
    assert data["budget_amount"] == 50000
    assert "id" in data


def test_get_categories(client):
    client.post(
        "/api/categories",
        json={"name": "Category 1", "group_name": "Essential"},
    )
    client.post(
        "/api/categories",
        json={"name": "Category 2", "group_name": "Lifestyle"},
    )

    response = client.get("/api/categories")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_category_tree(client):
    parent_response = client.post(
        "/api/categories",
        json={"name": "Food", "group_name": "Essential"},
    )
    parent_id = parent_response.json()["id"]

    client.post(
        "/api/categories",
        json={"name": "Restaurants", "group_name": "Essential", "parent_id": parent_id},
    )

    response = client.get("/api/categories/tree")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Food"
    assert len(data[0]["children"]) == 1
    assert data[0]["children"][0]["name"] == "Restaurants"


def test_create_category_with_parent(client):
    parent_response = client.post(
        "/api/categories",
        json={"name": "Parent", "group_name": "Essential"},
    )
    parent_id = parent_response.json()["id"]

    response = client.post(
        "/api/categories",
        json={"name": "Child", "group_name": "Essential", "parent_id": parent_id},
    )
    assert response.status_code == 201
    assert response.json()["parent_id"] == parent_id


def test_create_category_circular_self_reference(client):
    create_response = client.post(
        "/api/categories",
        json={"name": "Category", "group_name": "Essential"},
    )
    category_id = create_response.json()["id"]

    response = client.put(
        f"/api/categories/{category_id}",
        json={"parent_id": category_id},
    )
    assert response.status_code == 400
    detail = response.json()["detail"].lower()
    assert "parent" in detail or "circular" in detail


def test_create_category_circular_descendant_reference(client):
    grandparent_response = client.post(
        "/api/categories",
        json={"name": "Grandparent", "group_name": "Essential"},
    )
    grandparent_id = grandparent_response.json()["id"]

    parent_response = client.post(
        "/api/categories",
        json={"name": "Parent", "group_name": "Essential", "parent_id": grandparent_id},
    )
    parent_id = parent_response.json()["id"]

    child_response = client.post(
        "/api/categories",
        json={"name": "Child", "group_name": "Essential", "parent_id": parent_id},
    )
    child_id = child_response.json()["id"]

    response = client.put(
        f"/api/categories/{grandparent_id}",
        json={"parent_id": child_id},
    )
    assert response.status_code == 400
    assert "circular" in response.json()["detail"].lower()


def test_delete_category_with_children_fails(client):
    parent_response = client.post(
        "/api/categories",
        json={"name": "Parent", "group_name": "Essential"},
    )
    parent_id = parent_response.json()["id"]

    client.post(
        "/api/categories",
        json={"name": "Child", "group_name": "Essential", "parent_id": parent_id},
    )

    response = client.delete(f"/api/categories/{parent_id}")
    assert response.status_code == 400
    assert "child" in response.json()["detail"].lower()


def test_delete_category_without_children(client):
    create_response = client.post(
        "/api/categories",
        json={"name": "To Delete", "group_name": "Essential"},
    )
    category_id = create_response.json()["id"]

    response = client.delete(f"/api/categories/{category_id}")
    assert response.status_code == 204


def test_update_category(client):
    create_response = client.post(
        "/api/categories",
        json={"name": "Old Name", "group_name": "Essential"},
    )
    category_id = create_response.json()["id"]

    response = client.put(
        f"/api/categories/{category_id}",
        json={"name": "New Name", "emoji": "🆕"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"
    assert response.json()["emoji"] == "🆕"


def test_name_validation_too_long(client):
    response = client.post(
        "/api/categories",
        json={"name": "A" * 101, "group_name": "Essential"},
    )
    assert response.status_code == 422


def test_group_name_validation(client):
    response = client.post(
        "/api/categories",
        json={"name": "Test", "group_name": "InvalidGroup"},
    )
    assert response.status_code == 422
