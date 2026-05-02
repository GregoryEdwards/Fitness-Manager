"""Thin wrapper that re-exports CTkScrollableFrame with a friendlier name."""

from __future__ import annotations

import customtkinter as ctk


class ScrollableList(ctk.CTkScrollableFrame):
    pass
