"""CRUD for `body_metric`."""

from __future__ import annotations

import sqlite3
from typing import Optional

from app.models import BodyMetric


def list_all(conn: sqlite3.Connection) -> list[BodyMetric]:
    rows = conn.execute("SELECT * FROM body_metric ORDER BY date").fetchall()
    return [BodyMetric.from_row(r) for r in rows]


def get(conn: sqlite3.Connection, metric_id: int) -> Optional[BodyMetric]:
    row = conn.execute("SELECT * FROM body_metric WHERE id = ?", (metric_id,)).fetchone()
    return BodyMetric.from_row(row) if row else None


def create(conn: sqlite3.Connection, metric: BodyMetric) -> BodyMetric:
    cur = conn.execute(
        """
        INSERT INTO body_metric
            (date, weight_kg, body_fat_pct, measurements_json, notes)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            metric.date,
            metric.weight_kg,
            metric.body_fat_pct,
            metric.measurements_json,
            metric.notes,
        ),
    )
    conn.commit()
    metric.id = cur.lastrowid
    return metric


def delete(conn: sqlite3.Connection, metric_id: int) -> None:
    conn.execute("DELETE FROM body_metric WHERE id = ?", (metric_id,))
    conn.commit()
