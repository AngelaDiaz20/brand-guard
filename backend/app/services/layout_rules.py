"""Hardcoded layout rules for brand compliance validation.

These rules are intentionally stored in code (no database) and are expected to
move to persistent storage later.
"""

from __future__ import annotations

from typing import Literal, TypedDict


PieceType = Literal["1:1", "ST"]


class CanvasRule(TypedDict):
    width: float
    height: float


class SafeAreaRule(TypedDict):
    width: float
    height: float
    center_x: float
    center_y: float


class LogoRule(TypedDict):
    width: float
    height: float


class LogoContainerRule(TypedDict):
    width: float
    height: float


class LayoutRule(TypedDict):
    canvas: CanvasRule
    safe_area: SafeAreaRule
    logo: LogoRule
    logo_container: LogoContainerRule


LAYOUT_RULES: dict[PieceType, LayoutRule] = {
    "1:1": {
        "canvas": {"width": 1080.0, "height": 1080.0},
        "safe_area": {"width": 1000.0, "height": 1000.0, "center_x": 540.0, "center_y": 540.0},
        "logo": {"width": 71.1652, "height": 53.7317},
        "logo_container": {"width": 102.2869, "height": 100.6546},
    },
    "ST": {
        "canvas": {"width": 1080.0, "height": 1920.0},
        "safe_area": {"width": 960.0, "height": 1360.0, "center_x": 540.0, "center_y": 831.0},
        "logo": {"width": 71.1652, "height": 53.7317},
        "logo_container": {"width": 102.2869, "height": 100.6546},
    },
}

