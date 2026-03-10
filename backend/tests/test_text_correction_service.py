from __future__ import annotations

import unittest

from app.services.ocr_service import build_ocr_payload
from app.services.text_correction_service import correct_text


class TextCorrectionServiceTests(unittest.TestCase):
    def test_multiline_question_segmentation_and_accents(self) -> None:
        raw_text = "CUALES EL MARTILLOIDEAL\nPARA TRABAJOS DE CARPINTERIA\nEN CAOBA?"

        corrected = correct_text(raw_text)

        self.assertEqual(
            corrected,
            "¿Cuál es el martillo ideal para trabajos de carpintería en caoba?",
        )

    def test_spacing_and_question_punctuation(self) -> None:
        self.assertEqual(correct_text("que tal ?"), "¿Qué tal?")
        self.assertEqual(correct_text("Hola , mundo ."), "Hola, mundo.")

    def test_list_structure_is_preserved_in_uppercase(self) -> None:
        corrected = correct_text("A) MARTILLO DE BOLA\nB) SIERRA MANUAL")

        self.assertEqual(corrected, "A) MARTILLO DE BOLA\nB) SIERRA MANUAL")

    def test_ocr_character_fix_handles_enye_case(self) -> None:
        self.assertEqual(correct_text("UNA'"), "UÑA")

    def test_structured_layout_is_preserved_for_title_question_and_options(self) -> None:
        raw_text = (
            "TRIVIA PRO\n"
            "CUALES EL MARTILLOIDEAL\n"
            "PARA TRABAJOS DE CARPINTERIA\n"
            "EN CAOBA?\n"
            "A) MARTILLO DE BOLA\n"
            "B) MARTILLO DE GOMA\n"
            "C) MARTILLO DE CARPINTERO JAPONES\n"
            "D) MARTILLO DE CARPINTERO TIPO \"UNA'"
        )

        corrected = correct_text(raw_text)

        self.assertEqual(
            corrected,
            (
                "TRIVIA PRO\n\n"
                "¿Cuál es el martillo ideal para trabajos de carpintería en caoba?\n\n"
                "A) MARTILLO DE BOLA\n"
                "B) MARTILLO DE GOMA\n"
                "C) MARTILLO DE CARPINTERO JAPONÉS\n"
                "D) MARTILLO DE CARPINTERO TIPO \"UÑA\""
            ),
        )

    def test_build_ocr_payload_preserves_schema_and_raw_text(self) -> None:
        payload = build_ocr_payload(
            raw_text="CUALES EL MARTILLOIDEAL",
            words=[{"text": "CUALES", "box": [0, 0, 10, 10], "confidence": 0.95}],
            confidence={"avg": 0.95, "min": 0.95},
        )

        self.assertEqual(payload["rawText"], "CUALES EL MARTILLOIDEAL")
        self.assertEqual(payload["correctedText"], "¿Cuál es el martillo ideal?")
        self.assertEqual(payload["words"][0]["text"], "CUALES")
        self.assertEqual(payload["confidence"], {"avg": 0.95, "min": 0.95})
        self.assertIn("score", payload)


if __name__ == "__main__":
    unittest.main()
