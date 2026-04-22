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

    # Optional post-processing (blocks/lines) for supported formats.
    lines: list[dict] | None = None
    micro_blocks: list[dict] | None = Field(default=None, alias="microBlocks")
    blocks: list[dict] | None = None

    # Optional: región-aware OCR (debug/trazabilidad). Siempre opcional/backward compatible.
    regions: list[dict] | None = None
    regional_ocr: list[dict] | None = Field(default=None, alias="regionalOcr")
    incidental_regional_ocr: list[dict] | None = Field(default=None, alias="incidentalRegionalOcr")
    regional_layouts: list[dict] | None = Field(default=None, alias="regionalLayouts")
    yolo_detections: list[dict] | None = Field(default=None, alias="yoloDetections")
    global_lines: list[dict] | None = Field(default=None, alias="globalLines")
    global_micro_blocks: list[dict] | None = Field(default=None, alias="globalMicroBlocks")
    global_blocks: list[dict] | None = Field(default=None, alias="globalBlocks")


class StructuredFieldValue(BaseModel):
    """Single extracted structured field."""

    model_config = ConfigDict(populate_by_name=True)

    value: str | None = None
    source_block_id: str | None = Field(default=None, alias="sourceBlockId")
    confidence: float = 0.0
    status: str = "not_detected"
    message: str | None = None

    # Optional traceability (region-aware extraction). Always optional/backward compatible.
    source_region_id: str | None = Field(default=None, alias="sourceRegionId")
    source_region_class_name: str | None = Field(default=None, alias="sourceRegionClassName")
    source_region_bbox: list[int] | None = Field(default=None, alias="sourceRegionBbox")
    source_strategy: str | None = Field(default=None, alias="sourceStrategy")


class PriceBlockAnalysisResponse(BaseModel):
    """Visual analysis of the main price block."""

    model_config = ConfigDict(populate_by_name=True)

    main_block_detected: bool = Field(alias="mainBlockDetected")
    main_block_bbox: list[int] | None = Field(default=None, alias="mainBlockBbox")
    main_block_color: str = Field(alias="mainBlockColor")
    main_block_color_confidence: float = Field(alias="mainBlockColorConfidence")
    dominant_rgb: list[int] | None = Field(default=None, alias="dominantRgb")
    classification_strategy: str | None = Field(default=None, alias="classificationStrategy")
    messages: list[str] = Field(default_factory=list)


class ExcelFieldComparison(BaseModel):
    """Per-field Excel comparison result."""

    model_config = ConfigDict(populate_by_name=True)

    expected: str | None = None
    detected: str | None = None
    status: str
    message: str | None = None


class ExcelValidationResponse(BaseModel):
    """Optional Excel validation result."""

    model_config = ConfigDict(populate_by_name=True)

    enabled: bool
    executed: bool
    applies_to_format: bool | None = Field(default=None, alias="appliesToFormat")
    matched_row_index: int | None = Field(default=None, alias="matchedRowIndex")
    match_strategy: str | None = Field(default=None, alias="matchStrategy")
    overall_status: str = Field(alias="overallStatus")
    fields: dict[str, ExcelFieldComparison] = Field(default_factory=dict)
    messages: list[str] = Field(default_factory=list)


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

    # Optional, format-gated layer (must not break existing consumers).
    structured_fields: dict[str, StructuredFieldValue] | None = Field(default=None, alias="structuredFields")
    price_block_analysis: PriceBlockAnalysisResponse | None = Field(default=None, alias="priceBlockAnalysis")
    excel_validation: ExcelValidationResponse | None = Field(default=None, alias="excelValidation")
