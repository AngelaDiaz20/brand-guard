import unittest

from app.services.structured_piece_extraction_service import extract_structured_fields_from_blocks


class StructuredPieceExtractionServiceTests(unittest.TestCase):
    def test_ignores_promo_badge_blocks(self) -> None:
        blocks = [
            {"id": "block_1", "type": "promo_badge", "text": "CMR", "bbox": [140, 140, 40, 20], "confidence": 0.99},
            {"id": "block_2", "type": "brand", "text": "AUTOSTYLE", "bbox": [10, 80, 90, 22], "confidence": 0.86},
            {"id": "block_3", "type": "description", "text": "Paños de Microfibra x 30 unidades", "bbox": [10, 100, 250, 25], "confidence": 0.83},
            {"id": "block_4", "type": "price_main", "text": "S/ 25.90", "bbox": [10, 140, 80, 28], "confidence": 0.94},
            {"id": "block_5", "type": "sku", "text": "SKU: 3719383", "bbox": [10, 200, 120, 18], "confidence": 0.96},
        ]

        extracted = extract_structured_fields_from_blocks(blocks)
        self.assertEqual((extracted.get("brand") or {}).get("value"), "AUTOSTYLE")
        self.assertEqual((extracted.get("priceMain") or {}).get("value"), "25.90")
        self.assertEqual((extracted.get("sku") or {}).get("value"), "3719383")

    def test_ignores_blocks_from_product_photo_area_when_region_is_provided(self) -> None:
        blocks = [
            # Incidental label text inside product photo (should not drive brand/description/campaign).
            {
                "id": "block_photo_1",
                "type": "description",
                "text": "LIQUI MOLY TOPTEC 4100",
                "bbox": [600, 800, 200, 40],
                "confidence": 0.99,
                "regionClassName": "product_photo_area",
            },
            # Real layout text in info card.
            {
                "id": "block_info_1",
                "type": "description",
                "text": "Aceite de Motor Liqui Moly 5W-40 Top Tec 4100 1 L",
                "bbox": [40, 900, 600, 60],
                "confidence": 0.88,
                "regionClassName": "info_card_area",
            },
            {
                "id": "block_info_2",
                "type": "sku",
                "text": "SKU: 3655652",
                "bbox": [40, 980, 180, 22],
                "confidence": 0.92,
                "regionClassName": "sku_area",
            },
            {
                "id": "block_campaign",
                "type": "campaign",
                "text": "SOBRE RUEDAS",
                "bbox": [40, 60, 260, 30],
                "confidence": 0.90,
                "regionClassName": "campaign_area",
            },
        ]

        extracted = extract_structured_fields_from_blocks(
            blocks,
            excluded_region_classes={"product_photo_area"},
        )
        self.assertEqual((extracted.get("campaign") or {}).get("value"), "SOBRE RUEDAS")
        self.assertEqual(
            (extracted.get("description") or {}).get("value"),
            "Aceite de Motor Liqui Moly 5W-40 Top Tec 4100 1 L",
        )
        self.assertEqual((extracted.get("sku") or {}).get("value"), "3655652")


if __name__ == "__main__":
    unittest.main()
