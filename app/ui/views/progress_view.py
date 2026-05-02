"""Progress view: goals CRUD + matplotlib charts."""

from __future__ import annotations

from datetime import date
from tkinter import messagebox
from typing import Optional

import customtkinter as ctk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from app.models import BodyMetric, Goal
from app.repositories import body_metrics as bm_repo
from app.repositories import goals as goals_repo
from app.services import stats_service
from app.ui.widgets import EmptyState, ScrollableList, ViewHeader
from app.utils import iso_today, parse_float, parse_int


class ProgressView(ctk.CTkFrame):
    def __init__(self, master, app) -> None:
        super().__init__(master, fg_color="transparent")
        self.app = app

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        ViewHeader(
            self, "Progress",
            subtitle="Goals, body weight, and training trends.",
            action_label="+ New goal",
            action_command=self._new_goal,
        ).grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 12))

        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 20))
        self.body.grid_rowconfigure(0, weight=1)
        self.body.grid_columnconfigure(0, weight=1)
        self._render()

    def on_show(self) -> None:
        for c in self.body.winfo_children():
            c.destroy()
        self._render()

    def _render(self) -> None:
        scroll = ScrollableList(self.body, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew")

        # Goals card
        goals_card = _Card(scroll, "Goals")
        goals_card.pack(fill="x", pady=(0, 12))
        goals = goals_repo.list_all(self.app.conn)
        if not goals:
            EmptyState(
                goals_card.body, "No goals yet", "Add a goal to track progress.",
                cta_label="+ New goal", cta_command=self._new_goal,
            ).pack(fill="both", expand=True)
        else:
            for goal in goals:
                self._render_goal(goals_card.body, goal)

        # Body weight card with quick-add
        bw_card = _Card(scroll, "Body weight")
        bw_card.pack(fill="x", pady=(0, 12))
        self._render_bodyweight(bw_card.body)

        # Charts
        charts_card = _Card(scroll, "Training charts")
        charts_card.pack(fill="x", pady=(0, 12))
        self._render_charts(charts_card.body)

    # ---------------------------------------------------------- goals
    def _render_goal(self, parent, goal: Goal) -> None:
        row = ctk.CTkFrame(parent, fg_color=("gray92", "gray18"), corner_radius=8)
        row.pack(fill="x", pady=4)
        row.columnconfigure(0, weight=1)

        info = ctk.CTkFrame(row, fg_color="transparent")
        info.grid(row=0, column=0, sticky="ew", padx=10, pady=8)
        head = ctk.CTkLabel(
            info, text=goal.description, anchor="w",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        head.pack(anchor="w")

        target_text = ""
        if goal.target_value is not None:
            target_text = f"Target: {goal.target_value:g}"
            if goal.metric:
                target_text += f" {goal.metric}"
        if goal.target_date:
            target_text += f"  ·  by {goal.target_date}"
        if target_text:
            ctk.CTkLabel(info, text=target_text, text_color=("gray35", "gray70"), anchor="w").pack(
                anchor="w"
            )
        if goal.is_achieved:
            ctk.CTkLabel(
                info, text="Achieved", text_color=("white", "white"),
                fg_color="#2d8a4e", corner_radius=4, width=80,
            ).pack(anchor="w", pady=(4, 0))

        actions = ctk.CTkFrame(row, fg_color="transparent")
        actions.grid(row=0, column=1, padx=10)
        ctk.CTkButton(
            actions, text="Edit", width=70, command=lambda g=goal: self._edit_goal(g)
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            actions, text="Delete", width=70,
            fg_color=("#c44", "#a33"), hover_color=("#a33", "#822"),
            command=lambda g=goal: self._delete_goal(g),
        ).pack(side="left", padx=4)

    def _new_goal(self) -> None:
        GoalDialog(self, self.app, on_saved=self.on_show)

    def _edit_goal(self, goal: Goal) -> None:
        GoalDialog(self, self.app, goal=goal, on_saved=self.on_show)

    def _delete_goal(self, goal: Goal) -> None:
        if not messagebox.askyesno("Delete", f"Delete goal '{goal.description}'?"):
            return
        goals_repo.delete(self.app.conn, goal.id)
        self.on_show()

    # ----------------------------------------------------- body metric
    def _render_bodyweight(self, parent) -> None:
        bar = ctk.CTkFrame(parent, fg_color="transparent")
        bar.pack(fill="x")
        ctk.CTkLabel(bar, text="Date").pack(side="left", padx=4)
        date_var = ctk.StringVar(value=iso_today())
        ctk.CTkEntry(bar, textvariable=date_var, width=120).pack(side="left", padx=4)
        ctk.CTkLabel(bar, text="Weight (kg)").pack(side="left", padx=4)
        kg_var = ctk.StringVar()
        ctk.CTkEntry(bar, textvariable=kg_var, width=80).pack(side="left", padx=4)
        ctk.CTkLabel(bar, text="Body fat %").pack(side="left", padx=4)
        bf_var = ctk.StringVar()
        ctk.CTkEntry(bar, textvariable=bf_var, width=70).pack(side="left", padx=4)

        def add_metric() -> None:
            kg = parse_float(kg_var.get())
            bf = parse_float(bf_var.get())
            if kg is None and bf is None:
                return
            bm_repo.create(
                self.app.conn,
                BodyMetric(
                    id=None, date=date_var.get(),
                    weight_kg=kg, body_fat_pct=bf,
                ),
            )
            self.on_show()

        ctk.CTkButton(bar, text="Log", command=add_metric).pack(side="left", padx=8)

        trend = stats_service.bodyweight_trend(self.app.conn)
        if not trend:
            ctk.CTkLabel(
                parent, text="No body weight entries yet.",
                text_color=("gray45", "gray60"),
            ).pack(anchor="w", pady=8)
            return
        fig = Figure(figsize=(7, 2.6), dpi=100, facecolor="none")
        ax = fig.add_subplot(111)
        ax.plot([d for d, _ in trend], [v for _, v in trend], marker="o")
        ax.set_ylabel("kg")
        ax.set_title("Body weight")
        ax.grid(True, alpha=0.3)
        fig.autofmt_xdate()
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x", pady=(8, 0))

    # ----------------------------------------------------- charts
    def _render_charts(self, parent) -> None:
        # Weekly training volume
        volume = stats_service.weekly_volume(self.app.conn, weeks=12)
        run = stats_service.run_pace_trend(self.app.conn, weeks=12)
        swim = stats_service.swim_pace_trend(self.app.conn, weeks=12)

        if not (volume or run or swim):
            ctk.CTkLabel(
                parent,
                text="Log a session to populate charts.",
                text_color=("gray45", "gray60"),
            ).pack(pady=8)
            return

        fig = Figure(figsize=(8.5, 6.5), dpi=100, facecolor="none")
        axes = fig.subplots(3, 1)

        ax = axes[0]
        if volume:
            ax.bar([d for d, _ in volume], [v for _, v in volume], width=4)
        ax.set_title("Weekly gym volume (kg·reps)")
        ax.grid(True, alpha=0.3)

        ax = axes[1]
        if run:
            ax.plot([d for d, _ in run], [v / 60 for _, v in run], marker="o")
            ax.set_title("Run pace (min/km, lower is faster)")
            ax.invert_yaxis()
        else:
            ax.set_title("Run pace — no runs logged")
        ax.grid(True, alpha=0.3)

        ax = axes[2]
        if swim:
            ax.plot([d for d, _ in swim], [v for _, v in swim], marker="o")
            ax.set_title("Swim pace (sec/100m)")
            ax.invert_yaxis()
        else:
            ax.set_title("Swim pace — no swims logged")
        ax.grid(True, alpha=0.3)

        fig.autofmt_xdate()
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x", pady=(8, 0))


class _Card(ctk.CTkFrame):
    def __init__(self, master, title: str) -> None:
        super().__init__(master, corner_radius=10)
        ctk.CTkLabel(
            self, text=title, anchor="w",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(fill="x", padx=14, pady=(12, 4))
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=14, pady=(0, 14))


class GoalDialog(ctk.CTkToplevel):
    def __init__(self, master, app, goal: Optional[Goal] = None, on_saved=lambda: None) -> None:
        super().__init__(master)
        self.app = app
        self.goal = goal
        self.on_saved = on_saved
        self.title("Edit goal" if goal and goal.id else "New goal")
        self.geometry("420x440")
        self.transient(master)
        self.grab_set()

        pad = {"padx": 20, "pady": 6}
        self.desc_var = ctk.StringVar(value=goal.description if goal else "")
        self.metric_var = ctk.StringVar(value=(goal.metric or "") if goal else "")
        self.start_var = ctk.StringVar(value=str(goal.start_value) if goal and goal.start_value else "")
        self.target_var = ctk.StringVar(value=str(goal.target_value) if goal and goal.target_value else "")
        self.target_date_var = ctk.StringVar(value=(goal.target_date or "") if goal else "")
        self.achieved_var = ctk.BooleanVar(value=goal.is_achieved if goal else False)

        ctk.CTkLabel(self, text="Description *").pack(anchor="w", **pad)
        ctk.CTkEntry(self, textvariable=self.desc_var).pack(fill="x", **pad)

        ctk.CTkLabel(self, text="Metric (e.g. bodyweight_kg, 5k_time_sec)").pack(anchor="w", **pad)
        ctk.CTkEntry(self, textvariable=self.metric_var).pack(fill="x", **pad)

        ctk.CTkLabel(self, text="Start value").pack(anchor="w", **pad)
        ctk.CTkEntry(self, textvariable=self.start_var).pack(fill="x", **pad)

        ctk.CTkLabel(self, text="Target value").pack(anchor="w", **pad)
        ctk.CTkEntry(self, textvariable=self.target_var).pack(fill="x", **pad)

        ctk.CTkLabel(self, text="Target date (YYYY-MM-DD)").pack(anchor="w", **pad)
        ctk.CTkEntry(self, textvariable=self.target_date_var).pack(fill="x", **pad)

        ctk.CTkSwitch(self, text="Achieved", variable=self.achieved_var).pack(anchor="w", **pad)

        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", side="bottom", pady=12, padx=20)
        ctk.CTkButton(
            bar, text="Cancel", fg_color="transparent", border_width=1,
            command=self.destroy,
        ).pack(side="right", padx=4)
        ctk.CTkButton(bar, text="Save", command=self._save).pack(side="right", padx=4)

    def _save(self) -> None:
        description = self.desc_var.get().strip()
        if not description:
            messagebox.showerror("Invalid", "Description is required", parent=self)
            return
        goal = self.goal or Goal(id=None, description=description)
        goal.description = description
        goal.metric = self.metric_var.get().strip() or None
        goal.start_value = parse_float(self.start_var.get())
        goal.target_value = parse_float(self.target_var.get())
        goal.target_date = self.target_date_var.get().strip() or None
        goal.is_achieved = bool(self.achieved_var.get())
        if goal.id is None:
            goals_repo.create(self.app.conn, goal)
        else:
            goals_repo.update(self.app.conn, goal)
        self.on_saved()
        self.destroy()
