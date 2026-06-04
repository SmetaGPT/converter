from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache

TABLE_SEPARATOR_RE = re.compile(r"\s{2,}|\t+|\s*\|\s*")
TABLE_NUMERIC_SIGNAL_RE = re.compile(r"\d")
TABLE_LIST_MARKER_RE = re.compile(r"^(?:\d+|[A-Za-zА-Яа-я])[.)]?$")


@dataclass(frozen=True)
class ParsedTableBlock:
    rows: tuple[tuple[str, ...], ...]
    dominant_width: int
    flags: tuple[str, ...] = ()


def is_table_block(text: str) -> bool:
    parsed = parse_table_block(text)
    if parsed.dominant_width < 2 or len(parsed.rows) < 2:
        return False
    aligned_rows = [row for row in parsed.rows if len(row) == parsed.dominant_width]
    if len(aligned_rows) < 2:
        return False
    if _looks_like_numbered_list(aligned_rows):
        return False
    if parsed.dominant_width == 2 and parsed.flags and not _has_numeric_signal(aligned_rows):
        return False
    return True


def parse_table_rows(text: str) -> list[list[str]]:
    return [list(row) for row in parse_table_block(text).rows]


@lru_cache(maxsize=256)
def parse_table_block(text: str) -> ParsedTableBlock:
    raw_rows: list[list[str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        cells = [cell.strip() for cell in TABLE_SEPARATOR_RE.split(stripped) if cell.strip()]
        if cells:
            raw_rows.append(cells)

    dominant_width = _dominant_table_width(raw_rows)
    if not raw_rows:
        return ParsedTableBlock(rows=(), dominant_width=dominant_width)
    if dominant_width < 2:
        return ParsedTableBlock(rows=tuple(tuple(row) for row in raw_rows), dominant_width=dominant_width)

    normalized_rows: list[list[str]] = []
    ragged_rows = False
    for cells in raw_rows:
        if normalized_rows and len(cells) == 1 and len(normalized_rows[-1]) == dominant_width:
            normalized_rows[-1][-1] = f"{normalized_rows[-1][-1]}\n{cells[0]}"
            continue
        if len(cells) > dominant_width:
            cells = cells[: dominant_width - 1] + [" ".join(cells[dominant_width - 1 :])]
            ragged_rows = True
        elif len(cells) < dominant_width:
            cells = cells + [""] * (dominant_width - len(cells))
            ragged_rows = True
        normalized_rows.append(cells)

    flags = ("table_structure_warning",) if ragged_rows else ()
    return ParsedTableBlock(
        rows=tuple(tuple(row) for row in normalized_rows),
        dominant_width=dominant_width,
        flags=flags,
    )


def _dominant_table_width(rows: list[list[str]]) -> int:
    widths = [len(row) for row in rows if len(row) >= 2]
    if not widths:
        return 0
    counts: dict[int, int] = {}
    for width in widths:
        counts[width] = counts.get(width, 0) + 1
    return max(counts.items(), key=lambda item: (item[1], item[0]))[0]


def _has_numeric_signal(rows: list[tuple[str, ...]]) -> bool:
    return any(TABLE_NUMERIC_SIGNAL_RE.search(cell) for row in rows[1:] for cell in row[1:])


def _looks_like_numbered_list(rows: list[tuple[str, ...]]) -> bool:
    list_like_rows = 0
    prose_value_rows = 0
    numeric_value_rows = 0
    for first_cell, *rest_cells in rows:
        if not TABLE_LIST_MARKER_RE.fullmatch(first_cell.strip()):
            continue
        list_like_rows += 1
        if any(len(cell.strip()) >= 20 for cell in rest_cells):
            prose_value_rows += 1
        if any(TABLE_NUMERIC_SIGNAL_RE.search(cell) for cell in rest_cells):
            numeric_value_rows += 1
    return list_like_rows >= 2 and prose_value_rows >= 2 and numeric_value_rows <= 1


__all__ = ["ParsedTableBlock", "is_table_block", "parse_table_block", "parse_table_rows"]