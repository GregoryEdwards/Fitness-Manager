"""Paths, constants and runtime configuration."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

APP_NAME = "Fitness Planner"
APP_DIR_NAME = ".fitness_planner"


def _default_data_dir() -> Path:
    override = os.environ.get("FITNESS_PLANNER_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()
    return Path.home() / APP_DIR_NAME


DATA_DIR: Path = _default_data_dir()
DB_FILENAME = "fitness.db"
SETTINGS_FILENAME = "settings.json"


def db_path() -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR / DB_FILENAME


def settings_path() -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR / SETTINGS_FILENAME


@dataclass
class Settings:
    units: str = "metric"          # 'metric' or 'imperial'
    week_start: int = 0            # 0 = Monday … 6 = Sunday
    theme: str = "System"          # 'Light' | 'Dark' | 'System'
    color_theme: str = "blue"      # CustomTkinter color theme
    db_location: str = field(default_factory=lambda: str(db_path()))

    def save(self) -> None:
        path = settings_path()
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    @classmethod
    def load(cls) -> "Settings":
        path = settings_path()
        if not path.exists():
            s = cls()
            s.save()
            return s
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return cls()
        # Ignore unknown keys
        valid = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in valid})
