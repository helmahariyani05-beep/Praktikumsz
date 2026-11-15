"""SQLite connection handling and schema initialization.

Skema mengikuti `architecture.md` bagian 5 (Model Data) dan 8 (Konsistensi
dan Integritas Data):

- Foreign key SQLite selalu diaktifkan pada setiap koneksi baru.
- Constraint stok, quantity, dan status ditegakkan oleh database.
- Tidak ada akses database di luar modul ini dan layer repository.
"""

import sqlite3
from datetime import datetime

import click
from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS item (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,
    total_stock     INTEGER NOT NULL CHECK (total_stock >= 0),
    available_stock INTEGER NOT NULL
                    CHECK (available_stock >= 0),
    CHECK (available_stock <= total_stock)
);

CREATE TABLE IF NOT EXISTS loan (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT    NOT NULL,
    item_id    INTEGER NOT NULL REFERENCES item (id) ON UPDATE CASCADE,
    quantity   INTEGER NOT NULL CHECK (quantity > 0),
    status     TEXT    NOT NULL DEFAULT 'BORROWED'
               CHECK (status IN ('BORROWED', 'RETURNED', 'CANCELLED')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_loan_student_id ON loan (student_id);
"""


def _convert_timestamp(value):
    """Konversi kolom TIMESTAMP menjadi `datetime`.

    Konverter eksplisit dipakai karena konverter default `sqlite3` untuk
    TIMESTAMP sudah deprecated sejak Python 3.12.
    """
    return datetime.fromisoformat(value.decode())


sqlite3.register_converter("TIMESTAMP", _convert_timestamp)


def get_db():
    """Return the database connection for the current request/context.

    Koneksi dibuat sekali per application context, lalu ditutup otomatis oleh
    `close_db`. `PRAGMA foreign_keys = ON` dijalankan di sini agar setiap
    koneksi baru ikut menegakkan foreign key (default SQLite: OFF).
    """
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"],
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(exception=None):
    """Close the database connection at the end of the application context."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create all tables if they do not exist yet."""
    db = get_db()
    db.executescript(SCHEMA)
    db.commit()


@click.command("init-db")
def init_db_command():
    """CLI: buat database dan tabel (`flask --app run init-db`)."""
    init_db()
    click.echo(f"Database initialized: {current_app.config['DATABASE']}")


def init_app(app):
    """Register database teardown and CLI command on the Flask app."""
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
