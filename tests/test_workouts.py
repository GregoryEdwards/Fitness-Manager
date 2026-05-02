import pytest

from app.models import Workout, WorkoutExercise
from app.services import exercises_service, workouts_service


def test_save_and_load_roundtrip(conn):
    squat = next(e for e in exercises_service.list_all(conn) if e.name == "Back Squat")
    bench = next(e for e in exercises_service.list_all(conn) if e.name == "Bench Press")
    workout = Workout(
        id=None, name="Push Day", modality="gym",
        description="Test workout", estimated_minutes=45,
        exercises=[
            WorkoutExercise(id=None, workout_id=None, exercise_id=squat.id,
                            position=1, sets=3, target_reps="5", target_weight=80.0),
            WorkoutExercise(id=None, workout_id=None, exercise_id=bench.id,
                            position=2, sets=3, target_reps="5", target_weight=60.0),
        ],
    )
    saved = workouts_service.save(conn, workout)
    assert saved.id is not None

    fetched = workouts_service.get(conn, saved.id)
    assert fetched.name == "Push Day"
    assert len(fetched.exercises) == 2
    assert fetched.exercises[0].exercise_name == "Back Squat"
    assert fetched.exercises[1].target_weight == 60.0


def test_save_rejects_blank_name(conn):
    with pytest.raises(ValueError):
        workouts_service.save(conn, Workout(id=None, name="   ", modality="gym"))
