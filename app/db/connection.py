"""SQLite connection helpers and one-time DB initialisation."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from importlib import resources
from pathlib import Path
from typing import Iterator, Optional

from app import config

_SCHEMA_RESOURCE = ("app.db", "schema.sql")


def _load_schema_sql() -> str:
    pkg, name = _SCHEMA_RESOURCE
    return resources.files(pkg).joinpath(name).read_text(encoding="utf-8")


def get_conn(db_file: Optional[Path] = None) -> sqlite3.Connection:
    """Open a SQLite connection with sensible defaults."""
    target = Path(db_file) if db_file else config.db_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(target, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


@contextmanager
def transaction(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """Context manager for a single transaction with rollback on error."""
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def init_db(conn: sqlite3.Connection) -> None:
    """Apply the schema and seed defaults if the DB is empty."""
    sql = _load_schema_sql()
    with transaction(conn):
        conn.executescript(sql)
    # Seed lazily — avoid circular import.
    from app.db import seed
    seed.seed_if_empty(conn)


def ensure_initialised(db_file: Optional[Path] = None) -> sqlite3.Connection:
    conn = get_conn(db_file)
    init_db(conn)
    return conn
