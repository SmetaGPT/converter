from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable

TITLE_LINE_LIMIT = 10
SUMMARY_CHAR_LIMIT = 500

DOCUMENT_TYPE_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("федеральный закон", (r"\bфедеральн(?:ый|ого)\s+закон\b",)),
    ("технический регламент", (r"\bтехническ(?:ий|ого)\s+регламент\b",)),
    ("постановление", (r"\bпостановлени[ея]\b",)),
    ("распоряжение", (r"\bраспоряжени[ея]\b",)),
    ("приказ", (r"\bприказ\b",)),
    ("письмо", (r"\bписьмо\b",)),
    ("указ", (r"\bуказ\b",)),
    ("решение", (r"\bрешени[ея]\b",)),
    ("регламент", (r"\bрегламент\b",)),
    ("свод правил", (r"\bсвод\s+правил\b", r"(?<![A-Za-zА-Яа-яЁё])сп(?![A-Za-zА-Яа-яЁё])")),
    ("гост", (r"(?<![A-Za-zА-Яа-яЁё])гост(?![A-Za-zА-Яа-яЁё])",)),
    ("санпин", (r"(?<![A-Za-zА-Яа-яЁё])санпин(?![A-Za-zА-Яа-яЁё])",)),
    ("закон", (r"\bзакон\b",)),
    ("кодекс", (r"\bкодекс\b",)),
    ("методические указания", (r"\bметодическ(?:ие|их)\s+указан",)),
    ("методические рекомендации", (r"\bметодическ(?:ие|их)\s+рекомендац",)),
    ("методическое пособие", (r"\bметодическ(?:ое|ого)\s+пособи[ея]\b",)),
    ("методика", (r"\bметодик[аиуе]?\b",)),
)

SUBJECT_STOP_PATTERNS = (
    r"^в\s+соответствии\b",
    r"^приказываю\b",
    r"^постановляет\b",
    r"^постановляю\b",
    r"^утвердить\b",
    r"^1[.)]\s+",
)


def build_document_metadata(*, filename: str, units: Iterable[Any], search_text: str) -> dict[str, str]:
    text_lines = _unit_text_lines(units)
    if not text_lines:
        text_lines = _split_text_lines(search_text)

    title_lines = _title_lines(text_lines)
    fallback_title = Path(filename).stem.strip() or filename
    title = _select_title(fallback_title, title_lines)
    document_type = _classify_from_header(filename, title_lines, title)
    if document_type == "unknown":
        document_type = _classify_document_type([search_text[:1000]])
    subject = _subject_from_title_lines(title_lines, document_type) or _subject_from_filename(filename) or title
    short_summary = _summary(document_type, subject)
    confidence = _confidence(document_type, title_lines, subject, title)

    return {
        "title": title,
        "document_type": document_type,
        "short_summary": short_summary,
        "confidence": confidence,
        "method": "rule_based_title_extraction",
    }


def fallback_document_metadata(filename: str) -> dict[str, str]:
    title = Path(filename).stem.strip() or filename
    return {
        "title": title,
        "document_type": "unknown",
        "short_summary": _clip(title, SUMMARY_CHAR_LIMIT),
        "confidence": "low",
        "method": "filename_fallback",
    }


def _unit_text_lines(units: Iterable[Any]) -> list[str]:
    lines: list[str] = []
    for unit in units:
        unit_type = _unit_value(unit, "type")
        if unit_type in {"document", "page", "table", "table_row", "table_cell"}:
            continue
        text = _unit_value(unit, "text")
        if not isinstance(text, str):
            continue
        lines.extend(_split_text_lines(text))
    return _deduplicate_preserving_order(lines)


def _unit_value(unit: Any, key: str) -> object:
    if isinstance(unit, dict):
        return unit.get(key)
    return getattr(unit, key, None)


def _split_text_lines(text: str) -> list[str]:
    return [_normalize_space(line) for line in text.splitlines() if _normalize_space(line)]


def _title_lines(lines: list[str]) -> list[str]:
    if not lines:
        return []

    type_index = _document_type_line_index(lines)
    start_index = max(0, type_index - 2) if type_index is not None else 0
    selected: list[str] = []
    for line in lines[start_index : start_index + TITLE_LINE_LIMIT + 4]:
        if selected and _is_subject_stop_line(line):
            break
        selected.append(line)
        if len(selected) >= TITLE_LINE_LIMIT:
            break
    return selected


def _document_type_line_index(lines: list[str]) -> int | None:
    for index, line in enumerate(lines[:30]):
        if _classify_document_type([line]) != "unknown":
            return index
    return None


def _classify_document_type(texts: Iterable[str]) -> str:
    haystack = "\n".join(texts)
    for label, patterns in DOCUMENT_TYPE_PATTERNS:
        if any(re.search(pattern, haystack, flags=re.IGNORECASE) for pattern in patterns):
            return label
    return "unknown"


def _classify_from_header(filename: str, title_lines: list[str], title: str) -> str:
    file_stem = Path(filename).stem
    for text in (file_stem, *title_lines):
        exact_type = _classify_exact_type_line(text)
        if exact_type != "unknown":
            return exact_type
    return _classify_document_type([file_stem, title, *title_lines])


def _classify_exact_type_line(text: str) -> str:
    normalized = text.lower().strip(" .,:;№n")
    exact_labels = {label for label, _patterns in DOCUMENT_TYPE_PATTERNS if label != "unknown"}
    if normalized in exact_labels:
        return normalized
    for label in exact_labels:
        if normalized.startswith(f"{label} "):
            return label
    return "unknown"


def _subject_from_title_lines(title_lines: list[str], document_type: str) -> str:
    if not title_lines:
        return ""

    type_index = _document_type_line_index(title_lines)
    candidate_lines = title_lines[(type_index + 1) if type_index is not None else 0 :]
    subject_lines: list[str] = []
    for line in candidate_lines:
        if _is_date_or_number_line(line):
            continue
        if _is_subject_stop_line(line):
            break
        if _is_document_type_only_line(line, document_type):
            continue
        subject_lines.append(line)
        if len(" ".join(subject_lines)) >= SUMMARY_CHAR_LIMIT:
            break
    return _clip(" ".join(subject_lines), SUMMARY_CHAR_LIMIT)


def _subject_from_filename(filename: str) -> str:
    stem = Path(filename).stem
    stem = re.sub(r"\s*\(ред\.\s+от[^)]*\)", "", stem, flags=re.IGNORECASE)
    return _clip(_normalize_space(stem), SUMMARY_CHAR_LIMIT)


def _select_title(fallback_title: str, title_lines: list[str]) -> str:
    title = _clip(" ".join(title_lines), SUMMARY_CHAR_LIMIT)
    if not title:
        return _clip(fallback_title, SUMMARY_CHAR_LIMIT)
    if len(title) < 40 and len(fallback_title) > len(title):
        return _clip(fallback_title, SUMMARY_CHAR_LIMIT)
    return title


def _summary(document_type: str, subject: str) -> str:
    clean_subject = _clip(subject, SUMMARY_CHAR_LIMIT)
    if document_type == "unknown":
        return clean_subject
    return _clip(f"{document_type.capitalize()}: {clean_subject}", SUMMARY_CHAR_LIMIT)


def _confidence(document_type: str, title_lines: list[str], subject: str, title: str) -> str:
    if document_type != "unknown" and subject and subject != title and len(title_lines) >= 2:
        return "high"
    if document_type != "unknown" or subject:
        return "medium"
    return "low"


def _is_date_or_number_line(line: str) -> bool:
    normalized = line.lower()
    if re.search(r"\bот\s+\d{1,2}\b", normalized):
        return True
    if re.search(r"\b(?:n|№)\s*[\w\-/]+", normalized):
        return True
    return False


def _is_subject_stop_line(line: str) -> bool:
    normalized = line.lower()
    return any(re.search(pattern, normalized) for pattern in SUBJECT_STOP_PATTERNS)


def _is_document_type_only_line(line: str, document_type: str) -> bool:
    normalized = line.lower().strip(" .,:;№n")
    return document_type != "unknown" and normalized == document_type


def _normalize_space(value: str) -> str:
    return " ".join(value.split())


def _deduplicate_preserving_order(lines: list[str]) -> list[str]:
    result: list[str] = []
    previous = ""
    for line in lines:
        normalized = _normalize_space(line)
        if normalized and normalized != previous:
            result.append(normalized)
            previous = normalized
    return result


def _clip(value: str, limit: int) -> str:
    normalized = _normalize_space(value)
    if len(normalized) <= limit:
        return normalized
    clipped = normalized[: limit - 1].rstrip()
    if " " in clipped:
        clipped = clipped.rsplit(" ", 1)[0]
    return f"{clipped}…"