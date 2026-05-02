"""Workout list + editor (modality-aware fields)."""

from __future__ import annotations

from tkinter import messagebox
from typing import Optional

import customtkinter as ctk

from app.models import Workout, WorkoutExercise
from app.services import exercises_service, workouts_service
from app.utils import parse_float, parse_int
from app.ui.widgets import EmptyState, ScrollableList, ViewHeader


class WorkoutListView(ctk.CTkFrame):
    def __init__(self, master, app) -> None:
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        ViewHeader(
            self, "Workouts",
            subtitle="Reusable templates you can drop into a plan.",
            action_label="+ New workout",
            action_command=self._new_workout,
        ).grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 12))

        self.list_holder = ctk.CTkFrame(self, fg_color="transparent")
        self.list_holder.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 20))
        self.list_holder.grid_rowconfigure(0, weight=1)
        self.list_holder.grid_columnconfigure(0, weight=1)

        self._refresh()

    def on_show(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        for c in self.list_holder.winfo_children():
            c.destroy()
        workouts = workouts_service.list_all(self.app.conn)
        if not workouts:
            EmptyState(
                self.list_holder,
                "No workouts yet",
                "Create your first workout template to plan with.",
                cta_label="+ New workout",
                cta_command=self._new_workout,
            ).grid(row=0, column=0, sticky="nsew")
            return

        scroll = ScrollableList(self.list_holder, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew")
        for w in workouts:
            self._render_row(scroll, w)

    def _render_row(self, parent, workout: Workout) -> None:
        row = ctk.CTkFrame(parent, corner_radius=8, fg_color=("gray92", "gray18"))
        row.pack(fill="x", pady=4, padx=2)
        row.grid_columnconfigure(1, weight=1)

        badge = ctk.CTkLabel(
            row, text=workout.modality.upper(), width=64,
            text_color=("white", "white"),
            fg_color={"gym": "#3b6cdb", "run": "#2d8a4e",
                      "swim": "#188cad", "mixed": "#7a4fcc"}.get(workout.modality, "gray"),
            corner_radius=4,
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        badge.grid(row=0, column=0, padx=(10, 12), pady=10)

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.grid(row=0, column=1, sticky="ew", pady=8)
        ctk.CTkLabel(
            info, text=workout.name, anchor="w",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w")
        if workout.description:
            ctk.CTkLabel(
                info, text=workout.description, anchor="w",
                text_color=("gray35", "gray70"),
            ).pack(anchor="w")

        actions = ctk.CTkFrame(row, fg_color="transparent")
        actions.grid(row=0, column=2, padx=10)
        ctk.CTkButton(
            actions, text="Edit", width=70,
            command=lambda w=workout: self._edit(w.id),
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            actions, text="Delete", width=70,
            fg_color=("#c44", "#a33"), hover_color=("#a33", "#822"),
            command=lambda w=workout: self._delete(w),
        ).pack(side="left", padx=4)

    def _new_workout(self) -> None:
        WorkoutEditorDialog(self, self.app, on_saved=self._after_save)

    def _edit(self, workout_id: int) -> None:
        workout = workouts_service.get(self.app.conn, workout_id)
        if workout is None:
            return
        WorkoutEditorDialog(self, self.app, workout=workout, on_saved=self._after_save)

    def _after_save(self) -> None:
        self._refresh()
        self.app.refresh_view("plans")

    def _delete(self, workout: Workout) -> None:
        if not messagebox.askyesno("Delete", f"Delete workout '{workout.name}'?"):
            return
        workouts_service.delete(self.app.conn, workout.id)
        self._after_save()


# ----------------------------------------------------------------------
class WorkoutEditorDialog(ctk.CTkToplevel):
    def __init__(self, master, app, workout: Optional[Workout] = None, on_saved=lambda: None) -> None:
        super().__init__(master)
        self.app = app
        self.on_saved = on_saved
        self.workout = workout or Workout(id=None, name="", modality="gym")
        # Operate on a copy of the exercises so cancel really cancels.
        self.entries: list[WorkoutExercise] = [we for we in self.workout.exercises]

        self.title("Edit workout" if self.workout.id else "New workout")
        self.geometry("780x640")
        self.transient(master)
        self.grab_set()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self._build_header()
        self._build_picker()
        self._build_list()
        self._build_buttons()

    def _build_header(self) -> None:
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 4))
        bar.columnconfigure(1, weight=1)

        self.name_var = ctk.StringVar(value=self.workout.name)
        self.modality_var = ctk.StringVar(value=self.workout.modality)
        self.desc_var = ctk.StringVar(value=self.workout.description or "")
        self.minutes_var = ctk.StringVar(
            value=str(self.workout.estimated_minutes) if self.workout.estimated_minutes else ""
        )

        ctk.CTkLabel(bar, text="Name").grid(row=0, column=0, sticky="w", padx=4)
        ctk.CTkEntry(bar, textvariable=self.name_var).grid(row=0, column=1, sticky="ew", padx=4)
        ctk.CTkLabel(bar, text="Modality").grid(row=0, column=2, sticky="w", padx=4)
        ctk.CTkOptionMenu(
            bar, values=["gym", "run", "swim", "mixed"],
            variable=self.modality_var, width=110,
        ).grid(row=0, column=3, padx=4)

        ctk.CTkLabel(bar, text="Description").grid(row=1, column=0, sticky="w", padx=4, pady=(8, 0))
        ctk.CTkEntry(bar, textvariable=self.desc_var).grid(
            row=1, column=1, columnspan=2, sticky="ew", padx=4, pady=(8, 0)
        )
        ctk.CTkLabel(bar, text="Mins").grid(row=1, column=3, sticky="w", padx=4, pady=(8, 0))
        ctk.CTkEntry(bar, textvariable=self.minutes_var, width=70).grid(
            row=1, column=4, padx=4, pady=(8, 0)
        )

    def _build_picker(self) -> None:
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=1, column=0, sticky="ew", padx=16, pady=(8, 4))
        bar.columnconfigure(1, weight=1)
        ctk.CTkLabel(bar, text="Add exercise:").grid(row=0, column=0, padx=4)
        self.picker_var = ctk.StringVar()
        self._exercise_options = exercises_service.list_all(self.app.conn)
        labels = [f"[{e.modality}] {e.name}" for e in self._exercise_options]
        self.picker = ctk.CTkComboBox(bar, values=labels, variable=self.picker_var)
        self.picker.grid(row=0, column=1, sticky="ew", padx=4)
        ctk.CTkButton(bar, text="Add", width=80, command=self._add_picked).grid(
            row=0, column=2, padx=4
        )

    def _build_list(self) -> None:
        self.list_frame = ScrollableList(self, fg_color=("gray95", "gray14"))
        self.list_frame.grid(row=2, column=0, sticky="nsew", padx=16, pady=8)
        self._render_entries()

    def _build_buttons(self) -> None:
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 12))
        ctk.CTkButton(
            bar, text="Cancel", fg_color="transparent", border_width=1,
            command=self.destroy,
        ).pack(side="right", padx=4)
        ctk.CTkButton(bar, text="Save", command=self._save).pack(side="right", padx=4)

    # ------------------------------------------------------------------
    def _add_picked(self) -> None:
        label = self.picker_var.get()
        idx = next(
            (i for i, e in enumerate(self._exercise_options) if f"[{e.modality}] {e.name}" == label),
            None,
        )
        if idx is None:
            return
        ex = self._exercise_options[idx]
        we = WorkoutExercise(
            id=None,
            workout_id=self.workout.id,
            exercise_id=ex.id,
            position=len(self.entries) + 1,
            sets=3 if ex.metric_type == "weight_reps" else None,
            target_reps="8" if ex.metric_type == "weight_reps" else None,
            exercise_name=ex.name,
            exercise_modality=ex.modality,
            metric_type=ex.metric_type,
            default_unit=ex.default_unit,
        )
        self.entries.append(we)
        self.picker_var.set("")
        self._render_entries()

    def _render_entries(self) -> None:
        for c in self.list_frame.winfo_children():
            c.destroy()
        if not self.entries:
            ctk.CTkLabel(
                self.list_frame,
                text="No exercises yet — pick one above and press Add.",
                text_color=("gray45", "gray60"),
            ).pack(pady=24)
            return
        for idx, we in enumerate(self.entries):
            self._render_entry(idx, we)

    def _render_entry(self, idx: int, we: WorkoutExercise) -> None:
        card = ctk.CTkFrame(self.list_frame, corner_radius=8, fg_color=("gray90", "gray20"))
        card.pack(fill="x", pady=4, padx=2)
        card.columnconfigure(1, weight=1)

        title = ctk.CTkFrame(card, fg_color="transparent")
        title.grid(row=0, column=0, columnspan=4, sticky="ew", padx=8, pady=(8, 4))
        title.columnconfigure(0, weight=1)
        ctk.CTkLabel(
            title, text=f"{idx + 1}. {we.exercise_name or '(exercise)'}",
            anchor="w", font=ctk.CTkFont(weight="bold"),
        ).grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(title, text="↑", width=28, command=lambda i=idx: self._move(i, -1)).grid(row=0, column=1, padx=2)
        ctk.CTkButton(title, text="↓", width=28, command=lambda i=idx: self._move(i, 1)).grid(row=0, column=2, padx=2)
        ctk.CTkButton(
            title, text="✕", width=28,
            fg_color=("#c44", "#a33"), hover_color=("#a33", "#822"),
            command=lambda i=idx: self._remove(i),
        ).grid(row=0, column=3, padx=2)

        # Inputs
        fields = ctk.CTkFrame(card, fg_color="transparent")
        fields.grid(row=1, column=0, columnspan=4, sticky="ew", padx=8, pady=(0, 8))
        for col in range(8):
            fields.columnconfigure(col, weight=1)

        sets_var = ctk.StringVar(value=str(we.sets) if we.sets else "")
        reps_var = ctk.StringVar(value=we.target_reps or "")
        weight_var = ctk.StringVar(value=str(we.target_weight) if we.target_weight else "")
        dist_var = ctk.StringVar(value=str(we.target_distance) if we.target_distance else "")
        time_var = ctk.StringVar(value=str(we.target_duration_sec) if we.target_duration_sec else "")
        rpe_var = ctk.StringVar(value=str(we.target_rpe) if we.target_rpe else "")
        rest_var = ctk.StringVar(value=str(we.rest_sec) if we.rest_sec else "")
        notes_var = ctk.StringVar(value=we.notes or "")

        # Bind back to entry on each keystroke.
        sets_var.trace_add("write", lambda *_: setattr(we, "sets", parse_int(sets_var.get())))
        reps_var.trace_add("write", lambda *_: setattr(we, "target_reps", reps_var.get().strip() or None))
        weight_var.trace_add("write", lambda *_: setattr(we, "target_weight", parse_float(weight_var.get())))
        dist_var.trace_add("write", lambda *_: setattr(we, "target_distance", parse_float(dist_var.get())))
        time_var.trace_add("write", lambda *_: setattr(we, "target_duration_sec", parse_int(time_var.get())))
        rpe_var.trace_add("write", lambda *_: setattr(we, "target_rpe", parse_int(rpe_var.get())))
        rest_var.trace_add("write", lambda *_: setattr(we, "rest_sec", parse_int(rest_var.get())))
        notes_var.trace_add("write", lambda *_: setattr(we, "notes", notes_var.get().strip() or None))

        # Metric-type-aware field set.
        metric = we.metric_type or "weight_reps"
        col = 0
        col = _labelled(fields, "Sets", sets_var, col)
        if metric == "weight_reps":
            col = _labelled(fields, "Reps", reps_var, col)
            col = _labelled(fields, f"Weight ({we.default_unit or 'kg'})", weight_var, col)
        elif metric == "reps_only":
            col = _labelled(fields, "Reps", reps_var, col)
        elif metric == "distance_time":
            col = _labelled(fields, f"Distance ({we.default_unit or 'm'})", dist_var, col)
            col = _labelled(fields, "Time (s)", time_var, col)
        elif metric == "time_only":
            col = _labelled(fields, "Time (s)", time_var, col)

        col = _labelled(fields, "RPE", rpe_var, col, width=50)
        col = _labelled(fields, "Rest (s)", rest_var, col, width=70)
        # Notes spans remaining columns
        ctk.CTkLabel(fields, text="Notes").grid(row=0, column=col, sticky="w", padx=4)
        ctk.CTkEntry(fields, textvariable=notes_var).grid(
            row=1, column=col, sticky="ew", padx=4, columnspan=8 - col
        )

    def _move(self, idx: int, direction: int) -> None:
        new = idx + direction
        if 0 <= new < len(self.entries):
            self.entries[idx], self.entries[new] = self.entries[new], self.entries[idx]
            self._render_entries()

    def _remove(self, idx: int) -> None:
        del self.entries[idx]
        self._render_entries()

    def _save(self) -> None:
        self.workout.name = self.name_var.get().strip()
        self.workout.modality = self.modality_var.get()
        self.workout.description = self.desc_var.get().strip() or None
        self.workout.estimated_minutes = parse_int(self.minutes_var.get())
        for i, we in enumerate(self.entries, start=1):
            we.position = i
        self.workout.exercises = self.entries
        try:
            workouts_service.save(self.app.conn, self.workout)
        except ValueError as exc:
            messagebox.showerror("Invalid workout", str(exc), parent=self)
            return
        self.on_saved()
        self.destroy()


def _labelled(parent, label: str, var, col: int, width: int = 90) -> int:
    ctk.CTkLabel(parent, text=label).grid(row=0, column=col, sticky="w", padx=4)
    ctk.CTkEntry(parent, textvariable=var, width=width).grid(
        row=1, column=col, sticky="w", padx=4
    )
    return col + 1
