"""Session logging view: prefilled targets, edit actuals, save."""

from __future__ import annotations

from datetime import date
from tkinter import messagebox
from typing import Optional

import customtkinter as ctk

from app.models import SessionLog, SetLog
from app.services import plans_service, sessions_service, workouts_service
from app.ui.widgets import EmptyState, ScrollableList, ViewHeader
from app.utils import iso_today, parse_float, parse_int


class LogView(ctk.CTkFrame):
    def __init__(self, master, app) -> None:
        super().__init__(master, fg_color="transparent")
        self.app = app
        self._session: Optional[SessionLog] = None
        self._set_vars: list[dict[str, ctk.StringVar]] = []
        self._workouts = []

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        ViewHeader(
            self, "Log a session",
            subtitle="Pre-fill from a workout, then enter actual performance.",
        ).grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 12))

        self._build_picker()
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 20))
        self.body.grid_rowconfigure(0, weight=1)
        self.body.grid_columnconfigure(0, weight=1)

        self._render_empty()

    def on_show(self) -> None:
        self._refresh_workouts()
        if self._session is None:
            scheduled = plans_service.todays_workout(self.app.conn)
            if scheduled:
                self._prefill(scheduled.workout_id, iso_today(), plan_id=scheduled.plan_id)
                return
        self._render()

    # ----------------------------------------------------------------- picker
    def _build_picker(self) -> None:
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 8))
        bar.grid_columnconfigure(1, weight=1)

        self.date_var = ctk.StringVar(value=iso_today())
        self.workout_var = ctk.StringVar()

        ctk.CTkLabel(bar, text="Date").grid(row=0, column=0, padx=4)
        ctk.CTkEntry(bar, textvariable=self.date_var, width=130).grid(row=0, column=0, padx=(48, 12))

        ctk.CTkLabel(bar, text="From workout").grid(row=0, column=1, sticky="w")
        self._refresh_workouts()
        self.workout_picker = ctk.CTkComboBox(
            bar, values=self._workout_labels(), variable=self.workout_var,
        )
        self.workout_picker.grid(row=0, column=2, sticky="ew", padx=8)
        bar.grid_columnconfigure(2, weight=1)

        ctk.CTkButton(bar, text="Load", width=80, command=self._load_picked).grid(row=0, column=3, padx=4)
        ctk.CTkButton(
            bar, text="Blank", width=80, fg_color="transparent", border_width=1,
            command=self._load_blank,
        ).grid(row=0, column=4, padx=4)

    def _refresh_workouts(self) -> None:
        self._workouts = workouts_service.list_all(self.app.conn)
        if hasattr(self, "workout_picker"):
            self.workout_picker.configure(values=self._workout_labels())

    def _workout_labels(self) -> list[str]:
        return [f"[{w.modality}] {w.name}" for w in self._workouts]

    def _load_picked(self) -> None:
        label = self.workout_var.get()
        for w in self._workouts:
            if f"[{w.modality}] {w.name}" == label:
                self._prefill(w.id, self.date_var.get())
                return

    def _load_blank(self) -> None:
        self._session = SessionLog(
            id=None, date=self.date_var.get() or iso_today(),
            workout_id=None, status="done", sets=[],
        )
        self._render()

    # --------------------------------------------------------------- entry
    def start_from_scheduled(self, scheduled) -> None:
        self._prefill(scheduled.workout_id, iso_today(), plan_id=scheduled.plan_id)

    def _prefill(self, workout_id: int, on_date: str, plan_id: Optional[int] = None) -> None:
        self._session = sessions_service.prefill_from_workout(
            self.app.conn, workout_id, on_date, plan_id=plan_id
        )
        self.date_var.set(on_date)
        self._render()

    # --------------------------------------------------------------- render
    def _render_empty(self) -> None:
        for c in self.body.winfo_children():
            c.destroy()
        EmptyState(
            self.body,
            "No session loaded",
            "Pick a workout above to pre-fill, or start a blank session.",
        ).grid(row=0, column=0, sticky="nsew")

    def _render(self) -> None:
        for c in self.body.winfo_children():
            c.destroy()
        if self._session is None:
            self._render_empty()
            return

        scroll = ScrollableList(self.body, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew")

        # Top meta box
        meta = ctk.CTkFrame(scroll, fg_color=("gray92", "gray18"), corner_radius=8)
        meta.pack(fill="x", pady=(0, 8))
        meta.columnconfigure(1, weight=1)

        title = self._session.workout_name or "Ad-hoc session"
        ctk.CTkLabel(
            meta, text=title, font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, columnspan=4, sticky="w", padx=10, pady=(8, 4))

        ctk.CTkLabel(meta, text="Date").grid(row=1, column=0, sticky="w", padx=10)
        ctk.CTkEntry(meta, textvariable=self.date_var, width=130).grid(row=1, column=0, sticky="w", padx=(48, 4))

        self.status_var = ctk.StringVar(value=self._session.status)
        ctk.CTkLabel(meta, text="Status").grid(row=1, column=1, sticky="w", padx=10)
        ctk.CTkOptionMenu(
            meta, values=["done", "partial", "skipped"], variable=self.status_var, width=110,
        ).grid(row=1, column=1, padx=(56, 4), sticky="w")

        self.rpe_var = ctk.StringVar(
            value=str(self._session.perceived_exertion) if self._session.perceived_exertion else ""
        )
        ctk.CTkLabel(meta, text="Overall RPE (1-10)").grid(row=1, column=2, sticky="w", padx=10)
        ctk.CTkEntry(meta, textvariable=self.rpe_var, width=60).grid(row=1, column=2, sticky="e", padx=10)

        self.notes_var = ctk.StringVar(value=self._session.notes or "")
        ctk.CTkLabel(meta, text="Notes").grid(row=2, column=0, sticky="w", padx=10, pady=(8, 4))
        ctk.CTkEntry(meta, textvariable=self.notes_var).grid(
            row=2, column=1, columnspan=3, sticky="ew", padx=10, pady=(8, 8)
        )

        # Sets list
        self._set_vars = []
        if not self._session.sets:
            ctk.CTkLabel(
                scroll, text="No sets yet. Add a row below to record actuals.",
                text_color=("gray45", "gray60"),
            ).pack(pady=12)
        else:
            self._render_set_table(scroll)

        # Add-set + repeat-last bar
        bar = ctk.CTkFrame(scroll, fg_color="transparent")
        bar.pack(fill="x", pady=(8, 0))
        ctk.CTkButton(bar, text="+ Add set", command=self._add_set).pack(side="left", padx=4)
        ctk.CTkButton(
            bar, text="Repeat last set",
            fg_color="transparent", border_width=1,
            command=self._repeat_last,
        ).pack(side="left", padx=4)

        # Save bar
        save_bar = ctk.CTkFrame(scroll, fg_color="transparent")
        save_bar.pack(fill="x", pady=(16, 0))
        ctk.CTkButton(save_bar, text="Save session", width=160, command=self._save).pack(side="right")

    def _render_set_table(self, parent) -> None:
        table = ctk.CTkFrame(parent, fg_color=("gray95", "gray16"), corner_radius=8)
        table.pack(fill="x", pady=4)
        # Header row
        cols = ["#", "Exercise", "Set", "Reps", "Weight", "Distance", "Time (s)", "RPE", ""]
        for i, name in enumerate(cols):
            table.grid_columnconfigure(i, weight=(2 if i == 1 else 1))
            ctk.CTkLabel(
                table, text=name, font=ctk.CTkFont(size=11, weight="bold"),
            ).grid(row=0, column=i, padx=4, pady=(8, 2), sticky="w")

        for idx, set_log in enumerate(self._session.sets, start=1):
            self._render_set_row(table, idx, set_log)

    def _render_set_row(self, parent, idx: int, s: SetLog) -> None:
        row_index = idx
        ctk.CTkLabel(parent, text=str(idx)).grid(row=row_index, column=0, padx=4, pady=2)
        ctk.CTkLabel(
            parent, text=s.exercise_name or f"Exercise #{s.exercise_id}",
            anchor="w",
        ).grid(row=row_index, column=1, padx=4, pady=2, sticky="w")

        vars: dict[str, ctk.StringVar] = {
            "set_number": ctk.StringVar(value=str(s.set_number) if s.set_number else str(idx)),
            "reps": ctk.StringVar(value=str(s.reps) if s.reps is not None else ""),
            "weight": ctk.StringVar(value=str(s.weight) if s.weight is not None else ""),
            "distance": ctk.StringVar(value=str(s.distance) if s.distance is not None else ""),
            "duration_sec": ctk.StringVar(value=str(s.duration_sec) if s.duration_sec is not None else ""),
            "rpe": ctk.StringVar(value=str(s.rpe) if s.rpe is not None else ""),
        }
        ctk.CTkEntry(parent, textvariable=vars["set_number"], width=50).grid(row=row_index, column=2, padx=4)
        ctk.CTkEntry(parent, textvariable=vars["reps"], width=70).grid(row=row_index, column=3, padx=4)
        ctk.CTkEntry(parent, textvariable=vars["weight"], width=80).grid(row=row_index, column=4, padx=4)
        ctk.CTkEntry(parent, textvariable=vars["distance"], width=80).grid(row=row_index, column=5, padx=4)
        ctk.CTkEntry(parent, textvariable=vars["duration_sec"], width=80).grid(row=row_index, column=6, padx=4)
        ctk.CTkEntry(parent, textvariable=vars["rpe"], width=50).grid(row=row_index, column=7, padx=4)
        ctk.CTkButton(
            parent, text="✕", width=28,
            fg_color=("#c44", "#a33"), hover_color=("#a33", "#822"),
            command=lambda i=idx - 1: self._remove_set(i),
        ).grid(row=row_index, column=8, padx=4)
        # Track for save.
        self._set_vars.append({"_set": s, **vars})

    def _add_set(self) -> None:
        if self._session is None:
            return
        if not self._session.sets:
            messagebox.showinfo(
                "Pick an exercise",
                "Load a workout first so we know which exercise to add the set for.",
                parent=self,
            )
            return
        last = self._session.sets[-1]
        self._session.sets.append(
            SetLog(
                id=None, session_log_id=None, exercise_id=last.exercise_id,
                set_number=(last.set_number or 1) + 1, exercise_name=last.exercise_name,
            )
        )
        self._collect_into_session()
        self._render()

    def _repeat_last(self) -> None:
        if self._session is None or not self._session.sets:
            return
        self._collect_into_session()
        last = self._session.sets[-1]
        self._session.sets.append(
            SetLog(
                id=None, session_log_id=None, exercise_id=last.exercise_id,
                set_number=(last.set_number or 1) + 1,
                reps=last.reps, weight=last.weight,
                distance=last.distance, duration_sec=last.duration_sec,
                rpe=last.rpe, exercise_name=last.exercise_name,
            )
        )
        self._render()

    def _remove_set(self, idx: int) -> None:
        if self._session is None:
            return
        self._collect_into_session()
        if 0 <= idx < len(self._session.sets):
            del self._session.sets[idx]
        self._render()

    def _collect_into_session(self) -> None:
        if self._session is None:
            return
        new_sets: list[SetLog] = []
        for entry in self._set_vars:
            s: SetLog = entry["_set"]
            s.set_number = parse_int(entry["set_number"].get())
            s.reps = parse_int(entry["reps"].get())
            s.weight = parse_float(entry["weight"].get())
            s.distance = parse_float(entry["distance"].get())
            s.duration_sec = parse_int(entry["duration_sec"].get())
            s.rpe = parse_int(entry["rpe"].get())
            new_sets.append(s)
        self._session.sets = new_sets

    def _save(self) -> None:
        if self._session is None:
            return
        self._collect_into_session()
        self._session.date = self.date_var.get().strip()
        self._session.status = self.status_var.get()
        self._session.perceived_exertion = parse_int(self.rpe_var.get())
        self._session.notes = self.notes_var.get().strip() or None
        try:
            sessions_service.save(self.app.conn, self._session)
        except ValueError as exc:
            messagebox.showerror("Invalid session", str(exc), parent=self)
            return
        messagebox.showinfo("Saved", "Session logged.", parent=self)
        self._session = None
        self.app.refresh_view("dashboard")
        self.app.refresh_view("calendar")
        self.app.refresh_view("progress")
        self._render_empty()
