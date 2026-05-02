-- Canonical schema for Fitness Planner.
-- All tables use INTEGER PRIMARY KEY (rowid alias). Dates stored as ISO-8601 text.

CREATE TABLE IF NOT EXISTS exercise (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    modality TEXT NOT NULL CHECK (modality IN ('gym','run','swim')),
    category TEXT,
    muscle_groups TEXT,
    equipment TEXT,
    metric_type TEXT NOT NULL CHECK (metric_type IN ('weight_reps','distance_time','time_only','reps_only')),
    default_unit TEXT,
    notes TEXT,
    is_custom INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS workout (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    modality TEXT NOT NULL CHECK (modality IN ('gym','run','swim','mixed')),
    description TEXT,
    estimated_minutes INTEGER
);

CREATE TABLE IF NOT EXISTS workout_exercise (
    id INTEGER PRIMARY KEY,
    workout_id INTEGER NOT NULL REFERENCES workout(id) ON DELETE CASCADE,
    exercise_id INTEGER NOT NULL REFERENCES exercise(id),
    position INTEGER NOT NULL,
    sets INTEGER,
    target_reps TEXT,
    target_weight REAL,
    target_distance REAL,
    target_duration_sec INTEGER,
    target_rpe INTEGER,
    rest_sec INTEGER,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS plan (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    goal_type TEXT,
    start_date TEXT NOT NULL,
    weeks INTEGER NOT NULL,
    notes TEXT,
    is_active INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS plan_slot (
    id INTEGER PRIMARY KEY,
    plan_id INTEGER NOT NULL REFERENCES plan(id) ON DELETE CASCADE,
    week_index INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    workout_id INTEGER REFERENCES workout(id),
    intensity_modifier REAL NOT NULL DEFAULT 1.0
);

CREATE TABLE IF NOT EXISTS session_log (
    id INTEGER PRIMARY KEY,
    date TEXT NOT NULL,
    plan_id INTEGER REFERENCES plan(id),
    workout_id INTEGER REFERENCES workout(id),
    status TEXT NOT NULL CHECK (status IN ('done','partial','skipped')),
    perceived_exertion INTEGER,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS set_log (
    id INTEGER PRIMARY KEY,
    session_log_id INTEGER NOT NULL REFERENCES session_log(id) ON DELETE CASCADE,
    exercise_id INTEGER NOT NULL REFERENCES exercise(id),
    set_number INTEGER,
    reps INTEGER,
    weight REAL,
    distance REAL,
    duration_sec INTEGER,
    rpe INTEGER
);

CREATE TABLE IF NOT EXISTS goal (
    id INTEGER PRIMARY KEY,
    description TEXT NOT NULL,
    metric TEXT,
    start_value REAL,
    target_value REAL,
    target_date TEXT,
    is_achieved INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS body_metric (
    id INTEGER PRIMARY KEY,
    date TEXT NOT NULL,
    weight_kg REAL,
    body_fat_pct REAL,
    measurements_json TEXT,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_session_log_date ON session_log(date);
CREATE INDEX IF NOT EXISTS idx_set_log_session ON set_log(session_log_id);
CREATE INDEX IF NOT EXISTS idx_plan_slot_plan ON plan_slot(plan_id, week_index, day_of_week);
CREATE INDEX IF NOT EXISTS idx_exercise_modality ON exercise(modality);
CREATE INDEX IF NOT EXISTS idx_workout_modality ON workout(modality);
