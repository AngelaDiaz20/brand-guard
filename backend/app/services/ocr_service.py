"""Service responsible for OCR extraction with PaddleOCR."""

from __future__ import annotations

from functools import lru_cache
from io import BytesIO
from typing import Any, Sequence

import numpy as np
from PIL import Image, ImageOps


@lru_cache(maxsize=1)
def _get_ocr_engine() -> Any:
    """Build and cache a CPU-only PaddleOCR engine.

    IMPORTANT:
    - If you change lang/models, you MUST restart the backend because of lru_cache.
    """
    from paddleocr import PaddleOCR

    # For Spanish, PaddleOCR usually works best with lang="latin"
    return PaddleOCR(
        use_angle_cls=True,
        lang="latin",
        use_gpu=False,
        show_log=False,
        use_space_char=True,
    )


def _quad_to_xywh(points: Sequence[Sequence[float]]) -> list[int]:
    """Convert PaddleOCR quadrilateral points into [x, y, w, h]."""
    xs = [float(p[0]) for p in points]
    ys = [float(p[1]) for p in points]

    min_x = int(round(min(xs)))
    min_y = int(round(min(ys)))
    max_x = int(round(max(xs)))
    max_y = int(round(max(ys)))

    return [min_x, min_y, max(0, max_x - min_x), max(0, max_y - min_y)]


def _normalize_image_for_ocr(pil_image: Image.Image) -> np.ndarray:
    """Prepare image for OCR (robust orientation + RGB)."""
    # Fix EXIF orientation (common on photos from phones)
    pil_image = ImageOps.exif_transpose(pil_image)
    pil_image = pil_image.convert("RGB")
    return np.asarray(pil_image, dtype=np.uint8)


def _soft_fix_common_ocr_confusions(text: str) -> str:
    out_tokens: list[str] = []
    for tok in text.split():
        has_alpha = any(ch.isalpha() for ch in tok)
        has_zero = "0" in tok
        if has_alpha and has_zero:
            tok = tok.replace("0", "O")
        out_tokens.append(tok)
    return " ".join(out_tokens)


def run_ocr(image_bytes: bytes) -> dict[str, Any]:
    """Run OCR and return normalized text content."""
    try:
        with Image.open(BytesIO(image_bytes)) as image:
            image_array = _normalize_image_for_ocr(image)

        raw_result = _get_ocr_engine().ocr(image_array, cls=True)

        words: list[dict[str, Any]] = []
        lines_text: list[str] = []

        # PaddleOCR output is typically: [ [ [box, (text, conf)], ... ] ]
        lines = raw_result[0] if raw_result and isinstance(raw_result, list) else []

        for line in lines:
            if not isinstance(line, (list, tuple)) or len(line) < 2:
                continue

            box_points, text_info = line[0], line[1]
            if (
                not isinstance(box_points, (list, tuple))
                or len(box_points) != 4
                or not isinstance(text_info, (list, tuple))
                or len(text_info) < 2
            ):
                continue

            normalized_points: list[list[float]] = []
            for point in box_points:
                if not isinstance(point, (list, tuple)) or len(point) < 2:
                    normalized_points = []
                    break
                normalized_points.append([float(point[0]), float(point[1])])

            if not normalized_points:
                continue

            text = str(text_info[0]).strip()
            confidence = float(text_info[1])

            if not text:
                continue

            words.append(
                {
                    "text": text,
                    "box": _quad_to_xywh(normalized_points),
                    "confidence": confidence,
                }
            )

            # Keep a per-line list (better than concatenating word by word)
            lines_text.append(text)

        full_text = "\n".join(lines_text).strip()
        full_text = _soft_fix_common_ocr_confusions(full_text)

        return {
            "fullText": full_text,
            "words": words,
        }
    except Exception:
        return {}