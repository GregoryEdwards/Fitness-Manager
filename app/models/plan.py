from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PlanSlot:
    id: Optional[int]
    plan_id: int
    week_index: int
    day_of_week: int            # 0 = Monday … 6 = Sunday
    workout_id: Optional[int] = None
    intensity_modifier: float = 1.0
    workout_name: Optional[str] = None
    workout_modality: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> "PlanSlot":
        keys = row.keys()
        return cls(
            id=row["id"],
            plan_id=row["plan_id"],
            week_index=row["week_index"],
            day_of_week=row["day_of_week"],
            workout_id=row["workout_id"],
            intensity_modifier=row["intensity_modifier"],
            workout_name=row["workout_name"] if "workout_name" in keys else None,
            workout_modality=row["workout_modality"] if "workout_modality" in keys else None,
        )


@dataclass
class Plan:
    id: Optional[int]
    name: str
    goal_type: Optional[str]
    start_date: str             # ISO YYYY-MM-DD
    weeks: int
    notes: Optional[str] = None
    is_active: bool = False
    slots: list[PlanSlot] = field(default_factory=list)

    @classmethod
    def from_row(cls, row) -> "Plan":
        return cls(
            id=row["id"],
            name=row["name"],
            goal_type=row["goal_type"],
            start_date=row["start_date"],
            weeks=row["weeks"],
            notes=row["notes"],
            is_active=bool(row["is_active"]),
        )
