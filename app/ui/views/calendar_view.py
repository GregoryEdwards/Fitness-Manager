"""Monthly calendar view of the active plan, overlaid with logged sessions."""

from __future__ import annotations

import calendar as cal_mod
from datetime import date, datetime, timedelta
from typing import Optional

import customtkinter as ctk

from app.services import plans_service, sessions_service
from app.ui.widgets import ViewHeader
from app.utils import DAY_NAMES


class CalendarView(ctk.CTkFrame):
    def __init__(self, master, app) -> None:
        super().__init__(master, fg_color="transparent")
        self.app = app

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        ViewHeader(
            self, "Calendar",
            subtitle="Planned workouts and logged sessions.",
        ).grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 12))

        self.cursor: date = date.today().replace(day=1)
        self._build_nav()

        self.grid_holder = ctk.CTkFrame(self, fg_color="transparent")
        self.grid_holder.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 20))
        self.grid_holder.grid_rowconfigure(0, weight=1)
        self.grid_holder.grid_columnconfigure(0, weight=1)

        self._render()

    def on_show(self) -> None:
        self._render()

    def _build_nav(self) -> None:
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 8))
        bar.grid_columnconfigure(1, weight=1)
        ctk.CTkButton(bar, text="◀", width=40, command=self._prev_month).grid(row=0, column=0, padx=4)
        self.title_label = ctk.CTkLabel(
            bar, text=self.cursor.strftime("%B %Y"),
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        self.title_label.grid(row=0, column=1)
        ctk.CTkButton(bar, text="▶", width=40, command=self._next_month).grid(row=0, column=2, padx=4)
        ctk.CTkButton(bar, text="Today", width=80, command=self._today).grid(row=0, column=3, padx=8)

    def _prev_month(self) -> None:
        first = self.cursor.replace(day=1)
        prev_last = first - timedelta(days=1)
        self.cursor = prev_last.replace(day=1)
        self._render()

    def _next_month(self) -> None:
        first = self.cursor.replace(day=1)
        days_in_month = cal_mod.monthrange(first.year, first.month)[1]
        first_next = first + timedelta(days=days_in_month)
        self.cursor = first_next
        self._render()

    def _today(self) -> None:
        self.cursor = date.today().replace(day=1)
        self._render()

    def _render(self) -> None:
        for c in self.grid_holder.winfo_children():
            c.destroy()
        self.title_label.configure(text=self.cursor.strftime("%B %Y"))

        first = self.cursor.replace(day=1)
        days_in_month = cal_mod.monthrange(first.year, first.month)[1]
        last = first.replace(day=days_in_month)
        # Pad to full weeks (Mon-Sun).
        grid_start = first - timedelta(days=first.weekday())
        grid_end = last + timedelta(days=6 - last.weekday())

        scheduled = {
            s.on_date: s for s in plans_service.occurrences_in_range(
                self.app.conn, grid_start, grid_end
            )
        }
        sessions = {}
        for session in sessions_service.list_in_range(
            self.app.conn, grid_start.isoformat(), grid_end.isoformat()
        ):
            d = datetime.strptime(session.date, "%Y-%m-%d").date()
            sessions.setdefault(d, []).append(session)

        wrapper = ctk.CTkFrame(self.grid_holder, fg_color="transparent")
        wrapper.grid(row=0, column=0, sticky="nsew")
        for col in range(7):
            wrapper.grid_columnconfigure(col, weight=1, uniform="cal")
        for row in range(7):
            wrapper.grid_rowconfigure(row, weight=1)

        for col, name in enumerate(DAY_NAMES):
            ctk.CTkLabel(
                wrapper, text=name, font=ctk.CTkFont(size=12, weight="bold"),
            ).grid(row=0, column=col, sticky="ew", padx=2, pady=(0, 4))

        d = grid_start
        row = 1
        while d <= grid_end:
            for col in range(7):
                self._render_day(wrapper, row, col, d, scheduled.get(d), sessions.get(d, []))
                d += timedelta(days=1)
            row += 1

    def _render_day(self, parent, row: int, col: int, day: date, scheduled, sessions) -> None:
        in_month = day.month == self.cursor.month
        is_today = day == date.today()

        bg = ("white", "gray18") if in_month else ("gray92", "gray13")
        if is_today:
            bg = ("#dde7ff", "#1d2f55")

        cell = ctk.CTkFrame(parent, fg_color=bg, corner_radius=6, border_width=1,
                             border_color=("gray85", "gray25"))
        cell.grid(row=row, column=col, sticky="nsew", padx=2, pady=2)

        head = ctk.CTkFrame(cell, fg_color="transparent")
        head.pack(fill="x", padx=6, pady=(4, 0))
        color = ("gray20", "gray85") if in_month else ("gray55", "gray45")
        ctk.CTkLabel(
            head, text=str(day.day), text_color=color,
            font=ctk.CTkFont(size=12, weight="bold" if is_today else "normal"),
        ).pack(side="left")

        if scheduled:
            ctk.CTkLabel(
                cell, text=f"📋 {scheduled.workout_name}",
                anchor="w", text_color=("#1d4ed8", "#92b9ff"),
                font=ctk.CTkFont(size=11),
            ).pack(fill="x", padx=6, pady=1)
        for s in sessions:
            label = "✅" if s.status == "done" else ("⚠️" if s.status == "partial" else "❌")
            ctk.CTkLabel(
                cell, text=f"{label} {s.workout_name or 'session'}",
                anchor="w", text_color=("#0f5132", "#a3d9b1"),
                font=ctk.CTkFont(size=11),
            ).pack(fill="x", padx=6, pady=1)
