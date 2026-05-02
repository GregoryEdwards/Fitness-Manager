"""CRUD for the `exercise` table."""

from __future__ import annotations

import sqlite3
from typing import Optional

from app.models import Exercise


def list_all(
    conn: sqlite3.Connection,
    modality: Optional[str] = None,
    search: Optional[str] = None,
) -> list[Exercise]:
    sql = "SELECT * FROM exercise WHERE 1=1"
    params: list = []
    if modality:
        sql += " AND modality = ?"
        params.append(modality)
    if search:
        sql += (
            " AND (name LIKE ? OR muscle_groups LIKE ?"
            " OR equipment LIKE ? OR category LIKE ?)"
        )
        like = f"%{search}%"
        params.extend([like, like, like, like])
    sql += " ORDER BY modality, name"
    rows = conn.execute(sql, params).fetchall()
    return [Exercise.from_row(r) for r in rows]


def get(conn: sqlite3.Connection, exercise_id: int) -> Optional[Exercise]:
    row = conn.execute("SELECT * FROM exercise WHERE id = ?", (exercise_id,)).fetchone()
    return Exercise.from_row(row) if row else None


def create(conn: sqlite3.Connection, ex: Exercise) -> Exercise:
    cur = conn.execute(
        """
        INSERT INTO exercise
            (name, modality, category, muscle_groups, equipment,
             metric_type, default_unit, notes, is_custom)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ex.name,
            ex.modality,
            ex.category,
            ex.muscle_groups,
            ex.equipment,
            ex.metric_type,
            ex.default_unit,
            ex.notes,
            int(ex.is_custom),
        ),
    )
    conn.commit()
    ex.id = cur.lastrowid
    return ex


def update(conn: sqlite3.Connection, ex: Exercise) -> Exercise:
    if ex.id is None:
        raise ValueError("Cannot update an exercise without an id")
    conn.execute(
        """
        UPDATE exercise
           SET name = ?, modality = ?, category = ?, muscle_groups = ?,
               equipment = ?, metric_type = ?, default_unit = ?, notes = ?
         WHERE id = ?
        """,
        (
            ex.name,
            ex.modality,
            ex.category,
            ex.muscle_groups,
            ex.equipment,
            ex.metric_type,
            ex.default_unit,
            ex.notes,
            ex.id,
        ),
    )
    conn.commit()
    return ex


def delete(conn: sqlite3.Connection, exercise_id: int) -> None:
    conn.execute("DELETE FROM exercise WHERE id = ? AND is_custom = 1", (exercise_id,))
    conn.commit()


def clone(conn: sqlite3.Connection, exercise_id: int, new_name: Optional[str] = None) -> Exercise:
    src = get(conn, exercise_id)
    if src is None:
        raise LookupError(f"Exercise {exercise_id} not found")
    src.id = None
    src.is_custom = True
    src.name = new_name or f"{src.name} (copy)"
    return create(conn, src)
