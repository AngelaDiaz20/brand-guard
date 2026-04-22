from __future__ import annotations

"""OCR por región (recortes) como capa opcional.

Estrategia:
- Mantener OCR global.
- Para cada región propuesta, recortar con un padding relativo.
- Ejecutar OCR sobre el recorte.
- Re-proyectar bounding boxes a coordenadas globales.

Todo esto debe ser defensivo: si falla, no debe romper el análisis principal.
"""

from typing import Any

import cv2
import numpy as np

from app.services.ocr_service import run_ocr_on_image_array


def _decode_rgb(image_bytes: bytes) -> np.ndarray | None:
    if not image_bytes:
        return None
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if bgr is None:
        return None
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)


def _clamp_bbox(bbox: list[int], w: int, h: int) -> list[int]:
    x, y, bw, bh = [int(v) for v in bbox]
    x = max(0, min(x, w - 1))
    y = max(0, min(y, h - 1))
    bw = max(1, min(bw, w - x))
    bh = max(1, min(bh, h - y))
    return [x, y, bw, bh]


def _pad_bbox(bbox: list[int], w: int, h: int, pad_px: int) -> list[int]:
    x, y, bw, bh = bbox
    x2 = x + bw
    y2 = y + bh
    x = max(0, x - pad_px)
    y = max(0, y - pad_px)
    x2 = min(w, x2 + pad_px)
    y2 = min(h, y2 + pad_px)
    return _clamp_bbox([x, y, max(1, x2 - x), max(1, y2 - y)], w, h)


def _translate_words(words: list[dict[str, Any]], dx: int, dy: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for w in words or []:
        if not isinstance(w, dict):
            continue
        box = w.get("box")
        if not (isinstance(box, list) and len(box) == 4):
            continue
        x, y, bw, bh = [int(round(float(v))) for v in box]
        out.append(
            {
                "text": w.get("text", ""),
                "box": [x + dx, y + dy, bw, bh],
                "confidence": float(w.get("confidence", 0.0) or 0.0),
            }
        )
    return out


def run_regional_ocr(
    *,
    image_bytes: bytes,
    regions: list[dict[str, Any]],
    exclude_areas: list[list[int]] | None = None,
    keep_areas: list[list[int]] | None = None,
    max_regions_to_ocr: int = 8,
) -> dict[str, Any]:
    rgb = _decode_rgb(image_bytes)
    if rgb is None:
        return {"regionalOcr": [], "regionalWords": []}

    h, w = rgb.shape[:2]
    regional_ocr: list[dict[str, Any]] = []
    regional_words_global: list[dict[str, Any]] = []
    exclude_areas = [list(b) for b in (exclude_areas or []) if isinstance(b, list) and len(b) == 4]
    keep_areas = [list(b) for b in (keep_areas or []) if isinstance(b, list) and len(b) == 4]

    def is_in_area(box: list[int], area: list[int]) -> bool:
        x, y, bw, bh = box
        cx = x + bw / 2.0
        cy = y + bh / 2.0
        exx, exy, exw, exh = [float(v) for v in area]
        return exx <= cx <= (exx + exw) and exy <= cy <= (exy + exh)

    def is_excluded(box: list[int]) -> bool:
        if not exclude_areas:
            return False
        in_ex = any(is_in_area(box, ex) for ex in exclude_areas)
        if not in_ex:
            return False
        # Exception: if the word also belongs to a "keep" subregion (e.g., price tag inside photo),
        # do not exclude it.
        if keep_areas and any(is_in_area(box, ka) for ka in keep_areas):
            return False
        return True

    # Order: prefer panels/macros first (region_proposal already sorted).
    has_non_full = any(isinstance(r, dict) and str(r.get("kind") or "") != "full" for r in (regions or []))
    for region in (regions or [])[:max_regions_to_ocr]:
        if not isinstance(region, dict):
            continue
        rid = str(region.get("id") or "").strip()
        if has_non_full and str(region.get("kind") or "") == "full":
            continue
        bbox = region.get("bbox")
        if not rid or not (isinstance(bbox, list) and len(bbox) == 4):
            continue

        x, y, bw, bh = _clamp_bbox([int(v) for v in bbox], w, h)
        # Skip tiny regions.
        if (bw * bh) < int(0.02 * w * h):
            continue

        pad_px = int(max(8, 0.03 * min(bw, bh)))
        padded = _pad_bbox([x, y, bw, bh], w, h, pad_px=pad_px)
        px, py, pw, ph = padded

        crop = rgb[py : py + ph, px : px + pw].copy()
        try:
            payload = run_ocr_on_image_array(crop)
        except Exception:
            # Defensive: continue con las siguientes regiones.
            continue

        words_local = payload.get("words") if isinstance(payload, dict) else None
        words_local = words_local if isinstance(words_local, list) else []
        words_global = _translate_words(words_local, dx=px, dy=py)
        if exclude_areas:
            words_global = [wg for wg in words_global if not is_excluded(wg.get("box") or [0, 0, 0, 0])]

        for wg in words_global:
            wg["regionId"] = rid
        regional_words_global.extend(words_global)

        regional_ocr.append(
            {
                "regionId": rid,
                "bbox": [px, py, pw, ph],
                "regionClassName": region.get("className"),
                "regionKind": region.get("kind"),
                "regionConfidence": region.get("confidence"),
                "regionSource": region.get("source"),
                "rawText": payload.get("rawText") if isinstance(payload, dict) else "",
                "correctedText": payload.get("correctedText") if isinstance(payload, dict) else "",
                "confidence": payload.get("confidence") if isinstance(payload, dict) else None,
                "score": payload.get("score") if isinstance(payload, dict) else None,
                "words": words_local,
                "wordsGlobal": words_global,
            }
        )

    return {
        "regionalOcr": regional_ocr,
        "regionalWords": regional_words_global,
    }
