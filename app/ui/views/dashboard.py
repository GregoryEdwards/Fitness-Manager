"""Dashboard: today's workout, goals, recent activity."""

from __future__ import annotations

from datetime import date, timedelta

import customtkinter as ctk

from app.services import plans_service, sessions_service, stats_service
from app.repositories import goals as goals_repo
from app.ui.widgets import EmptyState, ScrollableList, ViewHeader


class DashboardView(ctk.CTkFrame):
    def __init__(self, master, app) -> None:
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        ViewHeader(
            self,
            "Dashboard",
            subtitle=date.today().strftime("%A, %d %B %Y"),
        ).grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 12))

        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 20))
        self.body.grid_columnconfigure(0, weight=2, uniform="dash")
        self.body.grid_columnconfigure(1, weight=1, uniform="dash")
        self.body.grid_rowconfigure(0, weight=1)
        self.body.grid_rowconfigure(1, weight=1)

        self._render()

    # ------------------------------------------------------------------
    def on_show(self) -> None:
        for child in self.body.winfo_children():
            child.destroy()
        self._render()

    def _render(self) -> None:
        self._render_today_card()
        self._render_summary_card()
        self._render_goals_card()
        self._render_recent_card()

    def _render_today_card(self) -> None:
        card = _Card(self.body, "Today")
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 8))
        scheduled = plans_service.todays_workout(self.app.conn)
        if scheduled is None:
            EmptyState(
                card.body,
                "No workout scheduled",
                "Activate a plan to see your daily session here.",
                cta_label="Open Plans",
                cta_command=lambda: self.app.show("plans"),
            ).pack(fill="both", expand=True)
            return
        ctk.CTkLabel(
            card.body, text=scheduled.workout_name,
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(anchor="w", pady=(2, 4))
        meta = (
            f"{scheduled.workout_modality.capitalize()}  ·  "
            f"Plan: {scheduled.plan_name}  ·  "
            f"Week {scheduled.week_index + 1}"
        )
        ctk.CTkLabel(card.body, text=meta, text_color=("gray35", "gray70")).pack(anchor="w")
        if scheduled.intensity_modifier != 1.0:
            tag = "Deload" if scheduled.intensity_modifier < 1 else "Push"
            ctk.CTkLabel(
                card.body,
                text=f"{tag} week ({int(scheduled.intensity_modifier * 100)}% intensity)",
                text_color=("gray40", "gray65"),
            ).pack(anchor="w", pady=(2, 6))

        actions = ctk.CTkFrame(card.body, fg_color="transparent")
        actions.pack(fill="x", pady=(12, 0))
        ctk.CTkButton(
            actions, text="Start session",
            command=lambda: self._start_session(scheduled),
        ).pack(side="left")
        ctk.CTkButton(
            actions, text="Open calendar", fg_color="transparent",
            border_width=1, command=lambda: self.app.show("calendar"),
        ).pack(side="left", padx=8)

    def _start_session(self, scheduled) -> None:
        # Defer import to avoid circulars during view construction.
        from app.ui.views.log_view import LogView
        # Force recreate so it picks the right workout.
        self.app.refresh_view("log")
        log_view = self.app._views.get("log")
        if isinstance(log_view, LogView):
            log_view.start_from_scheduled(scheduled)
        self.app.show("log")

    def _render_summary_card(self) -> None:
        card = _Card(self.body, "Last 7 days")
        card.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 8))
        summary = stats_service.weekly_summary(self.app.conn)
        if not summary:
            ctk.CTkLabel(
                card.body, text="No sessions logged this week.",
                text_color=("gray40", "gray65"),
            ).pack(anchor="w")
            return
        order = ["gym", "run", "swim", "mixed", "unknown"]
        for modality in order:
            if modality in summary:
                row = ctk.CTkFrame(card.body, fg_color="transparent")
                row.pack(fill="x", pady=2)
                ctk.CTkLabel(row, text=modality.capitalize(), anchor="w").pack(side="left")
                ctk.CTkLabel(
                    row, text=str(summary[modality]),
                    font=ctk.CTkFont(weight="bold"),
                ).pack(side="right")

    def _render_goals_card(self) -> None:
        card = _Card(self.body, "Goals")
        card.grid(row=1, column=0, sticky="nsew", padx=(0, 8), pady=(8, 0))
        goals = goals_repo.list_all(self.app.conn, include_achieved=False)
        if not goals:
            EmptyState(
                card.body,
                "No active goals",
                "Set a goal to track your progress.",
                cta_label="Add a goal",
                cta_command=lambda: self.app.show("progress"),
            ).pack(fill="both", expand=True)
            return
        list_frame = ScrollableList(card.body, fg_color="transparent")
        list_frame.pack(fill="both", expand=True)
        for goal in goals:
            row = ctk.CTkFrame(list_frame, fg_color=("gray90", "gray18"), corner_radius=6)
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(
                row, text=goal.description, anchor="w",
                font=ctk.CTkFont(weight="bold"),
            ).pack(fill="x", padx=10, pady=(8, 2))
            target_str = ""
            if goal.target_value is not None:
                target_str = f"Target: {goal.target_value:g}"
                if goal.metric:
                    target_str += f" {goal.metric}"
            if goal.target_date:
                target_str += f"  ·  by {goal.target_date}"
            if target_str:
                ctk.CTkLabel(
                    row, text=target_str, anchor="w",
                    text_color=("gray35", "gray70"),
                ).pack(fill="x", padx=10, pady=(0, 8))

    def _render_recent_card(self) -> None:
        card = _Card(self.body, "Recent sessions")
        card.grid(row=1, column=1, sticky="nsew", padx=(8, 0), pady=(8, 0))
        sessions = sessions_service.list_recent(self.app.conn, limit=8)
        if not sessions:
            ctk.CTkLabel(
                card.body, text="Log a session to see it here.",
                text_color=("gray40", "gray65"),
            ).pack(anchor="w")
            return
        for s in sessions:
            row = ctk.CTkFrame(card.body, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=s.date, width=90, anchor="w").pack(side="left")
            ctk.CTkLabel(
                row, text=s.workout_name or "(ad-hoc)",
                anchor="w",
            ).pack(side="left", padx=4)
            ctk.CTkLabel(
                row, text=s.status, text_color=("gray40", "gray60")
            ).pack(side="right")


class _Card(ctk.CTkFrame):
    def __init__(self, master, title: str) -> None:
        super().__init__(master, corner_radius=10)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            self, text=title, anchor="w",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 4))
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
