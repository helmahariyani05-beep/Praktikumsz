"""Repository untuk entitas `item`.

Semua fungsi menerima koneksi `sqlite3.Connection` sebagai argumen pertama dan
**tidak melakukan commit**. Pengelolaan transaksi database adalah tanggung
jawab service layer, sehingga beberapa operasi repository dapat dibungkus
dalam satu transaksi yang sama.

Seluruh query menggunakan parameterized query (placeholder `?`), tidak pernah
menyusun SQL dari input pengguna.
"""


def create(db, name, total_stock):
    """Simpan item baru dan kembalikan barisnya.

    `available_stock` diinisialisasi sama dengan `total_stock` di dalam query
    agar tidak ada celah antara nilai awal dan nilai tersimpan.
    """
    cursor = db.execute(
        """
        INSERT INTO item (name, total_stock, available_stock)
        VALUES (?, ?, ?)
        """,
        (name, total_stock, total_stock),
    )
    return get_by_id(db, cursor.lastrowid)


def get_all(db):
    """Kembalikan seluruh item, diurutkan berdasarkan id."""
    return db.execute(
        "SELECT id, name, total_stock, available_stock FROM item ORDER BY id"
    ).fetchall()


def get_by_id(db, item_id):
    """Kembalikan satu item berdasarkan id, atau `None` jika tidak ada."""
    return db.execute(
        "SELECT id, name, total_stock, available_stock FROM item WHERE id = ?",
        (item_id,),
    ).fetchone()


def decrement_available_stock(db, item_id, quantity):
    """Kurangi `available_stock` secara bersyarat.

    Pengurangan hanya dilakukan jika stok mencukupi, sehingga stok tidak
    pernah menjadi negatif walaupun ada permintaan bersamaan.

    Return: `True` jika satu baris terupdate, `False` jika stok tidak cukup.
    """
    cursor = db.execute(
        """
        UPDATE item
           SET available_stock = available_stock - ?
         WHERE id = ?
           AND available_stock >= ?
        """,
        (quantity, item_id, quantity),
    )
    return cursor.rowcount == 1


def increment_available_stock(db, item_id, quantity):
    """Tambah `available_stock` (dipakai saat pengembalian).

    Batas `available_stock <= total_stock` tetap ditegakkan oleh CHECK
    constraint pada skema. Return: `True` jika satu baris terupdate.
    """
    cursor = db.execute(
        """
        UPDATE item
           SET available_stock = available_stock + ?
         WHERE id = ?
        """,
        (quantity, item_id),
    )
    return cursor.rowcount == 1
