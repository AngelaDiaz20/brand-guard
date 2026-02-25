"""Service responsible for extracting metadata from images."""

from io import BytesIO

from fastapi import HTTPException, status
from PIL import Image, ImageCms, UnidentifiedImageError

from app.models.response_model import MetaResponse
from app.utils.image_utils import build_aspect_ratio, normalize_image_format


def extract_icc_profile_exact_label(image_info: dict) -> str | None:
    """
    Return the ICC profile name/description as shown by systems like macOS Finder/Preview,
    e.g. 'sRGB IEC61966-2.1', 'Display P3', 'Adobe RGB (1998)'.

    If the image has no embedded ICC profile, returns None.
    """
    icc_bytes = image_info.get("icc_profile")
    if not icc_bytes:
        return None

    try:
        profile = ImageCms.ImageCmsProfile(BytesIO(icc_bytes))

        # Usually matches Finder/Preview "Color profile"
        desc = ImageCms.getProfileDescription(profile)
        if desc and desc.strip():
            return desc.strip()

        # Fallback
        name = ImageCms.getProfileName(profile)
        if name and name.strip():
            return name.strip()

        return "ICC profile"
    except Exception:
        # If ICC data exists but can't be parsed, don't fail the whole request
        return "ICC profile (unreadable)"


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
                icc_profile=extract_icc_profile_exact_label(image.info),
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