"""Pipeline orchestration for preprocessing, OCR, and correction."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ocr.ocr_engine import TesseractOCREngine
from ocr.postprocess import TextPostprocessor
from ocr.preprocess import build_preprocess_variants, load_image


class OCRPipeline:
    """Production-oriented OCR pipeline for Peruvian advertising images."""

    def __init__(self, *, threshold: int = 85) -> None:
        self.ocr_engine = TesseractOCREngine()
        self.postprocessor = TextPostprocessor(threshold=threshold)

    def run(self, image_path: str | Path) -> dict[str, Any]:
        """Load an image, run OCR, and return corrected structured output."""
        image = load_image(image_path)
        variants = build_preprocess_variants(image)
        raw_result = self.ocr_engine.extract_best_text(variants)
        postprocessed = self.postprocessor.process(raw_result.text)

        return {
            "raw_text": postprocessed.raw_text,
            "corrected_text": postprocessed.corrected_text,
            "detected_brands": postprocessed.detected_brands,
            "detected_locations": postprocessed.detected_locations,
        }
