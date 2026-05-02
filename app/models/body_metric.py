from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class BodyMetric:
    id: Optional[int]
    date: str
    weight_kg: Optional[float] = None
    body_fat_pct: Optional[float] = None
    measurements_json: Optional[str] = None
    notes: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> "BodyMetric":
        return cls(
            id=row["id"],
            date=row["date"],
            weight_kg=row["weight_kg"],
            body_fat_pct=row["body_fat_pct"],
            measurements_json=row["measurements_json"],
            notes=row["notes"],
        )
