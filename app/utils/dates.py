"""Date helpers."""

from __future__ import annotations

from datetime import date, datetime, timedelta

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def iso_today() -> str:
    return date.today().isoformat()


def parse_iso(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def week_anchor_monday(d: date) -> date:
    return d - timedelta(days=d.weekday())
