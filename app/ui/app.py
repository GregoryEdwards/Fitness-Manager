"""Root window and navigation."""

from __future__ import annotations

import sqlite3
from typing import Callable

import customtkinter as ctk

from app import config
from app.config import Settings
from app.db.connection import ensure_initialised


NAV_ITEMS = [
    ("Dashboard", "dashboard"),
    ("Library", "library"),
    ("Workouts", "workouts"),
    ("Plans", "plans"),
    ("Calendar", "calendar"),
    ("Log", "log"),
    ("Progress", "progress"),
    ("Settings", "settings"),
]


class FitnessPlannerApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.settings: Settings = Settings.load()
        ctk.set_appearance_mode(self.settings.theme)
        ctk.set_default_color_theme(self.settings.color_theme)

        self.title(config.APP_NAME)
        self.geometry("1180x780")
        self.minsize(960, 640)

        self.conn: sqlite3.Connection = ensure_initialised()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_nav()
        self._build_content_area()

        self._views: dict[str, ctk.CTkFrame] = {}
        self._current_key: str | None = None
        self.show("dashboard")

    # ----------------------------------------------------------- nav
    def _build_nav(self) -> None:
        nav = ctk.CTkFrame(self, width=190, corner_radius=0)
        nav.grid(row=0, column=0, sticky="nsw")
        nav.grid_rowconfigure(len(NAV_ITEMS) + 1, weight=1)

        title = ctk.CTkLabel(
            nav, text=config.APP_NAME,
            font=ctk.CTkFont(size=18, weight="bold"),
            anchor="w",
        )
        title.grid(row=0, column=0, padx=18, pady=(20, 14), sticky="w")

        self._nav_buttons: dict[str, ctk.CTkButton] = {}
        for idx, (label, key) in enumerate(NAV_ITEMS, start=1):
            btn = ctk.CTkButton(
                nav,
                text=label,
                anchor="w",
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray85", "gray25"),
                corner_radius=6,
                command=self._make_nav_handler(key),
            )
            btn.grid(row=idx, column=0, padx=10, pady=2, sticky="ew")
            self._nav_buttons[key] = btn

        version = ctk.CTkLabel(nav, text="v0.1.0", text_color=("gray50", "gray60"))
        version.grid(row=len(NAV_ITEMS) + 2, column=0, pady=12)

    def _make_nav_handler(self, key: str) -> Callable[[], None]:
        return lambda: self.show(key)

    def _build_content_area(self) -> None:
        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray95", "gray13"))
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

    # ----------------------------------------------------------- routing
    def show(self, key: str) -> None:
        if self._current_key == key:
            return
        if key not in self._views:
            self._views[key] = self._build_view(key)
        for k, v in self._views.items():
            v.grid_remove()
        view = self._views[key]
        view.grid(row=0, column=0, sticky="nsew")
        if hasattr(view, "on_show"):
            view.on_show()
        self._current_key = key
        self._highlight_nav(key)

    def _highlight_nav(self, key: str) -> None:
        for k, btn in self._nav_buttons.items():
            if k == key:
                btn.configure(fg_color=("gray80", "gray30"))
            else:
                btn.configure(fg_color="transparent")

    def _build_view(self, key: str) -> ctk.CTkFrame:
        # Local imports avoid loading every view at startup.
        if key == "dashboard":
            from app.ui.views.dashboard import DashboardView
            return DashboardView(self.content, self)
        if key == "library":
            from app.ui.views.exercise_library import ExerciseLibraryView
            return ExerciseLibraryView(self.content, self)
        if key == "workouts":
            from app.ui.views.workout_editor import WorkoutListView
            return WorkoutListView(self.content, self)
        if key == "plans":
            from app.ui.views.plan_builder import PlanListView
            return PlanListView(self.content, self)
        if key == "calendar":
            from app.ui.views.calendar_view import CalendarView
            return CalendarView(self.content, self)
        if key == "log":
            from app.ui.views.log_view import LogView
            return LogView(self.content, self)
        if key == "progress":
            from app.ui.views.progress_view import ProgressView
            return ProgressView(self.content, self)
        if key == "settings":
            from app.ui.views.settings_view import SettingsView
            return SettingsView(self.content, self)
        raise ValueError(f"Unknown view: {key}")

    # ----------------------------------------------------------- helpers
    def refresh_view(self, key: str) -> None:
        """Rebuild a view (call after data changes that another view caches)."""
        if key in self._views:
            view = self._views.pop(key)
            view.destroy()
        if self._current_key == key:
            self._current_key = None
            self.show(key)


def run() -> None:
    app = FitnessPlannerApp()
    app.mainloop()
