"""RapidFuzz helper for OCR token correction."""

from __future__ import annotations

import unicodedata
from functools import lru_cache

from rapidfuzz import fuzz, process


class FuzzyCorrector:
    """Normalize OCR-like tokens and map them to the closest dictionary term."""

    def __init__(self, *, threshold: int = 85) -> None:
        self.threshold = threshold

    def correct(self, token: str, dictionary: tuple[str, ...] | list[str]) -> tuple[str | None, float]:
        if not token or not any(char.isalpha() for char in token):
            return None, 0.0

        normalized_token = self._normalize(token)
        normalized_choices = {self._normalize(choice): choice for choice in dictionary}

        match = process.extractOne(
            normalized_token,
            normalized_choices.keys(),
            scorer=fuzz.ratio,
            score_cutoff=self.threshold,
        )
        if match is None:
            return None, 0.0

        matched_key, score, _ = match
        return normalized_choices[matched_key], float(score)

    @staticmethod
    @lru_cache(maxsize=2048)
    def _normalize(value: str) -> str:
        cleaned = value.upper()
        cleaned = cleaned.replace("0", "O").replace("1", "I").replace("5", "S")

        decomposed = unicodedata.normalize("NFD", cleaned)
        without_accents = "".join(
            char for char in decomposed if unicodedata.category(char) != "Mn"
        )
        return unicodedata.normalize("NFC", without_accents)
