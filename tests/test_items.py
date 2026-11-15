"""Pengujian endpoint master data alat (`/items`)."""

import pytest


def test_get_items_when_database_is_empty(client):
    """GET /items pada database kosong mengembalikan daftar kosong."""
    response = client.get("/items")

    assert response.status_code == 200
    assert response.is_json
    assert response.get_json() == []


def test_create_item_with_valid_data(client):
    """POST /items dengan data valid mengembalikan 201 dan data alat."""
    response = client.post(
        "/items",
        json={"name": "Multimeter", "total_stock": 10},
    )

    assert response.status_code == 201
    data = response.get_json()
    assert isinstance(data["id"], int)
    assert data["name"] == "Multimeter"
    assert data["total_stock"] == 10
    assert data["available_stock"] == 10


def test_created_item_is_listed_by_get_items(client, make_item):
    """Alat yang baru dibuat muncul pada GET /items."""
    created = make_item(name="Osiloskop", total_stock=4)

    response = client.get("/items")

    assert response.status_code == 200
    items = response.get_json()
    assert len(items) == 1
    assert items[0] == created


@pytest.mark.parametrize(
    "payload",
    [
        {"total_stock": 5},
        {"name": "", "total_stock": 5},
        {"name": "   ", "total_stock": 5},
        {"name": None, "total_stock": 5},
    ],
)
def test_create_item_without_name_is_rejected(client, payload):
    """Nama wajib diisi; request tanpa nama valid ditolak 400."""
    response = client.post("/items", json=payload)

    assert response.status_code == 400
    assert "error" in response.get_json()
    assert client.get("/items").get_json() == []


@pytest.mark.parametrize("total_stock", [-1, -10])
def test_create_item_with_negative_stock_is_rejected(client, total_stock):
    """Stok total negatif ditolak dan tidak tersimpan."""
    response = client.post(
        "/items",
        json={"name": "Kabel", "total_stock": total_stock},
    )

    assert response.status_code == 400
    assert "error" in response.get_json()
    assert client.get("/items").get_json() == []


@pytest.mark.parametrize("total_stock", [1.5, "5", None, True])
def test_create_item_with_non_integer_stock_is_rejected(client, total_stock):
    """Stok total harus bilangan bulat, bukan float/string/boolean."""
    response = client.post(
        "/items",
        json={"name": "Kabel", "total_stock": total_stock},
    )

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_available_stock_equals_total_stock_on_creation(client):
    """Stok awal tersedia selalu sama dengan stok total."""
    response = client.post(
        "/items",
        json={"name": "Power Supply", "total_stock": 7},
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["available_stock"] == data["total_stock"] == 7


def test_create_item_with_malformed_json_is_rejected(client):
    """Body yang bukan JSON object ditolak dengan 400."""
    response = client.post(
        "/items",
        data="{bukan json",
        content_type="application/json",
    )

    assert response.status_code == 400
    assert "error" in response.get_json()
