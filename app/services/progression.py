"""Simple progressive overload helpers."""

from __future__ import annotations

from app.models import Workout, WorkoutExercise

DEFAULT_GYM_INCREMENT_KG = 2.5
DEFAULT_RUN_INCREMENT_PCT = 0.05  # +5% distance/week
DEFAULT_DELOAD_FRACTION = 0.7
DELOAD_EVERY_N_WEEKS = 4


def is_deload_week(week_index: int) -> bool:
    """Week indices are 0-based; weeks 4, 8, 12... are deloads (week_index % 4 == 3)."""
    return (week_index + 1) % DELOAD_EVERY_N_WEEKS == 0


def progression_modifier(week_index: int) -> float:
    if is_deload_week(week_index):
        return DEFAULT_DELOAD_FRACTION
    return 1.0 + 0.025 * week_index  # +2.5% per non-deload week, capped softly by usage


def project_targets(workout: Workout, week_index: int) -> Workout:
    """Return a *copy-like* projection of the workout with adjusted targets.

    The returned object reuses the original entries but with cloned numbers.
    """
    factor = progression_modifier(week_index)
    projected: list[WorkoutExercise] = []
    for we in workout.exercises:
        nw = WorkoutExercise(
            id=we.id,
            workout_id=we.workout_id,
            exercise_id=we.exercise_id,
            position=we.position,
            sets=we.sets,
            target_reps=we.target_reps,
            target_weight=_scale(we.target_weight, factor, round_to=DEFAULT_GYM_INCREMENT_KG),
            target_distance=_scale(we.target_distance, factor),
            target_duration_sec=we.target_duration_sec,
            target_rpe=we.target_rpe,
            rest_sec=we.rest_sec,
            notes=we.notes,
            exercise_name=we.exercise_name,
            exercise_modality=we.exercise_modality,
            metric_type=we.metric_type,
            default_unit=we.default_unit,
        )
        projected.append(nw)
    workout.exercises = projected
    return workout


def _scale(value, factor: float, round_to: float | None = None):
    if value is None:
        return None
    new_val = value * factor
    if round_to:
        new_val = round(new_val / round_to) * round_to
    return round(new_val, 2)
