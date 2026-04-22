from __future__ import annotations

"""Hybrid layout parsing: OCR global + OCR regional.

Principio:
- Mantener OCR global (compatibilidad/backward).
- Si OCR regional existe, construir líneas/microbloques/bloques por región y evitar mezclas entre regiones.
- Entregar trazabilidad por región y una vista "híbrida" consolidada.
"""

from typing import Any

from app.services.layout_block_parser import build_ocr_blocks


def _prefix_items(items: list[dict[str, Any]] | None, prefix: str, region_id: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for it in items or []:
        if not isinstance(it, dict):
            continue
        cloned = dict(it)
        if isinstance(cloned.get("id"), str) and cloned["id"]:
            cloned["id"] = f"{prefix}{cloned['id']}"
        cloned["regionId"] = region_id
        out.append(cloned)
    return out


def build_region_aware_layout(
    *,
    regional_ocr: list[dict[str, Any]] | None,
) -> dict[str, Any] | None:
    if not regional_ocr:
        return None

    regional_layouts: list[dict[str, Any]] = []
    all_lines: list[dict[str, Any]] = []
    all_micro: list[dict[str, Any]] = []
    all_blocks: list[dict[str, Any]] = []

    for entry in regional_ocr:
        if not isinstance(entry, dict):
            continue
        region_id = str(entry.get("regionId") or "").strip()
        bbox = entry.get("bbox")
        words_global = entry.get("wordsGlobal")
        if not region_id or not (isinstance(words_global, list) and words_global):
            continue

        try:
            payload = build_ocr_blocks(words_global)
        except Exception:
            continue

        prefix = f"{region_id}::"
        lines = _prefix_items(payload.get("lines") if isinstance(payload, dict) else None, prefix, region_id)
        micro = _prefix_items(payload.get("microBlocks") if isinstance(payload, dict) else None, prefix, region_id)
        blocks = _prefix_items(payload.get("blocks") if isinstance(payload, dict) else None, prefix, region_id)

        regional_layouts.append(
            {
                "regionId": region_id,
                "bbox": bbox,
                "lines": lines,
                "microBlocks": micro,
                "blocks": blocks,
            }
        )

        all_lines.extend(lines)
        all_micro.extend(micro)
        all_blocks.extend(blocks)

    if not all_blocks and not all_lines and not all_micro:
        return None

    def sort_key(it: dict[str, Any]) -> tuple[float, float]:
        bbox = it.get("bbox")
        if isinstance(bbox, list) and len(bbox) == 4:
            x, y, w, h = [float(v) for v in bbox]
            return (y + h / 2.0, x + w / 2.0)
        return (1e9, 1e9)

    all_lines = sorted(all_lines, key=sort_key)
    all_micro = sorted(all_micro, key=sort_key)
    all_blocks = sorted(all_blocks, key=sort_key)

    return {
        "lines": all_lines,
        "microBlocks": all_micro,
        "blocks": all_blocks,
        "regionalLayouts": regional_layouts,
    }

