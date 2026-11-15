"""Exception untuk kesalahan bisnis yang sudah diperkirakan.

Service layer melempar exception ini, lalu route layer (tahap berikutnya)
memetakannya menjadi respons JSON dengan HTTP status yang sesuai. Exception
ini tidak membawa detail internal database.
"""


class ServiceError(Exception):
    """Base class untuk kesalahan bisnis yang dapat ditampilkan ke client."""

    status_code = 400


class ValidationError(ServiceError):
    """Input tidak valid atau aturan bisnis ditolak (400 Bad Request)."""

    status_code = 400


class NotFoundError(ServiceError):
    """Data yang diminta tidak ditemukan (404 Not Found)."""

    status_code = 404
