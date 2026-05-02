"""CRUD for `plan` and `plan_slot`."""

from __future__ import annotations

import sqlite3
from typing import Optional

from app.db.connection import transaction
from app.models import Plan, PlanSlot


_SLOT_JOIN = """
SELECT ps.*,
       w.name AS workout_name,
       w.modality AS workout_modality
  FROM plan_slot ps
  LEFT JOIN workout w ON w.id = ps.workout_id
 WHERE ps.plan_id = ?
 ORDER BY ps.week_index, ps.day_of_week
"""


def list_all(conn: sqlite3.Connection) -> list[Plan]:
    rows = conn.execute("SELECT * FROM plan ORDER BY is_active DESC, name").fetchall()
    return [Plan.from_row(r) for r in rows]


def get(conn: sqlite3.Connection, plan_id: int) -> Optional[Plan]:
    row = conn.execute("SELECT * FROM plan WHERE id = ?", (plan_id,)).fetchone()
    if row is None:
        return None
    plan = Plan.from_row(row)
    plan.slots = [PlanSlot.from_row(r) for r in conn.execute(_SLOT_JOIN, (plan_id,))]
    return plan


def get_active(conn: sqlite3.Connection) -> Optional[Plan]:
    row = conn.execute("SELECT * FROM plan WHERE is_active = 1 LIMIT 1").fetchone()
    return get(conn, row["id"]) if row else None


def create(conn: sqlite3.Connection, plan: Plan) -> Plan:
    with transaction(conn):
        cur = conn.execute(
            "INSERT INTO plan (name, goal_type, start_date, weeks, notes, is_active)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (
                plan.name,
                plan.goal_type,
                plan.start_date,
                plan.weeks,
                plan.notes,
                int(plan.is_active),
            ),
        )
        plan.id = cur.lastrowid
        for slot in plan.slots:
            slot.plan_id = plan.id
            _insert_slot(conn, slot)
    return plan


def update(conn: sqlite3.Connection, plan: Plan) -> Plan:
    if plan.id is None:
        raise ValueError("Cannot update plan without id")
    with transaction(conn):
        conn.execute(
            """
            UPDATE plan
               SET name = ?, goal_type = ?, start_date = ?, weeks = ?,
                   notes = ?, is_active = ?
             WHERE id = ?
            """,
            (
                plan.name,
                plan.goal_type,
                plan.start_date,
                plan.weeks,
                plan.notes,
                int(plan.is_active),
                plan.id,
            ),
        )
        conn.execute("DELETE FROM plan_slot WHERE plan_id = ?", (plan.id,))
        for slot in plan.slots:
            slot.plan_id = plan.id
            _insert_slot(conn, slot)
    return plan


def delete(conn: sqlite3.Connection, plan_id: int) -> None:
    with transaction(conn):
        conn.execute("DELETE FROM plan WHERE id = ?", (plan_id,))


def set_active(conn: sqlite3.Connection, plan_id: int) -> None:
    with transaction(conn):
        conn.execute("UPDATE plan SET is_active = 0")
        conn.execute("UPDATE plan SET is_active = 1 WHERE id = ?", (plan_id,))


def upsert_slot(conn: sqlite3.Connection, slot: PlanSlot) -> PlanSlot:
    """Set or replace the slot for a (plan, week, day) cell."""
    with transaction(conn):
        existing = conn.execute(
            "SELECT id FROM plan_slot WHERE plan_id = ? AND week_index = ? AND day_of_week = ?",
            (slot.plan_id, slot.week_index, slot.day_of_week),
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE plan_slot SET workout_id = ?, intensity_modifier = ? WHERE id = ?",
                (slot.workout_id, slot.intensity_modifier, existing["id"]),
            )
            slot.id = existing["id"]
        else:
            cur = conn.execute(
                "INSERT INTO plan_slot"
                " (plan_id, week_index, day_of_week, workout_id, intensity_modifier)"
                " VALUES (?, ?, ?, ?, ?)",
                (
                    slot.plan_id,
                    slot.week_index,
                    slot.day_of_week,
                    slot.workout_id,
                    slot.intensity_modifier,
                ),
            )
            slot.id = cur.lastrowid
    return slot


def clear_slot(conn: sqlite3.Connection, plan_id: int, week_index: int, day_of_week: int) -> None:
    with transaction(conn):
        conn.execute(
            "DELETE FROM plan_slot WHERE plan_id = ? AND week_index = ? AND day_of_week = ?",
            (plan_id, week_index, day_of_week),
        )


def _insert_slot(conn: sqlite3.Connection, slot: PlanSlot) -> None:
    cur = conn.execute(
        "INSERT INTO plan_slot"
        " (plan_id, week_index, day_of_week, workout_id, intensity_modifier)"
        " VALUES (?, ?, ?, ?, ?)",
        (
            slot.plan_id,
            slot.week_index,
            slot.day_of_week,
            slot.workout_id,
            slot.intensity_modifier,
        ),
    )
    slot.id = cur.lastrowid
