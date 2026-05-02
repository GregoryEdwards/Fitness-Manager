"""Plan validation, scheduling, and resolution to dated occurrences."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional

from app.models import Plan, PlanSlot
from app.repositories import plans as repo

VALID_GOALS = {"fat_loss", "strength", "endurance", "general", None, ""}


def validate(plan: Plan) -> None:
    if not plan.name or not plan.name.strip():
        raise ValueError("Plan name is required")
    if plan.weeks <= 0:
        raise ValueError("Plan must have at least one week")
    if plan.goal_type not in VALID_GOALS:
        raise ValueError(f"Goal type must be one of {sorted(g for g in VALID_GOALS if g)}")
    try:
        datetime.strptime(plan.start_date, "%Y-%m-%d")
    except (TypeError, ValueError) as exc:
        raise ValueError("start_date must be ISO YYYY-MM-DD") from exc


def save(conn: sqlite3.Connection, plan: Plan) -> Plan:
    plan.name = plan.name.strip()
    validate(plan)
    if plan.id is None:
        return repo.create(conn, plan)
    return repo.update(conn, plan)


def get(conn: sqlite3.Connection, plan_id: int):
    return repo.get(conn, plan_id)


def list_all(conn: sqlite3.Connection):
    return repo.list_all(conn)


def get_active(conn: sqlite3.Connection):
    return repo.get_active(conn)


def set_active(conn: sqlite3.Connection, plan_id: int) -> None:
    repo.set_active(conn, plan_id)


def delete(conn: sqlite3.Connection, plan_id: int) -> None:
    repo.delete(conn, plan_id)


def set_slot(
    conn: sqlite3.Connection,
    plan_id: int,
    week_index: int,
    day_of_week: int,
    workout_id: Optional[int],
    intensity_modifier: float = 1.0,
) -> None:
    if workout_id is None:
        repo.clear_slot(conn, plan_id, week_index, day_of_week)
        return
    slot = PlanSlot(
        id=None,
        plan_id=plan_id,
        week_index=week_index,
        day_of_week=day_of_week,
        workout_id=workout_id,
        intensity_modifier=intensity_modifier,
    )
    repo.upsert_slot(conn, slot)


@dataclass
class ScheduledWorkout:
    plan_id: int
    plan_name: str
    week_index: int
    day_of_week: int
    workout_id: int
    workout_name: str
    workout_modality: str
    intensity_modifier: float
    on_date: date


def resolve_plan_dates(plan: Plan) -> list[ScheduledWorkout]:
    """Expand a plan into concrete dated occurrences."""
    if plan.id is None:
        return []
    start = datetime.strptime(plan.start_date, "%Y-%m-%d").date()
    # Anchor week 0 to the Monday of plan.start_date for predictability.
    anchor_monday = start - timedelta(days=start.weekday())
    out: list[ScheduledWorkout] = []
    for slot in plan.slots:
        if slot.workout_id is None:
            continue
        on_date = anchor_monday + timedelta(weeks=slot.week_index, days=slot.day_of_week)
        if on_date < start:
            continue
        out.append(
            ScheduledWorkout(
                plan_id=plan.id,
                plan_name=plan.name,
                week_index=slot.week_index,
                day_of_week=slot.day_of_week,
                workout_id=slot.workout_id,
                workout_name=slot.workout_name or "",
                workout_modality=slot.workout_modality or "",
                intensity_modifier=slot.intensity_modifier,
                on_date=on_date,
            )
        )
    out.sort(key=lambda s: s.on_date)
    return out


def occurrences_in_range(
    conn: sqlite3.Connection, start: date, end: date
) -> list[ScheduledWorkout]:
    plan = repo.get_active(conn)
    if plan is None:
        return []
    return [s for s in resolve_plan_dates(plan) if start <= s.on_date <= end]


def todays_workout(conn: sqlite3.Connection, today: Optional[date] = None) -> Optional[ScheduledWorkout]:
    today = today or date.today()
    plan = repo.get_active(conn)
    if plan is None:
        return None
    for s in resolve_plan_dates(plan):
        if s.on_date == today:
            return s
    return None
