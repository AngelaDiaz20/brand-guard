"""Orchestration service for upload analysis."""

from __future__ import annotations

import json
import logging
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

from app.services.layout_block_parser import build_ocr_blocks
from app.services.region_proposal_service import propose_regions
from app.services.regional_ocr_service import run_regional_ocr
from app.services.hybrid_layout_parser import build_region_aware_layout
from app.services.yolo_region_detector_service import detect_regions_with_yolo
from app.services.price_block_visual_classifier import as_dict as price_block_as_dict, classify_main_price_block_color
from app.services.structured_piece_extraction_service import (
    assign_prices_with_visual_rules,
    extract_structured_fields_from_blocks,
)
from app.services.excel_piece_validation_service import validate_against_excel

logger = logging.getLogger(__name__)


def _repo_root() -> Path:
    # backend/app/services/analysis_service.py -> repo root
    return Path(__file__).resolve().parents[3]


def _load_excel_validation_config() -> dict:
    path = _repo_root() / "backend" / "app" / "config" / "excel_validation_config.json"
    try:
        with path.open("r", encoding="utf-8") as fp:
            return json.load(fp) or {}
    except Exception:
        return {}


async def _read_optional_excel_bytes(excel_file: UploadFile | None) -> tuple[bytes | None, str | None]:
    if excel_file is None:
        return None, None
    try:
        data = await excel_file.read()
        filename = excel_file.filename or None
        if not data:
            return None, filename
        return data, filename
    except Exception:
        return None, excel_file.filename or None


def _normalize_piece_format(value: str | None) -> str | None:
    if value is None:
        return None
    v = str(value).strip().lower()
    return v or None


def _effective_piece_format(piece_format: str | None, layout_validation: dict | None, config: dict) -> str | None:
    normalized = _normalize_piece_format(piece_format)
    if normalized:
        return normalized

    aliases = (config or {}).get("layout_piece_type_aliases") or {}
    piece_type = None
    if isinstance(layout_validation, dict):
        piece_type = layout_validation.get("pieceType")
    if isinstance(piece_type, str) and piece_type in aliases:
        return _normalize_piece_format(str(aliases.get(piece_type)))
    return None


def _is_supported_format(effective_format: str | None, config: dict) -> bool:
    supported = (config or {}).get("supported_piece_formats") or []
    supported_set = {str(x).strip().lower() for x in supported if str(x).strip()}
    return bool(effective_format and effective_format in supported_set)


def _try_optional_structured_layer(
    *,
    image_bytes: bytes,
    ocr_result: dict | None,
    layout_validation: dict | None,
    excel_bytes: bytes | None,
    excel_filename: str | None,
    piece_format: str | None,
    debug: bool = False,
) -> dict[str, object]:
    """
    Returns a dict with optional keys:
    - ocr (patched with blocks/lines)
    - structured_fields
    - price_block_analysis
    - excel_validation
    """
    config = _load_excel_validation_config()
    effective_format = _effective_piece_format(piece_format, layout_validation, config)
    supported = _is_supported_format(effective_format, config)
    regional_enabled = bool((config or {}).get("enable_regional_ocr", True))
    regional_cfg = (config or {}).get("regional_ocr") or {}
    max_regions_to_ocr = int(regional_cfg.get("max_regions", 8) or 8)
    yolo_cfg = (config or {}).get("yolo") or {}
    yolo_enabled = bool(yolo_cfg.get("enabled", False))
    yolo_model_path = yolo_cfg.get("model_path") if isinstance(yolo_cfg.get("model_path"), str) else None
    yolo_min_regions = int(yolo_cfg.get("min_regions_for_use", 2) or 2)
    yolo_conf = float(yolo_cfg.get("conf", 0.25) or 0.25)
    yolo_iou = float(yolo_cfg.get("iou", 0.55) or 0.55)
    yolo_max_det = int(yolo_cfg.get("max_det", 30) or 30)
    allow_classes = yolo_cfg.get("allow_ocr_classes") or []
    allow_set = {str(x).strip() for x in allow_classes if str(x).strip()}
    exclude_classes = yolo_cfg.get("exclude_ocr_classes") or ["product_photo_area"]
    exclude_set = {str(x).strip() for x in exclude_classes if str(x).strip()}

    words = None
    if isinstance(ocr_result, dict):
        words = ocr_result.get("words")

    blocks_payload: dict[str, object] | None = None
    try:
        blocks_payload = build_ocr_blocks(words if isinstance(words, list) else None)
    except Exception:
        logger.exception("No se pudo reconstruir líneas/bloques desde OCR.")
        blocks_payload = None

    patched_ocr = None
    if isinstance(ocr_result, dict) and blocks_payload:
        patched_ocr = dict(ocr_result)
        patched_ocr["lines"] = blocks_payload.get("lines")
        patched_ocr["microBlocks"] = blocks_payload.get("microBlocks")
        patched_ocr["blocks"] = blocks_payload.get("blocks")

    def _center_in_bbox_xywh(box: list[int], area: list[int]) -> bool:
        x, y, bw, bh = [float(v) for v in box]
        cx = x + bw / 2.0
        cy = y + bh / 2.0
        ax, ay, aw, ah = [float(v) for v in area]
        return ax <= cx <= (ax + aw) and ay <= cy <= (ay + ah)

    excluded_areas: list[list[int]] = []
    keep_areas: list[list[int]] = []

    # Optional: region-aware OCR. This is *additive* and never replaces OCR global unless it succeeds end-to-end.
    # Only enabled for supported formats to avoid impacting unrelated flows.
    if supported and regional_enabled and isinstance(patched_ocr, dict):
        try:
            yolo_detections: list[dict] = []
            if yolo_enabled or debug:
                yolo_detections = detect_regions_with_yolo(
                    image_bytes=image_bytes,
                    model_path=yolo_model_path,
                    conf=yolo_conf,
                    iou=yolo_iou,
                    max_det=yolo_max_det,
                )

            # Exclude areas (e.g., product photo) to avoid incidental text contamination.
            excluded_areas = [
                d.get("bbox") for d in yolo_detections if str(d.get("className") or "").strip() in exclude_set
            ]
            excluded_areas = [b for b in excluded_areas if isinstance(b, list) and len(b) == 4]

            # Keep areas: semantic commercial regions that may overlap the photo area (e.g., price tag over the photo).
            keep_areas = [
                d.get("bbox")
                for d in yolo_detections
                if isinstance(d, dict)
                and isinstance(d.get("bbox"), list)
                and len(d.get("bbox")) == 4
                and str(d.get("className") or "").strip()
                and str(d.get("className") or "").strip() not in exclude_set
                and (not allow_set or str(d.get("className") or "").strip() in allow_set)
            ]
            keep_areas = [b for b in keep_areas if isinstance(b, list) and len(b) == 4]

            # Regions to OCR: prefer YOLO detections when they exist and meet minimum coverage.
            regions_for_ocr: list[dict] = []
            if yolo_detections:
                for det in yolo_detections:
                    cls = str(det.get("className") or "").strip()
                    if not cls:
                        continue
                    if cls in exclude_set:
                        continue
                    if allow_set and cls not in allow_set:
                        continue
                    # Normalize to common region schema used by regional OCR.
                    regions_for_ocr.append(
                        {
                            "id": det.get("id"),
                            "kind": "semantic",
                            "className": cls,
                            "bbox": det.get("bbox"),
                            "confidence": det.get("confidence"),
                            "source": "yolo",
                        }
                    )

            if len(regions_for_ocr) < yolo_min_regions:
                regions_for_ocr = propose_regions(image_bytes=image_bytes, ocr_words=words if isinstance(words, list) else None)

            # Debug-only: run OCR inside excluded areas (e.g., photo) to surface incidental text without contaminating extraction.
            if debug and yolo_detections and excluded_areas:
                incidental_regions: list[dict] = []
                for det in yolo_detections:
                    cls = str(det.get("className") or "").strip()
                    bb = det.get("bbox")
                    if cls in exclude_set and isinstance(bb, list) and len(bb) == 4:
                        incidental_regions.append(
                            {
                                "id": f"incidental::{det.get('id')}",
                                "kind": "incidental",
                                "className": cls,
                                "bbox": bb,
                                "confidence": det.get("confidence"),
                                "source": "yolo",
                            }
                        )
                if incidental_regions:
                    try:
                        incidental = run_regional_ocr(
                            image_bytes=image_bytes,
                            regions=incidental_regions,
                            exclude_areas=None,
                            keep_areas=None,
                            max_regions_to_ocr=min(3, max_regions_to_ocr),
                        )
                        incidental_ocr = incidental.get("regionalOcr") if isinstance(incidental, dict) else None
                        if isinstance(incidental_ocr, list) and incidental_ocr:
                            patched_ocr["incidentalRegionalOcr"] = incidental_ocr
                    except Exception:
                        logger.exception("Falló OCR incidental dentro de product_photo_area (debug).")

            # If YOLO provided a product photo region, also create a "masked global" view by filtering out words
            # whose centers fall inside the excluded area (unless they also fall in a keep area).
            if excluded_areas and isinstance(words, list):
                filtered_words: list[dict] = []
                for w in words:
                    if not isinstance(w, dict):
                        continue
                    box = w.get("box")
                    if not (isinstance(box, list) and len(box) == 4):
                        continue
                    box_i = [int(round(float(v))) for v in box]
                    in_excluded = any(_center_in_bbox_xywh(box_i, ex) for ex in excluded_areas)
                    in_keep = bool(keep_areas) and any(_center_in_bbox_xywh(box_i, ka) for ka in keep_areas)
                    if in_excluded and not in_keep:
                        continue
                    filtered_words.append(w)

                try:
                    masked_payload = build_ocr_blocks(filtered_words)
                except Exception:
                    masked_payload = None

                if isinstance(masked_payload, dict) and masked_payload.get("blocks"):
                    patched_ocr["globalLines"] = patched_ocr.get("lines")
                    patched_ocr["globalMicroBlocks"] = patched_ocr.get("microBlocks")
                    patched_ocr["globalBlocks"] = patched_ocr.get("blocks")

                    patched_ocr["yoloDetections"] = yolo_detections
                    patched_ocr["regions"] = regions_for_ocr
                    patched_ocr["lines"] = masked_payload.get("lines")
                    patched_ocr["microBlocks"] = masked_payload.get("microBlocks")
                    patched_ocr["blocks"] = masked_payload.get("blocks")

                    blocks_payload = {
                        "lines": patched_ocr.get("lines"),
                        "microBlocks": patched_ocr.get("microBlocks"),
                        "blocks": patched_ocr.get("blocks"),
                    }

            regional = run_regional_ocr(
                image_bytes=image_bytes,
                regions=regions_for_ocr,
                exclude_areas=excluded_areas,
                keep_areas=keep_areas,
                max_regions_to_ocr=max_regions_to_ocr,
            )
            regional_ocr = regional.get("regionalOcr") if isinstance(regional, dict) else None
            hybrid_layout = build_region_aware_layout(regional_ocr=regional_ocr if isinstance(regional_ocr, list) else None)

            if isinstance(hybrid_layout, dict) and hybrid_layout.get("blocks"):
                # Preserve global layout for debugging, then override the primary view with region-aware layout.
                patched_ocr["globalLines"] = patched_ocr.get("globalLines") or patched_ocr.get("lines")
                patched_ocr["globalMicroBlocks"] = patched_ocr.get("globalMicroBlocks") or patched_ocr.get("microBlocks")
                patched_ocr["globalBlocks"] = patched_ocr.get("globalBlocks") or patched_ocr.get("blocks")

                patched_ocr["yoloDetections"] = yolo_detections
                patched_ocr["regions"] = regions_for_ocr
                patched_ocr["regionalOcr"] = regional_ocr
                patched_ocr["regionalLayouts"] = hybrid_layout.get("regionalLayouts")

                patched_ocr["lines"] = hybrid_layout.get("lines")
                patched_ocr["microBlocks"] = hybrid_layout.get("microBlocks")
                patched_ocr["blocks"] = hybrid_layout.get("blocks")

                # Use hybrid blocks for downstream structured extraction.
                blocks_payload = {
                    "lines": patched_ocr.get("lines"),
                    "microBlocks": patched_ocr.get("microBlocks"),
                    "blocks": patched_ocr.get("blocks"),
                }

            # Debug: always surface detections/regions even if we didn't override blocks.
            if debug and yolo_detections:
                patched_ocr.setdefault("yoloDetections", yolo_detections)
                patched_ocr.setdefault("regions", regions_for_ocr)
        except Exception:
            logger.exception("Falló la capa opcional de OCR regional por regiones. Se mantiene OCR global.")

    out: dict[str, object] = {}
    if patched_ocr is not None:
        out["ocr"] = patched_ocr

    # Excel NO es la base del sistema: si el formato no aplica, se reporta "no aplica" sin afectar OCR/bloques.
    if excel_bytes and not supported:
        out["excel_validation"] = {
            "enabled": True,
            "executed": False,
            "appliesToFormat": False,
            "overallStatus": "not_applicable",
            "messages": [
                "Se cargó un Excel de validación, pero este formato no soporta comparación contra Excel.",
            ],
        }
        return out

    # Structured extraction is based on blocks/lines and runs only when the format applies.
    if not supported or not blocks_payload:
        return out

    blocks = blocks_payload.get("blocks") if isinstance(blocks_payload.get("blocks"), list) else []
    # Attach semantic region hints to blocks when possible (used to reduce cross-area contamination).
    yolo_detections_for_trace = None
    regions_for_trace = None
    if isinstance(patched_ocr, dict):
        yolo_detections_for_trace = patched_ocr.get("yoloDetections")
        regions_for_trace = patched_ocr.get("regions")

    region_by_id: dict[str, dict] = {}
    if isinstance(regions_for_trace, list):
        for r in regions_for_trace:
            if isinstance(r, dict) and isinstance(r.get("id"), str) and r.get("id"):
                region_by_id[r["id"]] = r

    def _region_class_from_yolo_bbox(block_bbox: list[int]) -> str | None:
        if not (isinstance(yolo_detections_for_trace, list) and yolo_detections_for_trace):
            return None
        bx, by, bw, bh = [float(v) for v in block_bbox]
        cx = bx + bw / 2.0
        cy = by + bh / 2.0
        candidates: list[tuple[float, dict]] = []
        for det in yolo_detections_for_trace:
            if not isinstance(det, dict):
                continue
            cls = det.get("className")
            bb = det.get("bbox")
            if not (isinstance(cls, str) and cls.strip() and isinstance(bb, list) and len(bb) == 4):
                continue
            ax, ay, aw, ah = [float(v) for v in bb]
            if ax <= cx <= (ax + aw) and ay <= cy <= (ay + ah):
                candidates.append((float(aw * ah), det))
        if not candidates:
            return None
        # Prefer the smallest containing detection (more specific).
        _, best = sorted(candidates, key=lambda t: t[0])[0]
        return str(best.get("className") or "").strip() or None

    if isinstance(blocks, list):
        for b in blocks:
            if not isinstance(b, dict):
                continue
            if isinstance(b.get("regionId"), str) and b.get("regionId") in region_by_id:
                cls = region_by_id[b["regionId"]].get("className")
                if isinstance(cls, str) and cls.strip():
                    b["regionClassName"] = cls.strip()
            elif isinstance(b.get("bbox"), list) and len(b.get("bbox")) == 4:
                cls = _region_class_from_yolo_bbox(b["bbox"])
                if cls:
                    b["regionClassName"] = cls

    extracted = extract_structured_fields_from_blocks(
        blocks if isinstance(blocks, list) else [],
        region_by_id=region_by_id or None,
        excluded_region_classes=exclude_set,
    )

    # Determine main price bbox from the extracted main block id.
    main_price_block_id = (extracted.get("priceMain") or {}).get("sourceBlockId")
    main_bbox = None
    if isinstance(main_price_block_id, str) and isinstance(blocks, list):
        main_block = next((b for b in blocks if isinstance(b, dict) and b.get("id") == main_price_block_id), None)
        if isinstance(main_block, dict) and isinstance(main_block.get("bbox"), list) and len(main_block["bbox"]) == 4:
            main_bbox = main_block["bbox"]

    color_result = classify_main_price_block_color(image_bytes, main_bbox)
    price_block_analysis = price_block_as_dict(color_result)

    # Add strategy + interpretive messages (conservative).
    messages = list(price_block_analysis.get("messages") or [])
    strategy = None
    if price_block_analysis.get("mainBlockColor") == "red":
        strategy = "main_red_then_secondary_is_regular"
        messages.extend(
            [
                "El precio principal se interpretó como precio CMR.",
                "El precio inferior (si existe) se interpretó como precio regular.",
            ]
        )
    elif price_block_analysis.get("mainBlockColor") == "black":
        strategy = "main_black_then_secondary_is_before"
        messages.extend(
            [
                "El precio principal se interpretó como precio regular.",
                "El precio inferior (si existe) se interpretó como precio antes.",
            ]
        )
    else:
        strategy = "indeterminate_color"
        messages.append("La clasificación de precios quedó ambigua por color indeterminado.")

    price_block_analysis["classificationStrategy"] = strategy
    price_block_analysis["messages"] = messages

    assigned_prices = assign_prices_with_visual_rules(extracted, price_block_analysis)

    block_by_id: dict[str, dict] = {}
    if isinstance(blocks, list):
        for b in blocks:
            if isinstance(b, dict) and isinstance(b.get("id"), str) and b.get("id"):
                block_by_id[b["id"]] = b

    def _enrich_with_trace(field_payload: dict | None) -> dict | None:
        if not isinstance(field_payload, dict):
            return field_payload
        source_block_id = field_payload.get("sourceBlockId")
        if not (isinstance(source_block_id, str) and source_block_id and source_block_id in block_by_id):
            return field_payload
        b = block_by_id[source_block_id]
        region_id = b.get("regionId") if isinstance(b.get("regionId"), str) else None
        region_class = b.get("regionClassName") if isinstance(b.get("regionClassName"), str) else None
        region_bbox = None
        if region_id and isinstance(region_by_id.get(region_id), dict):
            bb = region_by_id[region_id].get("bbox")
            if isinstance(bb, list) and len(bb) == 4:
                region_bbox = bb
        strategy = "global_ocr"
        if region_id:
            strategy = "regional_ocr"
        elif excluded_areas:
            strategy = "yolo_masked_global"
        enriched = dict(field_payload)
        enriched["sourceRegionId"] = region_id
        enriched["sourceRegionClassName"] = region_class
        enriched["sourceRegionBbox"] = region_bbox
        enriched["sourceStrategy"] = strategy
        return enriched

    structured_fields = {
        "campaign": _enrich_with_trace(extracted.get("campaign")),
        "dateRange": _enrich_with_trace(extracted.get("dateRange")),
        "brand": _enrich_with_trace(extracted.get("brand")),
        "description": _enrich_with_trace(extracted.get("description")),
        "sku": _enrich_with_trace(extracted.get("sku")),
        "priceCmr": _enrich_with_trace(assigned_prices.get("priceCmr")),
        "priceRegular": _enrich_with_trace(assigned_prices.get("priceRegular")),
        "priceBefore": _enrich_with_trace(assigned_prices.get("priceBefore")),
        # Keep trace candidates (optional) for debugging / UI.
        "priceMain": _enrich_with_trace(extracted.get("priceMain")),
        "priceSecondary": _enrich_with_trace(extracted.get("priceSecondary")),
    }

    out.update({
        "structured_fields": structured_fields,
        "price_block_analysis": price_block_analysis,
    })

    # Excel validation (optional, strictly downstream of structured extraction).
    if excel_bytes:
        out["excel_validation"] = validate_against_excel(
            excel_bytes=excel_bytes,
            excel_filename=excel_filename,
            structured_fields=structured_fields,
            config=config,
        )

    return out


async def analyze_upload(
    file: UploadFile,
    guidelines_path: Path,
    excel_file: UploadFile | None = None,
    piece_format: str | None = None,
    debug: bool = False,
) -> AnalyzeResponse:
    """Analyze uploaded image/PDF and return a unified response payload."""
    file_bytes, file_size_kb, file_type = await load_upload_bytes(file)
    excel_bytes, excel_filename = await _read_optional_excel_bytes(excel_file)
    guidelines = load_guidelines(guidelines_path)

    if file_type == "image":
        metadata = extract_image_metadata(
            image_bytes=file_bytes,
            filename=file.filename or "unknown",
            file_size_kb=file_size_kb,
        )
        ocr_result = run_ocr(file_bytes)
        validation = validate_technical_requirements(metadata, guidelines)
        layout_validation = validate_layout(file_bytes, ocr_words=ocr_result.get("words") if isinstance(ocr_result, dict) else None)

        optional_layer: dict[str, object] = {}
        try:
            optional_layer = _try_optional_structured_layer(
                image_bytes=file_bytes,
                ocr_result=ocr_result if isinstance(ocr_result, dict) else None,
                layout_validation=layout_validation if isinstance(layout_validation, dict) else None,
                excel_bytes=excel_bytes,
                excel_filename=excel_filename,
                piece_format=piece_format,
                debug=debug,
            )
        except Exception:
            logger.exception("Error en la capa opcional de validación contra Excel / extracción estructurada.")
            optional_layer = {}

        return AnalyzeResponse(
            meta=metadata,
            technical_validation=validation,
            visual_analysis=VisualAnalysisResponse(
                dominant_colors=extract_dominant_colors(file_bytes),
            ),
            ocr=OCRResponse(**(optional_layer.get("ocr") if isinstance(optional_layer.get("ocr"), dict) else ocr_result)) if ocr_result else None,
            layout_validation=LayoutValidationResponse(**layout_validation),
            structured_fields=optional_layer.get("structured_fields") if optional_layer else None,
            price_block_analysis=optional_layer.get("price_block_analysis") if optional_layer else None,
            excel_validation=optional_layer.get("excel_validation") if optional_layer else None,
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
