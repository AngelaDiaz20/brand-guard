"""Response models for technical image analysis."""

from pydantic import BaseModel, ConfigDict, Field


class MetaResponse(BaseModel):
    """Metadata extracted from an uploaded asset."""

    model_config = ConfigDict(populate_by_name=True)

    filename: str
    file_format: str = Field(alias="format")
    width: int
    height: int
    aspect_ratio: str = Field(alias="aspectRatio")
    file_size_kb: float = Field(alias="fileSizeKb")
    color_mode: str = Field(alias="colorMode")
    icc_profile: str | None = Field(alias="iccProfile")
    page_count: int | None = Field(default=None, alias="pageCount")


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


class LayoutBoundingBox(BaseModel):
    """Axis-aligned bounding box in pixels."""

    x: float
    y: float
    width: float
    height: float


class LayoutValidationResponse(BaseModel):
    """Layout compliance validation payload."""

    model_config = ConfigDict(populate_by_name=True)

    piece_type: str | None = Field(alias="pieceType")
    safe_area_bounding_box: LayoutBoundingBox | None = Field(alias="safeAreaBoundingBox")

    logo_detected: bool = Field(alias="logoDetected")
    logo_warning: bool = Field(default=False, alias="logoWarning")
    logo_bounding_box: LayoutBoundingBox | None = Field(default=None, alias="logoBoundingBox")
    logo_position: LayoutBoundingBox | None = Field(alias="logoPosition")
    logo_size_valid: bool = Field(alias="logoSizeValid")
    logo_inside_safe_area: bool = Field(alias="logoInsideSafeArea")
    logo_position_valid: bool = Field(alias="logoPositionValid")

    logo_container_detected: bool = Field(alias="logoContainerDetected")
    logo_container_bounding_box: LayoutBoundingBox | None = Field(default=None, alias="logoContainerBoundingBox")
    logo_container_position: LayoutBoundingBox | None = Field(alias="logoContainerPosition")
    logo_container_size_valid: bool = Field(alias="logoContainerSizeValid")

    text_inside_safe_area: bool = Field(default=True, alias="textInsideSafeArea")
    layout_score: int = Field(alias="layoutScore")



class AnalyzeResponse(BaseModel):
    """Top-level response payload for /analyze."""

    model_config = ConfigDict(populate_by_name=True)

    meta: MetaResponse
    technical_validation: TechnicalValidationResponse = Field(alias="technicalValidation")
    visual_analysis: VisualAnalysisResponse = Field(alias="visualAnalysis")
    ocr: OCRResponse | None = None
    layout_validation: LayoutValidationResponse | None = Field(default=None, alias="layoutValidation")
