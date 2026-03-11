"""Layout compliance validation (safe area, logo, optional logo container).

Implementation notes:
- Rules are hardcoded locally for now (see layout_rules.py).
- Logo detection uses template matching (multi-scale) in the top-right region.
- Bounding boxes are returned in the ORIGINAL image coordinate system.
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Iterable

import numpy as np
from PIL import Image, ImageDraw, ImageOps

from app.services.layout_rules import LAYOUT_RULES, PieceType


@dataclass(frozen=True)
class BBox:
    x: float
    y: float
    width: float
    height: float

    @property
    def x_min(self) -> float:
        return self.x

    @property
    def x_max(self) -> float:
        return self.x + self.width

    @property
    def y_min(self) -> float:
        return self.y

    @property
    def y_max(self) -> float:
        return self.y + self.height

    @property
    def center_x(self) -> float:
        return self.x + self.width / 2.0

    @property
    def center_y(self) -> float:
        return self.y + self.height / 2.0


def _detect_piece_type(width: int, height: int) -> PieceType | None:
    if width <= 0 or height <= 0:
        return None

    ratio = width / height
    if abs(ratio - 1.0) <= 0.03:
        return "1:1"
    if abs(ratio - (1080.0 / 1920.0)) <= 0.03:
        return "ST"
    return None


def _safe_area_bbox_for_canvas(piece_type: PieceType) -> BBox:
    rule = LAYOUT_RULES[piece_type]
    safe = rule["safe_area"]
    return BBox(
        x=safe["center_x"] - safe["width"] / 2.0,
        y=safe["center_y"] - safe["height"] / 2.0,
        width=safe["width"],
        height=safe["height"],
    )


def _resize_to_canvas(image: Image.Image, piece_type: PieceType) -> Image.Image:
    rule = LAYOUT_RULES[piece_type]
    canvas_w = int(round(rule["canvas"]["width"]))
    canvas_h = int(round(rule["canvas"]["height"]))
    return ImageOps.exif_transpose(image).convert("RGB").resize((canvas_w, canvas_h), Image.Resampling.LANCZOS)


def _pil_to_gray_np(image: Image.Image) -> np.ndarray:
    gray = image.convert("L")
    arr = np.asarray(gray, dtype=np.float32) / 255.0
    return arr


def _sobel_magnitude(gray: np.ndarray) -> np.ndarray:
    # 3x3 Sobel (edge-preserving padding)
    p = np.pad(gray, 1, mode="edge")

    gx = (
        (p[0:-2, 0:-2] + 2.0 * p[1:-1, 0:-2] + p[2:, 0:-2])
        - (p[0:-2, 2:] + 2.0 * p[1:-1, 2:] + p[2:, 2:])
    ) / 4.0
    gy = (
        (p[0:-2, 0:-2] + 2.0 * p[0:-2, 1:-1] + p[0:-2, 2:])
        - (p[2:, 0:-2] + 2.0 * p[2:, 1:-1] + p[2:, 2:])
    ) / 4.0

    mag = np.sqrt(gx * gx + gy * gy)
    max_val = float(mag.max())
    if max_val > 1e-8:
        mag = mag / max_val
    return mag.astype(np.float32)


def _generate_house_logo_template(width: int, height: int) -> Image.Image:
    # Placeholder house icon template (to be replaced by the official logo template).
    # This keeps the pipeline functional in environments where the true template isn't bundled yet.
    img = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(img)

    # Roof
    roof_h = int(round(height * 0.45))
    base_y = int(round(height * 0.55))
    draw.polygon(
        [
            (width * 0.15, base_y),
            (width * 0.5, height * 0.08),
            (width * 0.85, base_y),
        ],
        fill=255,
    )

    # Body
    draw.rectangle(
        [width * 0.25, base_y, width * 0.75, height * 0.92],
        fill=255,
    )

    # Door cutout (subtractive)
    door_w = width * 0.18
    door_h = height * 0.32
    door_x0 = width * 0.5 - door_w / 2.0
    door_y0 = height * 0.92 - door_h
    draw.rectangle([door_x0, door_y0, door_x0 + door_w, height * 0.92], fill=0)
    return img


def _get_logo_template_for_canvas(piece_type: PieceType) -> Image.Image:
    rule = LAYOUT_RULES[piece_type]
    w = int(round(rule["logo"]["width"]))
    h = int(round(rule["logo"]["height"]))
    return _generate_house_logo_template(w, h)


def _iter_scales(min_scale: float, max_scale: float, step: float) -> Iterable[float]:
    scale = min_scale
    while scale <= max_scale + 1e-9:
        yield float(round(scale, 4))
        scale += step


def _match_template_cosine(
    image_mag: np.ndarray,
    template_mag: np.ndarray,
    search_bbox: BBox,
) -> tuple[float, tuple[int, int]]:
    from numpy.lib.stride_tricks import sliding_window_view

    x0 = int(max(0, round(search_bbox.x)))
    y0 = int(max(0, round(search_bbox.y)))
    x1 = int(min(image_mag.shape[1], round(search_bbox.x_max)))
    y1 = int(min(image_mag.shape[0], round(search_bbox.y_max)))

    region = image_mag[y0:y1, x0:x1]
    th, tw = template_mag.shape
    if region.shape[0] < th or region.shape[1] < tw:
        return 0.0, (0, 0)

    windows = sliding_window_view(region, (th, tw))
    dot = np.tensordot(windows, template_mag, axes=([2, 3], [0, 1]))
    window_norm = np.sqrt(np.sum(windows * windows, axis=(2, 3)))
    template_norm = float(np.sqrt(np.sum(template_mag * template_mag)))
    score = dot / (window_norm * template_norm + 1e-8)

    flat_idx = int(np.argmax(score))
    pos = np.unravel_index(flat_idx, score.shape)
    best = float(score[pos])
    # pos is (y, x) within region's valid window grid
    return best, (int(pos[1] + x0), int(pos[0] + y0))


def _detect_logo_on_canvas(image_canvas: Image.Image, piece_type: PieceType) -> tuple[BBox | None, float]:
    rule = LAYOUT_RULES[piece_type]
    canvas_w = int(round(rule["canvas"]["width"]))
    canvas_h = int(round(rule["canvas"]["height"]))

    # Search only in the expected top-right zone to keep matching fast.
    search = BBox(
        x=canvas_w * 0.55,
        y=0.0,
        width=canvas_w * 0.45,
        height=canvas_h * 0.35,
    )

    # Downscale for matching performance.
    match_scale = 0.25
    small_w = max(1, int(round(canvas_w * match_scale)))
    small_h = max(1, int(round(canvas_h * match_scale)))
    image_small = image_canvas.resize((small_w, small_h), Image.Resampling.BILINEAR)

    gray = _pil_to_gray_np(image_small)
    mag = _sobel_magnitude(gray)

    search_small = BBox(
        x=search.x * match_scale,
        y=search.y * match_scale,
        width=search.width * match_scale,
        height=search.height * match_scale,
    )

    template_base = _get_logo_template_for_canvas(piece_type)

    best_score = 0.0
    best_bbox: BBox | None = None

    for scale in _iter_scales(0.80, 1.20, 0.05):
        tw = max(6, int(round(template_base.size[0] * scale * match_scale)))
        th = max(6, int(round(template_base.size[1] * scale * match_scale)))

        template_scaled = template_base.resize((int(round(template_base.size[0] * scale)), int(round(template_base.size[1] * scale))), Image.Resampling.BILINEAR)
        template_small = template_scaled.resize((tw, th), Image.Resampling.BILINEAR)
        template_gray = np.asarray(template_small, dtype=np.float32) / 255.0
        template_mag = _sobel_magnitude(template_gray)

        score, (x_small, y_small) = _match_template_cosine(mag, template_mag, search_small)
        if score > best_score:
            best_score = score
            x = x_small / match_scale
            y = y_small / match_scale
            w = float(template_scaled.size[0])
            h = float(template_scaled.size[1])
            best_bbox = BBox(x=float(x), y=float(y), width=w, height=h)

    # Empirical threshold for edge-based cosine similarity.
    if best_bbox is None or best_score < 0.42:
        return None, best_score

    # Clamp to canvas bounds
    clamped = BBox(
        x=float(max(0.0, min(best_bbox.x, canvas_w - 1.0))),
        y=float(max(0.0, min(best_bbox.y, canvas_h - 1.0))),
        width=float(min(best_bbox.width, canvas_w - best_bbox.x)),
        height=float(min(best_bbox.height, canvas_h - best_bbox.y)),
    )
    return clamped, best_score


def _detect_logo_container_on_canvas(
    image_canvas: Image.Image,
    piece_type: PieceType,
    logo_bbox: BBox,
) -> BBox | None:
    rule = LAYOUT_RULES[piece_type]
    expected_w = float(rule["logo_container"]["width"])
    expected_h = float(rule["logo_container"]["height"])
    canvas_w = int(round(rule["canvas"]["width"]))
    canvas_h = int(round(rule["canvas"]["height"]))

    # Search in a local crop around the logo.
    crop_w = expected_w * 1.7
    crop_h = expected_h * 1.7
    crop_x0 = int(max(0, round(logo_bbox.center_x - crop_w / 2.0)))
    crop_y0 = int(max(0, round(logo_bbox.center_y - crop_h / 2.0)))
    crop_x1 = int(min(canvas_w, round(crop_x0 + crop_w)))
    crop_y1 = int(min(canvas_h, round(crop_y0 + crop_h)))

    if crop_x1 - crop_x0 < 10 or crop_y1 - crop_y0 < 10:
        return None

    crop = image_canvas.crop((crop_x0, crop_y0, crop_x1, crop_y1))
    gray = _pil_to_gray_np(crop)
    mag = _sobel_magnitude(gray)

    mmax = float(mag.max())
    if mmax < 1e-6:
        return None

    edges = mag > max(0.18, mmax * 0.35)
    if edges.sum() < 150:
        return None

    ys, xs = np.where(edges)
    x_min = int(xs.min())
    x_max = int(xs.max())
    y_min = int(ys.min())
    y_max = int(ys.max())

    detected = BBox(
        x=float(crop_x0 + x_min),
        y=float(crop_y0 + y_min),
        width=float((x_max - x_min) + 1),
        height=float((y_max - y_min) + 1),
    )

    # Filter out cases where we only captured the logo edges (too small).
    if detected.width < logo_bbox.width * 1.15 or detected.height < logo_bbox.height * 1.15:
        return None

    # Must roughly match expected container dimensions (looser than the final ±8% check).
    if not (expected_w * 0.75 <= detected.width <= expected_w * 1.25):
        return None
    if not (expected_h * 0.75 <= detected.height <= expected_h * 1.25):
        return None

    return detected


def _scale_bbox(bbox: BBox, sx: float, sy: float) -> BBox:
    return BBox(x=bbox.x * sx, y=bbox.y * sy, width=bbox.width * sx, height=bbox.height * sy)


def validate_layout(image_bytes: bytes) -> dict:
    """Validate layout compliance for an uploaded image."""
    with Image.open(BytesIO(image_bytes)) as image:
        original_w, original_h = image.size
        piece_type = _detect_piece_type(original_w, original_h)

        if piece_type is None:
            return {
                "pieceType": None,
                "logoDetected": False,
                "logoPosition": None,
                "logoSizeValid": False,
                "logoInsideSafeArea": False,
                "logoPositionValid": False,
                "logoContainerDetected": False,
                "logoContainerPosition": None,
                "logoContainerSizeValid": False,
                "layoutScore": 0,
                "safeAreaBoundingBox": None,
            }

        rule = LAYOUT_RULES[piece_type]
        canvas_w = float(rule["canvas"]["width"])
        canvas_h = float(rule["canvas"]["height"])
        sx = original_w / canvas_w
        sy = original_h / canvas_h

        image_canvas = _resize_to_canvas(image, piece_type)
        safe_canvas = _safe_area_bbox_for_canvas(piece_type)
        safe_original = _scale_bbox(safe_canvas, sx, sy)

        logo_canvas, match_score = _detect_logo_on_canvas(image_canvas, piece_type)
        if logo_canvas is None:
            return {
                "pieceType": piece_type,
                "logoDetected": False,
                "logoPosition": None,
                "logoSizeValid": False,
                "logoInsideSafeArea": False,
                "logoPositionValid": False,
                "logoContainerDetected": False,
                "logoContainerPosition": None,
                "logoContainerSizeValid": False,
                "layoutScore": 0,
                "safeAreaBoundingBox": {
                    "x": safe_original.x,
                    "y": safe_original.y,
                    "width": safe_original.width,
                    "height": safe_original.height,
                },
            }

        logo_original = _scale_bbox(logo_canvas, sx, sy)

        expected_logo_w = float(rule["logo"]["width"]) * sx
        expected_logo_h = float(rule["logo"]["height"]) * sy
        size_ok = (
            abs(logo_original.width - expected_logo_w) <= expected_logo_w * 0.10
            and abs(logo_original.height - expected_logo_h) <= expected_logo_h * 0.10
        )

        inside_safe = (
            logo_original.x_min >= safe_original.x_min
            and logo_original.y_min >= safe_original.y_min
            and logo_original.x_max <= safe_original.x_max
            and logo_original.y_max <= safe_original.y_max
        )

        # Top-right region (relative, conservative)
        rel_x = logo_original.center_x / max(1.0, float(original_w))
        rel_y = logo_original.center_y / max(1.0, float(original_h))
        position_ok = rel_x >= 0.62 and rel_y <= 0.30

        container_bbox_canvas = _detect_logo_container_on_canvas(image_canvas, piece_type, logo_canvas)
        container_detected = container_bbox_canvas is not None
        container_size_ok = False
        container_original: BBox | None = None

        if container_bbox_canvas is not None:
            container_original = _scale_bbox(container_bbox_canvas, sx, sy)
            expected_cw = float(rule["logo_container"]["width"]) * sx
            expected_ch = float(rule["logo_container"]["height"]) * sy
            container_size_ok = (
                abs(container_original.width - expected_cw) <= expected_cw * 0.08
                and abs(container_original.height - expected_ch) <= expected_ch * 0.08
            )

        checks: list[bool] = [inside_safe, size_ok, position_ok]
        if container_detected:
            checks.append(container_size_ok)

        layout_score = int(round(100.0 * (sum(1 for c in checks if c) / len(checks)))) if checks else 0

        return {
            "pieceType": piece_type,
            "logoDetected": True,
            "logoPosition": {
                "x": logo_original.x,
                "y": logo_original.y,
                "width": logo_original.width,
                "height": logo_original.height,
            },
            "logoSizeValid": size_ok,
            "logoInsideSafeArea": inside_safe,
            "logoPositionValid": position_ok,
            "logoContainerDetected": container_detected,
            "logoContainerPosition": (
                None
                if container_original is None
                else {
                    "x": container_original.x,
                    "y": container_original.y,
                    "width": container_original.width,
                    "height": container_original.height,
                }
            ),
            "logoContainerSizeValid": container_size_ok if container_detected else False,
            "layoutScore": layout_score,
            "safeAreaBoundingBox": {
                "x": safe_original.x,
                "y": safe_original.y,
                "width": safe_original.width,
                "height": safe_original.height,
            },
        }
