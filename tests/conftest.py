"""Shared pytest fixtures: an isolated, fresh DB per test."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app.db.connection import ensure_initialised


@pytest.fixture()
def conn(tmp_path: Path) -> sqlite3.Connection:
    db_file = tmp_path / "test.db"
    connection = ensure_initialised(db_file)
    yield connection
    connection.close()
