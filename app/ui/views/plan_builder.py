"""Plan list + week × day grid editor."""

from __future__ import annotations

from datetime import date
from tkinter import messagebox
from typing import Optional

import customtkinter as ctk

from app.models import Plan
from app.services import plans_service, workouts_service
from app.ui.widgets import EmptyState, ScrollableList, ViewHeader
from app.utils import DAY_NAMES, iso_today, parse_int


class PlanListView(ctk.CTkFrame):
    def __init__(self, master, app) -> None:
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        ViewHeader(
            self, "Plans",
            subtitle="Multi-week schedules. One plan can be active at a time.",
            action_label="+ New plan",
            action_command=self._new_plan,
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
        plans = plans_service.list_all(self.app.conn)
        if not plans:
            EmptyState(
                self.list_holder,
                "No plans yet",
                "Create a multi-week plan to schedule your workouts.",
                cta_label="+ New plan",
                cta_command=self._new_plan,
            ).grid(row=0, column=0, sticky="nsew")
            return

        scroll = ScrollableList(self.list_holder, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew")
        for plan in plans:
            self._render_row(scroll, plan)

    def _render_row(self, parent, plan: Plan) -> None:
        row = ctk.CTkFrame(parent, corner_radius=8, fg_color=("gray92", "gray18"))
        row.pack(fill="x", pady=4, padx=2)
        row.grid_columnconfigure(0, weight=1)

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.grid(row=0, column=0, sticky="ew", padx=12, pady=10)

        name_row = ctk.CTkFrame(info, fg_color="transparent")
        name_row.pack(fill="x")
        ctk.CTkLabel(
            name_row, text=plan.name, anchor="w",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(side="left")
        if plan.is_active:
            ctk.CTkLabel(
                name_row, text="ACTIVE", text_color="white",
                fg_color="#2d8a4e", corner_radius=4,
                font=ctk.CTkFont(size=11, weight="bold"), width=70,
            ).pack(side="left", padx=8)

        meta = f"{plan.weeks} weeks  ·  Starts {plan.start_date}"
        if plan.goal_type:
            meta += f"  ·  Goal: {plan.goal_type}"
        ctk.CTkLabel(info, text=meta, text_color=("gray35", "gray70"), anchor="w").pack(
            anchor="w", pady=(2, 0)
        )

        actions = ctk.CTkFrame(row, fg_color="transparent")
        actions.grid(row=0, column=1, padx=10)
        ctk.CTkButton(
            actions, text="Edit", width=70, command=lambda p=plan: self._edit(p.id)
        ).pack(side="left", padx=4)
        if not plan.is_active:
            ctk.CTkButton(
                actions, text="Activate", width=80,
                command=lambda p=plan: self._activate(p.id),
            ).pack(side="left", padx=4)
        ctk.CTkButton(
            actions, text="Delete", width=70,
            fg_color=("#c44", "#a33"), hover_color=("#a33", "#822"),
            command=lambda p=plan: self._delete(p),
        ).pack(side="left", padx=4)

    def _new_plan(self) -> None:
        plan = Plan(
            id=None, name="New plan", goal_type="general",
            start_date=iso_today(), weeks=4, notes=None, is_active=False,
        )
        PlanEditorDialog(self, self.app, plan, on_saved=self._refresh)

    def _edit(self, plan_id: int) -> None:
        plan = plans_service.get(self.app.conn, plan_id)
        if plan:
            PlanEditorDialog(self, self.app, plan, on_saved=self._refresh)

    def _activate(self, plan_id: int) -> None:
        plans_service.set_active(self.app.conn, plan_id)
        self._refresh()
        self.app.refresh_view("dashboard")
        self.app.refresh_view("calendar")

    def _delete(self, plan: Plan) -> None:
        if not messagebox.askyesno("Delete", f"Delete plan '{plan.name}'?"):
            return
        plans_service.delete(self.app.conn, plan.id)
        self._refresh()
        self.app.refresh_view("calendar")
        self.app.refresh_view("dashboard")


# ----------------------------------------------------------------------
class PlanEditorDialog(ctk.CTkToplevel):
    def __init__(self, master, app, plan: Plan, on_saved=lambda: None) -> None:
        super().__init__(master)
        self.app = app
        self.plan = plan
        self.on_saved = on_saved

        self.title("Edit plan" if plan.id else "New plan")
        self.geometry("960x680")
        self.transient(master)
        self.grab_set()

        self.workouts = workouts_service.list_all(self.app.conn)
        self._workout_labels = ["—"] + [f"[{w.modality}] {w.name}" for w in self.workouts]
        self._workout_by_label = {
            f"[{w.modality}] {w.name}": w.id for w in self.workouts
        }

        # In-memory grid: (week_index, day_of_week) -> workout_id | None
        self._grid: dict[tuple[int, int], Optional[int]] = {}
        for slot in self.plan.slots:
            self._grid[(slot.week_index, slot.day_of_week)] = slot.workout_id

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self._build_meta()
        self._build_progression_bar()
        self._build_grid()
        self._build_buttons()

    def _build_meta(self) -> None:
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 4))
        for col in range(8):
            bar.columnconfigure(col, weight=1)

        self.name_var = ctk.StringVar(value=self.plan.name)
        self.goal_var = ctk.StringVar(value=self.plan.goal_type or "general")
        self.start_var = ctk.StringVar(value=self.plan.start_date)
        self.weeks_var = ctk.StringVar(value=str(self.plan.weeks))
        self.active_var = ctk.BooleanVar(value=self.plan.is_active)

        ctk.CTkLabel(bar, text="Name").grid(row=0, column=0, sticky="w", padx=4)
        ctk.CTkEntry(bar, textvariable=self.name_var).grid(row=1, column=0, columnspan=3, sticky="ew", padx=4)

        ctk.CTkLabel(bar, text="Goal").grid(row=0, column=3, sticky="w", padx=4)
        ctk.CTkOptionMenu(
            bar, values=["general", "fat_loss", "strength", "endurance"],
            variable=self.goal_var, width=140,
        ).grid(row=1, column=3, padx=4, sticky="ew")

        ctk.CTkLabel(bar, text="Start (YYYY-MM-DD)").grid(row=0, column=4, sticky="w", padx=4)
        ctk.CTkEntry(bar, textvariable=self.start_var, width=130).grid(row=1, column=4, padx=4, sticky="w")

        ctk.CTkLabel(bar, text="Weeks").grid(row=0, column=5, sticky="w", padx=4)
        ctk.CTkEntry(bar, textvariable=self.weeks_var, width=60).grid(row=1, column=5, padx=4, sticky="w")

        ctk.CTkSwitch(bar, text="Active", variable=self.active_var).grid(row=1, column=6, padx=12)

    def _build_progression_bar(self) -> None:
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=1, column=0, sticky="ew", padx=16, pady=(8, 0))
        ctk.CTkLabel(
            bar,
            text="Progression: deload every 4th week (auto-applied at save).",
            text_color=("gray40", "gray65"),
        ).pack(side="left")

    def _build_grid(self) -> None:
        outer = ctk.CTkScrollableFrame(self, fg_color=("gray95", "gray14"))
        outer.grid(row=2, column=0, sticky="nsew", padx=16, pady=8)
        self.grid_holder = outer
        self._render_grid()

    def _render_grid(self) -> None:
        for c in self.grid_holder.winfo_children():
            c.destroy()
        weeks = max(parse_int(self.weeks_var.get(), default=1) or 1, 1)

        # Header row
        header = ctk.CTkFrame(self.grid_holder, fg_color="transparent")
        header.pack(fill="x")
        ctk.CTkLabel(header, text="", width=80).grid(row=0, column=0)
        for d in range(7):
            ctk.CTkLabel(
                header, text=DAY_NAMES[d], width=120,
                font=ctk.CTkFont(weight="bold"),
            ).grid(row=0, column=d + 1, padx=4)

        for w in range(weeks):
            row = ctk.CTkFrame(self.grid_holder, fg_color="transparent")
            row.pack(fill="x", pady=2)
            label = f"Week {w + 1}" + ("  (deload)" if (w + 1) % 4 == 0 else "")
            ctk.CTkLabel(row, text=label, width=80, anchor="w").grid(row=0, column=0)
            for d in range(7):
                self._render_cell(row, w, d)

    def _render_cell(self, parent, week_index: int, day_of_week: int) -> None:
        current_id = self._grid.get((week_index, day_of_week))
        current_label = "—"
        for label, wid in self._workout_by_label.items():
            if wid == current_id:
                current_label = label
                break
        var = ctk.StringVar(value=current_label)

        def on_change(value: str, wi=week_index, dow=day_of_week, v=var) -> None:
            wid = self._workout_by_label.get(value)
            self._grid[(wi, dow)] = wid

        ctk.CTkOptionMenu(
            parent, values=self._workout_labels, variable=var,
            command=on_change, width=140, dynamic_resizing=False,
        ).grid(row=0, column=day_of_week + 1, padx=4)

    def _build_buttons(self) -> None:
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 12))

        def on_weeks_change(*_):
            self._render_grid()
        self.weeks_var.trace_add("write", on_weeks_change)

        ctk.CTkButton(
            bar, text="Cancel", fg_color="transparent", border_width=1,
            command=self.destroy,
        ).pack(side="right", padx=4)
        ctk.CTkButton(bar, text="Save", command=self._save).pack(side="right", padx=4)

    def _save(self) -> None:
        self.plan.name = self.name_var.get().strip()
        self.plan.goal_type = self.goal_var.get() or None
        self.plan.start_date = self.start_var.get().strip()
        self.plan.weeks = parse_int(self.weeks_var.get(), default=1) or 1
        self.plan.is_active = bool(self.active_var.get())

        from app.models import PlanSlot
        slots = []
        for (w, d), wid in self._grid.items():
            if w >= self.plan.weeks:
                continue
            if wid is None:
                continue
            modifier = 0.7 if (w + 1) % 4 == 0 else 1.0
            slots.append(
                PlanSlot(
                    id=None, plan_id=self.plan.id or 0,
                    week_index=w, day_of_week=d,
                    workout_id=wid, intensity_modifier=modifier,
                )
            )
        self.plan.slots = slots

        try:
            saved = plans_service.save(self.app.conn, self.plan)
        except ValueError as exc:
            messagebox.showerror("Invalid plan", str(exc), parent=self)
            return
        if saved.is_active:
            plans_service.set_active(self.app.conn, saved.id)
        self.on_saved()
        self.app.refresh_view("dashboard")
        self.app.refresh_view("calendar")
        self.destroy()
