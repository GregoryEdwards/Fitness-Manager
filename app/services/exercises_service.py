"""Validation + thin wrappers around the exercise repository."""

from __future__ import annotations

import sqlite3

from app.models import Exercise
from app.repositories import exercises as repo

VALID_MODALITIES = {"gym", "run", "swim"}
VALID_METRIC_TYPES = {"weight_reps", "distance_time", "time_only", "reps_only"}


def validate(ex: Exercise) -> None:
    if not ex.name or not ex.name.strip():
        raise ValueError("Exercise name is required")
    if ex.modality not in VALID_MODALITIES:
        raise ValueError(f"Modality must be one of {sorted(VALID_MODALITIES)}")
    if ex.metric_type not in VALID_METRIC_TYPES:
        raise ValueError(f"Metric type must be one of {sorted(VALID_METRIC_TYPES)}")


def create(conn: sqlite3.Connection, ex: Exercise) -> Exercise:
    ex.name = ex.name.strip()
    ex.is_custom = True
    validate(ex)
    return repo.create(conn, ex)


def update(conn: sqlite3.Connection, ex: Exercise) -> Exercise:
    if not ex.is_custom:
        raise ValueError("Built-in exercises cannot be edited; clone first")
    ex.name = ex.name.strip()
    validate(ex)
    return repo.update(conn, ex)


def delete(conn: sqlite3.Connection, exercise_id: int) -> None:
    ex = repo.get(conn, exercise_id)
    if ex is None:
        return
    if not ex.is_custom:
        raise ValueError("Built-in exercises cannot be deleted")
    repo.delete(conn, exercise_id)


def list_all(conn: sqlite3.Connection, modality=None, search=None):
    return repo.list_all(conn, modality=modality, search=search)


def get(conn: sqlite3.Connection, exercise_id: int):
    return repo.get(conn, exercise_id)


def clone(conn: sqlite3.Connection, exercise_id: int, new_name=None):
    return repo.clone(conn, exercise_id, new_name)
