"""Display formatters and tolerant parsers."""

from __future__ import annotations

from typing import Optional

KG_PER_LB = 0.45359237
KM_PER_MILE = 1.609344


def parse_int(value, default: Optional[int] = None) -> Optional[int]:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def parse_float(value, default: Optional[float] = None) -> Optional[float]:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def fmt_weight(value: Optional[float], units: str = "metric") -> str:
    if value is None:
        return ""
    if units == "imperial":
        return f"{value / KG_PER_LB:.1f} lb"
    return f"{value:g} kg"


def fmt_distance(value: Optional[float], units: str = "metric", default_unit: str = "km") -> str:
    if value is None:
        return ""
    if default_unit == "m":
        return f"{value:g} m"
    if units == "imperial":
        return f"{value / KM_PER_MILE:.2f} mi"
    return f"{value:g} km"


def fmt_duration(seconds: Optional[int]) -> str:
    if seconds is None:
        return ""
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def fmt_pace_per_km(seconds_per_km: Optional[float]) -> str:
    if seconds_per_km is None or seconds_per_km <= 0:
        return ""
    m, s = divmod(int(round(seconds_per_km)), 60)
    return f"{m}:{s:02d}/km"


def fmt_pace_per_100m(seconds_per_100m: Optional[float]) -> str:
    if seconds_per_100m is None or seconds_per_100m <= 0:
        return ""
    m, s = divmod(int(round(seconds_per_100m)), 60)
    return f"{m}:{s:02d}/100m"
