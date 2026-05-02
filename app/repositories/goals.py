"""CRUD for `goal`."""

from __future__ import annotations

import sqlite3
from typing import Optional

from app.models import Goal


def list_all(conn: sqlite3.Connection, include_achieved: bool = True) -> list[Goal]:
    sql = "SELECT * FROM goal"
    if not include_achieved:
        sql += " WHERE is_achieved = 0"
    sql += " ORDER BY is_achieved, COALESCE(target_date, '9999-12-31')"
    return [Goal.from_row(r) for r in conn.execute(sql)]


def get(conn: sqlite3.Connection, goal_id: int) -> Optional[Goal]:
    row = conn.execute("SELECT * FROM goal WHERE id = ?", (goal_id,)).fetchone()
    return Goal.from_row(row) if row else None


def create(conn: sqlite3.Connection, goal: Goal) -> Goal:
    cur = conn.execute(
        """
        INSERT INTO goal
            (description, metric, start_value, target_value, target_date, is_achieved)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            goal.description,
            goal.metric,
            goal.start_value,
            goal.target_value,
            goal.target_date,
            int(goal.is_achieved),
        ),
    )
    conn.commit()
    goal.id = cur.lastrowid
    return goal


def update(conn: sqlite3.Connection, goal: Goal) -> Goal:
    if goal.id is None:
        raise ValueError("Cannot update goal without id")
    conn.execute(
        """
        UPDATE goal
           SET description = ?, metric = ?, start_value = ?,
               target_value = ?, target_date = ?, is_achieved = ?
         WHERE id = ?
        """,
        (
            goal.description,
            goal.metric,
            goal.start_value,
            goal.target_value,
            goal.target_date,
            int(goal.is_achieved),
            goal.id,
        ),
    )
    conn.commit()
    return goal


def delete(conn: sqlite3.Connection, goal_id: int) -> None:
    conn.execute("DELETE FROM goal WHERE id = ?", (goal_id,))
    conn.commit()
