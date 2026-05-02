"""Standard view header with title, subtitle and an action button slot."""

from __future__ import annotations

from typing import Callable, Optional

import customtkinter as ctk


class ViewHeader(ctk.CTkFrame):
    def __init__(
        self,
        master,
        title: str,
        subtitle: Optional[str] = None,
        action_label: Optional[str] = None,
        action_command: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)

        text_frame = ctk.CTkFrame(self, fg_color="transparent")
        text_frame.grid(row=0, column=0, sticky="w", padx=4)
        ctk.CTkLabel(
            text_frame, text=title,
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(anchor="w")
        if subtitle:
            ctk.CTkLabel(
                text_frame, text=subtitle, text_color=("gray35", "gray70")
            ).pack(anchor="w")

        if action_label and action_command:
            ctk.CTkButton(
                self, text=action_label, command=action_command, width=140,
            ).grid(row=0, column=1, sticky="e", padx=6)
