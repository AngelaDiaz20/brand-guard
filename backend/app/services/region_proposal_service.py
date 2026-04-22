from __future__ import annotations

"""Region proposal (visión clásica) para OCR por zonas.

Objetivo:
- Proponer regiones visuales coherentes (relativas, sin coordenadas fijas).
- Permitir ejecutar OCR por recortes para evitar que el OCR global mezcle líneas de distintas zonas.

Esta capa es opcional y defensiva: si falla, el pipeline debe seguir funcionando con OCR global.
"""

from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np


@dataclass(frozen=True)
class RegionProposal:
    id: str
    kind: str
    bbox: list[int]  # [x, y, w, h]
    confidence: float
    source: str


def _clamp_bbox(bbox: list[int], w: int, h: int) -> list[int]:
    x, y, bw, bh = [int(v) for v in bbox]
    x = max(0, min(x, w - 1))
    y = max(0, min(y, h - 1))
    bw = max(1, min(bw, w - x))
    bh = max(1, min(bh, h - y))
    return [x, y, bw, bh]


def _decode_rgb(image_bytes: bytes) -> np.ndarray | None:
    if not image_bytes:
        return None
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if bgr is None:
        return None
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)


def _detect_1d_split(values: list[float], span: float, min_gap_frac: float) -> float | None:
    if len(values) < 6 or span <= 1e-6:
        return None
    sorted_vals = sorted(values)
    gaps = [(sorted_vals[i + 1] - sorted_vals[i], i) for i in range(len(sorted_vals) - 1)]
    if not gaps:
        return None
    gap, idx = max(gaps, key=lambda t: t[0])
    if (gap / span) < min_gap_frac:
        return None
    left = idx + 1
    right = len(sorted_vals) - left
    if left < 2 or right < 2:
        return None
    return float((sorted_vals[idx] + sorted_vals[idx + 1]) / 2.0)


def _iou(a: list[int], b: list[int]) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ax2, ay2 = ax + aw, ay + ah
    bx2, by2 = bx + bw, by + bh
    ix1, iy1 = max(ax, bx), max(ay, by)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0, ix2 - ix1), max(0, iy2 - iy1)
    inter = iw * ih
    union = (aw * ah) + (bw * bh) - inter
    return float(inter / union) if union > 0 else 0.0


def _merge_overlapping(bboxes: list[list[int]], iou_thr: float = 0.55) -> list[list[int]]:
    if not bboxes:
        return []
    remaining = [list(b) for b in bboxes]
    merged: list[list[int]] = []
    while remaining:
        base = remaining.pop(0)
        changed = True
        while changed:
            changed = False
            keep: list[list[int]] = []
            for other in remaining:
                if _iou(base, other) >= iou_thr:
                    x1 = min(base[0], other[0])
                    y1 = min(base[1], other[1])
                    x2 = max(base[0] + base[2], other[0] + other[2])
                    y2 = max(base[1] + base[3], other[1] + other[3])
                    base = [x1, y1, max(1, x2 - x1), max(1, y2 - y1)]
                    changed = True
                else:
                    keep.append(other)
            remaining = keep
        merged.append(base)
    return merged


def propose_regions(
    *,
    image_bytes: bytes,
    ocr_words: list[dict[str, Any]] | None = None,
    max_regions: int = 10,
) -> list[dict[str, Any]]:
    """Proponer regiones visuales para OCR regional (sin pixeles hardcodeados).

    Estrategias:
    - Split relativo (x/y) basado en distribución de centros de cajas OCR (cuando existe).
    - Detección de rectángulos/paneles por contornos (visión clásica).
    """
    rgb = _decode_rgb(image_bytes)
    if rgb is None:
        return []

    h, w = rgb.shape[:2]
    if h <= 1 or w <= 1:
        return []

    proposals: list[RegionProposal] = []

    # --------------------------------------------------
    # 1) Regions por splits relativos usando cajas OCR
    # --------------------------------------------------
    centers_x: list[float] = []
    centers_y: list[float] = []
    if isinstance(ocr_words, list):
        for item in ocr_words:
            if not isinstance(item, dict):
                continue
            box = item.get("box")
            if not (isinstance(box, list) and len(box) == 4):
                continue
            x, y, bw, bh = [float(v) for v in box]
            if bw <= 1 or bh <= 1:
                continue
            centers_x.append(x + bw / 2.0)
            centers_y.append(y + bh / 2.0)

    x_thr = _detect_1d_split(centers_x, span=float(w), min_gap_frac=0.18) if centers_x else None
    y_thr = _detect_1d_split(centers_y, span=float(h), min_gap_frac=0.18) if centers_y else None

    if x_thr is not None:
        proposals.append(RegionProposal(id="region_lr_left", kind="macro", bbox=[0, 0, int(x_thr), h], confidence=0.55, source="ocr_split"))
        proposals.append(
            RegionProposal(
                id="region_lr_right",
                kind="macro",
                bbox=[int(x_thr), 0, max(1, w - int(x_thr)), h],
                confidence=0.55,
                source="ocr_split",
            )
        )

    if y_thr is not None:
        proposals.append(RegionProposal(id="region_tb_top", kind="macro", bbox=[0, 0, w, int(y_thr)], confidence=0.55, source="ocr_split"))
        proposals.append(
            RegionProposal(
                id="region_tb_bottom",
                kind="macro",
                bbox=[0, int(y_thr), w, max(1, h - int(y_thr))],
                confidence=0.55,
                source="ocr_split",
            )
        )

    # Quadrants when both splits exist.
    if x_thr is not None and y_thr is not None:
        x0 = 0
        x1 = int(x_thr)
        x2 = w
        y0 = 0
        y1 = int(y_thr)
        y2 = h
        proposals.extend(
            [
                RegionProposal(id="region_q_tl", kind="macro", bbox=[x0, y0, max(1, x1 - x0), max(1, y1 - y0)], confidence=0.62, source="ocr_split"),
                RegionProposal(id="region_q_tr", kind="macro", bbox=[x1, y0, max(1, x2 - x1), max(1, y1 - y0)], confidence=0.62, source="ocr_split"),
                RegionProposal(id="region_q_bl", kind="macro", bbox=[x0, y1, max(1, x1 - x0), max(1, y2 - y1)], confidence=0.62, source="ocr_split"),
                RegionProposal(id="region_q_br", kind="macro", bbox=[x1, y1, max(1, x2 - x1), max(1, y2 - y1)], confidence=0.62, source="ocr_split"),
            ]
        )

    # --------------------------------------------------
    # 2) Regions por contornos (rectángulos/paneles)
    # --------------------------------------------------
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 40, 120)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
    closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=2)

    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    rects: list[list[int]] = []
    for c in contours:
        x, y, bw, bh = cv2.boundingRect(c)
        area = float(bw * bh)
        if area <= 1:
            continue
        area_frac = area / float(w * h)
        if area_frac < 0.018 or area_frac > 0.65:
            continue
        if bw < int(0.12 * w) or bh < int(0.08 * h):
            continue
        ar = float(bw) / float(max(1, bh))
        if ar < 0.18 or ar > 6.0:
            continue
        rects.append(_clamp_bbox([x, y, bw, bh], w, h))

    rects = _merge_overlapping(rects, iou_thr=0.60)
    rects = sorted(rects, key=lambda b: b[2] * b[3], reverse=True)[: max_regions]
    for i, b in enumerate(rects, start=1):
        proposals.append(RegionProposal(id=f"region_rect_{i}", kind="panel", bbox=b, confidence=0.58, source="contours"))

    # --------------------------------------------------
    # Normalización + dedupe ligero
    # --------------------------------------------------
    # Always include a fallback full-frame region at low confidence for debugging.
    proposals.append(RegionProposal(id="region_full", kind="full", bbox=[0, 0, w, h], confidence=0.10, source="fallback"))

    # Clamp + merge exact duplicates.
    seen: set[tuple[int, int, int, int]] = set()
    out: list[RegionProposal] = []
    for p in proposals:
        bbox = _clamp_bbox(p.bbox, w, h)
        key = (bbox[0], bbox[1], bbox[2], bbox[3])
        if key in seen:
            continue
        seen.add(key)
        out.append(RegionProposal(id=p.id, kind=p.kind, bbox=bbox, confidence=float(p.confidence), source=p.source))

    # Prefer panels/macros over full-frame, and medium-sized regions.
    out = sorted(
        out,
        key=lambda p: (
            0 if p.kind in {"panel", "macro"} else 1 if p.kind == "full" else 2,
            -min(1.0, (p.bbox[2] * p.bbox[3]) / float(w * h)),
            -p.confidence,
        ),
    )

    # Keep a small number of regions to avoid expensive OCR loops.
    out = out[: max_regions]

    return [
        {
            "id": p.id,
            "kind": p.kind,
            "bbox": p.bbox,
            "confidence": round(float(p.confidence), 4),
            "source": p.source,
        }
        for p in out
    ]

