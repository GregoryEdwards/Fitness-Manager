"""Settings: theme, units, week start, export/import/backup."""

from __future__ import annotations

from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from app import config
from app.config import Settings
from app.services import io_service
from app.ui.widgets import ViewHeader


class SettingsView(ctk.CTkFrame):
    def __init__(self, master, app) -> None:
        super().__init__(master, fg_color="transparent")
        self.app = app

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        ViewHeader(
            self, "Settings",
            subtitle="Personalise the app and manage your local data.",
        ).grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 12))

        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 20))
        self._build_appearance(body)
        self._build_units(body)
        self._build_data(body)

    # ---------------------------------------------------------- appearance
    def _build_appearance(self, parent) -> None:
        card = _Card(parent, "Appearance")
        card.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(card.body, text="Theme").pack(anchor="w")
        self.theme_var = ctk.StringVar(value=self.app.settings.theme)
        ctk.CTkOptionMenu(
            card.body, values=["System", "Light", "Dark"],
            variable=self.theme_var, command=self._change_theme,
        ).pack(anchor="w", pady=(2, 12))

        ctk.CTkLabel(card.body, text="Color theme").pack(anchor="w")
        self.color_var = ctk.StringVar(value=self.app.settings.color_theme)
        ctk.CTkOptionMenu(
            card.body, values=["blue", "green", "dark-blue"],
            variable=self.color_var, command=self._change_color,
        ).pack(anchor="w", pady=(2, 0))
        ctk.CTkLabel(
            card.body, text="(takes effect on next launch)",
            text_color=("gray45", "gray60"),
        ).pack(anchor="w")

    def _change_theme(self, value: str) -> None:
        ctk.set_appearance_mode(value)
        self.app.settings.theme = value
        self.app.settings.save()

    def _change_color(self, value: str) -> None:
        self.app.settings.color_theme = value
        self.app.settings.save()

    # --------------------------------------------------------------- units
    def _build_units(self, parent) -> None:
        card = _Card(parent, "Units & week")
        card.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(card.body, text="Units").pack(anchor="w")
        self.units_var = ctk.StringVar(value=self.app.settings.units)
        ctk.CTkOptionMenu(
            card.body, values=["metric", "imperial"],
            variable=self.units_var, command=self._change_units,
        ).pack(anchor="w", pady=(2, 12))

        ctk.CTkLabel(card.body, text="Week starts on").pack(anchor="w")
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        self.week_var = ctk.StringVar(value=days[self.app.settings.week_start])
        ctk.CTkOptionMenu(
            card.body, values=days, variable=self.week_var,
            command=lambda v: self._change_week_start(days.index(v)),
        ).pack(anchor="w", pady=(2, 0))

    def _change_units(self, value: str) -> None:
        self.app.settings.units = value
        self.app.settings.save()

    def _change_week_start(self, idx: int) -> None:
        self.app.settings.week_start = idx
        self.app.settings.save()

    # ----------------------------------------------------- import/export
    def _build_data(self, parent) -> None:
        card = _Card(parent, "Data")
        card.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            card.body, text=f"Database: {config.db_path()}",
            text_color=("gray35", "gray70"),
        ).pack(anchor="w", pady=(0, 12))

        bar = ctk.CTkFrame(card.body, fg_color="transparent")
        bar.pack(fill="x")
        ctk.CTkButton(bar, text="Export JSON…", command=self._export).pack(side="left", padx=4)
        ctk.CTkButton(bar, text="Import JSON…", command=self._import).pack(side="left", padx=4)
        ctk.CTkButton(
            bar, text="Backup now",
            fg_color="transparent", border_width=1,
            command=self._backup,
        ).pack(side="left", padx=4)

    def _export(self) -> None:
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("All files", "*.*")],
            initialfile="fitness-export.json",
        )
        if not filename:
            return
        path = io_service.export_json(self.app.conn, Path(filename))
        messagebox.showinfo("Exported", f"Saved {path}", parent=self)

    def _import(self) -> None:
        if not messagebox.askyesno(
            "Import",
            "Importing replaces the current database contents. Continue?",
            parent=self,
        ):
            return
        filename = filedialog.askopenfilename(
            filetypes=[("JSON", "*.json"), ("All files", "*.*")]
        )
        if not filename:
            return
        try:
            io_service.import_json(self.app.conn, Path(filename))
        except Exception as exc:
            messagebox.showerror("Import failed", str(exc), parent=self)
            return
        messagebox.showinfo("Imported", "Data imported. App will refresh.", parent=self)
        for key in ("dashboard", "library", "workouts", "plans", "calendar", "log", "progress"):
            self.app.refresh_view(key)

    def _backup(self) -> None:
        path = io_service.backup_db()
        messagebox.showinfo("Backup created", f"Backup written to {path}", parent=self)


class _Card(ctk.CTkFrame):
    def __init__(self, master, title: str) -> None:
        super().__init__(master, corner_radius=10)
        ctk.CTkLabel(
            self, text=title, anchor="w",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(fill="x", padx=14, pady=(12, 4))
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=14, pady=(0, 14))
