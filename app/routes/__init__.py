"""Registrasi blueprint dan error handler API.

Semua respons, termasuk error, dikembalikan dalam format JSON:
- Sukses: resource langsung (object atau array).
- Error: `{"error": "pesan"}` dengan HTTP status yang sesuai.
"""

from flask import current_app, jsonify
from werkzeug.exceptions import HTTPException

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


def _handle_http_exception(error):
    """Fallback JSON untuk HTTP error lain (misalnya 400 atau 415)."""
    return _error_response(error.name, error.code)


def _handle_internal_error(error):
    """Log detail di server, kirim pesan generik ke client."""
    current_app.logger.exception("Unhandled server error")
    return _error_response("Internal server error", 500)


def register_routes(app):
    """Daftarkan seluruh blueprint dan error handler JSON pada app."""
    app.register_blueprint(item_bp)
    app.register_blueprint(loan_bp)

    app.register_error_handler(ServiceError, _handle_service_error)
    app.register_error_handler(404, _handle_not_found)
    app.register_error_handler(405, _handle_method_not_allowed)
    app.register_error_handler(HTTPException, _handle_http_exception)
    app.register_error_handler(500, _handle_internal_error)
