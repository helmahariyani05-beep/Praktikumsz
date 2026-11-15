"""Pengujian peminjaman, pengembalian, dan riwayat pinjaman (`/loans`)."""

import pytest

from app.repositories import loan_repository


def borrow_payload(student_id="20240001", item_id=1, quantity=1):
    """Body request peminjaman standar untuk test."""
    return {"student_id": student_id, "item_id": item_id, "quantity": quantity}


# --- 6.2 Loan API ---------------------------------------------------------


def test_borrow_item_with_valid_data(client, make_item):
    """Peminjaman valid mengembalikan 201 dengan status BORROWED."""
    item = make_item(total_stock=10)

    response = client.post(
        "/loans",
        json=borrow_payload(item_id=item["id"], quantity=2),
    )

    assert response.status_code == 201
    data = response.get_json()
    assert isinstance(data["id"], int)
    assert data["student_id"] == "20240001"
    assert data["item_id"] == item["id"]
    assert data["quantity"] == 2
    assert data["status"] == "BORROWED"
    assert data["created_at"]


def test_borrow_reduces_available_stock_by_quantity(client, make_item, get_stock):
    """Stok tersedia berkurang tepat sebanyak quantity yang dipinjam."""
    item = make_item(total_stock=10)

    client.post("/loans", json=borrow_payload(item_id=item["id"], quantity=3))

    assert get_stock(item["id"]) == 7


def test_borrow_with_insufficient_stock_is_rejected(
    client, make_item, get_stock
):
    """Peminjaman melebihi stok ditolak 400 dan stok tidak berubah."""
    item = make_item(total_stock=3)

    response = client.post(
        "/loans",
        json=borrow_payload(item_id=item["id"], quantity=4),
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Insufficient stock"
    assert get_stock(item["id"]) == 3
    assert client.get("/loans/student/20240001").get_json() == []


def test_borrow_with_unknown_item_is_rejected(client):
    """Item yang tidak ada menghasilkan 404 Not Found."""
    response = client.post("/loans", json=borrow_payload(item_id=999, quantity=1))

    assert response.status_code == 404
    assert response.get_json()["error"] == "Item not found"


@pytest.mark.parametrize("quantity", [0, -1])
def test_borrow_with_non_positive_quantity_is_rejected(
    client, make_item, get_stock, quantity
):
    """Quantity nol atau negatif ditolak 400 tanpa mengubah stok."""
    item = make_item(total_stock=5)

    response = client.post(
        "/loans",
        json=borrow_payload(item_id=item["id"], quantity=quantity),
    )

    assert response.status_code == 400
    assert "error" in response.get_json()
    assert get_stock(item["id"]) == 5


def test_borrow_with_missing_student_id_is_rejected(client, make_item):
    """Student ID wajib diisi."""
    item = make_item(total_stock=5)

    response = client.post(
        "/loans",
        json={"item_id": item["id"], "quantity": 1},
    )

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_failed_borrow_keeps_stock_and_creates_no_loan(
    client, make_item, get_stock, monkeypatch
):
    """Jika pembuatan transaksi gagal, perubahan stok di-rollback."""
    item = make_item(total_stock=5)

    def fail_create(*args, **kwargs):
        raise RuntimeError("simulated failure")

    monkeypatch.setattr(loan_repository, "create", fail_create)

    with pytest.raises(RuntimeError):
        client.post(
            "/loans",
            json=borrow_payload(item_id=item["id"], quantity=2),
        )

    assert get_stock(item["id"]) == 5
    assert client.get("/loans/student/20240001").get_json() == []


# --- 6.3 Return API -------------------------------------------------------


def test_return_loan_marks_it_returned(client, make_item, make_loan, get_stock):
    """Pengembalian valid mengubah status menjadi RETURNED dan stok pulih."""
    item = make_item(total_stock=10)
    loan = make_loan(item_id=item["id"], quantity=4)
    assert get_stock(item["id"]) == 6

    response = client.put(f"/loans/{loan['id']}/return")

    assert response.status_code == 200
    data = response.get_json()
    assert data["id"] == loan["id"]
    assert data["status"] == "RETURNED"
    assert get_stock(item["id"]) == 10


def test_return_unknown_loan_is_rejected(client):
    """Transaksi yang tidak ada menghasilkan 404 Not Found."""
    response = client.put("/loans/999/return")

    assert response.status_code == 404
    assert response.get_json()["error"] == "Loan not found"


def test_return_already_returned_loan_is_rejected(
    client, make_item, make_loan, get_stock
):
    """Transaksi RETURNED tidak boleh dikembalikan dua kali."""
    item = make_item(total_stock=10)
    loan = make_loan(item_id=item["id"], quantity=3)

    first = client.put(f"/loans/{loan['id']}/return")
    second = client.put(f"/loans/{loan['id']}/return")

    assert first.status_code == 200
    assert second.status_code == 400
    assert second.get_json()["error"] == "Loan has already been returned"
    assert get_stock(item["id"]) == 10


def test_second_return_does_not_add_stock_again(
    client, make_item, make_loan, get_stock
):
    """Pengembalian ganda tidak menambah stok melebihi stok total."""
    item = make_item(total_stock=5)
    loan = make_loan(item_id=item["id"], quantity=2)

    client.put(f"/loans/{loan['id']}/return")
    client.put(f"/loans/{loan['id']}/return")

    assert get_stock(item["id"]) == 5


# --- 6.4 Student Loan History API ----------------------------------------


def test_history_for_student_with_loans(client, make_item, make_loan):
    """Riwayat menampilkan seluruh transaksi milik NIM yang diminta."""
    item = make_item(total_stock=10)
    first = make_loan(item_id=item["id"], quantity=1)
    second = make_loan(item_id=item["id"], quantity=2)

    response = client.get("/loans/student/20240001")

    assert response.status_code == 200
    history = response.get_json()
    assert {row["id"] for row in history} == {first["id"], second["id"]}
    assert all(row["student_id"] == "20240001" for row in history)
    assert all(row["item_id"] == item["id"] for row in history)


def test_history_for_student_without_loans_is_empty(client):
    """NIM tanpa transaksi mendapatkan daftar kosong dengan 200 OK."""
    response = client.get("/loans/student/20249999")

    assert response.status_code == 200
    assert response.get_json() == []


def test_history_only_contains_requested_student(client, make_item, make_loan):
    """Riwayat tidak memuat transaksi milik mahasiswa lain."""
    first_item = make_item(name="Multimeter", total_stock=5)
    second_item = make_item(name="Osiloskop", total_stock=5)

    make_loan(student_id="20240001", item_id=first_item["id"], quantity=1)
    make_loan(student_id="20240002", item_id=second_item["id"], quantity=1)

    response = client.get("/loans/student/20240001")

    assert response.status_code == 200
    history = response.get_json()
    assert len(history) == 1
    assert history[0]["student_id"] == "20240001"
    assert history[0]["item_id"] == first_item["id"]


# --- 7. Final Verification ------------------------------------------------


def test_stock_stays_consistent_across_multiple_transactions(
    client, make_item, make_loan, get_stock
):
    """Stok selalu sama dengan total dikurangi pinjaman yang masih aktif."""
    total_stock = 10
    item = make_item(name="Multimeter", total_stock=total_stock)
    active_quantity = 0

    def borrow(student_id, quantity):
        nonlocal active_quantity
        loan = make_loan(
            student_id=student_id,
            item_id=item["id"],
            quantity=quantity,
        )
        active_quantity += quantity
        assert get_stock(item["id"]) == total_stock - active_quantity
        return loan

    def return_loan(loan, quantity):
        nonlocal active_quantity
        response = client.put(f"/loans/{loan['id']}/return")
        assert response.status_code == 200
        active_quantity -= quantity
        assert get_stock(item["id"]) == total_stock - active_quantity

    first = borrow("20240001", 3)
    second = borrow("20240002", 2)
    return_loan(first, 3)
    third = borrow("20240003", 4)
    return_loan(second, 2)
    return_loan(third, 4)

    assert active_quantity == 0
    assert get_stock(item["id"]) == total_stock
    history = client.get("/loans/student/20240001").get_json()
    assert history[0]["status"] == "RETURNED"
