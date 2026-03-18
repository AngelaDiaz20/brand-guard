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
    x: float
    y: float
    width: float
    height: float


class LogoContainerRule(TypedDict):
    x: float
    y: float
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
        "logo": {"x": 989.0, "y": 90.0, "width": 71.0, "height": 54.0},
        "logo_container": {"x": 946.0, "y": 291.0, "width": 102.0, "height": 101.0},
    },
    "ST": {
        "canvas": {"width": 1080.0, "height": 1920.0},
        "safe_area": {"width": 960.0, "height": 1360.0, "center_x": 540.0, "center_y": 831.0},
        "logo": {"x": 946.0, "y": 291.0, "width": 71.0, "height": 54.0},
        "logo_container": {"x": 989.0, "y": 90.0, "width": 102.0, "height": 101.0},
    },
}
