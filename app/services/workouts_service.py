"""Validation + persistence helpers for workouts."""

from __future__ import annotations

import sqlite3

from app.models import Workout
from app.repositories import workouts as repo

VALID_MODALITIES = {"gym", "run", "swim", "mixed"}


def validate(workout: Workout) -> None:
    if not workout.name or not workout.name.strip():
        raise ValueError("Workout name is required")
    if workout.modality not in VALID_MODALITIES:
        raise ValueError(f"Modality must be one of {sorted(VALID_MODALITIES)}")
    seen_positions = set()
    for we in workout.exercises:
        if we.exercise_id is None:
            raise ValueError("Each workout entry must reference an exercise")
        if we.position in seen_positions:
            raise ValueError("Workout entries must have unique positions")
        seen_positions.add(we.position)
        if we.sets is not None and we.sets < 1:
            raise ValueError("Sets must be >= 1 if specified")


def save(conn: sqlite3.Connection, workout: Workout) -> Workout:
    workout.name = workout.name.strip()
    validate(workout)
    if workout.id is None:
        return repo.create(conn, workout)
    return repo.update(conn, workout)


def get(conn: sqlite3.Connection, workout_id: int):
    return repo.get(conn, workout_id)


def list_all(conn: sqlite3.Connection, modality=None):
    return repo.list_all(conn, modality=modality)


def delete(conn: sqlite3.Connection, workout_id: int) -> None:
    repo.delete(conn, workout_id)
