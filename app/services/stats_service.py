"""Aggregations for the progress view."""

from __future__ import annotations

import sqlite3
from collections import defaultdict
from datetime import date, datetime, timedelta


def weekly_volume(conn: sqlite3.Connection, weeks: int = 12) -> list[tuple[date, float]]:
    """Sum of weight x reps per ISO week (Mon-anchored), gym only."""
    cutoff = (date.today() - timedelta(weeks=weeks)).isoformat()
    rows = conn.execute(
        """
        SELECT sl.date, s.weight, s.reps
          FROM set_log s
          JOIN session_log sl ON sl.id = s.session_log_id
          JOIN exercise e ON e.id = s.exercise_id
         WHERE e.modality = 'gym'
           AND sl.date >= ?
           AND s.weight IS NOT NULL
           AND s.reps IS NOT NULL
        """,
        (cutoff,),
    ).fetchall()
    bucket: dict[date, float] = defaultdict(float)
    for r in rows:
        d = datetime.strptime(r["date"], "%Y-%m-%d").date()
        anchor = d - timedelta(days=d.weekday())
        bucket[anchor] += (r["weight"] or 0) * (r["reps"] or 0)
    return sorted(bucket.items())


def run_pace_trend(conn: sqlite3.Connection, weeks: int = 12) -> list[tuple[date, float]]:
    """Average pace (sec/km) per session for runs."""
    cutoff = (date.today() - timedelta(weeks=weeks)).isoformat()
    rows = conn.execute(
        """
        SELECT sl.date,
               SUM(s.distance) AS total_dist,
               SUM(s.duration_sec) AS total_secs
          FROM set_log s
          JOIN session_log sl ON sl.id = s.session_log_id
          JOIN exercise e ON e.id = s.exercise_id
         WHERE e.modality = 'run'
           AND sl.date >= ?
           AND s.distance IS NOT NULL
           AND s.duration_sec IS NOT NULL
         GROUP BY sl.id
         ORDER BY sl.date
        """,
        (cutoff,),
    ).fetchall()
    out: list[tuple[date, float]] = []
    for r in rows:
        if not r["total_dist"]:
            continue
        # distance is in km already for default unit; if metres assumed for intervals,
        # values < 50 are likely km, >= 50 likely metres — fold both.
        dist_km = r["total_dist"] if r["total_dist"] < 50 else r["total_dist"] / 1000
        if dist_km <= 0:
            continue
        pace = r["total_secs"] / dist_km
        out.append((datetime.strptime(r["date"], "%Y-%m-%d").date(), pace))
    return out


def swim_pace_trend(conn: sqlite3.Connection, weeks: int = 12) -> list[tuple[date, float]]:
    """Average pace (sec/100m) per swim session."""
    cutoff = (date.today() - timedelta(weeks=weeks)).isoformat()
    rows = conn.execute(
        """
        SELECT sl.date,
               SUM(s.distance) AS total_dist,
               SUM(s.duration_sec) AS total_secs
          FROM set_log s
          JOIN session_log sl ON sl.id = s.session_log_id
          JOIN exercise e ON e.id = s.exercise_id
         WHERE e.modality = 'swim'
           AND sl.date >= ?
           AND s.distance IS NOT NULL
           AND s.duration_sec IS NOT NULL
         GROUP BY sl.id
         ORDER BY sl.date
        """,
        (cutoff,),
    ).fetchall()
    out: list[tuple[date, float]] = []
    for r in rows:
        if not r["total_dist"]:
            continue
        per_100 = r["total_secs"] / (r["total_dist"] / 100)
        out.append((datetime.strptime(r["date"], "%Y-%m-%d").date(), per_100))
    return out


def estimated_one_rm_trend(conn: sqlite3.Connection, exercise_name: str) -> list[tuple[date, float]]:
    """Epley formula: 1RM = weight * (1 + reps/30). Best per session."""
    rows = conn.execute(
        """
        SELECT sl.date, s.weight, s.reps
          FROM set_log s
          JOIN session_log sl ON sl.id = s.session_log_id
          JOIN exercise e ON e.id = s.exercise_id
         WHERE e.name = ?
           AND s.weight IS NOT NULL AND s.reps IS NOT NULL AND s.reps > 0
         ORDER BY sl.date
        """,
        (exercise_name,),
    ).fetchall()
    by_day: dict[date, float] = {}
    for r in rows:
        d = datetime.strptime(r["date"], "%Y-%m-%d").date()
        e1rm = r["weight"] * (1 + r["reps"] / 30)
        by_day[d] = max(by_day.get(d, 0.0), e1rm)
    return sorted(by_day.items())


def weekly_summary(conn: sqlite3.Connection) -> dict[str, int]:
    """Counts of sessions in the last 7 days per modality."""
    cutoff = (date.today() - timedelta(days=7)).isoformat()
    rows = conn.execute(
        """
        SELECT w.modality AS modality, COUNT(*) AS c
          FROM session_log sl
          LEFT JOIN workout w ON w.id = sl.workout_id
         WHERE sl.date >= ? AND sl.status IN ('done','partial')
         GROUP BY w.modality
        """,
        (cutoff,),
    ).fetchall()
    return {r["modality"] or "unknown": r["c"] for r in rows}


def bodyweight_trend(conn: sqlite3.Connection) -> list[tuple[date, float]]:
    rows = conn.execute(
        "SELECT date, weight_kg FROM body_metric"
        " WHERE weight_kg IS NOT NULL ORDER BY date"
    ).fetchall()
    return [(datetime.strptime(r["date"], "%Y-%m-%d").date(), r["weight_kg"]) for r in rows]


def goal_progress(start_value, target_value, current_value) -> float:
    """Return a 0..1 progress value (clamped)."""
    if start_value is None or target_value is None or current_value is None:
        return 0.0
    if target_value == start_value:
        return 1.0 if current_value == target_value else 0.0
    raw = (current_value - start_value) / (target_value - start_value)
    return max(0.0, min(1.0, raw))
