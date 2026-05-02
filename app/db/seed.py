"""Default data: exercises, sample plans, etc. Idempotent."""

from __future__ import annotations

import sqlite3
from datetime import date

# (name, modality, category, muscle_groups, equipment, metric_type, default_unit, notes)
DEFAULT_EXERCISES: list[tuple] = [
    # ---- Gym: compound lifts ----
    ("Back Squat", "gym", "legs", "quads,glutes,core", "barbell", "weight_reps", "kg", None),
    ("Front Squat", "gym", "legs", "quads,core", "barbell", "weight_reps", "kg", None),
    ("Conventional Deadlift", "gym", "pull", "hamstrings,glutes,back", "barbell", "weight_reps", "kg", None),
    ("Romanian Deadlift", "gym", "pull", "hamstrings,glutes", "barbell", "weight_reps", "kg", None),
    ("Bench Press", "gym", "push", "chest,triceps,shoulders", "barbell", "weight_reps", "kg", None),
    ("Incline Dumbbell Press", "gym", "push", "chest,shoulders", "dumbbell", "weight_reps", "kg", None),
    ("Overhead Press", "gym", "push", "shoulders,triceps", "barbell", "weight_reps", "kg", None),
    ("Barbell Row", "gym", "pull", "back,biceps", "barbell", "weight_reps", "kg", None),
    ("Pull-up", "gym", "pull", "lats,biceps", "bodyweight", "reps_only", "reps", None),
    ("Chin-up", "gym", "pull", "lats,biceps", "bodyweight", "reps_only", "reps", None),
    ("Dip", "gym", "push", "chest,triceps", "bodyweight", "reps_only", "reps", None),
    # ---- Gym: accessories ----
    ("Walking Lunge", "gym", "legs", "quads,glutes", "dumbbell", "weight_reps", "kg", None),
    ("Bulgarian Split Squat", "gym", "legs", "quads,glutes", "dumbbell", "weight_reps", "kg", None),
    ("Leg Press", "gym", "legs", "quads,glutes", "machine", "weight_reps", "kg", None),
    ("Leg Curl", "gym", "legs", "hamstrings", "machine", "weight_reps", "kg", None),
    ("Leg Extension", "gym", "legs", "quads", "machine", "weight_reps", "kg", None),
    ("Calf Raise", "gym", "legs", "calves", "machine", "weight_reps", "kg", None),
    ("Lat Pulldown", "gym", "pull", "lats", "cable", "weight_reps", "kg", None),
    ("Seated Cable Row", "gym", "pull", "back", "cable", "weight_reps", "kg", None),
    ("Face Pull", "gym", "pull", "rear-delts,upper-back", "cable", "weight_reps", "kg", None),
    ("Lateral Raise", "gym", "push", "shoulders", "dumbbell", "weight_reps", "kg", None),
    ("Triceps Pushdown", "gym", "push", "triceps", "cable", "weight_reps", "kg", None),
    ("Biceps Curl", "gym", "pull", "biceps", "dumbbell", "weight_reps", "kg", None),
    ("Hammer Curl", "gym", "pull", "biceps,forearms", "dumbbell", "weight_reps", "kg", None),
    ("Plank", "gym", "core", "core", "bodyweight", "time_only", "sec", None),
    ("Hanging Leg Raise", "gym", "core", "core", "bodyweight", "reps_only", "reps", None),
    ("Cable Woodchop", "gym", "core", "core,obliques", "cable", "weight_reps", "kg", None),
    ("Hip Thrust", "gym", "legs", "glutes,hamstrings", "barbell", "weight_reps", "kg", None),
    ("Push-up", "gym", "push", "chest,triceps", "bodyweight", "reps_only", "reps", None),
    ("Goblet Squat", "gym", "legs", "quads,glutes", "dumbbell", "weight_reps", "kg", None),

    # ---- Running ----
    ("Easy Run", "run", "endurance", None, "road", "distance_time", "km",
     "Conversational pace, zone 2"),
    ("Long Run", "run", "endurance", None, "road", "distance_time", "km",
     "Steady, build aerobic base"),
    ("Tempo Run", "run", "threshold", None, "road", "distance_time", "km",
     "Comfortably hard, ~80-85% HRmax"),
    ("Interval 400m", "run", "intervals", None, "track", "distance_time", "m",
     "Repeats with equal or shorter rest"),
    ("Interval 800m", "run", "intervals", None, "track", "distance_time", "m", None),
    ("Interval 1km", "run", "intervals", None, "track", "distance_time", "m", None),
    ("Hill Repeats", "run", "intervals", None, "road", "time_only", "sec",
     "Hard up, jog/walk down"),
    ("Recovery Jog", "run", "recovery", None, "road", "distance_time", "km", None),
    ("Fartlek", "run", "intervals", None, "road", "time_only", "sec",
     "Unstructured surges"),

    # ---- Swimming ----
    ("Continuous Swim", "swim", "endurance", None, "pool", "distance_time", "m", None),
    ("Interval 50m", "swim", "intervals", None, "pool", "distance_time", "m", None),
    ("Interval 100m", "swim", "intervals", None, "pool", "distance_time", "m", None),
    ("Interval 200m", "swim", "intervals", None, "pool", "distance_time", "m", None),
    ("Drill Set", "swim", "technique", None, "pool", "distance_time", "m",
     "Catch-up, fingertip drag, etc."),
    ("Kick Set", "swim", "technique", None, "pool", "distance_time", "m",
     "Kickboard, vary intensity"),
    ("Pull Set", "swim", "technique", None, "pool", "distance_time", "m",
     "Pull buoy, focus on stroke"),
    ("Sprint 25m", "swim", "speed", None, "pool", "distance_time", "m", None),
]


def seed_if_empty(conn: sqlite3.Connection) -> None:
    """Insert default exercises and template plans only if the DB has none."""
    cur = conn.execute("SELECT COUNT(*) AS c FROM exercise")
    if cur.fetchone()["c"] > 0:
        return

    conn.executemany(
        """
        INSERT INTO exercise
            (name, modality, category, muscle_groups, equipment,
             metric_type, default_unit, notes, is_custom)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
        """,
        DEFAULT_EXERCISES,
    )
    _seed_template_workouts(conn)
    _seed_template_plans(conn)
    conn.commit()


def _ex(conn: sqlite3.Connection, name: str) -> int:
    row = conn.execute("SELECT id FROM exercise WHERE name = ?", (name,)).fetchone()
    if row is None:
        raise LookupError(f"Seed exercise missing: {name}")
    return row["id"]


def _seed_template_workouts(conn: sqlite3.Connection) -> None:
    workouts: dict[str, int] = {}

    def add_workout(name: str, modality: str, desc: str, minutes: int) -> int:
        cur = conn.execute(
            "INSERT INTO workout (name, modality, description, estimated_minutes)"
            " VALUES (?, ?, ?, ?)",
            (name, modality, desc, minutes),
        )
        workouts[name] = cur.lastrowid
        return cur.lastrowid

    def add_ex(workout_id: int, position: int, exercise_name: str, **kwargs) -> None:
        conn.execute(
            """
            INSERT INTO workout_exercise
                (workout_id, exercise_id, position, sets, target_reps,
                 target_weight, target_distance, target_duration_sec,
                 target_rpe, rest_sec, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                workout_id,
                _ex(conn, exercise_name),
                position,
                kwargs.get("sets"),
                kwargs.get("target_reps"),
                kwargs.get("target_weight"),
                kwargs.get("target_distance"),
                kwargs.get("target_duration_sec"),
                kwargs.get("target_rpe"),
                kwargs.get("rest_sec"),
                kwargs.get("notes"),
            ),
        )

    # Full Body A
    wid = add_workout("Full Body A", "gym", "Compound focus: squat, bench, row.", 60)
    add_ex(wid, 1, "Back Squat", sets=3, target_reps="5", target_rpe=7, rest_sec=180)
    add_ex(wid, 2, "Bench Press", sets=3, target_reps="5", target_rpe=7, rest_sec=180)
    add_ex(wid, 3, "Barbell Row", sets=3, target_reps="8", target_rpe=7, rest_sec=120)
    add_ex(wid, 4, "Plank", sets=3, target_duration_sec=45, rest_sec=60)

    # Full Body B
    wid = add_workout("Full Body B", "gym", "Hinge + press + pull-up.", 60)
    add_ex(wid, 1, "Romanian Deadlift", sets=3, target_reps="6", target_rpe=7, rest_sec=180)
    add_ex(wid, 2, "Overhead Press", sets=3, target_reps="6", target_rpe=7, rest_sec=180)
    add_ex(wid, 3, "Pull-up", sets=3, target_reps="5-10", rest_sec=120)
    add_ex(wid, 4, "Walking Lunge", sets=3, target_reps="10", target_rpe=7, rest_sec=90)

    # Easy 5K
    wid = add_workout("Easy 5K", "run", "Conversational pace, zone 2.", 35)
    add_ex(wid, 1, "Easy Run", target_distance=5.0, target_rpe=4)

    # 5K Long Run
    wid = add_workout("Long Run", "run", "Build aerobic base, steady effort.", 70)
    add_ex(wid, 1, "Long Run", target_distance=8.0, target_rpe=5)

    # 5K Intervals
    wid = add_workout("400m Intervals", "run", "6x400m with 90s rest.", 45)
    add_ex(wid, 1, "Interval 400m", sets=6, target_distance=400, target_rpe=8, rest_sec=90)

    # Tempo
    wid = add_workout("Tempo 4K", "run", "Comfortably hard 4 km tempo.", 40)
    add_ex(wid, 1, "Tempo Run", target_distance=4.0, target_rpe=8)

    # Swim continuous
    wid = add_workout("Continuous 1000m", "swim", "Steady, no stopping.", 35)
    add_ex(wid, 1, "Continuous Swim", target_distance=1000, target_rpe=5)

    # Swim intervals
    wid = add_workout("10x100m Swim", "swim", "10x100m on 30s rest.", 40)
    add_ex(wid, 1, "Interval 100m", sets=10, target_distance=100, target_rpe=8, rest_sec=30)

    # Swim technique
    wid = add_workout("Technique Set", "swim", "Drills + kick + pull.", 40)
    add_ex(wid, 1, "Drill Set", target_distance=400, notes="Catch-up + fingertip drag")
    add_ex(wid, 2, "Kick Set", target_distance=300)
    add_ex(wid, 3, "Pull Set", target_distance=300)


def _seed_template_plans(conn: sqlite3.Connection) -> None:
    """Three starter plans, all created inactive starting today."""
    today = date.today().isoformat()

    def w_id(name: str) -> int | None:
        row = conn.execute("SELECT id FROM workout WHERE name = ?", (name,)).fetchone()
        return row["id"] if row else None

    plans = [
        {
            "name": "Beginner Strength + Conditioning (8 wk)",
            "goal_type": "general",
            "weeks": 8,
            "schedule": [
                # (day_of_week, workout_name)
                (0, "Full Body A"),
                (2, "Easy 5K"),
                (4, "Full Body B"),
                (6, "Long Run"),
            ],
        },
        {
            "name": "5K Build (6 wk)",
            "goal_type": "endurance",
            "weeks": 6,
            "schedule": [
                (0, "Easy 5K"),
                (2, "400m Intervals"),
                (4, "Tempo 4K"),
                (6, "Long Run"),
            ],
        },
        {
            "name": "General Fitness Mixed (4 wk)",
            "goal_type": "general",
            "weeks": 4,
            "schedule": [
                (0, "Full Body A"),
                (1, "Continuous 1000m"),
                (3, "Easy 5K"),
                (5, "Full Body B"),
            ],
        },
    ]

    for p in plans:
        cur = conn.execute(
            "INSERT INTO plan (name, goal_type, start_date, weeks, notes, is_active)"
            " VALUES (?, ?, ?, ?, ?, 0)",
            (p["name"], p["goal_type"], today, p["weeks"], "Seeded template"),
        )
        plan_id = cur.lastrowid
        for week_index in range(p["weeks"]):
            for dow, w_name in p["schedule"]:
                wid = w_id(w_name)
                if wid is None:
                    continue
                # Apply a deload modifier every fourth week as a starter rule.
                modifier = 0.7 if (week_index + 1) % 4 == 0 else 1.0
                conn.execute(
                    "INSERT INTO plan_slot"
                    " (plan_id, week_index, day_of_week, workout_id, intensity_modifier)"
                    " VALUES (?, ?, ?, ?, ?)",
                    (plan_id, week_index, dow, wid, modifier),
                )
