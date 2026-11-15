"""Repository untuk entitas `loan`.

Konvensi sama dengan `item_repository`: koneksi database diteruskan sebagai
argumen, tidak ada commit di layer ini, dan semua query parameterized.

Status yang valid: `BORROWED`, `RETURNED`, `CANCELLED` (lihat skema).
"""


def create(db, student_id, item_id, quantity):
    """Buat transaksi peminjaman baru berstatus `BORROWED`.

    Pengurangan stok tidak dilakukan di sini; service layer yang mengatur
    urutan pengurangan stok dan pembuatan transaksi dalam satu transaksi
    database.
    """
    cursor = db.execute(
        """
        INSERT INTO loan (student_id, item_id, quantity, status)
        VALUES (?, ?, ?, 'BORROWED')
        """,
        (student_id, item_id, quantity),
    )
    return get_by_id(db, cursor.lastrowid)


def get_by_id(db, loan_id):
    """Kembalikan satu transaksi berdasarkan id, atau `None` jika tidak ada."""
    return db.execute(
        """
        SELECT id, student_id, item_id, quantity, status, created_at
          FROM loan
         WHERE id = ?
        """,
        (loan_id,),
    ).fetchone()


def update_status(db, loan_id, status):
    """Perbarui status transaksi.

    Return: `True` jika satu baris terupdate, `False` jika id tidak ditemukan.
    """
    cursor = db.execute(
        "UPDATE loan SET status = ? WHERE id = ?",
        (status, loan_id),
    )
    return cursor.rowcount == 1


def get_by_student_id(db, student_id):
    """Kembalikan riwayat peminjaman milik satu NIM, terbaru lebih dulu."""
    return db.execute(
        """
        SELECT id, student_id, item_id, quantity, status, created_at
          FROM loan
         WHERE student_id = ?
         ORDER BY created_at DESC, id DESC
        """,
        (student_id,),
    ).fetchall()
