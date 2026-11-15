"""Service layer untuk entitas `item`.

Service mengatur validasi, pemanggilan repository, dan commit/rollback
transaksi database. Route layer tidak boleh menyimpan aturan bisnis ini.
"""

from app import validators
from app.errors import NotFoundError
from app.repositories import item_repository


def _to_dict(row):
    """Ubah `sqlite3.Row` menjadi dict agar siap dijadikan JSON."""
    return dict(row)


def list_items(db):
    """Kembalikan seluruh alat beserta stok terkini dari database."""
    return [_to_dict(row) for row in item_repository.get_all(db)]


def add_item(db, payload):
    """Validasi input lalu simpan alat baru.

    `available_stock` diinisialisasi sama dengan `total_stock` oleh repository.
    Return: dict item yang baru dibuat.
    """
    data = validators.require_object(payload)
    name = validators.require_non_empty_string(data.get("name"), "name")
    total_stock = validators.require_non_negative_int(
        data.get("total_stock"), "total_stock"
    )

    try:
        row = item_repository.create(db, name, total_stock)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return _to_dict(row)
