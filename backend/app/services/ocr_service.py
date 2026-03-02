from __future__ import annotations

from functools import lru_cache
from io import BytesIO
from typing import Any, Sequence, Dict, List

import numpy as np
import cv2
from PIL import Image, ImageOps


# --------------------------------------------------
# OCR ENGINE
# --------------------------------------------------

@lru_cache(maxsize=1)
def _get_ocr_engine() -> Any:
    from paddleocr import PaddleOCR

    return PaddleOCR(
        use_angle_cls=True,
        lang="latin",
        use_gpu=False,
        show_log=False,
        use_space_char=True,
    )


# --------------------------------------------------
# IMAGE PREPROCESSING
# --------------------------------------------------

def _normalize_image(pil_image: Image.Image) -> np.ndarray:
    pil_image = ImageOps.exif_transpose(pil_image)
    pil_image = pil_image.convert("RGB")
    return np.asarray(pil_image, dtype=np.uint8)


def _enhance_for_ocr(image_array: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)

    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)

    thresh = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,
        2,
    )

    return cv2.cvtColor(thresh, cv2.COLOR_GRAY2RGB)


# --------------------------------------------------
# UTILS
# --------------------------------------------------

def _quad_to_xywh(points: Sequence[Sequence[float]]) -> List[int]:
    xs = [float(p[0]) for p in points]
    ys = [float(p[1]) for p in points]

    min_x = int(round(min(xs)))
    min_y = int(round(min(ys)))
    max_x = int(round(max(xs)))
    max_y = int(round(max(ys)))

    return [min_x, min_y, max(0, max_x - min_x), max(0, max_y - min_y)]


def _compute_confidence(words: List[Dict[str, Any]]) -> Dict[str, float]:
    if not words:
        return {"avg": 0.0, "min": 0.0}

    confidences = [w["confidence"] for w in words]
    return {
        "avg": float(sum(confidences) / len(confidences)),
        "min": float(min(confidences)),
    }


def _soft_fix_common_ocr_confusions(text: str) -> str:
    # Solo heurística ligera (NO ML todavía)
    replacements = {
        "promocion": "promoción",
        "valido": "válido",
        "mas": "más",
    }

    tokens = text.split()
    corrected = []

    for tok in tokens:
        base = tok.lower()
        if base in replacements:
            corrected.append(replacements[base])
        else:
            corrected.append(tok)

    return " ".join(corrected)


# --------------------------------------------------
# OCR CORE EXECUTION
# --------------------------------------------------

def _run_single_pass(image_array: np.ndarray) -> Dict[str, Any]:
    raw_result = _get_ocr_engine().ocr(image_array, cls=True)

    words: List[Dict[str, Any]] = []
    lines_text: List[str] = []

    lines = raw_result[0] if raw_result and isinstance(raw_result, list) else []

    for line in lines:
        if not isinstance(line, (list, tuple)) or len(line) < 2:
            continue

        box_points, text_info = line[0], line[1]

        if not text_info or len(text_info) < 2:
            continue

        text = str(text_info[0]).strip()
        confidence = float(text_info[1])

        if not text:
            continue

        words.append(
            {
                "text": text,
                "box": _quad_to_xywh(box_points),
                "confidence": confidence,
            }
        )

        lines_text.append(text)

    full_text = "\n".join(lines_text).strip()

    return {
        "fullText": full_text,
        "words": words,
    }


# --------------------------------------------------
# MAIN PUBLIC FUNCTION
# --------------------------------------------------

def run_ocr(image_bytes: bytes) -> Dict[str, Any]:
    """
    Returns:
    - rawText (exact OCR output)
    - correctedText (post-processed version)
    - words
    - confidence metrics
    """

    try:
        with Image.open(BytesIO(image_bytes)) as image:
            base_image = _normalize_image(image)

        # First pass
        result = _run_single_pass(base_image)
        confidence_metrics = _compute_confidence(result["words"])

        # If confidence low, enhance and retry
        if confidence_metrics["avg"] < 0.85:
            enhanced = _enhance_for_ocr(base_image)
            enhanced_result = _run_single_pass(enhanced)

            enhanced_conf = _compute_confidence(enhanced_result["words"])

            if enhanced_conf["avg"] > confidence_metrics["avg"]:
                result = enhanced_result
                confidence_metrics = enhanced_conf

        raw_text = result["fullText"]

        # VERSION 1 → RAW
        raw_version = raw_text

        # VERSION 2 → CORRECTED (heuristic for now, ML-ready)
        corrected_version = _soft_fix_common_ocr_confusions(raw_text)

        return {
            "rawText": raw_version,
            "correctedText": corrected_version,
            "words": result["words"],
            "confidence": confidence_metrics,
        }

    except Exception:
        return {}