"""Service responsible for OCR extraction with PaddleOCR."""

from functools import lru_cache
from io import BytesIO
from typing import Any, Sequence

import numpy as np
from PIL import Image


@lru_cache(maxsize=1)
def _get_ocr_engine() -> Any:
    """Build and cache a CPU-only PaddleOCR engine."""
    from paddleocr import PaddleOCR

    return PaddleOCR(use_angle_cls=True, lang="en", use_gpu=False, show_log=False)


def _quad_to_xywh(points: Sequence[Sequence[float]]) -> list[int]:
    """Convert PaddleOCR quadrilateral points into [x, y, w, h]."""
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]

    min_x = int(round(min(xs)))
    min_y = int(round(min(ys)))
    max_x = int(round(max(xs)))
    max_y = int(round(max(ys)))

    return [min_x, min_y, max(0, max_x - min_x), max(0, max_y - min_y)]


def run_ocr(image_bytes: bytes) -> dict[str, Any]:
    """Run OCR and return normalized text content."""
    try:
        with Image.open(BytesIO(image_bytes)) as image:
            image_array = np.asarray(image.convert("RGB"), dtype=np.uint8)

        raw_result = _get_ocr_engine().ocr(image_array, cls=True)

        words: list[dict[str, Any]] = []
        full_text_parts: list[str] = []

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
            full_text_parts.append(text)

        return {
            "fullText": " ".join(full_text_parts),
            "words": words,
        }
    except Exception:
        return {}
