"""Backup, JSON export and import."""

from __future__ import annotations

import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from app import config

EXPORT_TABLES = [
    "exercise",
    "workout",
    "workout_exercise",
    "plan",
    "plan_slot",
    "session_log",
    "set_log",
    "goal",
    "body_metric",
]


def export_json(conn: sqlite3.Connection, target: Path) -> Path:
    payload: dict = {"version": 1, "exported_at": datetime.utcnow().isoformat() + "Z", "tables": {}}
    for table in EXPORT_TABLES:
        rows = conn.execute(f"SELECT * FROM {table}").fetchall()
        payload["tables"][table] = [dict(r) for r in rows]
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return target


def import_json(conn: sqlite3.Connection, source: Path) -> None:
    """Replace all data in the DB with the contents of *source*."""
    source = Path(source)
    payload = json.loads(source.read_text(encoding="utf-8"))
    tables = payload.get("tables", {})
    try:
        conn.execute("BEGIN")
        for table in reversed(EXPORT_TABLES):
            conn.execute(f"DELETE FROM {table}")
        for table in EXPORT_TABLES:
            for row in tables.get(table, []):
                cols = ",".join(row.keys())
                placeholders = ",".join("?" for _ in row)
                conn.execute(
                    f"INSERT INTO {table} ({cols}) VALUES ({placeholders})",
                    list(row.values()),
                )
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def backup_db(target_dir: Path | None = None) -> Path:
    """Copy the live DB file with a timestamp."""
    src = config.db_path()
    target_dir = Path(target_dir) if target_dir else config.DATA_DIR / "backups"
    target_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dst = target_dir / f"fitness-{stamp}.db"
    shutil.copy2(src, dst)
    return dst
