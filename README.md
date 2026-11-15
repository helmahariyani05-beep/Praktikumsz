# Lab Equipment Loan System

REST API backend untuk mengelola master alat laboratorium, peminjaman, pengembalian, dan riwayat peminjaman mahasiswa. Dibangun dengan Python, Flask, dan SQLite, serta seluruh pertukaran data menggunakan JSON.

## Fitur

- Menampilkan daftar alat beserta stok terkini.
- Menambah master alat baru.
- Mencatat peminjaman dan mengurangi stok secara otomatis.
- Mengembalikan alat dan memulihkan stok.
- Menampilkan riwayat peminjaman berdasarkan NIM.
- Perubahan stok dan transaksi dijalankan secara atomik (commit/rollback).
- Stok tidak pernah negatif dan pengembalian ganda ditolak.

## Teknologi

- Python 3.10+
- Flask 3.1
- SQLite
- pytest

## Struktur Proyek

```text
.
├── app/
│   ├── __init__.py          # application factory
│   ├── config.py            # konfigurasi Flask
│   ├── database.py          # koneksi SQLite, skema, CLI init-db
│   ├── errors.py            # exception bisnis (400/404)
│   ├── validators.py        # validasi input
│   ├── repositories/        # query database (parameterized)
│   ├── routes/              # endpoint HTTP dan error handler JSON
│   └── services/            # aturan bisnis dan transaksi database
├── instance/                # database SQLite (tidak di-commit)
├── markdown/                # requirement, PRD, arsitektur, task
├── tests/                   # pengujian pytest
├── pytest.ini
├── requirements.txt
└── run.py
```

## Instalasi

Prasyarat: Python 3.10 atau lebih baru.

```powershell
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

```bash
# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Menjalankan Aplikasi

Inisialisasi database (cukup sekali, atau setelah database dihapus):

```powershell
flask --app run init-db
```

Jalankan server:

```powershell
python run.py
```

Server tersedia di `http://127.0.0.1:5000`.

Konfigurasi opsional melalui environment variable:

| Variable | Fungsi | Default |
|---|---|---|
| `PORT` | Port server | `5000` |
| `FLASK_DEBUG` | `1` untuk mode debug | `0` |
| `LAB_EQUIPMENT_DATABASE` | Lokasi file database SQLite | `instance/lab_equipment.db` |

Contoh:

```powershell
$env:PORT = "5001"
$env:LAB_EQUIPMENT_DATABASE = "C:\data\lab.db"
python run.py
```

Untuk mereset data, hentikan server, hapus `instance/lab_equipment.db`, lalu jalankan `flask --app run init-db` kembali.

## API

Semua request body dan response menggunakan JSON (`Content-Type: application/json`). Format error selalu:

```json
{
  "error": "pesan kesalahan"
}
```

### 1. GET `/items`

Menampilkan seluruh alat dan stok terkini. Status: `200 OK`.

```bash
curl http://127.0.0.1:5000/items
```

```json
[
  {
    "id": 1,
    "name": "Multimeter",
    "total_stock": 10,
    "available_stock": 7
  }
]
```

### 2. POST `/items`

Menambah master alat. `available_stock` otomatis sama dengan `total_stock`. Status: `201 Created`.

```bash
curl -X POST http://127.0.0.1:5000/items \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"Multimeter\", \"total_stock\": 10}"
```

```json
{
  "id": 1,
  "name": "Multimeter",
  "total_stock": 10,
  "available_stock": 10
}
```

Error: `400 Bad Request` jika `name` kosong atau `total_stock` bukan bilangan bulat non-negatif.

### 3. POST `/loans`

Membuat transaksi peminjaman dan mengurangi stok. Status: `201 Created`.

```bash
curl -X POST http://127.0.0.1:5000/loans \
  -H "Content-Type: application/json" \
  -d "{\"student_id\": \"20240001\", \"item_id\": 1, \"quantity\": 2}"
```

```json
{
  "id": 1,
  "student_id": "20240001",
  "item_id": 1,
  "quantity": 2,
  "status": "BORROWED",
  "created_at": "2026-11-15T08:46:34"
}
```

Error:

- `400 Bad Request` jika input tidak valid, `quantity` tidak positif, atau stok tidak mencukupi.
- `404 Not Found` jika `item_id` tidak ditemukan.

### 4. PUT `/loans/{id}/return`

Mengembalikan alat, mengubah status menjadi `RETURNED`, dan memulihkan stok. Tidak memerlukan body. Status: `200 OK`.

```bash
curl -X PUT http://127.0.0.1:5000/loans/1/return
```

Error:

- `400 Bad Request` jika transaksi sudah berstatus `RETURNED`.
- `404 Not Found` jika transaksi tidak ditemukan.

### 5. GET `/loans/student/{student_id}`

Menampilkan riwayat peminjaman milik satu NIM, terbaru lebih dulu. Status: `200 OK`.

```bash
curl http://127.0.0.1:5000/loans/student/20240001
```

Jika belum ada transaksi, response berupa daftar kosong `[]`.

### Ringkasan Endpoint

| Method | Endpoint | Sukses | Error |
|---|---|---|---|
| GET | `/items` | 200 | - |
| POST | `/items` | 201 | 400 |
| POST | `/loans` | 201 | 400, 404 |
| PUT | `/loans/{id}/return` | 200 | 400, 404 |
| GET | `/loans/student/{student_id}` | 200 | 400 |

### Menguji dengan Postman

1. Buat request baru dan pilih method serta URL sesuai tabel di atas.
2. Untuk `POST`, pilih tab **Body** → **raw** → **JSON**, lalu isi body sesuai contoh.
3. Kirim request dan periksa status code serta response JSON.

## Pengujian

```powershell
pytest -q
```

atau:

```powershell
python -m pytest -q
```

Test memakai database sementara, sehingga data aplikasi tidak berubah.

## Batasan

Sesuai ruang lingkup requirement saat ini, sistem belum menyediakan:

- autentikasi dan otorisasi Petugas Lab/Mahasiswa;
- endpoint ubah/hapus master alat;
- pembatalan transaksi berstatus `CANCELLED`;
- batas maksimum pinjaman, jatuh tempo, dan denda;
- pagination, pencarian, dan pengurutan;
- konfigurasi deployment production.
