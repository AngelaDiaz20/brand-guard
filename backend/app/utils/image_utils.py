"""Utility helpers for image metadata normalization."""

from math import gcd
from typing import Any


JPEG_ALIAS = "JPG"
JPEG_STANDARD = "JPEG"
EMBEDDED_ICC_LABEL = "Embedded"


def normalize_image_format(raw_format: str | None) -> str:
    """Normalize image format names to canonical values."""
    if raw_format is None:
        return ""

    normalized = raw_format.strip().upper()
    if normalized == JPEG_ALIAS:
        return JPEG_STANDARD
    return normalized


def build_aspect_ratio(width: int, height: int) -> str:
    """Return an aspect ratio string in reduced form (e.g. 16:9)."""
    if width <= 0 or height <= 0:
        return "0:0"

    divisor = gcd(width, height)
    return f"{width // divisor}:{height // divisor}"


def extract_icc_profile_label(image_info: dict[str, Any]) -> str | None:
    """Return a readable ICC profile label when profile data is present."""
    return EMBEDDED_ICC_LABEL if image_info.get("icc_profile") else None
