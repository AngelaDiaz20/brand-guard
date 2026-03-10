"""Structured post-processing for OCR text."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

TOKEN_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9']+", re.UNICODE)
ALPHA_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]", re.UNICODE)
ANSWER_OPTION_RE = re.compile(r"^\s*([A-Z])\)\s*(.+?)\s*$")
INTERROGATIVE_RE = re.compile(
    r"\b(que|cual|cuales|como|donde|cuando|por\s+que|quien|quienes)\b",
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
    "por que": "por qué",
}

ACCENT_FIXES = {
    "analisis": "análisis",
    "carpinteria": "carpintería",
    "catalogo": "catálogo",
    "categoria": "categoría",
    "coleccion": "colección",
    "conexion": "conexión",
    "configuracion": "configuración",
    "cuál": "cuál",
    "cual": "cuál",
    "cuales": "cuáles",
    "decoracion": "decoración",
    "descripcion": "descripción",
    "dimension": "dimensión",
    "especificacion": "especificación",
    "garantia": "garantía",
    "habitacion": "habitación",
    "imagenes": "imágenes",
    "imagen": "imagen",
    "informacion": "información",
    "instalacion": "instalación",
    "japones": "japonés",
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
    "que": "qué",
    "seccion": "sección",
    "tecnica": "técnica",
    "tecnicas": "técnicas",
    "tecnologia": "tecnología",
    "trafico": "tráfico",
    "uña": "uña",
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

TITLE_BLOCKER_WORDS = {
    "a",
    "al",
    "con",
    "de",
    "del",
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
    "y",
}

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

CORE_SPANISH_WORDS = """
a al algo algun alguna algunas alguno algunos ante antes aqui asi baja bajo bola caoba carpinteria
carpintero carpinteros catalogo categoria como con contra cual cuales cuando de del donde el en es
esta este goma ideal imagen la las los manual madera martillo mundo no o para por pro pregunta
preguntas que quien quienes se sin sobre son su sus tal tipo trabajos trivia u una unas uno unos
uso y ya japones japonesa japoneses uña
acero adhesivo ajuste aluminio anclaje andamio arena armario armazon atornillador barra broca brochas
cable cables caja cajas calibre canal canto carretilla cemento ceramica cierre clavo clavos cola
color colores compra compras concreto construccion corte cortar cubierta cuchilla cuchillas decoracion
destornillador disco discos diseno electricidad embalaje empaque enchufe enchufes energia equipo equipos
escala escuadra estructura exterior ferreteria fijacion fijaciones herramienta herramientas instalacion
lampara linea medicion modulo numero pagina promocion proteccion seccion sierra soporte soportes tabla
tablas taladro tecnica tensor tornillo tornillos trabajo venta vidrio
carpintería catálogo categoría decoración descripción dimensión energía especificación garantía imágenes
información instalación lámpara línea medición módulo número página promoción protección sección técnica
técnicas tecnología tráfico ubicación válido japonés cuál cuáles qué dónde cómo cuándo por qué
"""


class LineKind(str, Enum):
    BLANK = "BLANK"
    TITLE = "TITLE"
    QUESTION = "QUESTION"
    ANSWER_OPTION = "ANSWER_OPTION"
    NORMAL_TEXT = "NORMAL_TEXT"


@dataclass(frozen=True)
class StructuredLine:
    text: str
    kind: LineKind


def _normalize_unicode(text: str) -> str:
    normalized = text or ""
    for broken, fixed in MOJIBAKE_FIXES.items():
        normalized = normalized.replace(broken, fixed)
    return unicodedata.normalize("NFC", normalized)


def _strip_accents(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value)
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


def _normalize_key(value: str) -> str:
    return _strip_accents(value).replace("'", "").lower().strip()


SPANISH_WORDS = {_normalize_key(word) for word in CORE_SPANISH_WORDS.split()}


@lru_cache(maxsize=1)
def _get_optional_spacy_tokenizer() -> object | None:
    try:
        import spacy

        return spacy.blank("es")
    except Exception:
        return None


def normalize_text(text: str) -> str:
    normalized = _normalize_unicode(text)
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")

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
        normalized = normalized.replace(source, target)

    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = re.sub(r"\s+([,.;:!?])", r"\1", normalized)
    normalized = re.sub(r"([¿¡])\s+", r"\1", normalized)
    normalized = re.sub(r"([,.;:])(?=[^\s\n.,;:!?])", r"\1 ", normalized)
    normalized = re.sub(r"([!?])(?=[^\s\n!?.,;:\"])", r"\1 ", normalized)
    normalized = re.sub(r"[ ]*\n[ ]*", "\n", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def split_lines(text: str) -> list[str]:
    if not text:
        return []
    return [line.strip() for line in text.split("\n")]


def _is_mostly_upper(text: str) -> bool:
    letters = [char for char in text if char.isalpha()]
    if not letters:
        return False
    uppercase_count = sum(1 for char in letters if char.isupper())
    return uppercase_count / len(letters) >= 0.75


def _word_count(text: str) -> int:
    tokenizer = _get_optional_spacy_tokenizer()
    if tokenizer is not None:
        return sum(1 for token in tokenizer.make_doc(text) if token.is_alpha)
    return len([token for token in TOKEN_RE.findall(text) if token.strip()])


def _looks_like_question(text: str) -> bool:
    if "?" in text or "¿" in text:
        return True
    compact = _normalize_key(text)
    return bool(INTERROGATIVE_RE.search(compact))


def classify_line(text: str) -> LineKind:
    if not text:
        return LineKind.BLANK
    if ANSWER_OPTION_RE.match(text):
        return LineKind.ANSWER_OPTION
    if _looks_like_question(text):
        return LineKind.QUESTION
    words = [token for token in TOKEN_RE.findall(text) if token.strip()]
    first_word = _normalize_key(words[0]) if words else ""
    if (
        _word_count(text) <= 4
        and _is_mostly_upper(text)
        and not text.endswith(("?", "!", ".", ",", ";", ":"))
        and first_word not in TITLE_BLOCKER_WORDS
    ):
        return LineKind.TITLE
    return LineKind.NORMAL_TEXT


def _restore_case(template: str, replacement: str) -> str:
    if template.isupper():
        return replacement.upper()
    if template.islower():
        return replacement.lower()
    if template.istitle():
        return replacement.capitalize()
    return replacement


def _is_valid_word(token: str) -> bool:
    if not token:
        return False
    normalized = _normalize_key(token)
    return normalized in SPANISH_WORDS or normalized in ACCENT_FIXES


def _replace_inline_confusions(token: str) -> str:
    chars = list(token)
    for index, char in enumerate(chars):
        if char not in {"0", "1"}:
            continue
        prev_char = chars[index - 1] if index > 0 else ""
        next_char = chars[index + 1] if index + 1 < len(chars) else ""
        if not (prev_char.isalpha() and next_char.isalpha()):
            continue
        if char == "0":
            chars[index] = "O" if prev_char.isupper() and next_char.isupper() else "o"
        else:
            chars[index] = "l"

    normalized = "".join(chars)
    normalized = re.sub(r"n'", "ñ", normalized, flags=re.IGNORECASE)
    return normalized


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

    if _is_valid_word(normalized):
        return normalized.rstrip("'")

    candidate = _choose_best_candidate(normalized, _generate_ocr_variants(normalized))
    return candidate.rstrip("'")


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


def _apply_token_corrections(text: str) -> str:
    corrected = TOKEN_RE.sub(lambda match: _fix_ocr_token(match.group(0)), text)
    return TOKEN_RE.sub(lambda match: _segment_token(match.group(0)), corrected)


def _restore_token_accents(token: str, *, question_context: bool = False) -> str:
    key = _normalize_key(token)

    if question_context and key in QUESTION_WORDS:
        return _restore_case(token, QUESTION_WORDS[key])

    replacement = ACCENT_FIXES.get(key)
    if replacement:
        return _restore_case(token, replacement)

    return token


def _restore_accents(text: str, *, question_context: bool = False) -> str:
    return TOKEN_RE.sub(
        lambda match: _restore_token_accents(match.group(0), question_context=question_context),
        text,
    )


def _sentence_case_text(text: str) -> str:
    parts = re.split(r"(\W+)", text)
    capitalize_next = True
    normalized_parts: list[str] = []

    for part in parts:
        if not part:
            continue
        if TOKEN_RE.fullmatch(part):
            if part.upper() in KNOWN_ACRONYMS:
                normalized = part.upper()
            else:
                normalized = part.lower()
            if capitalize_next and normalized:
                normalized = normalized[:1].upper() + normalized[1:]
            normalized_parts.append(normalized)
            capitalize_next = False
            continue

        normalized_parts.append(part)
        if "¿" in part or "¡" in part or re.search(r"[.!?]\s*$", part):
            capitalize_next = True

    return "".join(normalized_parts)


def _fix_question_opening(text: str) -> str:
    normalized = text.lstrip()
    prefix = text[: len(text) - len(normalized)]
    if normalized.startswith("¿"):
        return text
    normalized = normalized.lstrip("?").lstrip()
    return f"{prefix}¿{normalized}"


def _fix_question_closing(text: str) -> str:
    stripped = text.rstrip()
    suffix = text[len(stripped) :]
    if stripped.endswith("?"):
        return text

    punctuation_match = re.search(r'([.!,:;"]+)$', stripped)
    if punctuation_match:
        terminal = punctuation_match.group(1)
        if '"' in terminal and not terminal.endswith('"'):
            return f"{stripped}?"
        head = stripped[: punctuation_match.start()]
        if terminal.endswith('"'):
            return f"{head}{terminal}?" + suffix

    return f"{stripped}?" + suffix


def _repair_question_grammar(text: str) -> str:
    repaired = re.sub(
        r"^(¿?\s*)cu[aá]les\s+(el|la|un|una)\b",
        lambda match: f"{match.group(1)}Cuál es {match.group(2)}",
        text,
        flags=re.IGNORECASE,
    )
    repaired = re.sub(
        r"^(¿?\s*)cu[aá]l\s+(el|la|un|una)\b",
        lambda match: f"{match.group(1)}Cuál es {match.group(2)}",
        repaired,
        flags=re.IGNORECASE,
    )
    repaired = re.sub(
        r"^(¿?\s*)cu[aá]les\s+(los|las|unos|unas)\b",
        lambda match: f"{match.group(1)}Cuáles son {match.group(2)}",
        repaired,
        flags=re.IGNORECASE,
    )
    repaired = re.sub(
        r"^(¿?\s*)cu[aá]l\s+(los|las|unos|unas)\b",
        lambda match: f"{match.group(1)}Cuáles son {match.group(2)}",
        repaired,
        flags=re.IGNORECASE,
    )
    repaired = re.sub(
        r"^(¿?\s*)qu[eé]\s+es\b",
        lambda match: f"{match.group(1)}Qué es",
        repaired,
        flags=re.IGNORECASE,
    )
    return repaired


def _balance_quotes(text: str) -> str:
    if text.count('"') % 2 == 0:
        return text

    punctuation_match = re.search(r"([?!.,;:]+)$", text)
    if punctuation_match:
        start = punctuation_match.start()
        return f'{text[:start]}"{text[start:]}'

    return f'{text}"'


def _normalize_output_spacing(text: str) -> str:
    normalized = normalize_text(text)
    normalized = re.sub(r'"\s+([,.;:?!])', r'"\1', normalized)
    normalized = re.sub(r'(?<=[\w\)])"(?=\w)', ' "', normalized)
    return normalized


def _correct_title(text: str) -> str:
    corrected = _apply_token_corrections(text)
    corrected = _restore_accents(corrected)
    corrected = _balance_quotes(corrected)
    return _normalize_output_spacing(corrected.upper())


def _correct_answer_option(text: str) -> str:
    match = ANSWER_OPTION_RE.match(text)
    if not match:
        return text
    marker, content = match.groups()
    corrected = _apply_token_corrections(content)
    corrected = _restore_accents(corrected)
    corrected = _balance_quotes(corrected)
    return _normalize_output_spacing(f"{marker}) {corrected.upper()}")


def _correct_normal_text(text: str) -> str:
    corrected = _apply_token_corrections(text)
    corrected = _restore_accents(corrected)
    corrected = _balance_quotes(corrected)
    if _is_mostly_upper(text) and _word_count(text) > 4:
        corrected = _sentence_case_text(corrected)
    return _normalize_output_spacing(corrected)


def _correct_question(lines: list[str]) -> str:
    merged = " ".join(line for line in lines if line)
    corrected = _apply_token_corrections(merged)
    corrected = _restore_accents(corrected, question_context=True)
    corrected = _repair_question_grammar(corrected)
    corrected = _sentence_case_text(corrected)
    corrected = _balance_quotes(corrected)
    corrected = _fix_question_opening(corrected)
    corrected = _fix_question_closing(corrected)
    return _normalize_output_spacing(corrected)


def _should_continue_question(current: list[str], next_line: StructuredLine) -> bool:
    if next_line.kind in {LineKind.BLANK, LineKind.TITLE, LineKind.ANSWER_OPTION}:
        return False
    joined = " ".join(current)
    if joined.rstrip().endswith("?"):
        return False
    return True


def _structure_lines(lines: list[str]) -> list[StructuredLine]:
    return [StructuredLine(text=line, kind=classify_line(line)) for line in lines]


def _insert_block_spacing(lines: list[StructuredLine]) -> list[str]:
    output: list[str] = []
    previous_kind: LineKind | None = None

    for line in lines:
        if line.kind == LineKind.BLANK:
            if output and output[-1] != "":
                output.append("")
            previous_kind = None
            continue

        if output:
            if previous_kind == LineKind.TITLE and line.kind != LineKind.TITLE and output[-1] != "":
                output.append("")
            elif previous_kind == LineKind.QUESTION and line.kind == LineKind.ANSWER_OPTION and output[-1] != "":
                output.append("")

        output.append(line.text)
        previous_kind = line.kind

    while output and output[-1] == "":
        output.pop()
    return output


def correct_text(raw_text: str) -> str:
    normalized = normalize_text(raw_text)
    if not normalized:
        return ""

    input_lines = split_lines(normalized)
    structured = _structure_lines(input_lines)
    corrected_lines: list[StructuredLine] = []

    index = 0
    while index < len(structured):
        current = structured[index]

        if current.kind == LineKind.BLANK:
            corrected_lines.append(current)
            index += 1
            continue

        if current.kind == LineKind.QUESTION:
            question_lines = [current.text]
            next_index = index + 1
            while next_index < len(structured) and _should_continue_question(
                question_lines,
                structured[next_index],
            ):
                question_lines.append(structured[next_index].text)
                next_index += 1

            corrected_lines.append(
                StructuredLine(text=_correct_question(question_lines), kind=LineKind.QUESTION)
            )
            index = next_index
            continue

        if current.kind == LineKind.TITLE:
            corrected_lines.append(
                StructuredLine(text=_correct_title(current.text), kind=LineKind.TITLE)
            )
            index += 1
            continue

        if current.kind == LineKind.ANSWER_OPTION:
            corrected_lines.append(
                StructuredLine(
                    text=_correct_answer_option(current.text),
                    kind=LineKind.ANSWER_OPTION,
                )
            )
            index += 1
            continue

        corrected_lines.append(
            StructuredLine(text=_correct_normal_text(current.text), kind=LineKind.NORMAL_TEXT)
        )
        index += 1

    return "\n".join(_insert_block_spacing(corrected_lines)).strip()


def estimate_correction_ratio(raw_text: str, corrected_text: str) -> float:
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
