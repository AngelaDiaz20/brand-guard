"""Service to load and validate Sodimac technical guidelines."""

import json
from pathlib import Path

from fastapi import HTTPException, status
from pydantic import BaseModel, ValidationError

from app.models.response_model import MetaResponse, TechnicalValidationResponse
from app.utils.image_utils import normalize_image_format

BYTES_IN_MEGABYTE = 1024 * 1024


class TechnicalRequirements(BaseModel):
    """Technical requirements read from the JSON configuration."""

    min_width_px: int
    min_height_px: int
    allowed_formats: list[str]
    max_file_size_mb: float
    min_pages: int | None = None
    max_pages: int | None = None
    required_text: str | None = None


class SodimacGuidelines(BaseModel):
    """Root schema for sodimac_guidelines.json."""

    brand: str
    technical_requirements: TechnicalRequirements


def load_guidelines(config_path: Path) -> SodimacGuidelines:
    """Load and validate guideline configuration from JSON file."""
    if not config_path.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Configuration file not found: {config_path}",
        )

    try:
        with config_path.open("r", encoding="utf-8") as config_file:
            raw_config = json.load(config_file)
        return SodimacGuidelines.model_validate(raw_config)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Guideline configuration is not valid JSON.",
        ) from exc
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Guideline configuration is invalid: {exc.errors()}",
        ) from exc


def validate_technical_requirements(
    metadata: MetaResponse,
    guidelines: SodimacGuidelines,
    page_count: int | None = None,
    extracted_text: str | None = None,
) -> TechnicalValidationResponse:
    """Validate metadata against JSON-driven technical requirements."""
    requirements = guidelines.technical_requirements
    allowed_formats = {normalize_image_format(fmt) for fmt in requirements.allowed_formats}
    image_size_bytes = metadata.file_size_kb * 1024
    max_size_bytes = requirements.max_file_size_mb * BYTES_IN_MEGABYTE

    normalized_format = normalize_image_format(metadata.file_format)
    format_allowed = normalized_format in allowed_formats
    dimensions_valid = (
        metadata.width >= requirements.min_width_px
        and metadata.height >= requirements.min_height_px
    )

    if normalized_format == "PDF":
        pages_valid = True
        if requirements.min_pages is not None:
            pages_valid = pages_valid and page_count is not None and page_count >= requirements.min_pages
        if requirements.max_pages is not None:
            pages_valid = pages_valid and page_count is not None and page_count <= requirements.max_pages

        required_text_valid = True
        if requirements.required_text:
            required_text_valid = requirements.required_text.lower() in (extracted_text or "").lower()

        dimensions_valid = dimensions_valid and pages_valid and required_text_valid

    file_size_valid = image_size_bytes <= max_size_bytes

    return TechnicalValidationResponse(
        format_allowed=format_allowed,
        dimensions_valid=dimensions_valid,
        file_size_valid=file_size_valid,
    )
