from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from doc_converter.formulas import get_known_formula_representation, get_noisy_form_recovery

FORMULA_RE = re.compile(r"(^|\s)[A-Za-zА-Яа-я][\wА-Яа-я]*\s*=|[=∑√≤≥±×÷≈]|\b(sum|sqrt|frac)\b", re.IGNORECASE)
FORMULA_CONTINUATION_OPERATORS = "+-x×÷*/="
FORMULA_IDENTIFIER_TOKEN_RE = re.compile(r"[A-Za-zА-Яа-я][A-Za-zА-Яа-я0-9]*(?:_\([^()]+\))?(?:\^\([^()]+\))?")
FORMULA_NUMBER_TOKEN_RE = re.compile(r"\d+(?:[.,]\d+)?")
FORMULA_LINE_WRAP_OPERATOR_RE = re.compile(
    rf"([{re.escape(FORMULA_CONTINUATION_OPERATORS)}])\s*(?:\r?\n)+\s*\1"
)
FORMULA_ASCII_MULTIPLY_RE = re.compile(
    r"(?<=[\)\]A-Za-zА-Яа-я0-9])\s+[xX]\s+(?=[\(\[A-Za-zА-Яа-я0-9])"
)
FORMULA_REPEAT_MULTIPLY_RE = re.compile(
    r"(?<=[\)\]A-Za-zА-Яа-я0-9])\s+(?:[×xX]\s+){1,}[×xX]\s+(?=[\(\[A-Za-zА-Яа-я0-9])"
)
FORMULA_TRAILING_REFERENCE_RE = re.compile(r"\s*[,;]?\s*\([0-9]+(?:\.[0-9]+)*\),?\s*$")
FORMULA_TRAILING_PUNCTUATION_RE = re.compile(r"\s*[,;]\s*$")
FORMULA_INLINE_DIVISION_RE = re.compile(
    r"(?<=[\)\]A-Za-zА-Яа-я0-9])\s*:\s*(?=[\(\[A-Za-zА-Яа-я0-9])"
)
CYRILLIC_TO_LATIN = {
    "А": "A",
    "Б": "B",
    "В": "V",
    "Г": "G",
    "Д": "D",
    "Е": "E",
    "Ё": "E",
    "Ж": "Zh",
    "З": "Z",
    "И": "I",
    "Й": "Y",
    "К": "K",
    "Л": "L",
    "М": "M",
    "Н": "N",
    "О": "O",
    "П": "P",
    "Р": "R",
    "С": "S",
    "Т": "T",
    "У": "U",
    "Ф": "F",
    "Х": "Kh",
    "Ц": "Ts",
    "Ч": "Ch",
    "Ш": "Sh",
    "Щ": "Shch",
    "Ъ": "",
    "Ы": "Y",
    "Ь": "",
    "Э": "E",
    "Ю": "Yu",
    "Я": "Ya",
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "e",
    "ж": "zh",
    "з": "z",
    "и": "i",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "kh",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "shch",
    "ъ": "",
    "ы": "y",
    "ь": "",
    "э": "e",
    "ю": "yu",
    "я": "ya",
}


def _formula_representation_from_text(text: str) -> dict[str, Any] | None:
    normalized = _recover_known_formula_linear_text(_normalize_formula_linear_text(text))
    known = _known_formula_representation(normalized)
    if known is not None:
        return _with_formula_provenance(known)

    range_match = re.fullmatch(r"([A-Za-zА-Яа-я]+)\s*=\s*1\s*÷\s*([A-Za-zА-Яа-я]+)", normalized)
    if range_match is not None:
        left, right = range_match.groups()
        return _with_formula_provenance(
            {
                "source_format": "mathtype_wmf_text_records",
                "linear_text": normalized,
                "display_latex": f"{_latex_identifier(left)} = 1 \\div {_latex_identifier(right)}",
                "calc_expr": None,
                "variables": {},
                "confidence": "high",
                "warnings": [],
            }
        )

    if any(marker in normalized for marker in ("_(", "^(", "=", "∑", "×", "÷")):
        heuristic_calc = _linear_formula_text_to_calc_expr(normalized)
        warnings = ["formula_display_latex_is_heuristic"]
        calc_expr = None
        variables: dict[str, str] = {}
        if heuristic_calc is not None:
            calc_expr, variables = heuristic_calc
            warnings.extend(
                [
                    "formula_calc_expr_is_heuristic",
                    "calculation_expression_requires_domain_variable_binding",
                ]
            )
        return _with_formula_provenance(
            {
                "source_format": "docx_text_linearized",
                "linear_text": normalized,
                "display_latex": _linear_formula_text_to_latex(normalized),
                "calc_expr": calc_expr,
                "variables": variables,
                "confidence": "low",
                "warnings": warnings,
            }
        )
    return None


def _with_formula_provenance(representation: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(representation)
    if isinstance(result.get("provenance"), dict):
        return result

    source_format = result.get("source_format")
    warnings = result.get("warnings")
    warning_set = {item for item in warnings if isinstance(item, str)} if isinstance(warnings, list) else set()
    if source_format == "mathtype_wmf_text_records":
        parser_path = "mathtype_wmf_known_pattern" if "formula_native_wmf_pattern_recovered" in warning_set else "mathtype_wmf_text_records"
        confidence_basis = "native_wmf_text_records"
    else:
        parser_path = "docx_text_heuristic"
        confidence_basis = "heuristic_text_normalization"

    result["provenance"] = {
        "parser_path": parser_path,
        "normalization": "formula_text_v1",
        "confidence_basis": confidence_basis,
    }
    return result


def _normalize_formula_linear_text(text: str) -> str:
    normalized = FORMULA_TRAILING_REFERENCE_RE.sub("", text.strip())
    normalized = re.sub(r"\s*,?\s*где:\s*$", "", normalized, flags=re.IGNORECASE)
    normalized = FORMULA_LINE_WRAP_OPERATOR_RE.sub(r"\1", normalized)
    normalized = _strip_formula_trailing_punctuation(normalized)
    return re.sub(r"\s+", " ", normalized)


def _recover_known_formula_linear_text(normalized: str) -> str:
    noisy_forms = get_noisy_form_recovery()
    return noisy_forms.get(normalized, normalized)


def _known_formula_representation(normalized: str) -> dict[str, Any] | None:
    return get_known_formula_representation(normalized)


def _linear_formula_text_to_latex(text: str) -> str:
    result = _normalize_formula_operator_text(text)
    result = result.replace("×", r" \times ").replace("÷", r" \div ")
    result = result.replace("%", r"\%")
    result = re.sub(r"\bsum_\(([^=()]+)=([^()]+)\)\^([A-Za-zА-Яа-я0-9]+)", _latex_sum_replacement, result)
    result = re.sub(r"([A-Za-zА-Яа-я][A-Za-zА-Яа-я0-9]*)_\(([^()]+)\)\^\(([^()]+)\)", _latex_sub_sup_replacement, result)
    result = re.sub(r"([A-Za-zА-Яа-я][A-Za-zА-Яа-я0-9]*)_\(([^()]+)\)", _latex_sub_replacement, result)
    result = re.sub(r"([A-Za-zА-Яа-я][A-Za-zА-Яа-я0-9]*)\^\(([^()]+)\)", _latex_sup_replacement, result)
    return result


def _linear_formula_text_to_calc_expr(text: str) -> tuple[str, dict[str, str]] | None:
    normalized = _normalize_formula_operator_text(text)
    if "sum_(" in normalized or "∑" in normalized:
        return None

    for candidate in _formula_calc_candidates(normalized):
        assignment_result = _linear_formula_assignment_to_calc_expr(candidate)
        if assignment_result is not None:
            return assignment_result
        expression_result = _linear_formula_expression_to_calc_expr(candidate)
        if expression_result is not None:
            return expression_result
    return None


def _formula_calc_candidates(text: str) -> list[str]:
    candidates: list[str] = []
    seen: set[str] = set()

    def add(candidate: str) -> None:
        normalized_candidate = _strip_formula_trailing_punctuation(candidate).strip()
        if normalized_candidate and normalized_candidate not in seen:
            seen.add(normalized_candidate)
            candidates.append(normalized_candidate)

    add(text)
    stripped_prefix = _strip_formula_narrative_prefix(text)
    if stripped_prefix != text.strip():
        add(stripped_prefix)

    for candidate in tuple(candidates):
        for clause in _formula_semicolon_clauses(candidate):
            add(clause)
            stripped_clause = _strip_formula_narrative_prefix(clause)
            if stripped_clause != clause:
                add(stripped_clause)

        for nested_formula in _extract_parenthesized_formula_candidates(candidate):
            add(nested_formula)

        if "=" not in candidate:
            continue
        parts = [_strip_formula_trailing_punctuation(part).strip() for part in candidate.split("=")]
        for part in reversed(parts[:-1]):
            if not part:
                continue
            stripped_part = _strip_formula_narrative_prefix(part)
            if stripped_part != part:
                add(stripped_part)
                continue
            add(part)

    return candidates


def _linear_formula_assignment_to_calc_expr(text: str) -> tuple[str, dict[str, str]] | None:
    if "=" not in text:
        return None

    left_text, right_text = (_strip_formula_trailing_punctuation(part).strip() for part in text.split("=", 1))
    left_match = FORMULA_IDENTIFIER_TOKEN_RE.fullmatch(left_text)
    if left_match is None:
        return None

    left_key = _formula_symbol_key(left_text)
    left_calc_name = _formula_symbol_to_calc_identifier(left_text)
    if not left_key or not left_calc_name:
        return None

    right_expr, variables = _tokenize_formula_expression(_normalize_formula_expression_candidate(right_text))
    if right_expr is None:
        return None

    variables = {left_key: left_calc_name, **variables}
    return f"{left_calc_name} = {right_expr}", variables


def _linear_formula_expression_to_calc_expr(text: str) -> tuple[str, dict[str, str]] | None:
    if "=" in text:
        return None

    expression_text = _normalize_formula_expression_candidate(text)
    expression, variables = _tokenize_formula_expression(expression_text)
    if expression is None:
        return None
    if not any(operator in expression for operator in (" + ", " - ", " * ", " / ", " ** ")):
        return None
    return expression, variables


def _strip_formula_narrative_prefix(text: str) -> str:
    stripped = text.strip()
    if ":" not in stripped:
        return stripped

    prefix, suffix = stripped.split(":", 1)
    if not re.search(r"[A-Za-zА-Яа-я]", prefix):
        return stripped
    if not any(marker in suffix for marker in ("=", "+", "-", "*", "/", "×", "÷", "^", "%", "(", ")", "x", "X")):
        return stripped
    return suffix.strip()


def _formula_semicolon_clauses(text: str) -> list[str]:
    clauses: list[str] = []
    for clause in text.split(";"):
        normalized_clause = _strip_formula_trailing_punctuation(clause).strip()
        if "=" in normalized_clause:
            clauses.append(normalized_clause)
    return clauses


def _extract_parenthesized_formula_candidates(text: str) -> list[str]:
    candidates: list[str] = []
    stack: list[int] = []
    start_index: int | None = None

    for index, char in enumerate(text):
        if char == "(":
            if not stack:
                start_index = index + 1
            stack.append(index)
            continue
        if char != ")" or not stack:
            continue
        stack.pop()
        if stack or start_index is None:
            continue
        candidate = _strip_formula_trailing_punctuation(text[start_index:index]).strip()
        if "=" in candidate:
            candidates.append(candidate)
        start_index = None

    return candidates


def _normalize_formula_expression_candidate(text: str) -> str:
    normalized = FORMULA_INLINE_DIVISION_RE.sub(" ÷ ", text.strip())
    normalized = normalized.replace("[", "(").replace("]", ")")
    return _strip_formula_trailing_punctuation(normalized)


def _strip_formula_trailing_punctuation(text: str) -> str:
    return FORMULA_TRAILING_PUNCTUATION_RE.sub("", text.strip())


def _tokenize_formula_expression(text: str) -> tuple[str | None, dict[str, str]]:
    tokens: list[str] = []
    variables: dict[str, str] = {}
    position = 0

    while position < len(text):
        char = text[position]
        if char.isspace():
            position += 1
            continue

        number_match = FORMULA_NUMBER_TOKEN_RE.match(text, position)
        if number_match is not None:
            tokens.append(number_match.group(0).replace(",", "."))
            position = number_match.end()
            continue

        identifier_match = FORMULA_IDENTIFIER_TOKEN_RE.match(text, position)
        if identifier_match is not None:
            raw_identifier = identifier_match.group(0)
            symbol_key = _formula_symbol_key(raw_identifier)
            calc_identifier = _formula_symbol_to_calc_identifier(raw_identifier)
            if not symbol_key or not calc_identifier:
                return None, {}
            variables.setdefault(symbol_key, calc_identifier)
            tokens.append(calc_identifier)
            position = identifier_match.end()
            continue

        if char in "+-*/()":
            tokens.append(char)
            position += 1
            continue

        if char == "^":
            tokens.append("**")
            position += 1
            continue

        if char == "×":
            tokens.append("*")
            position += 1
            continue

        if char == "÷":
            tokens.append("/")
            position += 1
            continue

        if char == "%":
            if not tokens or tokens[-1] in {"+", "-", "*", "/", "**", "("}:
                return None, {}
            tokens.extend(["/", "100"])
            position += 1
            continue

        return None, {}

    if not tokens:
        return None, {}
    return " ".join(tokens), variables


def _normalize_formula_operator_text(text: str) -> str:
    normalized = FORMULA_ASCII_MULTIPLY_RE.sub(" × ", text)
    return FORMULA_REPEAT_MULTIPLY_RE.sub(" × ", normalized)


def _formula_symbol_key(value: str) -> str:
    parsed = _parse_formula_identifier(value)
    if parsed is None:
        return ""
    base, subscript, superscript = parsed
    parts = [_sanitize_formula_symbol_part(base)]
    if subscript:
        parts.append(_sanitize_formula_symbol_part(subscript))
    if superscript:
        parts.append(_sanitize_formula_symbol_part(superscript))
    return "_".join(part for part in parts if part)


def _formula_symbol_to_calc_identifier(value: str) -> str:
    symbol_key = _formula_symbol_key(value)
    if not symbol_key:
        return ""

    transliterated_parts: list[str] = []
    for char in symbol_key:
        if char == "_":
            transliterated_parts.append("_")
        elif char.isascii() and char.isalnum():
            transliterated_parts.append(char)
        else:
            transliterated_parts.append(CYRILLIC_TO_LATIN.get(char, "_"))

    normalized = re.sub(r"_+", "_", "".join(transliterated_parts)).strip("_")
    if not normalized:
        return ""
    if normalized[0].isdigit():
        normalized = f"v_{normalized}"
    return normalized


def _sanitize_formula_symbol_part(value: str) -> str:
    return re.sub(r"_+", "_", re.sub(r"[^0-9A-Za-zА-Яа-я]+", "_", value)).strip("_")


def _parse_formula_identifier(value: str) -> tuple[str, str | None, str | None] | None:
    match = re.fullmatch(r"([A-Za-zА-Яа-я][A-Za-zА-Яа-я0-9]*)(?:_\(([^()]+)\))?(?:\^\(([^()]+)\))?", value)
    if match is None:
        return None
    return match.group(1), match.group(2), match.group(3)


def _latex_sum_replacement(match: re.Match[str]) -> str:
    index_name = match.group(1).strip()
    start = match.group(2).strip()
    end = match.group(3).strip()
    return rf"\sum_{{{index_name}={start}}}^{{{end}}}"


def _latex_sub_replacement(match: re.Match[str]) -> str:
    return f"{_latex_identifier(match.group(1))}_{{{_latex_script(match.group(2))}}}"


def _latex_sup_replacement(match: re.Match[str]) -> str:
    return f"{_latex_identifier(match.group(1))}^{{{_latex_script(match.group(2))}}}"


def _latex_sub_sup_replacement(match: re.Match[str]) -> str:
    return (
        f"{_latex_identifier(match.group(1))}_{{{_latex_script(match.group(2))}}}"
        f"^{{{_latex_script(match.group(3))}}}"
    )


def _latex_identifier(value: str) -> str:
    if re.fullmatch(r"[A-Za-z]", value):
        return value
    return rf"\mathrm{{{value}}}"


def _latex_script(value: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9]+", value):
        return value
    return rf"\text{{{value}}}"


def _trailing_formula_operator(text: str) -> str | None:
    stripped = text.rstrip()
    if stripped and stripped[-1] in FORMULA_CONTINUATION_OPERATORS:
        return stripped[-1]
    return None


def _looks_like_formula_continuation(text: str, trailing_operator: str) -> bool:
    return text.startswith(trailing_operator) or text.startswith(("(", "[", "{"))


def _merge_formula_text(previous_text: str, continuation_text: str, trailing_operator: str) -> str:
    remainder = continuation_text
    if remainder.startswith(trailing_operator):
        remainder = remainder[1:].lstrip()
    return f"{previous_text.rstrip()} {remainder}".strip()


def _looks_like_formula_text(text: str) -> bool:
    stripped = text.strip()
    if len(stripped) > 180:
        return False
    return bool(FORMULA_RE.search(stripped))
