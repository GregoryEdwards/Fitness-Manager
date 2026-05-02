from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Goal:
    id: Optional[int]
    description: str
    metric: Optional[str] = None
    start_value: Optional[float] = None
    target_value: Optional[float] = None
    target_date: Optional[str] = None
    is_achieved: bool = False

    @classmethod
    def from_row(cls, row) -> "Goal":
        return cls(
            id=row["id"],
            description=row["description"],
            metric=row["metric"],
            start_value=row["start_value"],
            target_value=row["target_value"],
            target_date=row["target_date"],
            is_achieved=bool(row["is_achieved"]),
        )
