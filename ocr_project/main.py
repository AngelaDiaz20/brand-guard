"""Example entry point for the OCR project."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ocr.pipeline import OCRPipeline


def parse_args() -> argparse.Namespace:
    project_root = Path(__file__).resolve().parent
    default_image = project_root / "examples" / "test_image.jpg"

    parser = argparse.ArgumentParser(description="Run OCR on a Peruvian advertising image.")
    parser.add_argument(
        "--image",
        type=Path,
        default=default_image,
        help="Path to the image that will be analyzed.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pipeline = OCRPipeline()
    try:
        result = pipeline.run(args.image)
    except RuntimeError as exc:
        result = {"error": str(exc)}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
