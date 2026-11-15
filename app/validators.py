"""Validator input yang dipakai bersama oleh service layer.

Semua fungsi melempar `ValidationError` dengan pesan yang informatif dan
aman ditampilkan ke client. Validasi dilakukan di backend, bukan hanya
mengandalkan data dari client.
"""

from app.errors import ValidationError


def require_object(payload):
    """Pastikan request body berupa JSON object."""
    if not isinstance(payload, dict):
        raise ValidationError("Request body must be a JSON object")
    return payload


def require_non_empty_string(value, field):
    """Kembalikan string yang sudah di-trim, atau tolak jika kosong."""
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{field} is required and must be a non-empty string")
    return value.strip()


def require_int(value, field):
    """Pastikan nilai berupa bilangan bulat (bukan boolean atau string)."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(f"{field} must be an integer")
    return value


def require_non_negative_int(value, field):
    """Pastikan nilai berupa bilangan bulat >= 0."""
    value = require_int(value, field)
    if value < 0:
        raise ValidationError(f"{field} must be greater than or equal to 0")
    return value


def require_positive_int(value, field):
    """Pastikan nilai berupa bilangan bulat > 0."""
    value = require_int(value, field)
    if value <= 0:
        raise ValidationError(f"{field} must be greater than 0")
    return value
