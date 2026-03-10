"""Dictionary-driven OCR correction and entity detection."""

from __future__ import annotations

import re
from collections import OrderedDict
from dataclasses import dataclass

from dictionaries.brands import BRANDS
from dictionaries.cities_peru import PERU_CITIES, PERU_DISTRICTS
from dictionaries.marketing_words import MARKETING_WORDS
from utils.fuzzy_corrector import FuzzyCorrector

WORD_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]+(?:['-][A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]+)*", re.UNICODE)


@dataclass(frozen=True)
class PostprocessResult:
    raw_text: str
    corrected_text: str
    detected_brands: list[str]
    detected_locations: list[str]


class TextPostprocessor:
    """Correct OCR tokens with Peruvian brand and location dictionaries."""

    def __init__(self, *, threshold: int = 85) -> None:
        self.corrector = FuzzyCorrector(threshold=threshold)
        self.brands = tuple(BRANDS)
        self.locations = tuple([*PERU_CITIES, *PERU_DISTRICTS])
        self.marketing_words = tuple(MARKETING_WORDS)

    def process(self, raw_text: str) -> PostprocessResult:
        """Return corrected text plus detected brands and locations."""
        corrected_text = WORD_RE.sub(self._correct_match, raw_text).strip()
        corrected_text = re.sub(r"\s+", " ", corrected_text).strip()

        detected_brands = self._find_present_terms(corrected_text, self.brands)
        detected_locations = self._find_present_terms(corrected_text, self.locations)

        return PostprocessResult(
            raw_text=raw_text,
            corrected_text=corrected_text,
            detected_brands=detected_brands,
            detected_locations=detected_locations,
        )

    def _correct_match(self, match: re.Match[str]) -> str:
        token = match.group(0)
        corrected = self._correct_token(token)
        return self._restore_case(token, corrected)

    def _correct_token(self, token: str) -> str:
        candidates = (
            self.brands,
            self.locations,
            self.marketing_words,
        )

        best_match = token
        best_score = 0.0

        for dictionary in candidates:
            candidate, score = self.corrector.correct(token, dictionary)
            if candidate is None or score <= best_score:
                continue
            best_match = candidate
            best_score = score

        return best_match

    @staticmethod
    def _restore_case(source: str, replacement: str) -> str:
        if source.isupper():
            return replacement.upper()
        if source.islower():
            return replacement.lower()
        if source.istitle():
            return replacement.title()
        return replacement

    @staticmethod
    def _find_present_terms(text: str, terms: tuple[str, ...]) -> list[str]:
        normalized_text = text.upper()
        found: OrderedDict[str, None] = OrderedDict()
        for term in terms:
            pattern = rf"(?<!\w){re.escape(term.upper())}(?!\w)"
            if re.search(pattern, normalized_text):
                found[term] = None
        return list(found.keys())
