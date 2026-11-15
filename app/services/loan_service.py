"""Service layer untuk transaksi peminjaman dan pengembalian alat.

Aturan utama (lihat `architecture.md` bagian 7 dan 8):

- Peminjaman dan pengembalian berjalan dalam satu transaksi database:
  perubahan stok dan status transaksi harus berhasil atau gagal bersama.
- Pengurangan stok bersifat kondisional agar stok tidak pernah negatif.
- Pengembalian ganda dicegah dengan pemeriksaan status di dalam transaksi.
"""

from datetime import datetime

from app import validators
from app.errors import NotFoundError, ValidationError
from app.repositories import item_repository, loan_repository

STATUS_BORROWED = "BORROWED"
STATUS_RETURNED = "RETURNED"


def _to_dict(row):
    """Ubah `sqlite3.Row` menjadi dict dengan timestamp ISO 8601."""
    data = dict(row)
    created_at = data.get("created_at")
    if isinstance(created_at, datetime):
        data["created_at"] = created_at.isoformat()
    return data


def borrow_item(db, payload):
    """Catat peminjaman baru dan kurangi stok secara atomik.

    Return: dict transaksi yang baru dibuat dengan status `BORROWED`.
    """
    data = validators.require_object(payload)
    student_id = validators.require_non_empty_string(
        data.get("student_id"), "student_id"
    )
    item_id = validators.require_positive_int(data.get("item_id"), "item_id")
    quantity = validators.require_positive_int(data.get("quantity"), "quantity")

    if item_repository.get_by_id(db, item_id) is None:
        raise NotFoundError("Item not found")

    try:
        if not item_repository.decrement_available_stock(db, item_id, quantity):
            raise ValidationError("Insufficient stock")
        row = loan_repository.create(db, student_id, item_id, quantity)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return _to_dict(row)


def return_loan(db, loan_id):
    """Tandai transaksi sebagai `RETURNED` dan pulihkan stok secara atomik.

    Return: dict transaksi yang sudah diperbarui.
    """
    loan_id = validators.require_positive_int(loan_id, "loan_id")

    loan = loan_repository.get_by_id(db, loan_id)
    if loan is None:
        raise NotFoundError("Loan not found")
    if loan["status"] == STATUS_RETURNED:
        raise ValidationError("Loan has already been returned")
    if loan["status"] != STATUS_BORROWED:
        raise ValidationError(f"Loan with status {loan['status']} cannot be returned")

    try:
        # Update bersyarat: hanya transaksi berstatus BORROWED yang berubah,
        # sehingga dua permintaan pengembalian bersamaan tidak menambah stok
        # dua kali.
        if not loan_repository.update_status(
            db, loan_id, STATUS_RETURNED, expected_status=STATUS_BORROWED
        ):
            raise ValidationError("Loan has already been returned")

        if not item_repository.increment_available_stock(
            db, loan["item_id"], loan["quantity"]
        ):
            raise NotFoundError("Item not found")

        db.commit()
    except Exception:
        db.rollback()
        raise

    return _to_dict(loan_repository.get_by_id(db, loan_id))


def get_student_history(db, student_id):
    """Kembalikan riwayat peminjaman milik satu NIM.

    Jika NIM belum memiliki transaksi, kembalikan daftar kosong.
    """
    student_id = validators.require_non_empty_string(student_id, "student_id")
    rows = loan_repository.get_by_student_id(db, student_id)
    return [_to_dict(row) for row in rows]
