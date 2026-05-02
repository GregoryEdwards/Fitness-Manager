from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SetLog:
    id: Optional[int]
    session_log_id: Optional[int]
    exercise_id: int
    set_number: Optional[int] = None
    reps: Optional[int] = None
    weight: Optional[float] = None
    distance: Optional[float] = None
    duration_sec: Optional[int] = None
    rpe: Optional[int] = None
    exercise_name: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> "SetLog":
        keys = row.keys()
        return cls(
            id=row["id"],
            session_log_id=row["session_log_id"],
            exercise_id=row["exercise_id"],
            set_number=row["set_number"],
            reps=row["reps"],
            weight=row["weight"],
            distance=row["distance"],
            duration_sec=row["duration_sec"],
            rpe=row["rpe"],
            exercise_name=row["exercise_name"] if "exercise_name" in keys else None,
        )


@dataclass
class SessionLog:
    id: Optional[int]
    date: str
    plan_id: Optional[int] = None
    workout_id: Optional[int] = None
    status: str = "done"
    perceived_exertion: Optional[int] = None
    notes: Optional[str] = None
    sets: list[SetLog] = field(default_factory=list)
    workout_name: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> "SessionLog":
        keys = row.keys()
        return cls(
            id=row["id"],
            date=row["date"],
            plan_id=row["plan_id"],
            workout_id=row["workout_id"],
            status=row["status"],
            perceived_exertion=row["perceived_exertion"],
            notes=row["notes"],
            workout_name=row["workout_name"] if "workout_name" in keys else None,
        )
