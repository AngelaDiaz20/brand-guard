"""Service responsible for extracting dominant image colors."""

from io import BytesIO

import numpy as np
from PIL import Image

from app.models.response_model import ColorInfo


def _to_hex(rgb: tuple[int, int, int]) -> str:
    """Convert an RGB tuple to hex color notation."""
    return f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"


def extract_dominant_colors(image_bytes: bytes, num_colors: int = 5) -> list[ColorInfo]:
    """Extract top-N dominant colors from an image payload."""
    if num_colors <= 0:
        return []

    with Image.open(BytesIO(image_bytes)) as image:
        image = image.convert("RGB")
        image.thumbnail((200, 200))

        pixels = np.asarray(image, dtype=np.uint8).reshape(-1, 3)
        if pixels.size == 0:
            return []

        quantized = (pixels // 24) * 24
        unique_colors, counts = np.unique(quantized, axis=0, return_counts=True)

        sort_indices = np.argsort(counts)[::-1]
        top_indices = sort_indices[:num_colors]
        total_pixels = int(counts.sum())

        dominant_colors: list[ColorInfo] = []
        for index in top_indices:
            color = tuple(int(channel) for channel in unique_colors[index])
            count = int(counts[index])
            dominant_colors.append(
                ColorInfo(
                    hex=_to_hex(color),
                    rgb=color,
                    percentage=round((count / total_pixels) * 100, 2),
                )
            )

        return dominant_colors
