from __future__ import annotations

from functools import lru_cache
from io import BytesIO
from threading import local, current_thread
from typing import Any, Sequence, Dict, List

import numpy as np
import cv2
from PIL import Image, ImageOps

from app.services.text_correction_service import correct_text, estimate_correction_ratio

_THREAD_LOCAL = local()

# --------------------------------------------------
# OCR ENGINE
# --------------------------------------------------

def _build_ocr_engine() -> Any:
    from paddleocr import PaddleOCR

    return PaddleOCR(
        use_angle_cls=True,
        lang="latin",
        use_gpu=False,
        show_log=False,
        use_space_char=True,
    )


@lru_cache(maxsize=1)
def _get_main_thread_ocr_engine() -> Any:
    return _build_ocr_engine()


def _get_ocr_engine() -> Any:
    # PaddleOCR is more stable with one engine instance per worker thread.
    if current_thread().name == "MainThread":
        return _get_main_thread_ocr_engine()

    engine = getattr(_THREAD_LOCAL, "ocr_engine", None)
    if engine is None:
        engine = _build_ocr_engine()
        _THREAD_LOCAL.ocr_engine = engine
    return engine


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


def _compute_score(
    raw_text: str,
    corrected_text: str,
    confidence_metrics: Dict[str, float],
) -> float | None:
    stripped_text = (corrected_text or raw_text).strip()
    if not stripped_text:
        return None

    length_score = min(len(stripped_text) / 120.0, 1.0)
    correction_ratio = estimate_correction_ratio(raw_text, corrected_text)
    score = (
        confidence_metrics["avg"] * 0.55
        + confidence_metrics["min"] * 0.20
        + length_score * 0.15
        + (1.0 - correction_ratio) * 0.10
    )
    return float(round(min(max(score, 0.0), 1.0), 4))


def build_ocr_payload(
    raw_text: str,
    words: List[Dict[str, Any]] | None = None,
    confidence: Dict[str, float] | None = None,
) -> Dict[str, Any]:
    """Build a backward-compatible OCR payload with correction metadata."""
    normalized_words = words or []
    confidence_metrics = confidence or _compute_confidence(normalized_words)
    corrected_version = correct_text(raw_text)

    return {
        "rawText": raw_text,
        "correctedText": corrected_version,
        "words": normalized_words,
        "confidence": confidence_metrics,
        "score": _compute_score(raw_text, corrected_version, confidence_metrics),
    }


def normalize_image_array(pil_image: Image.Image) -> np.ndarray:
    """Public wrapper reused by PDF OCR before dispatching to the engine."""
    return _normalize_image(pil_image)


def enhance_image_for_ocr(image_array: np.ndarray) -> np.ndarray:
    """Public wrapper to reuse the same preprocessing in PDF OCR."""
    return _enhance_for_ocr(image_array)


def compute_confidence_metrics(words: List[Dict[str, Any]]) -> Dict[str, float]:
    """Public confidence helper shared across OCR entry points."""
    return _compute_confidence(words)


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


def run_ocr_on_image_array(image_array: np.ndarray) -> Dict[str, Any]:
    """
    Execute PaddleOCR directly on a prepared image array.

    This raises upstream exceptions so callers can decide on fallbacks.
    """
    result = _run_single_pass(image_array)
    confidence_metrics = _compute_confidence(result["words"])

    if confidence_metrics["avg"] < 0.85:
        enhanced = _enhance_for_ocr(image_array)
        enhanced_result = _run_single_pass(enhanced)

        enhanced_conf = _compute_confidence(enhanced_result["words"])
        if enhanced_conf["avg"] > confidence_metrics["avg"]:
            result = enhanced_result
            confidence_metrics = enhanced_conf

    return build_ocr_payload(
        raw_text=result["fullText"],
        words=result["words"],
        confidence=confidence_metrics,
    )


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
        return run_ocr_on_image_array(base_image)

    except Exception:
        return {}
