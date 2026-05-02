"""Session logging service."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Optional

from app.models import SessionLog, SetLog
from app.repositories import sessions as repo
from app.repositories import workouts as workouts_repo

VALID_STATUSES = {"done", "partial", "skipped"}


def validate(session: SessionLog) -> None:
    try:
        datetime.strptime(session.date, "%Y-%m-%d")
    except (TypeError, ValueError) as exc:
        raise ValueError("date must be ISO YYYY-MM-DD") from exc
    if session.status not in VALID_STATUSES:
        raise ValueError(f"status must be one of {sorted(VALID_STATUSES)}")
    if session.perceived_exertion is not None and not 1 <= session.perceived_exertion <= 10:
        raise ValueError("perceived_exertion must be 1..10")


def save(conn: sqlite3.Connection, session: SessionLog) -> SessionLog:
    validate(session)
    if session.id is None:
        return repo.create(conn, session)
    return repo.update(conn, session)


def get(conn: sqlite3.Connection, session_id: int):
    return repo.get(conn, session_id)


def list_recent(conn: sqlite3.Connection, limit: int = 30):
    return repo.list_recent(conn, limit=limit)


def list_in_range(conn: sqlite3.Connection, start_iso: str, end_iso: str):
    return repo.list_in_range(conn, start_iso, end_iso)


def delete(conn: sqlite3.Connection, session_id: int) -> None:
    repo.delete(conn, session_id)


def prefill_from_workout(
    conn: sqlite3.Connection,
    workout_id: int,
    on_date: str,
    plan_id: Optional[int] = None,
) -> SessionLog:
    """Build an unsaved SessionLog with one SetLog per planned set."""
    workout = workouts_repo.get(conn, workout_id)
    if workout is None:
        raise LookupError(f"Workout {workout_id} not found")
    sets: list[SetLog] = []
    for we in workout.exercises:
        n_sets = max(we.sets or 1, 1)
        for i in range(1, n_sets + 1):
            sets.append(
                SetLog(
                    id=None,
                    session_log_id=None,
                    exercise_id=we.exercise_id,
                    set_number=i,
                    reps=_parse_reps(we.target_reps),
                    weight=we.target_weight,
                    distance=we.target_distance,
                    duration_sec=we.target_duration_sec,
                    rpe=we.target_rpe,
                    exercise_name=we.exercise_name,
                )
            )
    return SessionLog(
        id=None,
        date=on_date,
        plan_id=plan_id,
        workout_id=workout_id,
        status="done",
        perceived_exertion=None,
        notes=None,
        sets=sets,
        workout_name=workout.name,
    )


def _parse_reps(target_reps: Optional[str]) -> Optional[int]:
    if not target_reps:
        return None
    text = target_reps.strip()
    # If a range like "8-12", default to the lower bound.
    if "-" in text:
        text = text.split("-", 1)[0].strip()
    try:
        return int(text)
    except ValueError:
        return None
