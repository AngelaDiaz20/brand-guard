"""Orchestration service for upload analysis."""

from pathlib import Path

from fastapi import UploadFile

from app.models.response_model import AnalyzeResponse, LayoutValidationResponse, OCRResponse, VisualAnalysisResponse
from app.services.color_analysis_service import extract_dominant_colors
from app.services.guideline_validator import load_guidelines, validate_technical_requirements
from app.services.image_loader import load_upload_bytes
from app.services.layout_validation_service import validate_layout
from app.services.metadata_service import extract_image_metadata
from app.services.ocr_service import run_ocr
from app.services.pdf_analyzer import analyze_pdf_metadata


async def analyze_upload(file: UploadFile, guidelines_path: Path) -> AnalyzeResponse:
    """Analyze uploaded image/PDF and return a unified response payload."""
    file_bytes, file_size_kb, file_type = await load_upload_bytes(file)
    guidelines = load_guidelines(guidelines_path)

    if file_type == "image":
        metadata = extract_image_metadata(
            image_bytes=file_bytes,
            filename=file.filename or "unknown",
            file_size_kb=file_size_kb,
        )
        ocr_result = run_ocr(file_bytes)
        validation = validate_technical_requirements(metadata, guidelines)
        layout_validation = validate_layout(file_bytes)
        return AnalyzeResponse(
            meta=metadata,
            technical_validation=validation,
            visual_analysis=VisualAnalysisResponse(
                dominant_colors=extract_dominant_colors(file_bytes),
            ),
            ocr=OCRResponse(**ocr_result) if ocr_result else None,
            layout_validation=LayoutValidationResponse(**layout_validation),
        )

    pdf_result = analyze_pdf_metadata(
        file_bytes=file_bytes,
        filename=file.filename or "unknown",
        file_size_kb=file_size_kb,
    )
    validation = validate_technical_requirements(
        metadata=pdf_result.metadata,
        guidelines=guidelines,
        page_count=pdf_result.page_count,
        extracted_text=pdf_result.extracted_text,
    )

    return AnalyzeResponse(
        meta=pdf_result.metadata,
        technical_validation=validation,
        visual_analysis=VisualAnalysisResponse(dominant_colors=[]),
        ocr=OCRResponse(**pdf_result.ocr_payload) if pdf_result.ocr_payload else None,
    )
