"""Fixture bersama untuk pengujian API.

Setiap test memakai database SQLite sementara di `tmp_path`, sehingga tidak
mengubah database aplikasi dan hasilnya dapat diulang.
"""

import pytest

from app import create_app
from app.database import init_db


@pytest.fixture
def app(tmp_path, monkeypatch):
    """Buat aplikasi Flask dengan database kosong khusus untuk satu test."""
    database_path = tmp_path / "test.db"
    monkeypatch.setenv("LAB_EQUIPMENT_DATABASE", str(database_path))

    app = create_app()
    app.config.update(TESTING=True)

    with app.app_context():
        init_db()

    yield app


@pytest.fixture
def client(app):
    """HTTP client untuk memanggil endpoint tanpa menjalankan server."""
    return app.test_client()


@pytest.fixture
def make_item(client):
    """Factory: buat item lewat API dan kembalikan body responsnya."""

    def _make_item(name="Multimeter", total_stock=10):
        response = client.post(
            "/items",
            json={"name": name, "total_stock": total_stock},
        )
        assert response.status_code == 201
        return response.get_json()

    return _make_item


@pytest.fixture
def make_loan(client):
    """Factory: buat transaksi peminjaman lewat API."""

    def _make_loan(student_id="20240001", item_id=1, quantity=1):
        response = client.post(
            "/loans",
            json={
                "student_id": student_id,
                "item_id": item_id,
                "quantity": quantity,
            },
        )
        assert response.status_code == 201
        return response.get_json()

    return _make_loan


@pytest.fixture
def get_stock(client):
    """Factory: ambil `available_stock` terkini untuk satu item lewat API."""

    def _get_stock(item_id):
        response = client.get("/items")
        assert response.status_code == 200
        for item in response.get_json():
            if item["id"] == item_id:
                return item["available_stock"]
        raise AssertionError(f"Item {item_id} tidak ditemukan")

    return _get_stock
