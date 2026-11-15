"""Endpoint untuk transaksi peminjaman dan pengembalian alat."""

from flask import Blueprint, jsonify, request

from app.database import get_db
from app.services import loan_service

bp = Blueprint("loans", __name__)


@bp.post("/loans")
def create_loan():
    """POST /loans - buat transaksi peminjaman (201 Created)."""
    loan = loan_service.borrow_item(get_db(), request.get_json(silent=True))
    return jsonify(loan), 201


@bp.put("/loans/<int:loan_id>/return")
def return_loan(loan_id):
    """PUT /loans/{id}/return - kembalikan alat (200 OK)."""
    loan = loan_service.return_loan(get_db(), loan_id)
    return jsonify(loan), 200


@bp.get("/loans/student/<student_id>")
def student_history(student_id):
    """GET /loans/student/{student_id} - riwayat pinjaman (200 OK)."""
    history = loan_service.get_student_history(get_db(), student_id)
    return jsonify(history), 200
