"""Tesseract OCR extraction helpers."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pytesseract


@dataclass(frozen=True)
class OCRResult:
    text: str
    variant_name: str
    score: tuple[int, int]


class TesseractOCREngine:
    """Thin wrapper around pytesseract with multi-variant selection."""

    def __init__(self, *, lang: str = "spa", config: str = "--oem 3 --psm 6") -> None:
        self.lang = lang
        self.config = config

    def extract_text(self, image: np.ndarray) -> str:
        try:
            text = pytesseract.image_to_string(image, lang=self.lang, config=self.config)
        except pytesseract.TesseractNotFoundError as exc:
            raise RuntimeError(
                "Tesseract executable was not found. Install Tesseract OCR and ensure it is in PATH."
            ) from exc
        except pytesseract.TesseractError as exc:
            message = str(exc)
            if "traineddata" in message or "Could not initialize tesseract" in message:
                raise RuntimeError(
                    "Spanish Tesseract language data is missing. Install `spa.traineddata` or configure TESSDATA_PREFIX."
                ) from exc
            raise RuntimeError(f"Tesseract OCR failed: {message}") from exc
        return text.strip()

    def extract_best_text(self, images: dict[str, np.ndarray]) -> OCRResult:
        best_result = OCRResult(text="", variant_name="none", score=(0, 0))

        for variant_name, image in images.items():
            text = self.extract_text(image)
            score = self._score_text(text)
            candidate = OCRResult(text=text, variant_name=variant_name, score=score)
            if candidate.score > best_result.score:
                best_result = candidate

        return best_result

    @staticmethod
    def _score_text(text: str) -> tuple[int, int]:
        compact = "".join(char for char in text if char.isalnum())
        word_count = len([word for word in text.split() if any(ch.isalpha() for ch in word)])
        return (len(compact), word_count)
