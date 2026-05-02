"""CRUD for `session_log` and `set_log`."""

from __future__ import annotations

import sqlite3
from typing import Optional

from app.db.connection import transaction
from app.models import SessionLog, SetLog


_SESSION_BASE = """
SELECT sl.*, w.name AS workout_name
  FROM session_log sl
  LEFT JOIN workout w ON w.id = sl.workout_id
"""


def list_recent(conn: sqlite3.Connection, limit: int = 30) -> list[SessionLog]:
    rows = conn.execute(
        _SESSION_BASE + " ORDER BY sl.date DESC, sl.id DESC LIMIT ?", (limit,)
    ).fetchall()
    return [SessionLog.from_row(r) for r in rows]


def list_in_range(conn: sqlite3.Connection, start_iso: str, end_iso: str) -> list[SessionLog]:
    rows = conn.execute(
        _SESSION_BASE + " WHERE sl.date BETWEEN ? AND ? ORDER BY sl.date",
        (start_iso, end_iso),
    ).fetchall()
    return [SessionLog.from_row(r) for r in rows]


def get(conn: sqlite3.Connection, session_id: int) -> Optional[SessionLog]:
    row = conn.execute(_SESSION_BASE + " WHERE sl.id = ?", (session_id,)).fetchone()
    if row is None:
        return None
    session = SessionLog.from_row(row)
    set_rows = conn.execute(
        """
        SELECT s.*, e.name AS exercise_name
          FROM set_log s
          JOIN exercise e ON e.id = s.exercise_id
         WHERE s.session_log_id = ?
         ORDER BY s.id
        """,
        (session_id,),
    ).fetchall()
    session.sets = [SetLog.from_row(r) for r in set_rows]
    return session


def create(conn: sqlite3.Connection, session: SessionLog) -> SessionLog:
    with transaction(conn):
        cur = conn.execute(
            """
            INSERT INTO session_log
                (date, plan_id, workout_id, status, perceived_exertion, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                session.date,
                session.plan_id,
                session.workout_id,
                session.status,
                session.perceived_exertion,
                session.notes,
            ),
        )
        session.id = cur.lastrowid
        for s in session.sets:
            s.session_log_id = session.id
            _insert_set(conn, s)
    return session


def update(conn: sqlite3.Connection, session: SessionLog) -> SessionLog:
    if session.id is None:
        raise ValueError("Cannot update session without id")
    with transaction(conn):
        conn.execute(
            """
            UPDATE session_log
               SET date = ?, plan_id = ?, workout_id = ?, status = ?,
                   perceived_exertion = ?, notes = ?
             WHERE id = ?
            """,
            (
                session.date,
                session.plan_id,
                session.workout_id,
                session.status,
                session.perceived_exertion,
                session.notes,
                session.id,
            ),
        )
        conn.execute("DELETE FROM set_log WHERE session_log_id = ?", (session.id,))
        for s in session.sets:
            s.session_log_id = session.id
            _insert_set(conn, s)
    return session


def delete(conn: sqlite3.Connection, session_id: int) -> None:
    with transaction(conn):
        conn.execute("DELETE FROM session_log WHERE id = ?", (session_id,))


def _insert_set(conn: sqlite3.Connection, s: SetLog) -> None:
    conn.execute(
        """
        INSERT INTO set_log
            (session_log_id, exercise_id, set_number, reps,
             weight, distance, duration_sec, rpe)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            s.session_log_id,
            s.exercise_id,
            s.set_number,
            s.reps,
            s.weight,
            s.distance,
            s.duration_sec,
            s.rpe,
        ),
    )
