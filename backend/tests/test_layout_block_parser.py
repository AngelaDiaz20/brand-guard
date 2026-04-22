import unittest

from app.services.layout_block_parser import build_ocr_blocks


class LayoutBlockParserTests(unittest.TestCase):
    def test_groups_words_into_lines_and_blocks_with_traceability(self) -> None:
        words = [
            {"text": "SOBRE", "box": [10, 10, 50, 20], "confidence": 0.95},
            {"text": "RUEDAS", "box": [70, 12, 70, 20], "confidence": 0.93},
            {"text": "Del", "box": [10, 45, 25, 18], "confidence": 0.90},
            {"text": "lunes", "box": [40, 45, 50, 18], "confidence": 0.90},
            {"text": "16", "box": [95, 45, 20, 18], "confidence": 0.90},
            {"text": "al", "box": [120, 45, 15, 18], "confidence": 0.90},
            {"text": "22", "box": [140, 45, 20, 18], "confidence": 0.90},
            {"text": "de", "box": [165, 45, 15, 18], "confidence": 0.90},
            {"text": "marzo", "box": [185, 45, 45, 18], "confidence": 0.90},
            {"text": "AUTOSTYLE", "box": [10, 80, 90, 22], "confidence": 0.92},
            {"text": "SKU:", "box": [10, 220, 35, 18], "confidence": 0.94},
            {"text": "3719383", "box": [50, 220, 60, 18], "confidence": 0.96},
        ]

        payload = build_ocr_blocks(words)
        self.assertIn("lines", payload)
        self.assertIn("microBlocks", payload)
        self.assertIn("blocks", payload)

        lines = payload["lines"]
        micro_blocks = payload["microBlocks"]
        blocks = payload["blocks"]

        self.assertTrue(len(lines) >= 3)
        self.assertTrue(len(micro_blocks) >= 3)
        self.assertTrue(len(blocks) >= 3)

        # Lines should have stable ids.
        self.assertTrue(all(isinstance(line.get("id"), str) and line["id"] for line in lines))

        # Blocks should reference lines.
        self.assertTrue(all("lineIds" in block for block in blocks))

        # Campaign and date should not be fused in a single block.
        campaigns = [b for b in blocks if b.get("type") == "campaign"]
        dates = [b for b in blocks if b.get("type") == "date_range"]
        skus = [b for b in blocks if b.get("type") == "sku"]

        self.assertTrue(any("SOBRE RUEDAS" in str(b.get("text", "")) for b in campaigns))
        self.assertTrue(any("Del lunes" in str(b.get("text", "")) for b in dates))
        self.assertTrue(any("SKU" in str(b.get("text", "")) for b in skus))

        # Description and price main should not be fused.
        descriptions = [b for b in blocks if b.get("type") == "description"]
        prices = [b for b in blocks if b.get("type") == "price_main"]
        if descriptions and prices:
            desc_text = "\n".join(str(b.get("text", "")) for b in descriptions)
            price_text = "\n".join(str(b.get("text", "")) for b in prices)
            self.assertNotIn("S/ 25.90", desc_text)
            self.assertIn("25.90", price_text)

    def test_detects_promo_badge_and_keeps_it_separate(self) -> None:
        words = [
            {"text": "Paños", "box": [10, 100, 60, 20], "confidence": 0.92},
            {"text": "de", "box": [75, 100, 20, 20], "confidence": 0.90},
            {"text": "Microfibra", "box": [100, 100, 90, 20], "confidence": 0.92},
            {"text": "x", "box": [195, 100, 12, 20], "confidence": 0.90},
            {"text": "30", "box": [212, 100, 22, 20], "confidence": 0.90},
            {"text": "unidades", "box": [240, 100, 70, 20], "confidence": 0.90},
            {"text": "S/ 25.90", "box": [10, 140, 80, 28], "confidence": 0.94},
            # Badge lateral junto al precio (no debe contaminar extracción core).
            {"text": "CMR", "box": [140, 140, 40, 20], "confidence": 0.93},
            {"text": "Débito", "box": [140, 165, 55, 18], "confidence": 0.92},
            {"text": "SKU:", "box": [10, 200, 35, 18], "confidence": 0.94},
            {"text": "3719383", "box": [50, 200, 60, 18], "confidence": 0.96},
        ]

        payload = build_ocr_blocks(words)
        blocks = payload["blocks"]

        promo = [b for b in blocks if b.get("type") == "promo_badge"]
        self.assertTrue(promo, "Se esperaba al menos un bloque promo_badge.")
        promo_text = "\n".join(str(b.get("text", "")) for b in promo)
        self.assertIn("CMR", promo_text)

        prices = [b for b in blocks if b.get("type") == "price_main"]
        self.assertTrue(prices, "Se esperaba un bloque price_main para 'S/ 25.90'.")

        # Asegura que no se fusione badge con precio (en texto del bloque price_main).
        price_text = "\n".join(str(b.get("text", "")) for b in prices)
        self.assertNotIn("CMR", price_text)
        self.assertNotIn("Débito", price_text)


if __name__ == "__main__":
    unittest.main()
