"""Registrasi blueprint dan error handler API.

Semua respons, termasuk error, dikembalikan dalam format JSON:
- Sukses: resource langsung (object atau array).
- Error: `{"error": "pesan"}` dengan HTTP status yang sesuai.
"""

from flask import jsonify

from app.errors import ServiceError
from app.routes.item_routes import bp as item_bp
from app.routes.loan_routes import bp as loan_bp


def _error_response(message, status_code):
    return jsonify({"error": message}), status_code


def _handle_service_error(error):
    return _error_response(str(error), error.status_code)


def _handle_not_found(error):
    return _error_response("Resource not found", 404)


def _handle_method_not_allowed(error):
    return _error_response("Method not allowed", 405)


def register_routes(app):
    """Daftarkan seluruh blueprint dan error handler JSON pada app."""
    app.register_blueprint(item_bp)
    app.register_blueprint(loan_bp)

    app.register_error_handler(ServiceError, _handle_service_error)
    app.register_error_handler(404, _handle_not_found)
    app.register_error_handler(405, _handle_method_not_allowed)
