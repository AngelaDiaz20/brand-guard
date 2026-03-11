from __future__ import annotations

import unittest
from io import BytesIO

from PIL import Image, ImageDraw

from app.services.layout_rules import LAYOUT_RULES
from app.services.layout_validation_service import validate_layout


def make_png_bytes(image: Image.Image) -> bytes:
    buf = BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


class LayoutValidationServiceTests(unittest.TestCase):
    def test_detects_logo_and_validates_safe_area_and_size_1x1(self) -> None:
        rule = LAYOUT_RULES["1:1"]
        canvas_w = int(rule["canvas"]["width"])
        canvas_h = int(rule["canvas"]["height"])

        img = Image.new("RGB", (canvas_w, canvas_h), (255, 255, 255))

        logo_w = int(round(rule["logo"]["width"]))
        logo_h = int(round(rule["logo"]["height"]))

        # Draw a simple "house" icon (black) with a white mask.
        mask = Image.new("L", (logo_w, logo_h), 0)
        mdraw = ImageDraw.Draw(mask)
        mdraw.polygon(
            [
                (logo_w * 0.15, logo_h * 0.55),
                (logo_w * 0.5, logo_h * 0.08),
                (logo_w * 0.85, logo_h * 0.55),
            ],
            fill=255,
        )
        mdraw.rectangle([logo_w * 0.25, logo_h * 0.55, logo_w * 0.75, logo_h * 0.92], fill=255)
        door_w = logo_w * 0.18
        door_h = logo_h * 0.32
        door_x0 = logo_w * 0.5 - door_w / 2
        door_y0 = logo_h * 0.92 - door_h
        mdraw.rectangle([door_x0, door_y0, door_x0 + door_w, logo_h * 0.92], fill=0)
        house = Image.new("RGB", (logo_w, logo_h), (0, 0, 0))

        # Place near top-right but within safe area.
        logo_x = 950
        logo_y = 60
        img.paste(house, (logo_x, logo_y), mask)

        payload = validate_layout(make_png_bytes(img))

        self.assertEqual(payload["pieceType"], "1:1")
        self.assertTrue(payload["logoDetected"])
        self.assertTrue(payload["logoInsideSafeArea"])
        self.assertTrue(payload["logoSizeValid"])
        self.assertTrue(payload["logoPositionValid"])
        self.assertFalse(payload["logoContainerDetected"])
        self.assertEqual(payload["layoutScore"], 100)

    def test_detects_container_when_present_and_validates_size(self) -> None:
        rule = LAYOUT_RULES["1:1"]
        canvas_w = int(rule["canvas"]["width"])
        canvas_h = int(rule["canvas"]["height"])

        img = Image.new("RGB", (canvas_w, canvas_h), (255, 255, 255))

        logo_w = int(round(rule["logo"]["width"]))
        logo_h = int(round(rule["logo"]["height"]))
        container_w = int(round(rule["logo_container"]["width"]))
        container_h = int(round(rule["logo_container"]["height"]))

        # Place logo and its container in the expected region.
        logo_x = 940
        logo_y = 70

        container_x = int(round((logo_x + logo_w / 2) - container_w / 2))
        container_y = int(round((logo_y + logo_h / 2) - container_h / 2))

        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle(
            [container_x, container_y, container_x + container_w, container_y + container_h],
            radius=18,
            fill=(225, 225, 225),
        )

        # House icon on top
        mask = Image.new("L", (logo_w, logo_h), 0)
        mdraw = ImageDraw.Draw(mask)
        mdraw.polygon(
            [
                (logo_w * 0.15, logo_h * 0.55),
                (logo_w * 0.5, logo_h * 0.08),
                (logo_w * 0.85, logo_h * 0.55),
            ],
            fill=255,
        )
        mdraw.rectangle([logo_w * 0.25, logo_h * 0.55, logo_w * 0.75, logo_h * 0.92], fill=255)
        door_w = logo_w * 0.18
        door_h = logo_h * 0.32
        door_x0 = logo_w * 0.5 - door_w / 2
        door_y0 = logo_h * 0.92 - door_h
        mdraw.rectangle([door_x0, door_y0, door_x0 + door_w, logo_h * 0.92], fill=0)
        house = Image.new("RGB", (logo_w, logo_h), (0, 0, 0))
        img.paste(house, (logo_x, logo_y), mask)

        payload = validate_layout(make_png_bytes(img))

        self.assertTrue(payload["logoDetected"])
        self.assertTrue(payload["logoContainerDetected"])
        self.assertTrue(payload["logoContainerSizeValid"])
        self.assertEqual(payload["layoutScore"], 100)


if __name__ == "__main__":
    unittest.main()
