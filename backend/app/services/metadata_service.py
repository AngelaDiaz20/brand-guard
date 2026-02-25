"""Service responsible for extracting metadata from images."""

from io import BytesIO

from fastapi import HTTPException, status
from PIL import Image, UnidentifiedImageError

from app.models.response_model import MetaResponse
from app.utils.image_utils import (
    build_aspect_ratio,
    extract_icc_profile_label,
    normalize_image_format,
)


def extract_image_metadata(image_bytes: bytes, filename: str, file_size_kb: float) -> MetaResponse:
    """Extract required metadata fields from an image payload."""
    try:
        with Image.open(BytesIO(image_bytes)) as image:
            image_format = normalize_image_format(image.format)
            width, height = image.size
            return MetaResponse(
                filename=filename,
                file_format=image_format,
                width=width,
                height=height,
                aspect_ratio=build_aspect_ratio(width, height),
                file_size_kb=file_size_kb,
                color_mode=image.mode,
                icc_profile=extract_icc_profile_label(image.info),
            )
    except UnidentifiedImageError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is not a valid image.",
        ) from exc
    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to process image: {exc}",
        ) from exc
