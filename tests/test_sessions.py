from datetime import date

import pytest

from app.services import sessions_service, workouts_service
from app.models import SessionLog


def test_prefill_creates_one_set_per_planned_set(conn):
    workouts = workouts_service.list_all(conn, modality="gym")
    workout = next(w for w in workouts if w.name == "Full Body A")
    session = sessions_service.prefill_from_workout(
        conn, workout.id, date.today().isoformat()
    )
    full = workouts_service.get(conn, workout.id)
    expected = sum(max(we.sets or 1, 1) for we in full.exercises)
    assert len(session.sets) == expected
    assert all(s.exercise_id is not None for s in session.sets)


def test_save_and_fetch(conn):
    workouts = workouts_service.list_all(conn, modality="run")
    workout = next(w for w in workouts if w.name == "Easy 5K")
    session = sessions_service.prefill_from_workout(
        conn, workout.id, date.today().isoformat()
    )
    session.sets[0].distance = 5.2
    session.sets[0].duration_sec = 28 * 60
    session.perceived_exertion = 6
    session.notes = "Felt good"
    saved = sessions_service.save(conn, session)
    assert saved.id is not None

    fetched = sessions_service.get(conn, saved.id)
    assert fetched.notes == "Felt good"
    assert fetched.sets[0].distance == 5.2
    assert fetched.sets[0].duration_sec == 28 * 60


def test_invalid_status_rejected(conn):
    bad = SessionLog(id=None, date=date.today().isoformat(), status="hammered")
    with pytest.raises(ValueError):
        sessions_service.save(conn, bad)


def test_invalid_date_rejected(conn):
    bad = SessionLog(id=None, date="yesterday", status="done")
    with pytest.raises(ValueError):
        sessions_service.save(conn, bad)
