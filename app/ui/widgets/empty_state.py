"""Friendly empty-state placeholder with optional CTA."""

from __future__ import annotations

from typing import Callable, Optional

import customtkinter as ctk


class EmptyState(ctk.CTkFrame):
    def __init__(
        self,
        master,
        title: str,
        message: str = "",
        cta_label: Optional[str] = None,
        cta_command: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(master, fg_color="transparent")
        ctk.CTkLabel(
            self, text=title, font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(pady=(40, 8))
        if message:
            ctk.CTkLabel(self, text=message, text_color=("gray40", "gray65")).pack(pady=(0, 12))
        if cta_label and cta_command:
            ctk.CTkButton(self, text=cta_label, command=cta_command, width=160).pack()
