"""Conservative visual classifier for the main price block.

Goal:
- Determine whether the main price block background is RED or BLACK
- Otherwise return INDETERMINATE with traceability

This module intentionally avoids brittle pixel-perfect rules.
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Any

from PIL import Image, ImageOps
import numpy as np


@dataclass(frozen=True)
class PriceBlockColorResult:
    color: str  # "red" | "black" | "indeterminate"
    confidence: float
    dominant_rgb: tuple[int, int, int] | None
    bbox: list[int] | None  # [x, y, w, h] in original image coords
    messages: list[str]


def _safe_crop(image: Image.Image, bbox: list[int]) -> Image.Image | None:
    if not bbox or len(bbox) != 4:
        return None
    x, y, w, h = [int(v) for v in bbox]
    if w <= 2 or h <= 2:
        return None
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(image.width, x + w)
    y1 = min(image.height, y + h)
    if x1 - x0 <= 2 or y1 - y0 <= 2:
        return None
    return image.crop((x0, y0, x1, y1))


def _border_band_pixels(rgb: np.ndarray, band: int) -> np.ndarray:
    h, w, _ = rgb.shape
    band = max(1, min(band, min(h, w) // 3))

    top = rgb[:band, :, :]
    bottom = rgb[h - band :, :, :]
    left = rgb[:, :band, :]
    right = rgb[:, w - band :, :]
    return np.concatenate([top.reshape(-1, 3), bottom.reshape(-1, 3), left.reshape(-1, 3), right.reshape(-1, 3)], axis=0)


def _median_rgb(pixels: np.ndarray) -> tuple[int, int, int] | None:
    if pixels.size == 0:
        return None
    med = np.median(pixels, axis=0)
    return int(med[0]), int(med[1]), int(med[2])


def classify_main_price_block_color(image_bytes: bytes, main_bbox: list[int] | None) -> PriceBlockColorResult:
    messages: list[str] = []
    if not image_bytes or not main_bbox:
        return PriceBlockColorResult(
            color="indeterminate",
            confidence=0.0,
            dominant_rgb=None,
            bbox=main_bbox,
            messages=["No hay región de precio principal para analizar el color."],
        )

    try:
        with Image.open(BytesIO(image_bytes)) as img:
            img = ImageOps.exif_transpose(img).convert("RGB")

            x, y, w, h = [int(v) for v in main_bbox]
            pad = int(round(max(w, h) * 0.18))
            expanded = [x - pad, y - pad, w + 2 * pad, h + 2 * pad]

            crop = _safe_crop(img, expanded)
            if crop is None:
                return PriceBlockColorResult(
                    color="indeterminate",
                    confidence=0.0,
                    dominant_rgb=None,
                    bbox=main_bbox,
                    messages=["La región del precio principal es demasiado pequeña para analizar."],
                )

            arr = np.asarray(crop, dtype=np.uint8)
            if arr.size == 0:
                return PriceBlockColorResult(
                    color="indeterminate",
                    confidence=0.0,
                    dominant_rgb=None,
                    bbox=main_bbox,
                    messages=["No se pudo leer píxeles de la región del precio principal."],
                )

            band = max(2, int(round(min(crop.width, crop.height) * 0.12)))
            pixels = _border_band_pixels(arr, band=band)
            med = _median_rgb(pixels)
            if med is None:
                return PriceBlockColorResult(
                    color="indeterminate",
                    confidence=0.0,
                    dominant_rgb=None,
                    bbox=main_bbox,
                    messages=["No se pudo estimar el color dominante de la región del precio principal."],
                )

            r, g, b = med
            lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
            redness = float(r - max(g, b))

            # Conservative thresholds tuned for "big red/black badge" typical designs.
            is_black = lum <= 70 and max(r, g, b) <= 110
            is_red = (r >= 125 and g <= 120 and b <= 120 and redness >= 35) or (r >= 150 and redness >= 25)

            if is_black and not is_red:
                conf = float(min(1.0, max(0.0, (90.0 - lum) / 60.0)))
                messages.append("El bloque principal fue clasificado como negro.")
                return PriceBlockColorResult(
                    color="black",
                    confidence=round(conf, 4),
                    dominant_rgb=med,
                    bbox=main_bbox,
                    messages=messages,
                )

            if is_red and not is_black:
                conf = float(min(1.0, max(0.0, (redness - 25.0) / 60.0)))
                messages.append("El bloque principal fue clasificado como rojo.")
                return PriceBlockColorResult(
                    color="red",
                    confidence=round(conf, 4),
                    dominant_rgb=med,
                    bbox=main_bbox,
                    messages=messages,
                )

            messages.append("No se pudo determinar con suficiente confianza el color del bloque principal.")
            return PriceBlockColorResult(
                color="indeterminate",
                confidence=0.0,
                dominant_rgb=med,
                bbox=main_bbox,
                messages=messages,
            )
    except Exception:
        return PriceBlockColorResult(
            color="indeterminate",
            confidence=0.0,
            dominant_rgb=None,
            bbox=main_bbox,
            messages=["Ocurrió un error al analizar el color del bloque de precio principal."],
        )


def as_dict(result: PriceBlockColorResult) -> dict[str, Any]:
    return {
        "mainBlockDetected": bool(result.bbox),
        "mainBlockBbox": result.bbox,
        "mainBlockColor": result.color,
        "mainBlockColorConfidence": result.confidence,
        "dominantRgb": list(result.dominant_rgb) if result.dominant_rgb else None,
        "messages": list(result.messages),
    }

