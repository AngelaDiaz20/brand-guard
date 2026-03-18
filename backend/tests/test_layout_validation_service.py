from __future__ import annotations

import unittest
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw

from app.services.layout_rules import LAYOUT_RULES
from app.services.layout_validation_service import validate_layout


def make_png_bytes(image: Image.Image) -> bytes:
    buf = BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()

def load_official_logo_template() -> Image.Image | None:
    repo_root = Path(__file__).resolve().parents[2]
    candidates = [
        repo_root / "assets" / "brand" / "sodimac_logo.png",
        repo_root / "backend" / "assets" / "brand" / "sodimac_logo.png",
        repo_root / "backend" / "assets" / "brand" / "sodimac" / "logo.png",
    ]
    path = next((p for p in candidates if p.exists()), None)
    if path is None:
        return None
    return Image.open(path).convert("RGBA")


def paste_template_logo(img: Image.Image, *, x: int, y: int, width: int, height: int) -> None:
    template = load_official_logo_template()
    if template is None:
        raise RuntimeError("No se encontró el template oficial del logo para las pruebas.")

    template = template.resize((width, height), Image.Resampling.LANCZOS)
    rgb = template.convert("RGB")
    alpha = template.split()[-1]

    # If fully opaque, derive a mask from non-white pixels.
    if alpha.getextrema() == (255, 255):
        gray = template.convert("L")
        alpha = gray.point(lambda p: 255 if p < 250 else 0)

    img.paste(rgb, (x, y), alpha)


class LayoutValidationServiceTests(unittest.TestCase):
    def test_detects_logo_and_validates_safe_area_and_size_1x1(self) -> None:
        rule = LAYOUT_RULES["1:1"]
        canvas_w = int(rule["canvas"]["width"])
        canvas_h = int(rule["canvas"]["height"])

        img = Image.new("RGB", (canvas_w, canvas_h), (255, 255, 255))

        logo_w = int(round(rule["logo"]["width"]))
        logo_h = int(round(rule["logo"]["height"]))

        # Place near top-right but within safe area.
        logo_x = 950
        logo_y = 60
        paste_template_logo(img, x=logo_x, y=logo_y, width=logo_w, height=logo_h)

        payload = validate_layout(make_png_bytes(img))

        self.assertEqual(payload["pieceType"], "1:1")
        self.assertTrue(payload["logoDetected"])
        self.assertFalse(payload["logoWarning"])
        self.assertTrue(payload["logoInsideSafeArea"])
        self.assertTrue(payload["logoSizeValid"])
        self.assertTrue(payload["logoPositionValid"])
        self.assertFalse(payload["logoContainerDetected"])
        self.assertEqual(payload["layoutScore"], 100)
        self.assertTrue(payload["textInsideSafeArea"])

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

        paste_template_logo(img, x=logo_x, y=logo_y, width=logo_w, height=logo_h)

        payload = validate_layout(make_png_bytes(img))

        self.assertTrue(payload["logoDetected"])
        self.assertTrue(payload["logoContainerDetected"])
        self.assertTrue(payload["logoContainerSizeValid"])
        self.assertEqual(payload["layoutScore"], 100)

    def test_logo_absence_triggers_warning_but_does_not_force_score_to_zero(self) -> None:
        rule = LAYOUT_RULES["1:1"]
        canvas_w = int(rule["canvas"]["width"])
        canvas_h = int(rule["canvas"]["height"])

        img = Image.new("RGB", (canvas_w, canvas_h), (255, 255, 255))
        payload = validate_layout(make_png_bytes(img), ocr_words=[])

        self.assertEqual(payload["pieceType"], "1:1")
        self.assertFalse(payload["logoDetected"])
        self.assertTrue(payload["logoWarning"])
        self.assertEqual(payload["layoutScore"], 100)


if __name__ == "__main__":
    unittest.main()
