"""CRUD for `workout` and `workout_exercise`."""

from __future__ import annotations

import sqlite3
from typing import Optional

from app.db.connection import transaction
from app.models import Workout, WorkoutExercise

_WORKOUT_EX_JOIN = """
SELECT we.*,
       e.name AS exercise_name,
       e.modality AS exercise_modality,
       e.metric_type AS metric_type,
       e.default_unit AS default_unit
  FROM workout_exercise we
  JOIN exercise e ON e.id = we.exercise_id
 WHERE we.workout_id = ?
 ORDER BY we.position
"""


def list_all(conn: sqlite3.Connection, modality: Optional[str] = None) -> list[Workout]:
    sql = "SELECT * FROM workout"
    params: list = []
    if modality:
        sql += " WHERE modality = ?"
        params.append(modality)
    sql += " ORDER BY name"
    return [Workout.from_row(r) for r in conn.execute(sql, params)]


def get(conn: sqlite3.Connection, workout_id: int) -> Optional[Workout]:
    row = conn.execute("SELECT * FROM workout WHERE id = ?", (workout_id,)).fetchone()
    if row is None:
        return None
    workout = Workout.from_row(row)
    workout.exercises = [
        WorkoutExercise.from_row(r) for r in conn.execute(_WORKOUT_EX_JOIN, (workout_id,))
    ]
    return workout


def create(conn: sqlite3.Connection, workout: Workout) -> Workout:
    with transaction(conn):
        cur = conn.execute(
            "INSERT INTO workout (name, modality, description, estimated_minutes)"
            " VALUES (?, ?, ?, ?)",
            (workout.name, workout.modality, workout.description, workout.estimated_minutes),
        )
        workout.id = cur.lastrowid
        for idx, we in enumerate(workout.exercises, start=1):
            we.workout_id = workout.id
            we.position = idx
            _insert_workout_exercise(conn, we)
    return workout


def update(conn: sqlite3.Connection, workout: Workout) -> Workout:
    if workout.id is None:
        raise ValueError("Cannot update workout without id")
    with transaction(conn):
        conn.execute(
            "UPDATE workout SET name = ?, modality = ?, description = ?, estimated_minutes = ?"
            " WHERE id = ?",
            (
                workout.name,
                workout.modality,
                workout.description,
                workout.estimated_minutes,
                workout.id,
            ),
        )
        conn.execute("DELETE FROM workout_exercise WHERE workout_id = ?", (workout.id,))
        for idx, we in enumerate(workout.exercises, start=1):
            we.workout_id = workout.id
            we.position = idx
            _insert_workout_exercise(conn, we)
    return workout


def delete(conn: sqlite3.Connection, workout_id: int) -> None:
    with transaction(conn):
        conn.execute("DELETE FROM workout WHERE id = ?", (workout_id,))


def _insert_workout_exercise(conn: sqlite3.Connection, we: WorkoutExercise) -> None:
    conn.execute(
        """
        INSERT INTO workout_exercise
            (workout_id, exercise_id, position, sets, target_reps,
             target_weight, target_distance, target_duration_sec,
             target_rpe, rest_sec, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            we.workout_id,
            we.exercise_id,
            we.position,
            we.sets,
            we.target_reps,
            we.target_weight,
            we.target_distance,
            we.target_duration_sec,
            we.target_rpe,
            we.rest_sec,
            we.notes,
        ),
    )
