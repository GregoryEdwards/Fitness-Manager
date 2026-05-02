from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Exercise:
    id: Optional[int]
    name: str
    modality: str               # 'gym' | 'run' | 'swim'
    category: Optional[str] = None
    muscle_groups: Optional[str] = None
    equipment: Optional[str] = None
    metric_type: str = "weight_reps"
    default_unit: Optional[str] = None
    notes: Optional[str] = None
    is_custom: bool = True

    @classmethod
    def from_row(cls, row) -> "Exercise":
        return cls(
            id=row["id"],
            name=row["name"],
            modality=row["modality"],
            category=row["category"],
            muscle_groups=row["muscle_groups"],
            equipment=row["equipment"],
            metric_type=row["metric_type"],
            default_unit=row["default_unit"],
            notes=row["notes"],
            is_custom=bool(row["is_custom"]),
        )
