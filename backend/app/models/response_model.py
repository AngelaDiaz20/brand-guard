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


class ColorInfo(BaseModel):
    """Dominant color information."""

    hex: str
    rgb: tuple[int, int, int]
    percentage: float


class VisualAnalysisResponse(BaseModel):
    """Visual analysis payload."""

    model_config = ConfigDict(populate_by_name=True)

    dominant_colors: list[ColorInfo] = Field(alias="dominantColors")


class OCRWord(BaseModel):
    """Detected OCR word."""

    text: str
    box: list[int]
    confidence: float


class OCRConfidence(BaseModel):
    """Confidence metrics for OCR."""

    avg: float
    min: float


class OCRResponse(BaseModel):
    """OCR payload with raw + corrected versions."""

    model_config = ConfigDict(populate_by_name=True)

    raw_text: str = Field(alias="rawText")
    corrected_text: str = Field(alias="correctedText")
    words: list[OCRWord]
    confidence: OCRConfidence

    # 🔥 Preparado para futuro score ML
    score: float | None = None



class AnalyzeResponse(BaseModel):
    """Top-level response payload for /analyze."""

    model_config = ConfigDict(populate_by_name=True)

    meta: MetaResponse
    technical_validation: TechnicalValidationResponse = Field(alias="technicalValidation")
    visual_analysis: VisualAnalysisResponse = Field(alias="visualAnalysis")
    ocr: OCRResponse | None = None
