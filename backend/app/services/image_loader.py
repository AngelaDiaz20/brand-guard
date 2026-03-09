"""File loading and early validation helpers."""

from io import BytesIO
from pathlib import Path
from typing import Literal

from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
ALLOWED_IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png"}
PDF_EXTENSION = ".pdf"
PDF_CONTENT_TYPE = "application/pdf"
BYTES_IN_KILOBYTE = 1024


def _detect_file_type(
    file: UploadFile,
    file_bytes: bytes,
) -> Literal["image", "pdf"]:
    """Detect whether payload is an image or PDF using bytes + upload metadata."""
    content_type = (file.content_type or "").lower()
    extension = Path(file.filename or "").suffix.lower()

    if file_bytes.startswith(b"%PDF-"):
        return "pdf"

    try:
        with Image.open(BytesIO(file_bytes)) as image:
            if (image.format or "").upper() in {"JPEG", "JPG", "PNG"}:
                return "image"
    except (UnidentifiedImageError, OSError):
        pass

    has_valid_image_extension = extension in ALLOWED_IMAGE_EXTENSIONS
    has_valid_image_content_type = content_type in ALLOWED_IMAGE_CONTENT_TYPES
    if has_valid_image_extension or has_valid_image_content_type:
        return "image"

    if extension == PDF_EXTENSION or content_type == PDF_CONTENT_TYPE:
        return "pdf"

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Only JPG, JPEG, PNG and PDF files are accepted.",
    )


async def load_upload_bytes(file: UploadFile) -> tuple[bytes, float, Literal["image", "pdf"]]:
    """Read uploaded file bytes and return payload + size in KB."""
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    file_type = _detect_file_type(file=file, file_bytes=file_bytes)
    file_size_kb = round(len(file_bytes) / BYTES_IN_KILOBYTE, 2)
    return file_bytes, file_size_kb, file_type
