"""Layout compliance validation (safe area, logo, optional logo container).

Implementation notes:
- Rules are hardcoded locally for now (see layout_rules.py).
- Logo detection uses template matching (multi-scale) in the top-right region.
- Bounding boxes are returned in the ORIGINAL image coordinate system.
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from functools import lru_cache
from pathlib import Path
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
    # Fallback "house" icon template used only if the official template cannot be loaded.
    img = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(img)

    base_y = int(round(height * 0.55))
    draw.polygon(
        [
            (width * 0.15, base_y),
            (width * 0.5, height * 0.08),
            (width * 0.85, base_y),
        ],
        fill=255,
    )
    draw.rectangle([width * 0.25, base_y, width * 0.75, height * 0.92], fill=255)

    door_w = width * 0.18
    door_h = height * 0.32
    door_x0 = width * 0.5 - door_w / 2.0
    door_y0 = height * 0.92 - door_h
    draw.rectangle([door_x0, door_y0, door_x0 + door_w, height * 0.92], fill=0)
    return img


def _repo_root() -> Path:
    # backend/app/services/layout_validation_service.py -> repo root
    return Path(__file__).resolve().parents[3]


@lru_cache(maxsize=1)
def _load_official_logo_template() -> Image.Image | None:
    candidates = [
        _repo_root() / "assets" / "brand" / "sodimac_logo.png",
        _repo_root() / "backend" / "assets" / "brand" / "sodimac_logo.png",
        _repo_root() / "backend" / "assets" / "brand" / "sodimac" / "logo.png",
    ]

    path = next((p for p in candidates if p.exists()), None)
    if path is None:
        return None

    try:
        with Image.open(path) as img:
            img = ImageOps.exif_transpose(img).convert("RGBA")
            alpha = img.split()[-1]
            bbox = alpha.getbbox()
            if bbox:
                img = img.crop(bbox)

            # Composite on white to avoid edge artifacts from transparency.
            bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
            bg.alpha_composite(img)
            return bg.convert("L")
    except Exception:
        return None


def _get_logo_template_for_canvas(piece_type: PieceType) -> Image.Image:
    rule = LAYOUT_RULES[piece_type]
    w = int(round(rule["logo"]["width"]))
    h = int(round(rule["logo"]["height"]))

    official = _load_official_logo_template()
    if official is None:
        return _generate_house_logo_template(w, h)

    return official.resize((w, h), Image.Resampling.LANCZOS)


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

    # Threshold for edge-based cosine similarity.
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


def _bbox_inside(inner: BBox, outer: BBox) -> bool:
    return (
        inner.x_min >= outer.x_min
        and inner.y_min >= outer.y_min
        and inner.x_max <= outer.x_max
        and inner.y_max <= outer.y_max
    )


def _text_inside_safe_area(
    *,
    safe_area_original: BBox,
    ocr_words: list[dict] | None,
) -> bool:
    if not ocr_words:
        return True

    for w in ocr_words:
        box = w.get("box") if isinstance(w, dict) else None
        if not (isinstance(box, list) and len(box) == 4):
            continue

        try:
            x, y, width, height = (float(box[0]), float(box[1]), float(box[2]), float(box[3]))
        except Exception:
            continue

        if width <= 0 or height <= 0:
            continue

        word_bbox = BBox(x=x, y=y, width=width, height=height)
        if not _bbox_inside(word_bbox, safe_area_original):
            return False

    return True


def _compute_layout_score(
    *,
    logo_detected: bool,
    logo_inside_safe_area: bool,
    logo_position_valid: bool,
    logo_size_valid: bool,
    logo_container_detected: bool,
    logo_container_size_valid: bool,
    text_inside_safe_area: bool,
) -> int:
    # Required score components:
    # - safeAreaCompliance
    # - logoPlacement
    # - logoSize
    # - containerSize
    # - textInsideSafeArea
    #
    # IMPORTANT: logoDetected must NOT affect the score.
    # Keep a fixed denominator so "logo no encontrado" doesn't change the score.
    safe_area_compliance = logo_inside_safe_area if logo_detected else True
    logo_placement = logo_position_valid if logo_detected else True
    logo_size = logo_size_valid if logo_detected else True
    container_size = (
        True
        if not logo_detected
        else (not logo_container_detected) or logo_container_size_valid
    )

    checks: list[bool] = [
        safe_area_compliance,
        logo_placement,
        logo_size,
        container_size,
        text_inside_safe_area,
    ]

    return int(round(100.0 * (sum(1 for c in checks if c) / len(checks)))) if checks else 0


def validate_layout(image_bytes: bytes, ocr_words: list[dict] | None = None) -> dict:
    """Validate layout compliance for an uploaded image."""
    with Image.open(BytesIO(image_bytes)) as image:
        original_w, original_h = image.size
        piece_type = _detect_piece_type(original_w, original_h)

        if piece_type is None:
            return {
                "pieceType": None,
                "logoDetected": False,
                "logoWarning": False,
                "logoBoundingBox": None,
                "logoPosition": None,
                "logoSizeValid": False,
                "logoInsideSafeArea": False,
                "logoPositionValid": False,
                "logoContainerDetected": False,
                "logoContainerBoundingBox": None,
                "logoContainerPosition": None,
                "logoContainerSizeValid": False,
                "textInsideSafeArea": True,
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

        text_inside_safe_area = _text_inside_safe_area(safe_area_original=safe_original, ocr_words=ocr_words)

        logo_canvas, match_score = _detect_logo_on_canvas(image_canvas, piece_type)
        if logo_canvas is None:
            layout_score = _compute_layout_score(
                logo_detected=False,
                logo_inside_safe_area=False,
                logo_position_valid=False,
                logo_size_valid=False,
                logo_container_detected=False,
                logo_container_size_valid=False,
                text_inside_safe_area=text_inside_safe_area,
            )
            return {
                "pieceType": piece_type,
                "logoDetected": False,
                "logoWarning": True,
                "logoBoundingBox": None,
                "logoPosition": None,
                "logoSizeValid": False,
                "logoInsideSafeArea": False,
                "logoPositionValid": False,
                "logoContainerDetected": False,
                "logoContainerBoundingBox": None,
                "logoContainerPosition": None,
                "logoContainerSizeValid": False,
                "textInsideSafeArea": text_inside_safe_area,
                "layoutScore": layout_score,
                "safeAreaBoundingBox": {
                    "x": safe_original.x,
                    "y": safe_original.y,
                    "width": safe_original.width,
                    "height": safe_original.height,
                },
            }

        logo_original = _scale_bbox(logo_canvas, sx, sy)

        expected_logo_w = float(rule["logo"]["width"])
        expected_logo_h = float(rule["logo"]["height"])
        size_ok = (
            abs(logo_canvas.width - expected_logo_w) <= expected_logo_w * 0.10
            and abs(logo_canvas.height - expected_logo_h) <= expected_logo_h * 0.10
        )

        inside_safe = _bbox_inside(logo_canvas, safe_canvas)

        expected_x = float(rule["logo"]["x"])
        expected_y = float(rule["logo"]["y"])
        position_ok = abs(logo_canvas.x - expected_x) <= 40.0 and abs(logo_canvas.y - expected_y) <= 40.0

        container_bbox_canvas = _detect_logo_container_on_canvas(image_canvas, piece_type, logo_canvas)
        container_detected = container_bbox_canvas is not None
        container_size_ok = False
        container_original: BBox | None = None

        if container_bbox_canvas is not None:
            container_original = _scale_bbox(container_bbox_canvas, sx, sy)
            expected_cw = float(rule["logo_container"]["width"])
            expected_ch = float(rule["logo_container"]["height"])
            container_size_ok = (
                abs(container_bbox_canvas.width - expected_cw) <= expected_cw * 0.10
                and abs(container_bbox_canvas.height - expected_ch) <= expected_ch * 0.10
            )

        layout_score = _compute_layout_score(
            logo_detected=True,
            logo_inside_safe_area=inside_safe,
            logo_position_valid=position_ok,
            logo_size_valid=size_ok,
            logo_container_detected=container_detected,
            logo_container_size_valid=container_size_ok,
            text_inside_safe_area=text_inside_safe_area,
        )

        return {
            "pieceType": piece_type,
            "logoDetected": True,
            "logoWarning": False,
            "logoBoundingBox": {
                "x": logo_original.x,
                "y": logo_original.y,
                "width": logo_original.width,
                "height": logo_original.height,
            },
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
            "logoContainerBoundingBox": (
                None
                if container_original is None
                else {
                    "x": container_original.x,
                    "y": container_original.y,
                    "width": container_original.width,
                    "height": container_original.height,
                }
            ),
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
            "textInsideSafeArea": text_inside_safe_area,
            "layoutScore": layout_score,
            "safeAreaBoundingBox": {
                "x": safe_original.x,
                "y": safe_original.y,
                "width": safe_original.width,
                "height": safe_original.height,
            },
        }
