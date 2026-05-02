from app.models import Exercise
from app.services import exercises_service
import pytest


def test_seed_loads_default_exercises(conn):
    items = exercises_service.list_all(conn)
    assert len(items) >= 30
    names = {e.name for e in items}
    assert "Back Squat" in names
    assert "Easy Run" in names
    assert "Continuous Swim" in names


def test_create_and_search_custom(conn):
    new = exercises_service.create(
        conn,
        Exercise(id=None, name="Sled Push", modality="gym", metric_type="weight_reps",
                 muscle_groups="legs,core"),
    )
    assert new.id is not None
    found = exercises_service.list_all(conn, search="sled")
    assert any(e.id == new.id for e in found)


def test_cannot_delete_builtin(conn):
    builtins = [e for e in exercises_service.list_all(conn) if not e.is_custom]
    with pytest.raises(ValueError):
        exercises_service.delete(conn, builtins[0].id)


def test_validate_rejects_bad_modality(conn):
    with pytest.raises(ValueError):
        exercises_service.create(
            conn,
            Exercise(id=None, name="X", modality="badminton", metric_type="reps_only"),
        )
