from app.services.progression import (
    is_deload_week,
    progression_modifier,
    project_targets,
)
from app.models import Workout, WorkoutExercise


def test_deload_every_fourth_week():
    assert not is_deload_week(0)
    assert not is_deload_week(1)
    assert not is_deload_week(2)
    assert is_deload_week(3)        # week 4
    assert not is_deload_week(4)
    assert is_deload_week(7)        # week 8


def test_modifier_rises_then_deloads():
    assert progression_modifier(0) == 1.0
    assert progression_modifier(1) > 1.0
    assert progression_modifier(3) < 1.0


def test_project_targets_scales_weight_to_increment():
    we = WorkoutExercise(
        id=None, workout_id=None, exercise_id=1, position=1,
        sets=3, target_reps="5", target_weight=80.0,
        metric_type="weight_reps",
    )
    workout = Workout(id=None, name="Test", modality="gym", exercises=[we])
    projected = project_targets(workout, week_index=2)  # +5%
    weight = projected.exercises[0].target_weight
    # 80 * 1.05 = 84 → rounded to 2.5 increment is 85.0
    assert weight in (82.5, 85.0)


def test_project_targets_handles_none():
    we = WorkoutExercise(
        id=None, workout_id=None, exercise_id=1, position=1,
        sets=3, target_reps="5", metric_type="reps_only",
    )
    workout = Workout(id=None, name="Bodyweight", modality="gym", exercises=[we])
    projected = project_targets(workout, week_index=1)
    assert projected.exercises[0].target_weight is None
