"""Structured extraction for slideshow/mtlk-like pieces.

This service is intentionally conservative:
- prefers returning null/"not_detected" over guessing
- uses OCR blocks + relative positions + content patterns (regex)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Literal


_MONTHS = (
    "enero|febrero|marzo|abril|mayo|junio|julio|agosto|setiembre|septiembre|octubre|noviembre|diciembre"
)
_DAYS = "lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo"

SKU_RE = re.compile(r"\bSKU\b[:\s#-]*([0-9]{5,12})\b", re.IGNORECASE)
PRICE_RE = re.compile(r"(?:S\/\s*)?(\d{1,4}(?:[.,]\d{2}))\b")
DATE_HINT_RE = re.compile(rf"\b(?:del|desde|hasta|al|sobre)\b|\b(?:{_DAYS})\b|\b(?:{_MONTHS})\b", re.IGNORECASE)


def _norm_space(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def _only_digits(text: str) -> str:
    return re.sub(r"\D+", "", text or "")


def _norm_price(value: str) -> str:
    v = (value or "").strip().replace(",", ".")
    return v


def _is_upperish(text: str) -> float:
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    upp = sum(1 for c in letters if c.isupper())
    return upp / float(len(letters))


def _looks_like_brand(text: str) -> bool:
    t = _norm_space(text)
    if not t or len(t) > 28:
        return False
    if any(ch.isdigit() for ch in t):
        return False
    tokens = t.split()
    if len(tokens) > 3:
        return False
    upper_ratio = _is_upperish(t)
    return upper_ratio >= 0.8 and all(len(tok) >= 2 for tok in tokens)


def _looks_like_campaign(text: str) -> bool:
    t = _norm_space(text)
    if not t:
        return False
    if any(ch.isdigit() for ch in t):
        return False
    tokens = t.split()
    if len(tokens) > 5:
        return False
    return _is_upperish(t) >= 0.75


def _looks_like_description(text: str) -> bool:
    t = _norm_space(text)
    if not t or len(t) < 8:
        return False
    if SKU_RE.search(t):
        return False
    if PRICE_RE.search(t) and len(t) < 18:
        return False
    return True


@dataclass(frozen=True)
class StructuredField:
    value: str | None
    source_block_id: str | None
    confidence: float
    status: Literal["detected", "not_detected", "ambiguous", "not_applicable"]


def _field(value: str | None, block_id: str | None, confidence: float, status: str) -> dict[str, Any]:
    return {
        "value": value,
        "sourceBlockId": block_id,
        "confidence": round(float(confidence), 4),
        "status": status,
    }


def extract_structured_fields_from_blocks(
    ocr_blocks: list[dict[str, Any]],
    *,
    region_by_id: dict[str, dict[str, Any]] | None = None,
    prefer_semantic_regions: bool = True,
    excluded_region_classes: set[str] | None = None,
) -> dict[str, Any]:
    """Extract core fields from OCR blocks.

    This function is backward compatible and accepts optional region metadata:
    - If blocks have `regionId` and we can map it to a YOLO `className`, extraction will prefer blocks
      from the expected semantic areas (campaign/date/info_card/price/sku).
    - If a block is marked as coming from an excluded class (e.g., product_photo_area),
      it will not participate in the core extraction.

    Prices are extracted as main/secondary candidates here; final assignment depends on visual rules.
    """
    excluded_region_classes = {str(x).strip() for x in (excluded_region_classes or set()) if str(x).strip()}

    def region_class_for_block(b: dict[str, Any]) -> str | None:
        rid = b.get("regionId")
        if isinstance(rid, str) and rid and region_by_id and isinstance(region_by_id.get(rid), dict):
            cls = region_by_id[rid].get("className")
            return str(cls).strip() if isinstance(cls, str) and str(cls).strip() else None
        # Also support direct annotation by upstream parsers.
        cls2 = b.get("regionClassName")
        return str(cls2).strip() if isinstance(cls2, str) and str(cls2).strip() else None

    blocks = []
    for b in (ocr_blocks or []):
        if not isinstance(b, dict):
            continue
        region_class = region_class_for_block(b) if region_by_id or "regionClassName" in b else None
        if region_class and region_class in excluded_region_classes:
            continue
        blocks.append(
            {
                "id": str(b.get("id", "")),
                "type": str(b.get("type", "")) if isinstance(b.get("type"), str) else "",
                "text": _norm_space(str(b.get("text", ""))),
                "bbox": b.get("bbox"),
                "confidence": float(b.get("confidence", 0.0) or 0.0),
                "regionId": b.get("regionId"),
                "regionClassName": region_class,
            }
        )
    blocks = [b for b in blocks if b["id"] and b["text"]]
    # Exclude auxiliary promo/badge blocks (e.g., "CMR", "Débito") from core extraction.
    blocks = [b for b in blocks if (b.get("type") or "") != "promo_badge"]

    # Defaults (conservative)
    out: dict[str, Any] = {
        "campaign": _field(None, None, 0.0, "not_detected"),
        "dateRange": _field(None, None, 0.0, "not_detected"),
        "brand": _field(None, None, 0.0, "not_detected"),
        "description": _field(None, None, 0.0, "not_detected"),
        "sku": _field(None, None, 0.0, "not_detected"),
        "priceMain": _field(None, None, 0.0, "not_detected"),
        "priceSecondary": _field(None, None, 0.0, "not_detected"),
    }

    if not blocks:
        return out

    # Optional semantic-region routing (YOLO classes) to reduce cross-area contamination.
    semantic_enabled = bool(prefer_semantic_regions and any(b.get("regionClassName") for b in blocks))
    field_to_region_classes: dict[str, list[str]] = {
        "campaign": ["campaign_area"],
        "dateRange": ["date_area"],
        "brand": ["info_card_area"],
        "description": ["info_card_area"],
        "sku": ["sku_area", "info_card_area"],
        "priceMain": ["price_main_area"],
        "priceSecondary": ["price_secondary_area"],
    }

    def blocks_for(field: str) -> list[dict[str, Any]]:
        if not semantic_enabled:
            return blocks
        desired = field_to_region_classes.get(field) or []
        if not desired:
            return blocks
        scoped = [b for b in blocks if b.get("regionClassName") in desired]
        return scoped if scoped else blocks

    # SKU
    sku_candidates: list[tuple[float, str, str]] = []
    for b in blocks_for("sku"):
        type_boost = 1.10 if b.get("type") == "sku" else 1.0
        m = SKU_RE.search(b["text"])
        if m:
            sku_candidates.append((type_boost * 0.98 * b["confidence"], b["id"], m.group(1)))
            continue
        digits = _only_digits(b["text"])
        if digits and 5 <= len(digits) <= 12 and len(b["text"]) <= len(digits) + 2:
            sku_candidates.append((type_boost * 0.75 * b["confidence"], b["id"], digits))

    if sku_candidates:
        sku_candidates.sort(reverse=True, key=lambda t: t[0])
        conf, block_id, value = sku_candidates[0]
        out["sku"] = _field(value, block_id, conf, "detected")

    # Date/range
    date_candidates: list[tuple[float, str, str]] = []
    for b in blocks_for("dateRange"):
        if DATE_HINT_RE.search(b["text"]) and any(ch.isdigit() for ch in b["text"]):
            type_boost = 1.08 if b.get("type") == "date_range" else 1.0
            date_candidates.append((type_boost * 0.8 * b["confidence"], b["id"], b["text"]))
    if date_candidates:
        date_candidates.sort(reverse=True, key=lambda t: t[0])
        conf, block_id, value = date_candidates[0]
        out["dateRange"] = _field(value, block_id, conf, "detected")

    # Prices (candidates; final assignment depends on visual classifier)
    price_blocks: list[tuple[float, str, str, list[int] | None]] = []
    for b in blocks_for("priceMain"):
        matches = PRICE_RE.findall(b["text"])
        if not matches:
            continue
        # choose the last numeric occurrence as the most "price-like"
        value = _norm_price(matches[-1])
        bbox = b["bbox"] if isinstance(b.get("bbox"), list) and len(b["bbox"]) == 4 else None
        height = float(bbox[3]) if bbox else 0.0
        type_boost = 1.12 if b.get("type") == "price_main" else 1.0
        score = type_boost * ((0.65 * b["confidence"]) + (0.35 * min(1.0, height / 120.0)))
        price_blocks.append((score, b["id"], value, bbox))

    if price_blocks:
        price_blocks.sort(reverse=True, key=lambda t: t[0])
        main_score, main_id, main_value, _ = price_blocks[0]
        out["priceMain"] = _field(main_value, main_id, main_score, "detected")

        # secondary: find a different block; prefer one that contains hints "regular/antes/cmr" or is short
        secondary_candidates: list[tuple[float, str, str]] = []
        for score, bid, value, _ in price_blocks[1:]:
            text = next((b["text"] for b in blocks if b["id"] == bid), "")
            block_type = next((b.get("type") for b in blocks if b["id"] == bid), "")
            hint = 0.16 if block_type == "price_secondary" else 0.0
            hint += 0.08 if re.search(r"\b(regular|antes|cmr)\b", text, re.IGNORECASE) else 0.0
            secondary_candidates.append((score + hint, bid, value))
        if secondary_candidates:
            secondary_candidates.sort(reverse=True, key=lambda t: t[0])
            sec_score, sec_id, sec_value = secondary_candidates[0]
            out["priceSecondary"] = _field(sec_value, sec_id, sec_score, "detected")

    # Brand
    brand_candidates: list[tuple[float, str, str]] = []
    for b in blocks_for("brand"):
        if _looks_like_brand(b["text"]):
            type_boost = 1.08 if b.get("type") == "brand" else 1.0
            brand_candidates.append((type_boost * 0.92 * b["confidence"], b["id"], b["text"]))
    if brand_candidates:
        brand_candidates.sort(reverse=True, key=lambda t: t[0])
        conf, block_id, value = brand_candidates[0]
        out["brand"] = _field(value, block_id, conf, "detected")

    # Campaign (optional)
    campaign_candidates: list[tuple[float, str, str]] = []
    scoped_campaign = blocks_for("campaign")
    for b in scoped_campaign[: min(6, len(scoped_campaign))]:
        if _looks_like_campaign(b["text"]) and not _looks_like_brand(b["text"]):
            type_boost = 1.05 if b.get("type") == "campaign" else 1.0
            campaign_candidates.append((type_boost * 0.75 * b["confidence"], b["id"], b["text"]))
    if campaign_candidates:
        campaign_candidates.sort(reverse=True, key=lambda t: t[0])
        conf, block_id, value = campaign_candidates[0]
        out["campaign"] = _field(value, block_id, conf, "detected")

    # Description
    desc_candidates: list[tuple[float, str, str]] = []
    for b in blocks_for("description"):
        if _looks_like_description(b["text"]) and not _looks_like_brand(b["text"]) and not SKU_RE.search(b["text"]):
            length_boost = min(0.25, len(b["text"]) / 160.0)
            type_boost = 1.05 if b.get("type") == "description" else 1.0
            desc_candidates.append((type_boost * (0.70 * b["confidence"] + length_boost), b["id"], b["text"]))
    if desc_candidates:
        desc_candidates.sort(reverse=True, key=lambda t: t[0])
        conf, block_id, value = desc_candidates[0]
        out["description"] = _field(value, block_id, conf, "detected")

    return out


def assign_prices_with_visual_rules(
    extracted: dict[str, Any],
    price_block_analysis: dict[str, Any] | None,
) -> dict[str, Any]:
    """Map priceMain/priceSecondary into priceCmr/priceRegular/priceBefore based on visual rules."""
    extracted = dict(extracted or {})
    main = (extracted.get("priceMain") or {}).get("value")
    secondary = (extracted.get("priceSecondary") or {}).get("value")
    main_block_id = (extracted.get("priceMain") or {}).get("sourceBlockId")
    secondary_block_id = (extracted.get("priceSecondary") or {}).get("sourceBlockId")

    color = (price_block_analysis or {}).get("mainBlockColor", "indeterminate")
    color_conf = float((price_block_analysis or {}).get("mainBlockColorConfidence", 0.0) or 0.0)

    def not_detected() -> dict[str, Any]:
        return _field(None, None, 0.0, "not_detected")

    def ambiguous(msg: str) -> dict[str, Any]:
        return _field(None, None, 0.0, "ambiguous") | {"message": msg}

    out: dict[str, Any] = {
        "priceCmr": not_detected(),
        "priceRegular": not_detected(),
        "priceBefore": not_detected(),
    }

    if not main:
        return out

    if color == "red":
        out["priceCmr"] = _field(main, main_block_id, max(0.6, color_conf), "detected")
        if secondary:
            out["priceRegular"] = _field(secondary, secondary_block_id, max(0.55, color_conf), "detected")
        return out

    if color == "black":
        out["priceRegular"] = _field(main, main_block_id, max(0.6, color_conf), "detected")
        if secondary:
            out["priceBefore"] = _field(secondary, secondary_block_id, max(0.55, color_conf), "detected")
        return out

    out["priceCmr"] = ambiguous("El color del bloque principal es indeterminado; no se asignó precio CMR.")
    out["priceRegular"] = ambiguous("El color del bloque principal es indeterminado; no se asignó precio regular.")
    out["priceBefore"] = ambiguous("El color del bloque principal es indeterminado; no se asignó precio antes.")
    return out
