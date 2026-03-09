"""Service responsible for extracting metadata and text from PDF files."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from typing import Any

from fastapi import HTTPException, status

from app.models.response_model import MetaResponse
from app.utils.image_utils import build_aspect_ratio

POINTS_PER_INCH = 72
PDF_DIMENSION_DPI = 150


@dataclass
class PDFAnalysisResult:
    """Normalized analysis payload for PDF files."""

    metadata: MetaResponse
    extracted_text: str
    page_count: int
    ocr_payload: dict[str, object] | None


def _extract_pdf_text(pdf: Any) -> str:
    """Extract embedded text from all PDF pages."""
    chunks: list[str] = []

    for page in pdf.pages:
        text = (page.extract_text() or "").strip()
        if text:
            chunks.append(text)

    return "\n".join(chunks).strip()


def _ocr_pdf(file_bytes: bytes) -> tuple[str, list[dict[str, object]], dict[str, float]]:
    """Run OCR over rendered PDF pages when no embedded text is available."""
    try:
        import pytesseract
        from pdf2image import convert_from_bytes
        from pytesseract import Output

        images = convert_from_bytes(file_bytes, dpi=300)
    except ModuleNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "PDF OCR dependencies are missing. Install pdf2image and pytesseract, "
                "and ensure Poppler/Tesseract binaries are available."
            ),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Unable to run PDF OCR. Ensure Poppler is installed for pdf2image "
                "and Tesseract OCR is available in the system."
            ),
        ) from exc

    texts: list[str] = []
    words: list[dict[str, object]] = []
    confidences: list[float] = []

    for image in images:
        rgb_image = image.convert("RGB")
        page_text = pytesseract.image_to_string(rgb_image).strip()
        if page_text:
            texts.append(page_text)

        data = pytesseract.image_to_data(rgb_image, output_type=Output.DICT)
        total_items = len(data.get("text", []))

        for index in range(total_items):
            raw_text = str(data["text"][index]).strip()
            raw_confidence = str(data["conf"][index]).strip()

            if not raw_text:
                continue

            try:
                confidence_value = float(raw_confidence)
            except ValueError:
                confidence_value = -1.0

            normalized_confidence = (
                max(0.0, min(confidence_value / 100.0, 1.0)) if confidence_value >= 0 else 0.0
            )

            words.append(
                {
                    "text": raw_text,
                    "box": [
                        int(data["left"][index]),
                        int(data["top"][index]),
                        int(data["width"][index]),
                        int(data["height"][index]),
                    ],
                    "confidence": normalized_confidence,
                }
            )

            if confidence_value >= 0:
                confidences.append(normalized_confidence)

    confidence_metrics = {
        "avg": float(sum(confidences) / len(confidences)) if confidences else 0.0,
        "min": float(min(confidences)) if confidences else 0.0,
    }

    return "\n".join(texts).strip(), words, confidence_metrics


def analyze_pdf_metadata(
    file_bytes: bytes,
    filename: str,
    file_size_kb: float,
) -> PDFAnalysisResult:
    """Extract normalized metadata and text from PDF bytes."""
    try:
        import pdfplumber

        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            page_count = len(pdf.pages)
            if page_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="The uploaded PDF has no pages.",
                )

            first_page = pdf.pages[0]
            width = int(round(first_page.width * PDF_DIMENSION_DPI / POINTS_PER_INCH))
            height = int(round(first_page.height * PDF_DIMENSION_DPI / POINTS_PER_INCH))
            extracted_text = _extract_pdf_text(pdf)
    except ModuleNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PDF analysis dependency is missing. Install pdfplumber.",
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to process PDF: {exc}",
        ) from exc

    ocr_payload: dict[str, object] | None = None
    if not extracted_text:
        ocr_text, words, confidence = _ocr_pdf(file_bytes)
        extracted_text = ocr_text
        ocr_payload = {
            "rawText": ocr_text,
            "correctedText": ocr_text,
            "words": words,
            "confidence": confidence,
            "score": None,
        }
    elif extracted_text:
        ocr_payload = {
            "rawText": extracted_text,
            "correctedText": extracted_text,
            "words": [],
            "confidence": {"avg": 1.0, "min": 1.0},
            "score": None,
        }

    metadata = MetaResponse(
        filename=filename,
        file_format="PDF",
        width=width,
        height=height,
        aspect_ratio=build_aspect_ratio(width, height),
        file_size_kb=file_size_kb,
        color_mode="N/A",
        icc_profile=None,
        page_count=page_count,
    )

    return PDFAnalysisResult(
        metadata=metadata,
        extracted_text=extracted_text,
        page_count=page_count,
        ocr_payload=ocr_payload,
    )
