"""Optional Excel-based validation for structured fields.

Rules:
- Excel is optional and must never break the main analysis.
- Empty Excel values are treated as "valid empty" (the field is not validated).
- Matching is by SKU first, then brand+description similarity.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from io import BytesIO
from typing import Any


def _strip_accents(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))


def _norm_key(text: str) -> str:
    t = _strip_accents((text or "").strip()).upper()
    t = re.sub(r"[\s\-]+", "_", t)
    t = re.sub(r"[^A-Z0-9_]+", "", t)
    return t


def _norm_text(text: str | None) -> str:
    t = _strip_accents((text or "").strip()).lower()
    t = re.sub(r"\s+", " ", t)
    return t


def _only_digits(text: str | None) -> str:
    return re.sub(r"\D+", "", text or "")


def _norm_price(value: str | None) -> str:
    if value is None:
        return ""
    v = str(value).strip().replace(",", ".")
    return v


def _parse_price_float(value: str | None) -> float | None:
    v = _norm_price(value)
    if not v:
        return None
    try:
        return float(v)
    except Exception:
        return None


def _token_set(text: str) -> set[str]:
    tokens = re.split(r"[^a-z0-9]+", _norm_text(text))
    return {t for t in tokens if t and len(t) >= 2}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / float(union) if union else 0.0


_DEFAULT_HEADER_SYNONYMS: dict[str, set[str]] = {
    "campaign": {"CAMPANA", "CAMPAÑA", "CAMPAIGN", "CAMPAÑA/ENCABEZADO", "ENCABEZADO"},
    "brand": {"MARCA", "BRAND"},
    "description": {"DESCRIPCION", "DESCRIPCIÓN", "DESC", "DESCRIP"},
    "sku": {"SKU", "CODIGO", "CÓDIGO", "COD_PRODUCTO"},
    "price_cmr": {"PRECIO_CMR", "PRECIO_CMR_", "CMR", "PRECIO_CMR(S/)"},
    "price_regular": {"PRECIO_REGULAR", "PRECIO_REGULAR_", "REGULAR", "PRECIO_REGULAR(S/)"},
    "price_before": {"PRECIO_ANTES", "PRECIO_ANTES_", "ANTES", "PRECIO_ANTERIOR"},
}


@dataclass(frozen=True)
class ExcelTable:
    rows: list[dict[str, str | None]]
    header_map: dict[str, str]  # field -> normalized header key used


def _load_xlsx_rows(excel_bytes: bytes) -> list[list[Any]]:
    try:
        import openpyxl  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("No se pudo importar openpyxl para leer archivos .xlsx.") from exc

    wb = openpyxl.load_workbook(BytesIO(excel_bytes), data_only=True, read_only=True)
    ws = wb.worksheets[0]
    rows: list[list[Any]] = []
    for row in ws.iter_rows(values_only=True):
        rows.append(list(row))
    return rows


def _load_xls_rows(excel_bytes: bytes) -> list[list[Any]]:
    try:
        import xlrd  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("No se pudo importar xlrd para leer archivos .xls.") from exc

    book = xlrd.open_workbook(file_contents=excel_bytes)
    sheet = book.sheet_by_index(0)
    rows: list[list[Any]] = []
    for r in range(sheet.nrows):
        rows.append([sheet.cell_value(r, c) for c in range(sheet.ncols)])
    return rows


def _find_header_row(rows: list[list[Any]], limit: int) -> int | None:
    for idx, row in enumerate(rows[: max(1, limit)]):
        if not row:
            continue
        non_empty = [v for v in row if str(v or "").strip()]
        if len(non_empty) >= 2:
            return idx
    return None


def _build_table(rows: list[list[Any]], header_row_limit: int, max_rows: int) -> ExcelTable:
    header_idx = _find_header_row(rows, limit=header_row_limit)
    if header_idx is None:
        return ExcelTable(rows=[], header_map={})

    header_raw = rows[header_idx]
    header_keys = [_norm_key(str(h or "")) for h in header_raw]
    data_rows = rows[header_idx + 1 : header_idx + 1 + max(0, max_rows)]

    # Build field -> header_key map using synonyms.
    header_set = set(header_keys)
    field_to_header: dict[str, str] = {}
    synonyms_norm = {field: {_norm_key(s) for s in syns} for field, syns in _DEFAULT_HEADER_SYNONYMS.items()}
    for field, candidates in synonyms_norm.items():
        match = next((h for h in header_keys if h in candidates), None)
        if match and match in header_set:
            field_to_header[field] = match

    normalized_rows: list[dict[str, str | None]] = []
    for row in data_rows:
        if not row or not any(str(v or "").strip() for v in row):
            continue
        row_map: dict[str, str | None] = {}
        for col_idx, value in enumerate(row):
            if col_idx >= len(header_keys):
                continue
            key = header_keys[col_idx]
            if not key:
                continue
            raw = None if value is None else str(value).strip()
            row_map[key] = raw if raw else None
        normalized_rows.append(row_map)

    return ExcelTable(rows=normalized_rows, header_map=field_to_header)


def load_excel_table(excel_bytes: bytes, filename: str | None, config: dict[str, Any] | None = None) -> ExcelTable:
    cfg = config or {}
    header_limit = int(((cfg.get("excel") or {}).get("header_row_search_limit")) or 10)
    max_rows = int(((cfg.get("excel") or {}).get("max_rows")) or 5000)

    name = (filename or "").lower()
    if name.endswith(".xls"):
        rows = _load_xls_rows(excel_bytes)
    else:
        rows = _load_xlsx_rows(excel_bytes)
    return _build_table(rows, header_row_limit=header_limit, max_rows=max_rows)


def _best_row_by_sku(table: ExcelTable, sku: str) -> tuple[int | None, list[int]]:
    header = table.header_map.get("sku")
    if not header:
        return None, []
    target = _only_digits(sku)
    candidates: list[int] = []
    for idx, row in enumerate(table.rows):
        cell = _only_digits(row.get(header))
        if cell and target and cell == target:
            candidates.append(idx)
    if len(candidates) == 1:
        return candidates[0], candidates
    return None, candidates


def _score_row(table: ExcelTable, row: dict[str, str | None], detected: dict[str, str | None]) -> float:
    brand_h = table.header_map.get("brand")
    desc_h = table.header_map.get("description")

    brand_score = _jaccard(_token_set(row.get(brand_h, "") if brand_h else ""), _token_set(detected.get("brand") or ""))
    desc_score = _jaccard(_token_set(row.get(desc_h, "") if desc_h else ""), _token_set(detected.get("description") or ""))
    return 0.6 * brand_score + 0.4 * desc_score


def _best_row_by_text(table: ExcelTable, detected: dict[str, str | None], min_score: float, min_margin: float) -> tuple[int | None, str]:
    if not table.rows:
        return None, "not_found"
    scores = [(idx, _score_row(table, row, detected)) for idx, row in enumerate(table.rows)]
    scores.sort(key=lambda t: t[1], reverse=True)
    best_idx, best_score = scores[0]
    second_score = scores[1][1] if len(scores) > 1 else 0.0
    if best_score >= min_score and (best_score - second_score) >= min_margin:
        return best_idx, "brand_description"
    return None, "ambiguous"


def _compare_field(field_name: str, expected: str | None, detected: str | None) -> dict[str, Any]:
    if expected is None or str(expected).strip() == "":
        # Empty Excel means: do not validate this field (valid empty)
        return {
            "expected": None,
            "detected": detected,
            "status": "valid_empty",
            "message": "El Excel no define este campo; no se valida.",
        }

    if detected is None or str(detected).strip() == "":
        return {"expected": expected, "detected": None, "status": "not_detected"}

    if field_name.startswith("price_"):
        e = _parse_price_float(expected)
        d = _parse_price_float(detected)
        if e is None or d is None:
            # fallback to normalized string compare
            match = _norm_text(str(expected)) == _norm_text(str(detected))
        else:
            match = abs(e - d) <= 0.01
        return {"expected": expected, "detected": detected, "status": "match" if match else "mismatch"}

    match = _norm_text(str(expected)) == _norm_text(str(detected))
    if not match and field_name in {"description", "campaign"}:
        # allow containment when one side is shorter (conservative)
        a = _norm_text(str(expected))
        b = _norm_text(str(detected))
        if a and b and (a in b or b in a) and (min(len(a), len(b)) / max(len(a), len(b))) >= 0.8:
            match = True
    return {"expected": expected, "detected": detected, "status": "match" if match else "mismatch"}


def validate_against_excel(
    excel_bytes: bytes | None,
    excel_filename: str | None,
    structured_fields: dict[str, Any] | None,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not excel_bytes:
        return {
            "enabled": False,
            "executed": False,
            "overallStatus": "not_executed",
            "messages": ["No se cargó un Excel de validación."],
        }

    cfg = config or {}
    min_score = float(((cfg.get("matching") or {}).get("min_score")) or 0.55)
    min_margin = float(((cfg.get("matching") or {}).get("min_margin")) or 0.12)

    messages: list[str] = []
    try:
        table = load_excel_table(excel_bytes, excel_filename, config=cfg)
    except Exception:
        return {
            "enabled": True,
            "executed": False,
            "overallStatus": "error",
            "messages": ["No se pudo leer el archivo Excel. Verifica que sea .xlsx o .xls válido."],
        }

    detected = structured_fields or {}
    detected_values: dict[str, str | None] = {
        "campaign": (detected.get("campaign") or {}).get("value"),
        "brand": (detected.get("brand") or {}).get("value"),
        "description": (detected.get("description") or {}).get("value"),
        "sku": (detected.get("sku") or {}).get("value"),
        "price_cmr": (detected.get("priceCmr") or {}).get("value"),
        "price_regular": (detected.get("priceRegular") or {}).get("value"),
        "price_before": (detected.get("priceBefore") or {}).get("value"),
    }

    matched_row: int | None = None
    match_strategy: str | None = None

    sku = detected_values.get("sku")
    if sku:
        row_idx, sku_candidates = _best_row_by_sku(table, sku)
        if row_idx is not None:
            matched_row = row_idx
            match_strategy = "sku"
            messages.append("Se encontró coincidencia por SKU.")
        elif sku_candidates:
            # tie-break among SKU duplicates
            scored = [(idx, _score_row(table, table.rows[idx], detected_values)) for idx in sku_candidates]
            scored.sort(key=lambda t: t[1], reverse=True)
            if scored and scored[0][1] >= min_score:
                matched_row = scored[0][0]
                match_strategy = "sku"
                messages.append("Se encontraron múltiples filas con el mismo SKU; se eligió la mejor por similitud de texto.")
            else:
                messages.append("Se encontraron múltiples filas con el mismo SKU; no fue posible desambiguar con confianza.")

    if matched_row is None:
        row_idx, strategy = _best_row_by_text(table, detected_values, min_score=min_score, min_margin=min_margin)
        if row_idx is not None:
            matched_row = row_idx
            match_strategy = strategy
            messages.append("Se encontró coincidencia por marca + descripción.")
        else:
            match_strategy = strategy
            if strategy == "ambiguous":
                messages.append("No se pudo identificar una fila de Excel de forma confiable (resultado ambiguo).")
            else:
                messages.append("No se encontró una fila candidata en el Excel.")

    if matched_row is None:
        return {
            "enabled": True,
            "executed": True,
            "appliesToFormat": True,
            "matchedRowIndex": None,
            "matchStrategy": match_strategy,
            "overallStatus": "ambiguous" if match_strategy == "ambiguous" else "not_found",
            "fields": {},
            "messages": messages,
        }

    row = table.rows[matched_row]

    def cell(field: str) -> str | None:
        hk = table.header_map.get(field)
        return row.get(hk) if hk else None

    comparisons: dict[str, Any] = {
        "campaign": _compare_field("campaign", cell("campaign"), detected_values.get("campaign")),
        "brand": _compare_field("brand", cell("brand"), detected_values.get("brand")),
        "description": _compare_field("description", cell("description"), detected_values.get("description")),
        "sku": _compare_field("sku", cell("sku"), detected_values.get("sku")),
        "priceCmr": _compare_field("price_cmr", cell("price_cmr"), detected_values.get("price_cmr")),
        "priceRegular": _compare_field("price_regular", cell("price_regular"), detected_values.get("price_regular")),
        "priceBefore": _compare_field("price_before", cell("price_before"), detected_values.get("price_before")),
    }

    mismatches = [k for k, v in comparisons.items() if v.get("status") == "mismatch"]
    overall = "match" if not mismatches else "partial_match"

    return {
        "enabled": True,
        "executed": True,
        "appliesToFormat": True,
        "matchedRowIndex": matched_row + 2,  # +1 header, +1 to make it 1-based for UI
        "matchStrategy": match_strategy,
        "overallStatus": overall,
        "fields": comparisons,
        "messages": messages + ["La comparación con Excel se ejecutó correctamente."],
    }

