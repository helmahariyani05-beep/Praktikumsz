"""Endpoint untuk master data alat laboratorium."""

from flask import Blueprint, jsonify, request

from app.database import get_db
from app.services import item_service

bp = Blueprint("items", __name__)


@bp.get("/items")
def list_items():
    """GET /items - daftar alat beserta stok terkini (200 OK)."""
    items = item_service.list_items(get_db())
    return jsonify(items), 200


@bp.post("/items")
def create_item():
    """POST /items - tambah master alat baru (201 Created)."""
    item = item_service.add_item(get_db(), request.get_json(silent=True))
    return jsonify(item), 201
