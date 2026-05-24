from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from doc_converter.schema_validation import validate_json_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export a document.v1.json package into human-readable Markdown.")
    parser.add_argument("document", type=Path, help="Path to document.v1.json or a document package directory.")
    parser.add_argument("output", type=Path, nargs="?", help="Output Markdown path. Defaults to human-readable.md next to document.v1.json.")
    args = parser.parse_args(argv)

    document_path = _resolve_document_path(args.document.expanduser().resolve())
    output_path = args.output.expanduser().resolve() if args.output is not None else document_path.parent / "human-readable.md"

    payload = validate_json_file(document_path, "document.v1.schema.json")
    markdown = build_human_readable_markdown(payload)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "ok", "output": str(output_path)}, ensure_ascii=False))
    return 0


def build_human_readable_markdown(payload: dict[str, Any]) -> str:
    raw_metadata = payload.get("metadata")
    metadata = raw_metadata if isinstance(raw_metadata, dict) else {}
    raw_source = payload.get("source")
    source = raw_source if isinstance(raw_source, dict) else {}
    title = _string_value(metadata.get("title")) or _string_value(source.get("filename")) or "Документ"

    units = [unit for unit in payload.get("units", []) if isinstance(unit, dict)]
    units_by_parent = _units_by_parent(units)
    emitted_unit_ids: set[str] = set()

    lines = [f"# {title}", ""]
    filename = _string_value(source.get("filename"))
    if filename:
        lines.extend([f"Источник: {filename}", ""])

    for unit in sorted(units, key=lambda item: int(item.get("order", 0))):
        unit_id = _string_value(unit.get("unit_id"))
        if not unit_id or unit_id in emitted_unit_ids:
            continue
        unit_type = _string_value(unit.get("type"))
        if unit_type == "document":
            emitted_unit_ids.add(unit_id)
            continue
        if unit_type == "table":
            lines.extend(_render_table(unit, units_by_parent, emitted_unit_ids))
            continue
        if unit_type in {"table_row", "table_cell"}:
            continue

        rendered = _render_unit(unit)
        if rendered:
            lines.extend(rendered)
            emitted_unit_ids.add(unit_id)

    return "\n".join(lines).rstrip() + "\n"


def _resolve_document_path(path: Path) -> Path:
    if path.is_file():
        return path
    candidate = path / "document.v1.json"
    if candidate.is_file():
        return candidate
    raise FileNotFoundError(f"document.v1.json not found: {path}")


def _units_by_parent(units: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for unit in units:
        parent_id = _string_value(unit.get("parent_id"))
        if parent_id:
            result.setdefault(parent_id, []).append(unit)
    for children in result.values():
        children.sort(key=lambda item: int(item.get("order", 0)))
    return result


def _render_unit(unit: dict[str, Any]) -> list[str]:
    unit_type = _string_value(unit.get("type"))
    text = _string_value(unit.get("text"))
    if unit_type == "section" and text:
        return [f"## {text}", ""]
    if unit_type == "formula":
        return _render_formula(unit)
    if unit_type == "formula_image":
        asset_ref = _string_value(unit.get("asset_ref"))
        return [f"![formula]({asset_ref})", ""] if asset_ref else []
    if unit_type == "figure":
        asset_ref = _string_value(unit.get("asset_ref"))
        return [f"![figure]({asset_ref})", ""] if asset_ref else []
    if text:
        return [text, ""]
    return []


def _render_formula(unit: dict[str, Any]) -> list[str]:
    text = _string_value(unit.get("text"))
    formula = unit.get("formula") if isinstance(unit.get("formula"), dict) else None
    if not formula:
        return [text, ""] if text else []

    display_latex = _string_value(formula.get("display_latex"))
    calc_expr = _string_value(formula.get("calc_expr"))
    linear_text = _string_value(formula.get("linear_text")) or text
    formula_number = _formula_number(text)

    lines: list[str] = []
    if display_latex:
        lines.extend(["$$", display_latex, "$$"])
        if formula_number:
            lines.append(f"Формула {formula_number}")
        lines.append("")
    elif text:
        lines.extend([text, ""])

    if calc_expr:
        lines.extend(["```python", calc_expr, "```", ""])
    elif not display_latex and linear_text and linear_text != text:
        lines.extend([linear_text, ""])
    return lines


def _render_table(
    table_unit: dict[str, Any],
    units_by_parent: dict[str, list[dict[str, Any]]],
    emitted_unit_ids: set[str],
) -> list[str]:
    table_id = _string_value(table_unit.get("unit_id"))
    if not table_id:
        return []
    rows: list[list[str]] = []
    for row_unit in units_by_parent.get(table_id, []):
        row_id = _string_value(row_unit.get("unit_id"))
        if not row_id:
            continue
        cells = [_escape_table_cell(_string_value(cell.get("text"))) for cell in units_by_parent.get(row_id, [])]
        if cells:
            rows.append(cells)
            emitted_unit_ids.add(row_id)
            for cell in units_by_parent.get(row_id, []):
                cell_id = _string_value(cell.get("unit_id"))
                if cell_id:
                    emitted_unit_ids.add(cell_id)
    emitted_unit_ids.add(table_id)
    if not rows:
        return []

    width = max(len(row) for row in rows)
    normalized_rows = [row + [""] * (width - len(row)) for row in rows]
    header = normalized_rows[0]
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join(["---"] * width) + " |"]
    for row in normalized_rows[1:]:
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")
    return lines


def _formula_number(text: str) -> str | None:
    match = re.search(r"\(([0-9]+(?:\.[0-9]+)*)\),?\s*$", text)
    return match.group(1) if match is not None else None


def _escape_table_cell(value: str) -> str:
    return value.replace("|", r"\|").replace("\r\n", "<br>").replace("\n", "<br>")


def _string_value(value: Any) -> str:
    return value if isinstance(value, str) else ""


if __name__ == "__main__":
    raise SystemExit(main())