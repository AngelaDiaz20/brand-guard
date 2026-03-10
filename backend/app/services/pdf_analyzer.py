"""Service responsible for extracting metadata and text from PDF files."""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from io import BytesIO
from typing import Any

from fastapi import HTTPException, status

from app.models.response_model import MetaResponse
from app.services.ocr_service import (
    build_ocr_payload,
    compute_confidence_metrics,
    enhance_image_for_ocr,
    normalize_image_array,
    run_ocr_on_image_array,
)
from app.utils.image_utils import build_aspect_ratio

POINTS_PER_INCH = 72
PDF_DIMENSION_DPI = 150
PDF_OCR_DPI = 300
PDF_TEXT_LENGTH_THRESHOLD = 40
PDF_MAX_OCR_WORKERS = 4


@dataclass
class PDFAnalysisResult:
    """Normalized analysis payload for PDF files."""

    metadata: MetaResponse
    extracted_text: str
    page_count: int
    ocr_payload: dict[str, object] | None


@dataclass
class PDFPageExtraction:
    """Embedded text extracted from a single PDF page."""

    page_index: int
    text: str
    words: list[dict[str, object]]


@dataclass
class PDFPageOCRResult:
    """OCR result extracted from a single rendered PDF page."""

    page_index: int
    payload: dict[str, Any]
    engine: str


def _normalize_pdf_word(raw_word: dict[str, Any]) -> dict[str, object] | None:
    text = str(raw_word.get("text", "")).strip()
    if not text:
        return None

    scale = PDF_OCR_DPI / POINTS_PER_INCH
    x0 = float(raw_word.get("x0", 0.0))
    x1 = float(raw_word.get("x1", x0))
    top = float(raw_word.get("top", 0.0))
    bottom = float(raw_word.get("bottom", top))

    return {
        "text": text,
        "box": [
            int(round(x0 * scale)),
            int(round(top * scale)),
            int(round(max(0.0, x1 - x0) * scale)),
            int(round(max(0.0, bottom - top) * scale)),
        ],
        "confidence": 1.0,
    }


def _extract_pdf_pages(pdf: Any) -> list[PDFPageExtraction]:
    """Extract embedded text and word coordinates from all PDF pages."""
    pages: list[PDFPageExtraction] = []

    for page_index, page in enumerate(pdf.pages):
        try:
            text = (page.extract_text() or "").strip()
        except Exception:
            text = ""

        try:
            raw_words = page.extract_words() or []
        except Exception:
            raw_words = []

        normalized_words = [
            normalized
            for normalized in (_normalize_pdf_word(word) for word in raw_words)
            if normalized is not None
        ]
        pages.append(
            PDFPageExtraction(
                page_index=page_index,
                text=text,
                words=normalized_words,
            )
        )

    return pages


def _should_run_pdf_ocr(text: str) -> bool:
    return len(text.strip()) < PDF_TEXT_LENGTH_THRESHOLD


def _render_pdf_pages(file_bytes: bytes) -> list[Any]:
    try:
        from pdf2image import convert_from_bytes

        return convert_from_bytes(file_bytes, dpi=PDF_OCR_DPI)
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


def _ocr_page_with_tesseract(image_array: Any) -> dict[str, Any]:
    import pytesseract
    from pytesseract import Output

    page_text = pytesseract.image_to_string(image_array).strip()
    data = pytesseract.image_to_data(image_array, output_type=Output.DICT)

    words: list[dict[str, object]] = []
    for index in range(len(data.get("text", []))):
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

    return build_ocr_payload(
        raw_text=page_text,
        words=words,
        confidence=compute_confidence_metrics(words),
    )


def _ocr_page(page_index: int, rendered_page: Any) -> PDFPageOCRResult:
    image_array = normalize_image_array(rendered_page)

    try:
        payload = run_ocr_on_image_array(image_array)
        return PDFPageOCRResult(page_index=page_index, payload=payload, engine="paddleocr")
    except Exception:
        try:
            fallback_image = enhance_image_for_ocr(image_array)
            payload = _ocr_page_with_tesseract(fallback_image)
            return PDFPageOCRResult(page_index=page_index, payload=payload, engine="tesseract")
        except ModuleNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    "PDF OCR dependencies are missing. Install pdf2image and pytesseract, "
                    "and ensure Poppler/Tesseract binaries are available."
                ),
            ) from exc
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unable to OCR PDF page {page_index + 1}: {exc}",
            ) from exc


def _run_parallel_pdf_ocr(
    file_bytes: bytes,
    page_indexes: list[int],
) -> dict[int, PDFPageOCRResult]:
    if not page_indexes:
        return {}

    rendered_pages = _render_pdf_pages(file_bytes)
    worker_count = max(1, min(len(page_indexes), PDF_MAX_OCR_WORKERS, os.cpu_count() or 1))
    page_map = {page_index: rendered_pages[page_index] for page_index in page_indexes}

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = {
            executor.submit(_ocr_page, page_index, rendered_page): page_index
            for page_index, rendered_page in page_map.items()
        }
        results = [future.result() for future in futures]

    return {result.page_index: result for result in sorted(results, key=lambda item: item.page_index)}


def _merge_page_text(primary_text: str, secondary_text: str) -> str:
    primary = primary_text.strip()
    secondary = secondary_text.strip()

    if not primary:
        return secondary
    if not secondary:
        return primary

    normalized_primary = " ".join(primary.split()).lower()
    normalized_secondary = " ".join(secondary.split()).lower()

    if normalized_primary == normalized_secondary:
        return primary if len(primary) >= len(secondary) else secondary
    if normalized_primary in normalized_secondary:
        return secondary
    if normalized_secondary in normalized_primary:
        return primary

    return f"{primary}\n{secondary}"


def _select_page_payload(
    embedded_page: PDFPageExtraction,
    ocr_result: PDFPageOCRResult | None,
) -> dict[str, Any]:
    embedded_confidence = (
        compute_confidence_metrics(embedded_page.words)
        if embedded_page.words
        else {"avg": 1.0, "min": 1.0}
        if embedded_page.text
        else {"avg": 0.0, "min": 0.0}
    )
    embedded_payload = build_ocr_payload(
        raw_text=embedded_page.text,
        words=embedded_page.words,
        confidence=embedded_confidence,
    )

    if ocr_result is None or not ocr_result.payload.get("rawText"):
        return embedded_payload
    if not embedded_page.text:
        return ocr_result.payload

    embedded_raw = str(embedded_payload["rawText"]).strip()
    ocr_raw = str(ocr_result.payload.get("rawText", "")).strip()
    if not ocr_raw:
        return embedded_payload

    embedded_score = float(embedded_payload.get("score") or 0.0)
    ocr_score = float(ocr_result.payload.get("score") or 0.0)

    if _should_run_pdf_ocr(embedded_raw):
        if len(ocr_raw) > len(embedded_raw) or ocr_score >= embedded_score:
            return ocr_result.payload
        merged_text = _merge_page_text(embedded_raw, ocr_raw)
        selected_words = embedded_page.words or ocr_result.payload.get("words", [])
        selected_confidence = (
            compute_confidence_metrics(selected_words)
            if selected_words
            else embedded_confidence if embedded_raw else ocr_result.payload["confidence"]
        )
        return build_ocr_payload(
            raw_text=merged_text,
            words=selected_words,
            confidence=selected_confidence,
        )

    return embedded_payload if embedded_score >= ocr_score else ocr_result.payload

def _build_pdf_ocr_payload(
    file_bytes: bytes,
    extracted_pages: list[PDFPageExtraction],
) -> tuple[str, dict[str, object] | None]:
    ocr_targets = [page.page_index for page in extracted_pages if _should_run_pdf_ocr(page.text)]
    has_embedded_fallback = any(page.text.strip() or page.words for page in extracted_pages)
    try:
        ocr_results = _run_parallel_pdf_ocr(file_bytes, ocr_targets) if ocr_targets else {}
    except HTTPException:
        if not has_embedded_fallback:
            raise
        ocr_results = {}

    selected_payloads = [_select_page_payload(page, ocr_results.get(page.page_index)) for page in extracted_pages]
    selected_texts = [str(payload["rawText"]).strip() for payload in selected_payloads if payload["rawText"]]
    selected_words = [
        word
        for payload in selected_payloads
        for word in payload.get("words", [])
        if isinstance(word, dict)
    ]

    extracted_text = "\n".join(selected_texts).strip()
    if not extracted_text and not selected_words:
        return "", None

    confidence = compute_confidence_metrics(selected_words)
    if not selected_words and extracted_text:
        confidence = {"avg": 1.0, "min": 1.0}

    payload = build_ocr_payload(
        raw_text=extracted_text,
        words=selected_words,
        confidence=confidence,
    )
    return extracted_text, payload


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
            extracted_pages = _extract_pdf_pages(pdf)
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

    extracted_text, ocr_payload = _build_pdf_ocr_payload(
        file_bytes=file_bytes,
        extracted_pages=extracted_pages,
    )

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
