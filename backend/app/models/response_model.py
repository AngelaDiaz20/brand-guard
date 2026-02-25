"""Response models for technical image analysis."""

from pydantic import BaseModel, ConfigDict, Field


class MetaResponse(BaseModel):
    """Metadata extracted from an uploaded image."""

    model_config = ConfigDict(populate_by_name=True)

    filename: str
    file_format: str = Field(alias="format")
    width: int
    height: int
    aspect_ratio: str = Field(alias="aspectRatio")
    file_size_kb: float = Field(alias="fileSizeKb")
    color_mode: str = Field(alias="colorMode")
    icc_profile: str | None = Field(alias="iccProfile")


class TechnicalValidationResponse(BaseModel):
    """Validation result against technical requirements."""

    model_config = ConfigDict(populate_by_name=True)

    format_allowed: bool = Field(alias="formatAllowed")
    dimensions_valid: bool = Field(alias="dimensionsValid")
    file_size_valid: bool = Field(alias="fileSizeValid")


class AnalyzeResponse(BaseModel):
    """Top-level response payload for /analyze."""

    model_config = ConfigDict(populate_by_name=True)

    meta: MetaResponse
    technical_validation: TechnicalValidationResponse = Field(alias="technicalValidation")
