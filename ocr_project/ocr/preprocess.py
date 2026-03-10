"""Image preprocessing for stylized ad creatives."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def load_image(image_path: str | Path) -> np.ndarray:
    """Load an image from disk as a BGR OpenCV array."""
    path = Path(image_path)
    image = cv2.imread(str(path))
    if image is None:
        raise FileNotFoundError(f"Unable to read image at {path}")
    return image


def preprocess_for_ocr(image: np.ndarray) -> np.ndarray:
    """Apply a conservative OCR preprocessing chain."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    thresholded = cv2.adaptiveThreshold(
        enhanced,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11,
    )

    denoised = cv2.medianBlur(thresholded, 3)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    opened = cv2.morphologyEx(denoised, cv2.MORPH_OPEN, kernel)
    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel)
    return closed


def build_preprocess_variants(image: np.ndarray) -> dict[str, np.ndarray]:
    """Create multiple OCR-friendly variants and let the engine pick the best one."""
    base = preprocess_for_ocr(image)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    contrast_boost = cv2.convertScaleAbs(gray, alpha=1.5, beta=10)
    otsu = cv2.threshold(contrast_boost, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    dilated = cv2.dilate(base, kernel, iterations=1)

    return {
        "adaptive": base,
        "otsu": otsu,
        "dilated": dilated,
    }
