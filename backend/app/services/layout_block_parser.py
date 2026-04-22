"""Flexible OCR layout grouping utilities (no absolute coordinate assumptions).

This module takes OCR words with bounding boxes and groups them into:
- lines (based on vertical proximity/overlap)
- blocks (based on inter-line proximity and x-overlap)

The output is designed to be stable, traceable, and safe to extend.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


@dataclass(frozen=True)
class OcrWordToken:
    index: int
    text: str
    box: list[int]  # [x, y, w, h]
    confidence: float

    @property
    def x(self) -> int:
        return int(self.box[0])

    @property
    def y(self) -> int:
        return int(self.box[1])

    @property
    def w(self) -> int:
        return int(self.box[2])

    @property
    def h(self) -> int:
        return int(self.box[3])

    @property
    def x2(self) -> int:
        return self.x + self.w

    @property
    def y2(self) -> int:
        return self.y + self.h

    @property
    def cx(self) -> float:
        return self.x + self.w / 2.0

    @property
    def cy(self) -> float:
        return self.y + self.h / 2.0


@dataclass(frozen=True)
class OcrLine:
    word_indexes: list[int]
    text: str
    bbox: list[int]  # [x, y, w, h]
    confidence: float


@dataclass(frozen=True)
class OcrBlock:
    id: str
    line_indexes: list[int]
    word_indexes: list[int]
    text: str
    bbox: list[int]  # [x, y, w, h]
    confidence: float


@dataclass(frozen=True)
class OcrMicroBlock:
    id: str
    zone: str
    role: str
    line_indexes: list[int]
    word_indexes: list[int]
    text: str
    bbox: list[int]  # [x, y, w, h]
    confidence: float


def _clamp_int(value: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, int(value)))


def _union_bbox_xywh(bboxes: list[list[int]]) -> list[int]:
    if not bboxes:
        return [0, 0, 0, 0]
    xs = [b[0] for b in bboxes]
    ys = [b[1] for b in bboxes]
    x2s = [b[0] + b[2] for b in bboxes]
    y2s = [b[1] + b[3] for b in bboxes]
    x1 = int(min(xs))
    y1 = int(min(ys))
    x2 = int(max(x2s))
    y2 = int(max(y2s))
    return [x1, y1, max(0, x2 - x1), max(0, y2 - y1)]


def _vertical_overlap_ratio(a: OcrWordToken, b: OcrWordToken) -> float:
    top = max(a.y, b.y)
    bottom = min(a.y2, b.y2)
    overlap = max(0, bottom - top)
    denom = max(1, min(a.h, b.h))
    return overlap / float(denom)


def _x_overlap_ratio_xywh(a: list[int], b: list[int]) -> float:
    ax1, ay1, aw, ah = a
    bx1, by1, bw, bh = b
    ax2 = ax1 + aw
    bx2 = bx1 + bw
    overlap = max(0, min(ax2, bx2) - max(ax1, bx1))
    denom = max(1, min(aw, bw))
    return overlap / float(denom)


def _global_bbox_xywh(bboxes: list[list[int]]) -> list[int]:
    if not bboxes:
        return [0, 0, 0, 0]
    return _union_bbox_xywh(bboxes)


def _detect_1d_split(values: list[float], span: float, min_gap_frac: float = 0.20) -> float | None:
    """Detect a stable split threshold using the largest gap heuristic."""
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


SKU_HINT_RE = re.compile(r"\bSKU\b", re.IGNORECASE)
PRICE_REGULAR_RE = re.compile(r"precio\s+regular", re.IGNORECASE)
DATE_HINT_RE = re.compile(
    r"\b(?:del|desde|hasta|al)\b|\b(?:lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo)\b|\b(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|setiembre|septiembre|octubre|noviembre|diciembre)\b",
    re.IGNORECASE,
)
PRICE_VALUE_RE = re.compile(r"(?:S\/\s*)?\d{1,4}(?:[.,]\d{2})\b", re.IGNORECASE)
CURRENCY_RE = re.compile(r"\bS\s*\/", re.IGNORECASE)
PROMO_BADGE_RE = re.compile(
    r"\b(?:cmr|d[ée]bito|exclusivo\s+con|oportunidad\s+única|oportunidad\s+unica|falabella)\b",
    re.IGNORECASE,
)


def _upper_ratio(text: str) -> float:
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    return sum(1 for c in letters if c.isupper()) / float(len(letters))


def classify_text_role(text: str) -> str:
    """Conservative role classifier used to prevent bad merges and provide lightweight block typing."""
    t = (text or "").strip()
    if not t:
        return "unknown"

    if SKU_HINT_RE.search(t):
        return "sku"
    if PRICE_REGULAR_RE.search(t):
        return "price_secondary"
    # Price main: prefer explicit currency, but also support bare values like "25.90" in short numeric-only strings.
    if (CURRENCY_RE.search(t) or "S\u2044" in t or "S\\/" in t) and PRICE_VALUE_RE.search(t):
        return "price_main"
    if PRICE_VALUE_RE.search(t) and not any(ch.isalpha() for ch in t) and len(t) <= 12:
        return "price_main"

    if DATE_HINT_RE.search(t) and any(ch.isdigit() for ch in t):
        return "date_range"

    # Promo/badge side labels near price (ignore for core product extraction).
    # Keep this after date/price/SKU checks and before campaign/brand/description heuristics.
    if PROMO_BADGE_RE.search(t) and not re.search(r"\bprecio\b", t, re.IGNORECASE):
        norm = re.sub(r"\s+", " ", t)
        if len(norm) <= 60:
            return "promo_badge"

    norm = re.sub(r"\s+", " ", t)
    tokens = norm.split(" ")
    # Prefer classifying multi-token uppercase phrases as campaign (not brand).
    if len(norm) <= 18 and not any(ch.isdigit() for ch in norm) and _upper_ratio(norm) >= 0.86 and len(tokens) == 1:
        return "brand"
    if len(norm) <= 55 and not any(ch.isdigit() for ch in norm) and _upper_ratio(norm) >= 0.75 and 1 <= len(tokens) <= 6:
        return "campaign"

    if len(norm) >= 10 and not SKU_HINT_RE.search(norm) and not PRICE_REGULAR_RE.search(norm):
        return "description"

    return "unknown"


def normalize_ocr_words(words: list[dict[str, Any]] | None) -> list[OcrWordToken]:
    """Normalize OCR words from the existing OCR payload format."""
    if not words:
        return []

    normalized: list[OcrWordToken] = []
    for idx, item in enumerate(words):
        try:
            text = str(item.get("text", "")).strip()
            box = item.get("box")
            confidence = float(item.get("confidence", 0.0))
            if not text or not isinstance(box, list) or len(box) != 4:
                continue
            box_int = [_clamp_int(int(round(float(v))), -10_000, 10_000) for v in box]
            normalized.append(OcrWordToken(index=idx, text=text, box=box_int, confidence=confidence))
        except Exception:
            continue

    return normalized


def group_words_into_lines(tokens: list[OcrWordToken]) -> list[OcrLine]:
    if not tokens:
        return []

    tokens_sorted = sorted(tokens, key=lambda t: (t.cy, t.cx))

    lines_words: list[list[OcrWordToken]] = []
    line_bbox: list[list[int]] = []

    for token in tokens_sorted:
        placed = False
        best_li: int | None = None
        best_score = -1e9
        for li, words_in_line in enumerate(lines_words):
            bbox = line_bbox[li]
            line_y1 = float(bbox[1])
            line_y2 = float(bbox[1] + bbox[3])
            line_h = float(max(1, bbox[3]))
            line_cy = (line_y1 + line_y2) / 2.0

            # Use line bbox (not the last token) to avoid chaining across lines.
            dy = abs(token.cy - line_cy)
            y_threshold = max(3.0, 0.55 * float(max(line_h, token.h)))

            # Compute overlap between token bbox and line bbox (vertical).
            top = max(line_y1, float(token.y))
            bottom = min(line_y2, float(token.y2))
            overlap_px = max(0.0, bottom - top)
            overlap_ratio = overlap_px / float(max(1.0, min(line_h, float(token.h))))

            # Horizontal guard: avoid merging different columns into the same line.
            line_x1 = float(bbox[0])
            line_x2 = float(bbox[0] + bbox[2])
            token_x1 = float(token.x)
            token_x2 = float(token.x2)
            horiz_dist = 0.0
            if token_x1 > line_x2:
                horiz_dist = token_x1 - line_x2
            elif line_x1 > token_x2:
                horiz_dist = line_x1 - token_x2

            horiz_threshold = max(10.0, 2.8 * float(max(line_h, token.h)))
            if horiz_dist > horiz_threshold:
                continue

            if overlap_ratio >= 0.45 or (overlap_ratio >= 0.25 and dy <= y_threshold):
                # Score candidate line to pick the best one (prevents "first line wins" mistakes).
                score = (overlap_ratio * 3.0) - (dy / max(1.0, line_h)) - (horiz_dist / max(1.0, horiz_threshold))
                if score > best_score:
                    best_score = score
                    best_li = li

        if best_li is not None:
            lines_words[best_li].append(token)
            line_bbox[best_li] = _union_bbox_xywh([w.box for w in lines_words[best_li]])
            placed = True

        if not placed:
            lines_words.append([token])
            line_bbox.append(token.box)

    lines: list[OcrLine] = []
    for words_in_line, bbox in zip(lines_words, line_bbox, strict=False):
        words_in_line_sorted = sorted(words_in_line, key=lambda t: t.x)
        text = " ".join(w.text for w in words_in_line_sorted).strip()
        word_indexes = [w.index for w in words_in_line_sorted]
        conf = float(sum(w.confidence for w in words_in_line_sorted) / max(1, len(words_in_line_sorted)))
        lines.append(OcrLine(word_indexes=word_indexes, text=text, bbox=bbox, confidence=conf))

    # Refine: split lines that still contain two internal columns (strong horizontal gap).
    refined: list[OcrLine] = []
    for line in lines:
        token_indexes = list(line.word_indexes)
        if len(token_indexes) < 4:
            refined.append(line)
            continue

        # Detect a split based on token centers within the line width.
        token_boxes = [tokens[i].box for i in token_indexes if 0 <= i < len(tokens)]
        if not token_boxes:
            refined.append(line)
            continue
        line_bbox = _global_bbox_xywh(token_boxes)
        span = float(max(1, line_bbox[2]))
        centers = [float(b[0] + b[2] / 2.0) for b in token_boxes]
        x_thr = _detect_1d_split(centers, span=span, min_gap_frac=0.34)
        if x_thr is None:
            refined.append(line)
            continue

        left_idxs: list[int] = []
        right_idxs: list[int] = []
        for idx in token_indexes:
            if 0 <= idx < len(tokens):
                cx = tokens[idx].cx
                (left_idxs if cx < x_thr else right_idxs).append(idx)

        if len(left_idxs) < 2 or len(right_idxs) < 2:
            refined.append(line)
            continue

        def build_line(indexes: list[int]) -> OcrLine:
            toks = sorted([tokens[i] for i in indexes if 0 <= i < len(tokens)], key=lambda t: t.x)
            txt = " ".join(t.text for t in toks).strip()
            bbox = _union_bbox_xywh([t.box for t in toks])
            conf = float(sum(t.confidence for t in toks) / max(1, len(toks)))
            return OcrLine(word_indexes=[t.index for t in toks], text=txt, bbox=bbox, confidence=conf)

        refined.append(build_line(left_idxs))
        refined.append(build_line(right_idxs))

    # Refine: split promo badges from core content when they were co-linear (e.g., "S/ 25.90 CMR").
    promo_refined: list[OcrLine] = []
    for line in refined:
        token_indexes = list(line.word_indexes)
        if len(token_indexes) < 2:
            promo_refined.append(line)
            continue

        toks = [tokens[i] for i in token_indexes if 0 <= i < len(tokens)]
        if len(toks) < 2:
            promo_refined.append(line)
            continue

        roles = [classify_text_role(t.text) for t in toks]
        if "promo_badge" not in roles or all(r == "promo_badge" for r in roles):
            promo_refined.append(line)
            continue

        promo_idxs = [t.index for t, r in zip(toks, roles, strict=False) if r == "promo_badge"]
        other_idxs = [t.index for t, r in zip(toks, roles, strict=False) if r != "promo_badge"]
        if not other_idxs or not promo_idxs:
            promo_refined.append(line)
            continue

        other_bbox = _union_bbox_xywh([tokens[i].box for i in other_idxs if 0 <= i < len(tokens)])
        promo_bbox = _union_bbox_xywh([tokens[i].box for i in promo_idxs if 0 <= i < len(tokens)])
        horiz_dist = 0.0
        if promo_bbox[0] > (other_bbox[0] + other_bbox[2]):
            horiz_dist = float(promo_bbox[0] - (other_bbox[0] + other_bbox[2]))
        elif other_bbox[0] > (promo_bbox[0] + promo_bbox[2]):
            horiz_dist = float(other_bbox[0] - (promo_bbox[0] + promo_bbox[2]))

        height_ref = float(max(8, min(other_bbox[3], promo_bbox[3])))
        if horiz_dist <= max(12.0, 1.15 * height_ref):
            promo_refined.append(line)
            continue

        def build_line_from_indexes(indexes: list[int]) -> OcrLine:
            toks2 = sorted([tokens[i] for i in indexes if 0 <= i < len(tokens)], key=lambda t: t.x)
            txt2 = " ".join(t.text for t in toks2).strip()
            bbox2 = _union_bbox_xywh([t.box for t in toks2])
            conf2 = float(sum(t.confidence for t in toks2) / max(1, len(toks2)))
            return OcrLine(word_indexes=[t.index for t in toks2], text=txt2, bbox=bbox2, confidence=conf2)

        promo_refined.append(build_line_from_indexes(other_idxs))
        promo_refined.append(build_line_from_indexes(promo_idxs))

    # Ensure top-to-bottom order.
    return sorted(promo_refined, key=lambda l: (l.bbox[1] + l.bbox[3] / 2.0, l.bbox[0]))


def group_lines_into_blocks(lines: list[OcrLine]) -> list[OcrBlock]:
    if not lines:
        return []

    blocks_lines: list[list[int]] = []
    blocks_word_indexes: list[list[int]] = []
    blocks_bbox: list[list[int]] = []
    blocks_conf: list[list[float]] = []

    for idx, line in enumerate(lines):
        placed = False
        for bi, current_line_indexes in enumerate(blocks_lines):
            last_line = lines[current_line_indexes[-1]]
            gap = line.bbox[1] - (last_line.bbox[1] + last_line.bbox[3])
            typical_h = max(8.0, float((line.bbox[3] + last_line.bbox[3]) / 2.0))
            close_enough = gap <= 1.55 * typical_h

            x_overlap_last = _x_overlap_ratio_xywh(last_line.bbox, line.bbox)
            x_overlap_block = _x_overlap_ratio_xywh(blocks_bbox[bi], line.bbox)

            last_cx = last_line.bbox[0] + last_line.bbox[2] / 2.0
            line_cx = line.bbox[0] + line.bbox[2] / 2.0
            dx = abs(line_cx - last_cx)
            far_apart = dx > max(last_line.bbox[2], line.bbox[2]) * 0.95 and max(x_overlap_last, x_overlap_block) < 0.10

            if close_enough and not far_apart and (x_overlap_last >= 0.18 or x_overlap_block >= 0.22):
                current_line_indexes.append(idx)
                blocks_word_indexes[bi].extend(line.word_indexes)
                blocks_bbox[bi] = _union_bbox_xywh([blocks_bbox[bi], line.bbox])
                blocks_conf[bi].append(line.confidence)
                placed = True
                break

        if not placed:
            blocks_lines.append([idx])
            blocks_word_indexes.append(list(line.word_indexes))
            blocks_bbox.append(list(line.bbox))
            blocks_conf.append([line.confidence])

    blocks: list[OcrBlock] = []
    for bi, line_indexes in enumerate(blocks_lines, start=1):
        text = "\n".join(lines[i].text for i in line_indexes).strip()
        bbox = blocks_bbox[bi - 1]
        conf_list = blocks_conf[bi - 1]
        confidence = float(sum(conf_list) / max(1, len(conf_list)))
        blocks.append(
            OcrBlock(
                id=f"block_{bi}",
                line_indexes=line_indexes,
                word_indexes=blocks_word_indexes[bi - 1],
                text=text,
                bbox=bbox,
                confidence=confidence,
            )
        )

    return sorted(blocks, key=lambda b: (b.bbox[1] + b.bbox[3] / 2.0, b.bbox[0]))


def _assign_line_zones(lines: list[OcrLine]) -> list[str]:
    """Assign each line to a relative macrozone (TL/TR/BL/BR) using distribution gaps (no fixed pixels)."""
    if not lines:
        return []
    global_bbox = _global_bbox_xywh([l.bbox for l in lines])
    gx, gy, gw, gh = global_bbox
    if gw <= 0 or gh <= 0:
        return ["Z_ALL"] * len(lines)

    cxs = [float(l.bbox[0] + l.bbox[2] / 2.0) for l in lines]
    cys = [float(l.bbox[1] + l.bbox[3] / 2.0) for l in lines]
    x_thr = _detect_1d_split(cxs, span=float(gw), min_gap_frac=0.20)
    y_thr = _detect_1d_split(cys, span=float(gh), min_gap_frac=0.22)

    zones: list[str] = []
    for cx, cy in zip(cxs, cys, strict=False):
        x_part = "L" if (x_thr is not None and cx < x_thr) else "R" if x_thr is not None else "A"
        y_part = "T" if (y_thr is not None and cy < y_thr) else "B" if y_thr is not None else "A"
        if x_part == "A" and y_part == "A":
            zones.append("Z_ALL")
        else:
            zones.append(f"Z_{y_part}{x_part}")
    return zones


def _assign_internal_subzones(lines: list[OcrLine], indexes: list[int]) -> dict[int, str]:
    """Within a macrozone, detect internal left/right and top/bottom subzones by distribution gaps."""
    if len(indexes) < 4:
        return {i: "S_ALL" for i in indexes}

    bboxes = [lines[i].bbox for i in indexes]
    global_bbox = _global_bbox_xywh(bboxes)
    gw = float(max(1, global_bbox[2]))
    gh = float(max(1, global_bbox[3]))

    cxs = [float(lines[i].bbox[0] + lines[i].bbox[2] / 2.0) for i in indexes]
    cys = [float(lines[i].bbox[1] + lines[i].bbox[3] / 2.0) for i in indexes]

    x_thr = _detect_1d_split(cxs, span=gw, min_gap_frac=0.14)
    y_thr = _detect_1d_split(cys, span=gh, min_gap_frac=0.18)

    out: dict[int, str] = {}
    for idx in indexes:
        cx = float(lines[idx].bbox[0] + lines[idx].bbox[2] / 2.0)
        cy = float(lines[idx].bbox[1] + lines[idx].bbox[3] / 2.0)
        x_part = "L" if (x_thr is not None and cx < x_thr) else "R" if x_thr is not None else "A"
        y_part = "T" if (y_thr is not None and cy < y_thr) else "B" if y_thr is not None else "A"
        if x_part == "A" and y_part == "A":
            out[idx] = "S_ALL"
        else:
            out[idx] = f"S_{y_part}{x_part}"
    return out


def _should_merge_lines(
    prev_role: str,
    next_role: str,
    micro_bbox: list[int],
    next_bbox: list[int],
    gap: float,
    typical_h: float,
) -> bool:
    # Semantic barriers: keep these as isolated blocks by default.
    strong_isolated = {"sku", "price_main", "price_secondary", "promo_badge"}
    if prev_role in strong_isolated or next_role in strong_isolated:
        return False

    # Prevent campaign/date fusion even when close.
    if (prev_role == "campaign" and next_role == "date_range") or (prev_role == "date_range" and next_role == "campaign"):
        return False

    # Brand should not absorb other roles by proximity.
    if prev_role == "brand" and next_role != "brand":
        return False
    if next_role == "brand" and prev_role != "brand":
        return False

    # Prevent description from merging with other roles too aggressively.
    if prev_role == "description" and next_role not in {"description", "unknown"}:
        return False
    if next_role == "description" and prev_role not in {"description", "unknown"}:
        return False

    # Spatial constraints: much stricter than final block-level merging.
    if gap > 0.95 * typical_h:
        return False

    x_overlap = _x_overlap_ratio_xywh(micro_bbox, next_bbox)
    left_delta = abs(float(micro_bbox[0]) - float(next_bbox[0]))
    width_ref = float(max(1, min(micro_bbox[2], next_bbox[2])))
    aligned_left = (left_delta / width_ref) <= 0.16

    # Require strong overlap or alignment; avoid global proximity fusing.
    return x_overlap >= 0.32 or (aligned_left and x_overlap >= 0.18)


def group_lines_into_microblocks(lines: list[OcrLine]) -> list[OcrMicroBlock]:
    """Hierarchical grouping: lines -> microblocks, using macrozones + strict merge rules."""
    if not lines:
        return []

    macro_zones = _assign_line_zones(lines)
    by_macro: dict[str, list[int]] = {}
    for idx, zone in enumerate(macro_zones):
        by_macro.setdefault(zone, []).append(idx)

    microblocks: list[OcrMicroBlock] = []
    micro_id = 1

    for macro_zone, indexes in by_macro.items():
        subzones = _assign_internal_subzones(lines, indexes)
        by_cluster: dict[str, list[int]] = {}
        for i in indexes:
            by_cluster.setdefault(subzones.get(i, "S_ALL"), []).append(i)

        for sub_zone, cluster_indexes in by_cluster.items():
            cluster_indexes_sorted = sorted(
                cluster_indexes, key=lambda i: (lines[i].bbox[1] + lines[i].bbox[3] / 2.0, lines[i].bbox[0])
            )

            zone = f"{macro_zone}|{sub_zone}"
            current_line_indexes = []
            current_word_indexes = []
            current_bbox: list[int] | None = None
            current_conf: list[float] = []
            current_role: str | None = None

            def flush() -> None:
                nonlocal micro_id, current_line_indexes, current_word_indexes, current_bbox, current_conf, current_role
                if not current_line_indexes or current_bbox is None:
                    current_line_indexes = []
                    current_word_indexes = []
                    current_bbox = None
                    current_conf = []
                    current_role = None
                    return

                text = "\n".join(lines[i].text for i in current_line_indexes).strip()
                role = current_role or classify_text_role(text)
                confidence = float(sum(current_conf) / max(1, len(current_conf)))
                microblocks.append(
                    OcrMicroBlock(
                        id=f"micro_{micro_id}",
                        zone=zone,
                        role=role,
                        line_indexes=list(current_line_indexes),
                        word_indexes=list(current_word_indexes),
                        text=text,
                        bbox=list(current_bbox),
                        confidence=confidence,
                    )
                )
                micro_id += 1
                current_line_indexes = []
                current_word_indexes = []
                current_bbox = None
                current_conf = []
                current_role = None

            for i in cluster_indexes_sorted:
                line = lines[i]
                role = classify_text_role(line.text)

                if current_bbox is None:
                    current_line_indexes = [i]
                    current_word_indexes = list(line.word_indexes)
                    current_bbox = list(line.bbox)
                    current_conf = [line.confidence]
                    current_role = role
                    continue

                last_line = lines[current_line_indexes[-1]]
                gap = float(line.bbox[1] - (last_line.bbox[1] + last_line.bbox[3]))
                typical_h = float(max(8.0, (line.bbox[3] + last_line.bbox[3]) / 2.0))

                if not _should_merge_lines(
                    prev_role=current_role or "unknown",
                    next_role=role,
                    micro_bbox=current_bbox,
                    next_bbox=line.bbox,
                    gap=gap,
                    typical_h=typical_h,
                ):
                    flush()
                    current_line_indexes = [i]
                    current_word_indexes = list(line.word_indexes)
                    current_bbox = list(line.bbox)
                    current_conf = [line.confidence]
                    current_role = role
                    continue

                # Merge line into current microblock.
                current_line_indexes.append(i)
                current_word_indexes.extend(line.word_indexes)
                current_bbox = _union_bbox_xywh([current_bbox, line.bbox])
                current_conf.append(line.confidence)

                # Keep a conservative role: prefer the more "specific" one.
                if current_role in {"unknown", "description"} and role not in {"unknown"}:
                    current_role = role

            flush()

    return sorted(microblocks, key=lambda b: (b.bbox[1] + b.bbox[3] / 2.0, b.bbox[0]))


def group_microblocks_into_semantic_blocks(microblocks: list[OcrMicroBlock]) -> list[OcrBlock]:
    """Final block grouping with very limited merges to avoid over-grouping."""
    if not microblocks:
        return []

    blocks: list[OcrBlock] = []
    block_id = 1

    def can_merge(a: OcrMicroBlock, b: OcrMicroBlock) -> bool:
        if a.zone != b.zone or a.role != b.role:
            return False
        if a.role not in {"description", "date_range", "campaign"}:
            return False
        gap = float(b.bbox[1] - (a.bbox[1] + a.bbox[3]))
        typical_h = float(max(8.0, (a.bbox[3] + b.bbox[3]) / 2.0))
        if gap > 0.85 * typical_h:
            return False
        x_overlap = _x_overlap_ratio_xywh(a.bbox, b.bbox)
        return x_overlap >= 0.30

    current = microblocks[0]
    for nxt in microblocks[1:]:
        if can_merge(current, nxt):
            merged_text = (current.text + "\n" + nxt.text).strip()
            merged_bbox = _union_bbox_xywh([current.bbox, nxt.bbox])
            merged_conf = float((current.confidence + nxt.confidence) / 2.0)
            merged_lines = list(current.line_indexes) + list(nxt.line_indexes)
            merged_words = list(current.word_indexes) + list(nxt.word_indexes)
            current = OcrMicroBlock(
                id=current.id,
                zone=current.zone,
                role=current.role,
                line_indexes=merged_lines,
                word_indexes=merged_words,
                text=merged_text,
                bbox=merged_bbox,
                confidence=merged_conf,
            )
            continue

        blocks.append(
            OcrBlock(
                id=f"block_{block_id}",
                line_indexes=list(current.line_indexes),
                word_indexes=list(current.word_indexes),
                text=current.text,
                bbox=list(current.bbox),
                confidence=float(current.confidence),
            )
        )
        block_id += 1
        current = nxt

    blocks.append(
        OcrBlock(
            id=f"block_{block_id}",
            line_indexes=list(current.line_indexes),
            word_indexes=list(current.word_indexes),
            text=current.text,
            bbox=list(current.bbox),
            confidence=float(current.confidence),
        )
    )
    return blocks


def build_ocr_blocks(words: list[dict[str, Any]] | None) -> dict[str, Any]:
    """Convenience wrapper that returns a JSON-serializable structure."""
    tokens = normalize_ocr_words(words)
    lines = group_words_into_lines(tokens)
    microblocks = group_lines_into_microblocks(lines)
    blocks = group_microblocks_into_semantic_blocks(microblocks)
    line_ids = [f"line_{i + 1}" for i in range(len(lines))]
    line_roles = [classify_text_role(line.text) for line in lines]
    return {
        "lines": [
            {
                "id": line_ids[i],
                "text": line.text,
                "bbox": line.bbox,
                "confidence": round(float(line.confidence), 4),
                "wordIndexes": list(line.word_indexes),
                "type": line_roles[i],
            }
            for i, line in enumerate(lines)
        ],
        "microBlocks": [
            {
                "id": micro.id,
                "type": micro.role,
                "zone": micro.zone,
                "macroZone": micro.zone.split("|", 1)[0] if "|" in micro.zone else micro.zone,
                "subZone": micro.zone.split("|", 1)[1] if "|" in micro.zone else "S_ALL",
                "text": micro.text,
                "bbox": micro.bbox,
                "confidence": round(float(micro.confidence), 4),
                "wordIndexes": list(micro.word_indexes),
                "lineIndexes": list(micro.line_indexes),
                "lineIds": [line_ids[i] for i in micro.line_indexes if 0 <= i < len(line_ids)],
                "debug": {
                    "lineRoles": [line_roles[i] for i in micro.line_indexes if 0 <= i < len(line_roles)],
                },
            }
            for micro in microblocks
        ],
        "blocks": [
            {
                "id": block.id,
                "type": classify_text_role(block.text),
                "text": block.text,
                "bbox": block.bbox,
                "confidence": round(float(block.confidence), 4),
                "wordIndexes": list(block.word_indexes),
                "lineIndexes": list(block.line_indexes),
                "lineIds": [line_ids[i] for i in block.line_indexes if 0 <= i < len(line_ids)],
            }
            for block in blocks
        ],
    }
