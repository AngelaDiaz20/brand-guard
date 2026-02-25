"""File loading and early validation helpers."""

from pathlib import Path

from fastapi import HTTPException, UploadFile, status

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}
BYTES_IN_KILOBYTE = 1024


def _is_supported_file(file: UploadFile) -> bool:
    """Check extension and MIME type to allow JPG/PNG uploads only."""
    extension = Path(file.filename or "").suffix.lower()
    has_valid_extension = extension in ALLOWED_EXTENSIONS
    has_valid_content_type = (file.content_type or "").lower() in ALLOWED_CONTENT_TYPES
    return has_valid_extension or has_valid_content_type


async def load_upload_bytes(file: UploadFile) -> tuple[bytes, float]:
    """Read uploaded file bytes and return payload + size in KB."""
    if not _is_supported_file(file):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPG and PNG files are accepted.",
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    file_size_kb = round(len(file_bytes) / BYTES_IN_KILOBYTE, 2)
    return file_bytes, file_size_kb
