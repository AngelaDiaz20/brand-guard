"""Post-OCR Spanish text correction heuristics."""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache

from app.services.structured_text_correction_service import (
    correct_text as structured_correct_text,
)

TOKEN_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9']+", re.UNICODE)
ALPHA_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]", re.UNICODE)
LIST_OPTION_RE = re.compile(r"^([A-Z])\)\s*(.+)$")
QUESTION_START_RE = re.compile(
    r"^\s*[¿]?\s*(que|como|cuando|donde|quien|quienes|cual|cuales|cuanto|cuanta|cuantos|cuantas)\b",
    re.IGNORECASE,
)

QUESTION_WORDS = {
    "que": "qué",
    "como": "cómo",
    "cuando": "cuándo",
    "donde": "dónde",
    "quien": "quién",
    "quienes": "quiénes",
    "cual": "cuál",
    "cuales": "cuáles",
    "cuanto": "cuánto",
    "cuanta": "cuánta",
    "cuantos": "cuántos",
    "cuantas": "cuántas",
}

COMMON_ACCENT_FIXES = {
    "analisis": "análisis",
    "catalogo": "catálogo",
    "carpinteria": "carpintería",
    "categoria": "categoría",
    "codigo": "código",
    "coleccion": "colección",
    "conexion": "conexión",
    "configuracion": "configuración",
    "decoracion": "decoración",
    "descripcion": "descripción",
    "dimension": "dimensión",
    "electricidad": "electricidad",
    "especificacion": "especificación",
    "fotografia": "fotografía",
    "garantia": "garantía",
    "habitacion": "habitación",
    "herramienta": "herramienta",
    "herramientas": "herramientas",
    "imagen": "imagen",
    "imagenes": "imágenes",
    "informacion": "información",
    "instalacion": "instalación",
    "lampara": "lámpara",
    "linea": "línea",
    "manual": "manual",
    "mas": "más",
    "medicion": "medición",
    "modulo": "módulo",
    "numero": "número",
    "pagina": "página",
    "promocion": "promoción",
    "proteccion": "protección",
    "seccion": "sección",
    "tecnica": "técnica",
    "tecnicas": "técnicas",
    "tecnologia": "tecnología",
    "trafico": "tráfico",
    "ubicacion": "ubicación",
    "valido": "válido",
}

KNOWN_ACRONYMS = {
    "API",
    "CMYK",
    "CPU",
    "DPI",
    "GPU",
    "HDMI",
    "IP",
    "LED",
    "NFC",
    "OCR",
    "PDF",
    "RAM",
    "RGB",
    "SKU",
    "TV",
    "USB",
}

LOWERCASE_TITLE_WORDS = {
    "a",
    "al",
    "con",
    "de",
    "del",
    "e",
    "el",
    "en",
    "la",
    "las",
    "los",
    "o",
    "para",
    "por",
    "sin",
    "u",
    "un",
    "una",
    "unos",
    "unas",
    "y",
}

SINGULAR_ARTICLES = {"el", "la", "un", "una", "este", "esta", "ese", "esa"}
PLURAL_ARTICLES = {"los", "las", "unos", "unas", "estos", "estas", "esos", "esas"}

MOJIBAKE_FIXES = {
    "Ã¡": "á",
    "Ã©": "é",
    "Ã­": "í",
    "Ã³": "ó",
    "Ãº": "ú",
    "Ã¼": "ü",
    "Ã±": "ñ",
    "Â¿": "¿",
    "Â¡": "¡",
}

_CORE_SPANISH_WORDS = """
a al algo algun alguna algunas alguno algunos ante antes aqui asi bajo bola buena bueno buenas
buenos cada caoba carpinteria casa catalogo categoria como con contra cual cuales cuando cuanto
cuanta cuantas cuantos de del desde donde dos el ella ellas ello ellos en entre era eran es esa
esas ese eso esos esta estaba estaban estado estan estar este estos esta estas fue fueron gran
grande hay ideal imagenes la las lo los manual martillo madera mas medida medidas mientras mundo
no nombre o opcion opciones para pero por pregunta preguntas producto productos promocion protección
que quien quienes se sin sobre son su sus tal trabajo trabajos tres tu tus u un una unas uno unos
usar valido y ya
acero actividad adaptador adhesivo ajuste aluminio anclaje andamio angulo arena armario armazon
atornillador barra broca brochas cable cables caja cajas calibre canal canto carretilla cemento
ceramica cierre clavo clavos cola color colores compra compras concreto construccion corte cortar
cubierta cubierta cuchilla cuchillas decoracion destornillador disco discos diseno electricidad
embalaje empaque enchufe enchufes energia equipo equipos escala escuadra estructura exterior ferreteria
fijacion fijaciones pintura placa placas puerta puertas pulgada pulgadas regla repisa repuesto
repuestos resistencia revestimiento sierra soporte soportes tabla tablas taladro tecnica tensor tipo
tipos tornillo tornillos uso usos venta vidrio
carpintería catálogo categoría decoración descripción dimensión energía especificación garantía imágenes
información instalación lámpara línea manual medición módulo número página promoción protección sección
técnica técnicas tecnología tráfico ubicación válido
uña trivia pro
"""


def _normalize_unicode(text: str) -> str:
    normalized = text or ""
    for broken, fixed in MOJIBAKE_FIXES.items():
        normalized = normalized.replace(broken, fixed)
    return unicodedata.normalize("NFC", normalized)


def _strip_accents(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value)
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


def _normalize_key(value: str) -> str:
    return _strip_accents(value).replace("'", "").lower()


SPANISH_WORDS = {_normalize_key(word) for word in _CORE_SPANISH_WORDS.split()}
ACCENT_REPLACEMENTS = {
    **{key: value for key, value in QUESTION_WORDS.items()},
    **{key: value for key, value in COMMON_ACCENT_FIXES.items()},
}


def _is_valid_word(token: str) -> bool:
    if not token:
        return False
    normalized = _normalize_key(token)
    return normalized in SPANISH_WORDS or normalized in ACCENT_REPLACEMENTS


def _restore_case(template: str, replacement: str) -> str:
    if template.isupper():
        return replacement.upper()
    if template.islower():
        return replacement.lower()
    if template.istitle():
        return replacement.capitalize()
    return replacement


def normalize_text(text: str) -> str:
    """Normalize OCR whitespace and punctuation without changing meaning."""
    text = _normalize_unicode(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    quote_map = {
        "“": '"',
        "”": '"',
        "«": '"',
        "»": '"',
        "‘": "'",
        "’": "'",
        "`": "'",
        "´": "'",
    }
    for source, target in quote_map.items():
        text = text.replace(source, target)

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r"([¿¡])\s+", r"\1", text)
    text = re.sub(r"([,.;:])(?=[^\s\n.,;:!?])", r"\1 ", text)
    text = re.sub(r"([!?])(?=[^\s\n!?.,;:])", r"\1 ", text)
    text = re.sub(r"[ ]*\n[ ]*", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _replace_inline_confusions(token: str) -> str:
    token = re.sub(r"(?<=[A-Za-zÁÉÍÓÚÜÑáéíóúüñ])0(?=[A-Za-zÁÉÍÓÚÜÑáéíóúüñ])", "o", token)
    token = re.sub(r"(?<=[A-Za-zÁÉÍÓÚÜÑáéíóúüñ])1(?=[A-Za-zÁÉÍÓÚÜÑáéíóúüñ])", "l", token)
    token = re.sub(r"n'", "ñ", token, flags=re.IGNORECASE)
    return token


def _generate_ocr_variants(token: str) -> list[str]:
    variants: set[str] = set()
    base = token.rstrip("'")

    if base != token:
        for index, char in enumerate(base):
            if char.lower() != "n":
                continue
            replacement = "Ñ" if char.isupper() else "ñ"
            variants.add(base[:index] + replacement + base[index + 1 :])

    for match in re.finditer(r"rn", token, flags=re.IGNORECASE):
        replacement = "M" if token[match.start()].isupper() else "m"
        variants.add(token[: match.start()] + replacement + token[match.end() :])

    for index, char in enumerate(token):
        if char.lower() == "c":
            replacement = "E" if char.isupper() else "e"
            variants.add(token[:index] + replacement + token[index + 1 :])
        elif char.lower() == "e":
            replacement = "C" if char.isupper() else "c"
            variants.add(token[:index] + replacement + token[index + 1 :])

    return [variant for variant in variants if variant and variant != token]


def _choose_best_candidate(original: str, candidates: list[str]) -> str:
    valid_candidates = [candidate for candidate in candidates if _is_valid_word(candidate)]
    if len(valid_candidates) == 1:
        return valid_candidates[0]
    if len(valid_candidates) > 1:
        valid_candidates.sort(key=lambda item: (-len(item), item))
        return valid_candidates[0]
    return original


def _fix_ocr_token(token: str) -> str:
    normalized = _replace_inline_confusions(token)

    if token.endswith("'"):
        enye_candidates = [
            candidate
            for candidate in _generate_ocr_variants(normalized)
            if "ñ" in candidate.lower() and _is_valid_word(candidate)
        ]
        if len(enye_candidates) == 1:
            return enye_candidates[0]

    if _is_valid_word(token) or _is_valid_word(normalized):
        return normalized.rstrip("'")

    candidate = _choose_best_candidate(normalized, _generate_ocr_variants(normalized))
    return candidate.rstrip("'")


def fix_ocr_characters(text: str) -> str:
    """Repair conservative OCR character confusions inside tokens."""
    return TOKEN_RE.sub(lambda match: _fix_ocr_token(match.group(0)), text)


@lru_cache(maxsize=512)
def _segment_indices(token_key: str) -> tuple[int, ...] | None:
    if len(token_key) <= 12 or token_key in SPANISH_WORDS:
        return None

    @lru_cache(maxsize=None)
    def solve(start: int) -> tuple[int, ...] | None:
        if start == len(token_key):
            return ()

        best: tuple[int, ...] | None = None
        for end in range(start + 2, len(token_key) + 1):
            piece = token_key[start:end]
            if piece not in SPANISH_WORDS:
                continue
            remainder = solve(end)
            if remainder is None:
                continue
            candidate = (end,) + remainder
            if best is None or len(candidate) < len(best):
                best = candidate
        return best

    result = solve(0)
    if result is None or len(result) < 2:
        return None
    return result


def _segment_token(token: str) -> str:
    if len(token) <= 12 or not token.isalpha() or _is_valid_word(token):
        return token

    boundaries = _segment_indices(_normalize_key(token))
    if boundaries is None:
        return token

    parts: list[str] = []
    start = 0
    for end in boundaries:
        parts.append(token[start:end])
        start = end
    return " ".join(parts)


def segment_words(text: str) -> str:
    """Split long merged OCR tokens when the resulting words are valid Spanish."""
    return TOKEN_RE.sub(lambda match: _segment_token(match.group(0)), text)


def _iter_blocks(text: str) -> list[list[str]]:
    blocks: list[list[str]] = []
    current: list[str] = []

    for line in text.split("\n"):
        if line.strip():
            current.append(line)
            continue
        if current:
            blocks.append(current)
            current = []
        blocks.append([""])

    if current:
        blocks.append(current)

    return blocks


def _join_blocks(blocks: list[list[str]]) -> str:
    lines: list[str] = []
    for block in blocks:
        if block == [""]:
            lines.append("")
        else:
            lines.extend(block)
    return "\n".join(lines)


def _block_looks_like_question(lines: list[str]) -> bool:
    compact = " ".join(line.strip() for line in lines if line.strip())
    if not compact:
        return False
    if "?" in compact or "¿" in compact:
        return True
    return bool(QUESTION_START_RE.search(_normalize_key(compact)))


def _restore_token_accents(token: str, question_context: bool) -> str:
    key = _normalize_key(token)

    if question_context and key in QUESTION_WORDS:
        return _restore_case(token, QUESTION_WORDS[key])

    replacement = COMMON_ACCENT_FIXES.get(key)
    if replacement:
        return _restore_case(token, replacement)

    return token


def restore_accents(text: str) -> str:
    """Restore common Spanish accents, with extra support for questions."""
    corrected_blocks: list[list[str]] = []
    for block in _iter_blocks(text):
        if block == [""]:
            corrected_blocks.append(block)
            continue

        question_context = _block_looks_like_question(block)
        corrected_blocks.append(
            [
                TOKEN_RE.sub(
                    lambda match: _restore_token_accents(match.group(0), question_context),
                    line,
                )
                for line in block
            ]
        )

    return _join_blocks(corrected_blocks)


def _repair_cual_question(line: str) -> str:
    pattern = re.compile(
        r"^(?P<prefix>\s*[¿]?\s*)(?P<question>cuál|cuáles)(?P<space>\s+)(?P<article>el|la|un|una|los|las|unos|unas)\b",
        re.IGNORECASE,
    )
    match = pattern.match(line)
    if not match:
        return line

    question = match.group("question")
    article = match.group("article")
    article_key = _normalize_key(article)

    if article_key in SINGULAR_ARTICLES:
        replacement_question = _restore_case(question, "cuál")
        verb = _restore_case(question, "es")
    else:
        replacement_question = _restore_case(question, "cuáles")
        verb = _restore_case(question, "son")

    start = match.group("prefix")
    remainder = line[match.end() :]
    return f"{start}{replacement_question} {verb} {article}{remainder}"


def _ensure_opening_question_mark(line: str) -> str:
    stripped = line.lstrip()
    if not stripped or stripped.startswith("¿"):
        return line
    return f"{line[: len(line) - len(stripped)]}¿{stripped.lstrip('?').lstrip()}"


def _ensure_closing_question_mark(line: str) -> str:
    stripped = line.rstrip()
    if not stripped or stripped.endswith("?"):
        return line
    return f"{stripped}?"


def fix_questions(text: str) -> str:
    """Detect question blocks and ensure Spanish question punctuation."""
    corrected_blocks: list[list[str]] = []
    for block in _iter_blocks(text):
        if block == [""] or not _block_looks_like_question(block):
            corrected_blocks.append(block)
            continue

        fixed = block[:]
        fixed[0] = _repair_cual_question(fixed[0])
        fixed[0] = _ensure_opening_question_mark(fixed[0])
        fixed[-1] = _ensure_closing_question_mark(fixed[-1])
        corrected_blocks.append(fixed)

    return _join_blocks(corrected_blocks)


def _is_known_acronym(token: str) -> bool:
    return token.upper() in KNOWN_ACRONYMS


def _sentence_case_fragment(fragment: str, capitalize_first: bool = True) -> str:
    parts = re.split(r"(\W+)", fragment)
    capitalize_next = capitalize_first
    normalized_parts: list[str] = []

    for part in parts:
        if not part:
            continue
        if TOKEN_RE.fullmatch(part):
            token = part
            if _is_known_acronym(token):
                normalized = token.upper()
            else:
                normalized = token.lower()
                if capitalize_next:
                    normalized = normalized[:1].upper() + normalized[1:]
            normalized_parts.append(normalized)
            capitalize_next = False
            continue

        normalized_parts.append(part)
        if re.search(r"[.!?]\s*$", part) or "¿" in part or "¡" in part:
            capitalize_next = True

    return "".join(normalized_parts)


def _title_case_line(line: str) -> str:
    words = re.split(r"(\s+)", line.lower())
    position = 0
    normalized: list[str] = []
    for item in words:
        if not item:
            continue
        if item.isspace():
            normalized.append(item)
            continue
        if _is_known_acronym(item):
            normalized.append(item.upper())
        elif position > 0 and item in LOWERCASE_TITLE_WORDS:
            normalized.append(item)
        else:
            normalized.append(item[:1].upper() + item[1:])
        position += 1
    return "".join(normalized)


def _line_is_mostly_upper(line: str) -> bool:
    letters = [char for char in line if char.isalpha()]
    if not letters:
        return False
    uppercase_count = sum(1 for char in letters if char.isupper())
    return uppercase_count / len(letters) >= 0.8


def _should_title_case_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped or stripped[:1] in {"¿", "¡"}:
        return False
    if stripped.endswith((".", "?", "!", ":", ";")):
        return False
    return len(stripped.split()) <= 4


def normalize_case(text: str) -> str:
    """Convert obvious OCR shouting to sentence case while preserving acronyms."""
    normalized_lines: list[str] = []
    continue_sentence = False
    for line in text.split("\n"):
        if not line.strip():
            normalized_lines.append("")
            continue_sentence = False
            continue

        list_match = LIST_OPTION_RE.match(line.strip())
        if list_match:
            marker, content = list_match.groups()
            normalized_lines.append(f"{marker}) {_sentence_case_fragment(content)}")
            continue_sentence = False
            continue

        if _line_is_mostly_upper(line):
            if _should_title_case_line(line) and not continue_sentence:
                normalized_lines.append(_title_case_line(line))
            else:
                normalized_lines.append(
                    _sentence_case_fragment(line, capitalize_first=not continue_sentence)
                )
            continue_sentence = not line.rstrip().endswith((".", "?", "!", ":"))
            continue

        if line == line.lower():
            normalized_lines.append(_sentence_case_fragment(line, capitalize_first=not continue_sentence))
            continue_sentence = not line.rstrip().endswith((".", "?", "!", ":"))
            continue

        normalized_lines.append(line)
        continue_sentence = not line.rstrip().endswith((".", "?", "!", ":"))

    return "\n".join(normalized_lines)


def correct_text(raw_text: str) -> str:
    """Return a safer, corrected version of the OCR text without changing raw text."""
    return structured_correct_text(raw_text)


def estimate_correction_ratio(raw_text: str, corrected_text: str) -> float:
    """Estimate how much the corrected version differs from the raw OCR text."""
    raw_tokens = TOKEN_RE.findall(raw_text or "")
    corrected_tokens = TOKEN_RE.findall(corrected_text or "")
    total = max(len(raw_tokens), len(corrected_tokens), 1)

    changed = 0
    for index in range(total):
        raw_token = raw_tokens[index].lower() if index < len(raw_tokens) else ""
        corrected_token = corrected_tokens[index].lower() if index < len(corrected_tokens) else ""
        if raw_token != corrected_token:
            changed += 1

    if not ALPHA_RE.search(corrected_text or "") and not ALPHA_RE.search(raw_text or ""):
        return 0.0

    return float(min(max(changed / total, 0.0), 1.0))
