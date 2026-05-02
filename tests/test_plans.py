from datetime import date, timedelta

import pytest

from app.models import Plan, PlanSlot
from app.services import plans_service, workouts_service


def _first_workout(conn):
    workouts = workouts_service.list_all(conn)
    assert workouts, "seed should provide template workouts"
    return workouts[0]


def test_save_plan_with_slots(conn):
    w = _first_workout(conn)
    plan = Plan(
        id=None, name="Test plan", goal_type="strength",
        start_date=date.today().isoformat(), weeks=2, is_active=True,
        slots=[
            PlanSlot(id=None, plan_id=0, week_index=0, day_of_week=0,
                     workout_id=w.id, intensity_modifier=1.0),
            PlanSlot(id=None, plan_id=0, week_index=0, day_of_week=2,
                     workout_id=w.id, intensity_modifier=1.0),
        ],
    )
    saved = plans_service.save(conn, plan)
    assert saved.id is not None

    plans_service.set_active(conn, saved.id)
    active = plans_service.get_active(conn)
    assert active is not None
    assert active.id == saved.id
    assert len(active.slots) == 2


def test_resolve_dates_anchors_to_monday(conn):
    w = _first_workout(conn)
    start = date(2026, 5, 4)  # Monday
    plan = Plan(
        id=None, name="Anchor", goal_type="general",
        start_date=start.isoformat(), weeks=1, is_active=False,
        slots=[
            PlanSlot(id=None, plan_id=0, week_index=0, day_of_week=2, workout_id=w.id),
        ],
    )
    saved = plans_service.save(conn, plan)
    occurrences = plans_service.resolve_plan_dates(plans_service.get(conn, saved.id))
    assert occurrences[0].on_date == start + timedelta(days=2)


def test_save_rejects_zero_weeks(conn):
    with pytest.raises(ValueError):
        plans_service.save(
            conn,
            Plan(id=None, name="Bad", goal_type="general",
                 start_date=date.today().isoformat(), weeks=0),
        )
