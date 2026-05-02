# Fitness Planner

A local-first, single-user desktop app for planning and tracking gym, running and
swimming workouts. Built with Python + CustomTkinter + SQLite. No accounts, no
cloud, no internet required after install.

## Features

- **Dashboard** — today's planned workout, weekly summary, active goals, recent sessions.
- **Exercise Library** — searchable catalog of ~45 seeded exercises across gym, run and
  swim modalities. Add, edit, clone or delete custom exercises.
- **Workout Editor** — compose workouts with metric-aware fields (weight×reps for
  the gym, distance/time for runs and swims), reorder, set rest and RPE.
- **Plan Builder** — multi-week schedules in a week × day grid. Auto-applies a
  deload modifier every 4th week.
- **Calendar** — monthly view that overlays planned workouts with logged sessions.
- **Session Log** — pre-fills targets from the planned workout, edit actual reps,
  weight, distance, time and RPE; "repeat last set" and add/remove rows.
- **Progress** — goals with target dates, body weight log, and matplotlib charts
  for gym volume, run pace and swim pace.
- **Settings** — theme (light/dark/system), units (metric/imperial), week-start
  day, JSON export/import and one-click DB backup.

All data lives in `~/.fitness_planner/fitness.db` (override with the
`FITNESS_PLANNER_DATA_DIR` environment variable).

## Requirements

- Python 3.11+
- Tkinter must be available to your Python install:
  - **Debian/Ubuntu:** `sudo apt-get install python3-tk`
  - **Fedora:** `sudo dnf install python3-tkinter`
  - **macOS / Windows:** ships with python.org installers.

## Install & run

```bash
python -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install -e .
python -m app.main                  # or:  fitness-planner
```

On first launch the app creates `~/.fitness_planner/fitness.db`, applies the
schema and seeds default exercises and three starter plans.

## Project layout

```
app/
├── main.py                 # entry point
├── config.py               # paths, settings persistence
├── db/
│   ├── schema.sql          # canonical schema
│   ├── connection.py       # connection + init
│   └── seed.py             # default exercises, workouts, plans
├── models/                 # dataclasses
├── repositories/           # SQL CRUD per table
├── services/               # validation, plan resolution, stats, export/import
├── utils/                  # date and formatting helpers
└── ui/
    ├── app.py              # root window + nav rail
    ├── views/              # one screen per file
    └── widgets/            # reusable widgets
tests/                      # pytest suite for repos + services
```

The architecture is strict: **UI → services → repositories → db**. The UI never
constructs SQL directly.

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check app tests
black app tests
```

The test suite covers the data layer (repositories + services). The GUI is
exercised manually.

## Build a single-file executable

```bash
pip install pyinstaller
pyinstaller --onefile --windowed -n fitness-planner app/main.py
```

The resulting binary lives in `dist/`.

## Data model

See [`app/db/schema.sql`](app/db/schema.sql). Tables:

- `exercise`, `workout`, `workout_exercise`
- `plan`, `plan_slot`
- `session_log`, `set_log`
- `goal`, `body_metric`

## License

MIT
