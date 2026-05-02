"""Exercise library: searchable list, add/edit/delete custom exercises."""

from __future__ import annotations

from tkinter import messagebox
from typing import Optional

import customtkinter as ctk

from app.models import Exercise
from app.services import exercises_service
from app.ui.widgets import EmptyState, ScrollableList, ViewHeader


MODALITY_FILTERS = ["All", "Gym", "Run", "Swim"]
METRIC_LABELS = {
    "weight_reps": "Weight × Reps",
    "distance_time": "Distance × Time",
    "time_only": "Time only",
    "reps_only": "Reps only",
}


class ExerciseLibraryView(ctk.CTkFrame):
    def __init__(self, master, app) -> None:
        super().__init__(master, fg_color="transparent")
        self.app = app

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        ViewHeader(
            self, "Exercise Library",
            subtitle="Browse, customise and clone exercises.",
            action_label="+ New exercise",
            action_command=self._open_new,
        ).grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 12))

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 8))
        toolbar.grid_columnconfigure(2, weight=1)

        self.modality_var = ctk.StringVar(value="All")
        ctk.CTkLabel(toolbar, text="Modality:").grid(row=0, column=0, padx=(0, 6))
        ctk.CTkOptionMenu(
            toolbar, values=MODALITY_FILTERS, variable=self.modality_var,
            command=lambda _v: self._refresh(),
            width=110,
        ).grid(row=0, column=1, padx=(0, 12))

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._refresh())
        ctk.CTkEntry(
            toolbar, placeholder_text="Search by name, muscle, equipment…",
            textvariable=self.search_var,
        ).grid(row=0, column=2, sticky="ew")

        self.list_holder = ctk.CTkFrame(self, fg_color="transparent")
        self.list_holder.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 20))
        self.list_holder.grid_rowconfigure(0, weight=1)
        self.list_holder.grid_columnconfigure(0, weight=1)

        self._refresh()

    def on_show(self) -> None:
        self._refresh()

    # ------------------------------------------------------------------
    def _refresh(self) -> None:
        for child in self.list_holder.winfo_children():
            child.destroy()
        modality = self.modality_var.get().lower()
        modality = None if modality == "all" else modality
        search = self.search_var.get().strip() or None
        items = exercises_service.list_all(self.app.conn, modality=modality, search=search)

        if not items:
            EmptyState(
                self.list_holder,
                "No matching exercises",
                "Try adjusting your filters or add a new exercise.",
                cta_label="+ New exercise",
                cta_command=self._open_new,
            ).grid(row=0, column=0, sticky="nsew")
            return

        scroll = ScrollableList(self.list_holder, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)
        for ex in items:
            self._render_row(scroll, ex)

    def _render_row(self, parent, ex: Exercise) -> None:
        row = ctk.CTkFrame(parent, corner_radius=8, fg_color=("gray92", "gray18"))
        row.pack(fill="x", pady=4, padx=2)
        row.grid_columnconfigure(1, weight=1)

        badge = ctk.CTkLabel(
            row, text=ex.modality.upper(), width=58,
            text_color=("white", "white"),
            fg_color=_modality_color(ex.modality),
            corner_radius=4,
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        badge.grid(row=0, column=0, padx=(10, 12), pady=10)

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.grid(row=0, column=1, sticky="ew", pady=8)
        ctk.CTkLabel(
            info, text=ex.name, anchor="w",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w")
        details = " · ".join(
            x for x in [
                METRIC_LABELS.get(ex.metric_type, ex.metric_type),
                ex.category,
                ex.equipment,
                ex.muscle_groups,
            ] if x
        )
        if details:
            ctk.CTkLabel(
                info, text=details, anchor="w",
                text_color=("gray35", "gray70"),
            ).pack(anchor="w")

        actions = ctk.CTkFrame(row, fg_color="transparent")
        actions.grid(row=0, column=2, padx=10)
        if ex.is_custom:
            ctk.CTkButton(
                actions, text="Edit", width=70,
                command=lambda e=ex: self._open_edit(e),
            ).pack(side="left", padx=4)
            ctk.CTkButton(
                actions, text="Delete", width=70,
                fg_color=("#c44", "#a33"), hover_color=("#a33", "#822"),
                command=lambda e=ex: self._delete(e),
            ).pack(side="left", padx=4)
        else:
            ctk.CTkLabel(
                actions, text="Built-in", text_color=("gray45", "gray55"),
            ).pack(side="left", padx=4)
            ctk.CTkButton(
                actions, text="Clone", width=70,
                command=lambda e=ex: self._clone(e),
            ).pack(side="left", padx=4)

    # ------------------------------------------------------------------
    def _open_new(self) -> None:
        ExerciseDialog(self, self.app, on_saved=self._refresh)

    def _open_edit(self, ex: Exercise) -> None:
        ExerciseDialog(self, self.app, exercise=ex, on_saved=self._refresh)

    def _clone(self, ex: Exercise) -> None:
        new_ex = exercises_service.clone(self.app.conn, ex.id)
        ExerciseDialog(self, self.app, exercise=new_ex, on_saved=self._refresh)

    def _delete(self, ex: Exercise) -> None:
        if not messagebox.askyesno("Delete", f"Delete '{ex.name}'? This cannot be undone."):
            return
        try:
            exercises_service.delete(self.app.conn, ex.id)
        except ValueError as exc:
            messagebox.showerror("Delete failed", str(exc))
            return
        self._refresh()


def _modality_color(modality: str) -> str:
    return {
        "gym": "#3b6cdb",
        "run": "#2d8a4e",
        "swim": "#188cad",
    }.get(modality, "gray")


class ExerciseDialog(ctk.CTkToplevel):
    def __init__(
        self,
        master,
        app,
        exercise: Optional[Exercise] = None,
        on_saved=lambda: None,
    ) -> None:
        super().__init__(master)
        self.app = app
        self.on_saved = on_saved
        self.exercise = exercise
        self.title("Edit exercise" if exercise and exercise.id else "New exercise")
        self.geometry("440x540")
        self.transient(master)
        self.grab_set()

        self._build_form()

    def _build_form(self) -> None:
        pad = {"padx": 20, "pady": 6}

        self.name_var = ctk.StringVar(value=self.exercise.name if self.exercise else "")
        self.modality_var = ctk.StringVar(value=(self.exercise.modality if self.exercise else "gym"))
        self.metric_var = ctk.StringVar(
            value=(self.exercise.metric_type if self.exercise else "weight_reps")
        )
        self.category_var = ctk.StringVar(value=(self.exercise.category or "") if self.exercise else "")
        self.muscle_var = ctk.StringVar(value=(self.exercise.muscle_groups or "") if self.exercise else "")
        self.equipment_var = ctk.StringVar(value=(self.exercise.equipment or "") if self.exercise else "")
        self.unit_var = ctk.StringVar(value=(self.exercise.default_unit or "kg") if self.exercise else "kg")

        ctk.CTkLabel(self, text="Name *").pack(anchor="w", **pad)
        ctk.CTkEntry(self, textvariable=self.name_var).pack(fill="x", **pad)

        ctk.CTkLabel(self, text="Modality *").pack(anchor="w", **pad)
        ctk.CTkOptionMenu(
            self, values=["gym", "run", "swim"], variable=self.modality_var,
        ).pack(fill="x", **pad)

        ctk.CTkLabel(self, text="Metric type *").pack(anchor="w", **pad)
        ctk.CTkOptionMenu(
            self, values=list(METRIC_LABELS.keys()), variable=self.metric_var,
        ).pack(fill="x", **pad)

        ctk.CTkLabel(self, text="Category (e.g. push, intervals)").pack(anchor="w", **pad)
        ctk.CTkEntry(self, textvariable=self.category_var).pack(fill="x", **pad)

        ctk.CTkLabel(self, text="Muscle groups (comma-separated)").pack(anchor="w", **pad)
        ctk.CTkEntry(self, textvariable=self.muscle_var).pack(fill="x", **pad)

        ctk.CTkLabel(self, text="Equipment").pack(anchor="w", **pad)
        ctk.CTkEntry(self, textvariable=self.equipment_var).pack(fill="x", **pad)

        ctk.CTkLabel(self, text="Default unit").pack(anchor="w", **pad)
        ctk.CTkEntry(self, textvariable=self.unit_var).pack(fill="x", **pad)

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.pack(fill="x", side="bottom", pady=12, padx=20)
        ctk.CTkButton(
            buttons, text="Cancel", fg_color="transparent", border_width=1,
            command=self.destroy,
        ).pack(side="right", padx=4)
        ctk.CTkButton(buttons, text="Save", command=self._save).pack(side="right", padx=4)

    def _save(self) -> None:
        ex = self.exercise or Exercise(id=None, name="", modality="gym")
        ex.name = self.name_var.get().strip()
        ex.modality = self.modality_var.get()
        ex.metric_type = self.metric_var.get()
        ex.category = self.category_var.get().strip() or None
        ex.muscle_groups = self.muscle_var.get().strip() or None
        ex.equipment = self.equipment_var.get().strip() or None
        ex.default_unit = self.unit_var.get().strip() or None
        ex.is_custom = True
        try:
            if ex.id is None:
                exercises_service.create(self.app.conn, ex)
            else:
                exercises_service.update(self.app.conn, ex)
        except ValueError as exc:
            messagebox.showerror("Invalid", str(exc), parent=self)
            return
        self.on_saved()
        self.destroy()
