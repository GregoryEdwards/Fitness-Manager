from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class WorkoutExercise:
    id: Optional[int]
    workout_id: Optional[int]
    exercise_id: int
    position: int
    sets: Optional[int] = None
    target_reps: Optional[str] = None
    target_weight: Optional[float] = None
    target_distance: Optional[float] = None
    target_duration_sec: Optional[int] = None
    target_rpe: Optional[int] = None
    rest_sec: Optional[int] = None
    notes: Optional[str] = None
    # Convenience for UI rendering — populated by repo joins.
    exercise_name: Optional[str] = None
    exercise_modality: Optional[str] = None
    metric_type: Optional[str] = None
    default_unit: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> "WorkoutExercise":
        keys = row.keys()
        return cls(
            id=row["id"],
            workout_id=row["workout_id"],
            exercise_id=row["exercise_id"],
            position=row["position"],
            sets=row["sets"],
            target_reps=row["target_reps"],
            target_weight=row["target_weight"],
            target_distance=row["target_distance"],
            target_duration_sec=row["target_duration_sec"],
            target_rpe=row["target_rpe"],
            rest_sec=row["rest_sec"],
            notes=row["notes"],
            exercise_name=row["exercise_name"] if "exercise_name" in keys else None,
            exercise_modality=row["exercise_modality"] if "exercise_modality" in keys else None,
            metric_type=row["metric_type"] if "metric_type" in keys else None,
            default_unit=row["default_unit"] if "default_unit" in keys else None,
        )


@dataclass
class Workout:
    id: Optional[int]
    name: str
    modality: str
    description: Optional[str] = None
    estimated_minutes: Optional[int] = None
    exercises: list[WorkoutExercise] = field(default_factory=list)

    @classmethod
    def from_row(cls, row) -> "Workout":
        return cls(
            id=row["id"],
            name=row["name"],
            modality=row["modality"],
            description=row["description"],
            estimated_minutes=row["estimated_minutes"],
        )
