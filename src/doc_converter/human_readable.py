from __future__ import annotations

import json
import re
from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Any
from urllib.parse import quote

from .schema_validation import validate_json_file


@dataclass(frozen=True)
class ExportedRunDocument:
    original_filename: str
    relative_input_path: str
    status_label: str
    issue: str | None
    document_path: Path
    html_path: Path
    search_text_path: Path | None


@dataclass(frozen=True)
class RunDocumentRecord:
    original_filename: str
    relative_input_path: str
    status_label: str
    issue: str | None
    document_path: Path


def export_document_markdown(document: Path, output_path: Path | None = None) -> Path:
    document_path, payload = load_validated_document(document)
    target_path = output_path.expanduser().resolve() if output_path is not None else document_path.parent / "human-readable.md"
    _write_text(target_path, build_human_readable_markdown(payload))
    return target_path


def export_document_html(document: Path, output_path: Path | None = None) -> Path:
    document_path, payload = load_validated_document(document)
    target_path = output_path.expanduser().resolve() if output_path is not None else document_path.parent / "human-readable.html"
    _write_text(target_path, build_human_readable_html(payload))
    return target_path


def export_run_human_readable_html(run_dir: Path, output_path: Path | None = None) -> Path:
    run_path = run_dir.expanduser().resolve()
    exported_documents = _export_run_documents(run_path)
    if not exported_documents:
        raise FileNotFoundError(f"No document.v1.json files found in run directory: {run_path}")

    target_path = output_path.expanduser().resolve() if output_path is not None else run_path / "human-readable-index.html"
    _write_text(target_path, build_human_readable_run_index_html(run_path, exported_documents))
    return target_path


def load_validated_document(document: Path) -> tuple[Path, dict[str, Any]]:
    document_path = resolve_document_path(document.expanduser().resolve())
    payload = validate_json_file(document_path, "document.v1.schema.json")
    return document_path, payload


def resolve_document_path(path: Path) -> Path:
    if path.is_file():
        return path
    candidate = path / "document.v1.json"
    if candidate.is_file():
        return candidate
    raise FileNotFoundError(f"document.v1.json not found: {path}")


def build_human_readable_markdown(payload: dict[str, Any]) -> str:
    title, filename = _document_title_and_filename(payload)
    units = [unit for unit in payload.get("units", []) if isinstance(unit, dict)]
    units_by_parent = _units_by_parent(units)
    emitted_unit_ids: set[str] = set()

    lines = [f"# {title}", ""]
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
            lines.extend(_render_table_markdown(unit, units_by_parent, emitted_unit_ids))
            continue
        if unit_type in {"table_row", "table_cell"}:
            continue

        rendered = _render_unit_markdown(unit)
        if rendered:
            lines.extend(rendered)
            emitted_unit_ids.add(unit_id)

    return "\n".join(lines).rstrip() + "\n"


def build_human_readable_html(payload: dict[str, Any]) -> str:
    title, filename = _document_title_and_filename(payload)
    units = [unit for unit in payload.get("units", []) if isinstance(unit, dict)]
    units_by_parent = _units_by_parent(units)
    emitted_unit_ids: set[str] = set()

    body: list[str] = [f"<h1>{escape(title)}</h1>"]
    if filename:
        body.append(f"<p>Источник: {escape(filename)}</p>")

    for unit in sorted(units, key=lambda item: int(item.get("order", 0))):
        unit_id = _string_value(unit.get("unit_id"))
        if not unit_id or unit_id in emitted_unit_ids:
            continue
        unit_type = _string_value(unit.get("type"))
        if unit_type == "document":
            emitted_unit_ids.add(unit_id)
            continue
        if unit_type == "table":
            table_html = _render_table_html(unit, units_by_parent, emitted_unit_ids)
            if table_html:
                body.append(table_html)
            continue
        if unit_type in {"table_row", "table_cell"}:
            continue

        rendered = _render_unit_html(unit)
        if rendered:
            body.append(rendered)
            emitted_unit_ids.add(unit_id)

    body_html = "\n".join(body)
    return (
        "<!doctype html>\n"
        "<html lang=\"ru\">\n"
        "<head>\n"
        "  <meta charset=\"utf-8\">\n"
        "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        f"  <title>{escape(title)}</title>\n"
        "  <script>\n"
        "    window.MathJax = {tex: {displayMath: [['$$', '$$']], inlineMath: []}, options: {skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code']}};\n"
        "  </script>\n"
        "  <script async src=\"https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js\"></script>\n"
        "  <style>\n"
        "    :root { --page:#f7f3eb; --paper:#fffdf8; --ink:#1f2933; --line:#d9cbb7; --accent:#7a3f24; --soft:#f2dfc8; --code:#183044; }\n"
        "    * { box-sizing:border-box; }\n"
        "    body { margin:0; background:linear-gradient(180deg,#efe3d1 0,var(--page) 320px,#f9f5ed 100%); color:var(--ink); font:18px/1.72 Georgia,'Times New Roman',serif; }\n"
        "    main { width:min(980px,calc(100% - 32px)); margin:32px auto; padding:clamp(28px,4vw,56px); background:var(--paper); border:1px solid var(--line); box-shadow:0 18px 50px rgba(55,42,28,.13); }\n"
        "    h1 { margin:0 0 28px; color:#24170f; font-size:clamp(25px,4vw,40px); line-height:1.16; text-transform:uppercase; }\n"
        "    h2,h3,h4,h5,h6 { margin:2rem 0 .75rem; color:#332018; line-height:1.25; }\n"
        "    p { margin:.82rem 0; text-indent:1.6em; text-align:justify; overflow-wrap:anywhere; hyphens:auto; }\n"
        "    code { font-family:Consolas,'Cascadia Mono',monospace; font-size:.93em; color:var(--code); background:#f2ede3; border-radius:4px; padding:.05rem .25rem; }\n"
        "    pre { overflow:auto; padding:16px 18px; background:#102131; color:#edf6ff; border-radius:6px; border:1px solid #243b51; line-height:1.48; font-size:14px; }\n"
        "    pre code { background:transparent; color:inherit; padding:0; }\n"
        "    img { max-width:100%; height:auto; display:block; margin:1rem auto; border:1px solid var(--line); border-radius:6px; background:white; }\n"
        "    .formula-block { margin:1.25rem 0; padding:18px 20px; overflow-x:auto; background:linear-gradient(90deg,#fff7eb,#fffdf8); border-left:4px solid var(--accent); border-radius:6px; text-align:center; white-space:normal; overflow-wrap:anywhere; }\n"
        "    .formula-block p { margin:.35rem 0 0; text-indent:0; text-align:center; }\n"
        "    .formula-block.formula-plain { text-align:left; }\n"
        "    .formula-plain-text { margin:0; font:17px/1.6 'Times New Roman',Georgia,serif; white-space:normal; overflow-wrap:anywhere; }\n"
        "    .formula-label { margin-top:10px; font-size:14px; color:#6b4a39; text-indent:0; }\n"
        "    .table-wrap { width:100%; overflow-x:auto; margin:1rem 0 1.35rem; border:1px solid var(--line); border-radius:6px; background:#fffaf1; }\n"
        "    .table-wrap.table-plain { padding:14px 16px; overflow-x:visible; }\n"
        "    .table-plain-row { margin:.45rem 0; text-indent:0; text-align:left; overflow-wrap:anywhere; }\n"
        "    table { width:100%; min-width:680px; border-collapse:collapse; font-size:14.5px; line-height:1.42; }\n"
        "    th,td { border-bottom:1px solid var(--line); border-right:1px solid var(--line); padding:8px 10px; vertical-align:top; }\n"
        "    th { background:var(--soft); color:#2d1d13; font-weight:700; text-align:left; }\n"
        "    .asset-link { font-size:14px; color:#6b4a39; text-align:center; text-indent:0; }\n"
        "    @media print { body { background:white; } main { margin:0; width:100%; box-shadow:none; border:0; } .table-wrap,.formula-block,pre { break-inside:avoid; } }\n"
        "  </style>\n"
        "</head>\n"
        f"<body><main>\n{body_html}\n</main></body>\n"
        "</html>\n"
    )


def build_human_readable_run_index_html(run_dir: Path, exported_documents: list[ExportedRunDocument]) -> str:
    run_id = escape(run_dir.name)
    rows: list[str] = []
    for document in exported_documents:
        html_href = _relative_href(run_dir, document.html_path)
        json_href = _relative_href(run_dir, document.document_path)
        search_href = _relative_href(run_dir, document.search_text_path) if document.search_text_path is not None else None
        issue = escape(document.issue) if document.issue else ""
        search_link = f'<a href="{search_href}">search_text.txt</a>' if search_href else ""
        rows.append(
            "<tr>"
            f"<td>{escape(document.original_filename)}</td>"
            f"<td>{escape(document.relative_input_path)}</td>"
            f"<td>{escape(document.status_label)}</td>"
            f"<td>{issue}</td>"
            f"<td><a href=\"{html_href}\">human-readable.html</a></td>"
            f"<td><a href=\"{json_href}\">document.v1.json</a></td>"
            f"<td>{search_link}</td>"
            "</tr>"
        )

    rows_html = "\n".join(rows)
    return (
        "<!doctype html>\n"
        "<html lang=\"ru\">\n"
        "<head>\n"
        "  <meta charset=\"utf-8\">\n"
        "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        f"  <title>HTML QC index: {run_id}</title>\n"
        "  <style>\n"
        "    body { margin:0; font:16px/1.5 Segoe UI,Tahoma,sans-serif; background:#f6f7f9; color:#16202a; }\n"
        "    main { max-width:1200px; margin:24px auto; padding:24px; background:white; border:1px solid #d7dce2; border-radius:10px; box-shadow:0 14px 32px rgba(20,32,44,.08); }\n"
        "    h1 { margin-top:0; }\n"
        "    table { width:100%; border-collapse:collapse; }\n"
        "    th,td { border:1px solid #d7dce2; padding:10px 12px; text-align:left; vertical-align:top; }\n"
        "    th { background:#eef3f8; }\n"
        "    tr:nth-child(even) { background:#fafbfd; }\n"
        "    a { color:#0b5cab; text-decoration:none; }\n"
        "    a:hover { text-decoration:underline; }\n"
        "    .meta { color:#52606d; margin-bottom:18px; }\n"
        "  </style>\n"
        "</head>\n"
        "<body><main>\n"
        f"<h1>HTML QC index</h1>\n<p class=\"meta\">Run: {run_id}. Документы: {len(exported_documents)}</p>\n"
        "<table>\n<thead><tr><th>Исходный файл</th><th>Относительный путь</th><th>Статус</th><th>Пояснение</th><th>HTML</th><th>Canonical JSON</th><th>Search text</th></tr></thead>\n"
        f"<tbody>\n{rows_html}\n</tbody>\n</table>\n"
        "</main></body>\n"
        "</html>\n"
    )


def _export_run_documents(run_dir: Path) -> list[ExportedRunDocument]:
    exported_documents: list[ExportedRunDocument] = []
    for record in _load_run_document_records(run_dir):
        html_path = export_document_html(record.document_path)
        search_text_path = record.document_path.with_name("search_text.txt")
        exported_documents.append(
            ExportedRunDocument(
                original_filename=record.original_filename,
                relative_input_path=record.relative_input_path,
                status_label=record.status_label,
                issue=record.issue,
                document_path=record.document_path,
                html_path=html_path,
                search_text_path=search_text_path if search_text_path.exists() else None,
            )
        )
    return exported_documents


def _load_run_document_records(run_dir: Path) -> list[RunDocumentRecord]:
    catalog_path = run_dir / "processed-documents-catalog.json"
    records: list[RunDocumentRecord] = []
    if catalog_path.is_file():
        raw_catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        if isinstance(raw_catalog, dict):
            raw_documents = raw_catalog.get("documents", [])
            if isinstance(raw_documents, list):
                for item in raw_documents:
                    if not isinstance(item, dict):
                        continue
                    output_dir = _string_value(item.get("output_dir"))
                    if not output_dir:
                        continue
                    document_path = run_dir / output_dir / "document.v1.json"
                    if not document_path.is_file():
                        continue
                    records.append(
                        RunDocumentRecord(
                            original_filename=_string_value(item.get("original_filename")) or document_path.parent.name,
                            relative_input_path=_string_value(item.get("relative_input_path")) or document_path.parent.name,
                            status_label=_string_value(item.get("status_label"))
                            or _string_value(item.get("status"))
                            or "Неизвестный статус",
                            issue=_string_value(item.get("issue")) or None,
                            document_path=document_path,
                        )
                    )
    if records:
        return records

    documents_dir = run_dir / "documents"
    for document_path in sorted(documents_dir.glob("*/document.v1.json")):
        records.append(
            RunDocumentRecord(
                original_filename=document_path.parent.name,
                relative_input_path=document_path.parent.name,
                status_label="Без каталога",
                issue=None,
                document_path=document_path,
            )
        )
    return records


def _document_title_and_filename(payload: dict[str, Any]) -> tuple[str, str]:
    raw_metadata = payload.get("metadata")
    metadata = raw_metadata if isinstance(raw_metadata, dict) else {}
    raw_source = payload.get("source")
    source = raw_source if isinstance(raw_source, dict) else {}
    title = _string_value(metadata.get("title")) or _string_value(source.get("filename")) or "Документ"
    filename = _string_value(source.get("filename"))
    return title, filename


def _units_by_parent(units: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for unit in units:
        parent_id = _string_value(unit.get("parent_id"))
        if parent_id:
            result.setdefault(parent_id, []).append(unit)
    for children in result.values():
        children.sort(key=lambda item: int(item.get("order", 0)))
    return result


def _render_unit_markdown(unit: dict[str, Any]) -> list[str]:
    unit_type = _string_value(unit.get("type"))
    text = _string_value(unit.get("text"))
    if unit_type == "section" and text:
        return [f"## {text}", ""]
    if unit_type in {"formula", "formula_image"} and isinstance(unit.get("formula"), dict):
        return _render_formula_markdown(unit)
    if unit_type == "formula_image":
        asset_ref = _string_value(unit.get("asset_ref"))
        return [f"![formula]({asset_ref})", ""] if asset_ref else []
    if unit_type == "figure":
        asset_ref = _string_value(unit.get("asset_ref"))
        return [f"![figure]({asset_ref})", ""] if asset_ref else []
    if text:
        return [text, ""]
    return []


def _render_formula_markdown(unit: dict[str, Any]) -> list[str]:
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


def _render_unit_html(unit: dict[str, Any]) -> str:
    unit_type = _string_value(unit.get("type"))
    text = _string_value(unit.get("text"))
    if unit_type == "section" and text:
        return f"<h2>{_html_with_breaks(text)}</h2>"
    if unit_type in {"formula", "formula_image"} and isinstance(unit.get("formula"), dict):
        return _render_formula_html(unit)
    if unit_type in {"figure", "formula_image"}:
        asset_ref = _string_value(unit.get("asset_ref"))
        if asset_ref:
            alt = "formula" if unit_type == "formula_image" else "figure"
            href = _href_value(asset_ref)
            return (
                f'<img src="{href}" alt="{alt}">'
                f'<p class="asset-link"><a href="{href}">{escape(asset_ref)}</a></p>'
            )
    if text:
        return f"<p>{_html_with_breaks(text)}</p>"
    return ""


def _render_formula_html(unit: dict[str, Any]) -> str:
    text = _string_value(unit.get("text"))
    formula = unit.get("formula") if isinstance(unit.get("formula"), dict) else None
    if not formula:
        return f"<p>{_html_with_breaks(text)}</p>" if text else ""

    display_latex = _string_value(formula.get("display_latex"))
    calc_expr = _string_value(formula.get("calc_expr"))
    linear_text = _string_value(formula.get("linear_text")) or text
    formula_number = _formula_number(text)
    asset_ref = _string_value(unit.get("asset_ref"))
    render_as_math = _should_render_formula_as_math(formula, display_latex)

    blocks: list[str] = []
    if render_as_math and display_latex:
        latex_block = [f'<div class="formula-block">$$\n{escape(display_latex)}\n$$']
        if formula_number:
            latex_block.append(f'<div class="formula-label">Формула {escape(formula_number)}</div>')
        latex_block.append("</div>")
        blocks.append("".join(latex_block))
    elif linear_text or text:
        plain_text = linear_text or text
        plain_block = [f'<div class="formula-block formula-plain"><div class="formula-plain-text">{_html_with_breaks(plain_text)}</div>']
        if formula_number:
            plain_block.append(f'<div class="formula-label">Формула {escape(formula_number)}</div>')
        plain_block.append("</div>")
        blocks.append("".join(plain_block))

    if calc_expr:
        blocks.append(f"<pre><code>{escape(calc_expr)}</code></pre>")
    if asset_ref:
        href = _href_value(asset_ref)
        blocks.append(f'<p class="asset-link"><a href="{href}">{escape(asset_ref)}</a></p>')
    return "\n".join(blocks)


def _should_render_formula_as_math(formula: dict[str, Any], display_latex: str) -> bool:
    if not display_latex:
        return False
    confidence = _string_value(formula.get("confidence"))
    if confidence == "low":
        return False
    source_format = _string_value(formula.get("source_format"))
    warnings = formula.get("warnings")
    if source_format in {"docx_text_linearized", "heuristic_latex"} and confidence != "high":
        return False
    return not (isinstance(warnings, list) and any("heuristic" in _string_value(item) for item in warnings))


def _render_table_markdown(
    table_unit: dict[str, Any],
    units_by_parent: dict[str, list[dict[str, Any]]],
    emitted_unit_ids: set[str],
) -> list[str]:
    table_id = _string_value(table_unit.get("unit_id"))
    if not table_id:
        return []
    rows = _table_rows(table_id, units_by_parent, emitted_unit_ids)
    if not rows:
        return []

    if _table_has_structure_warning(table_unit):
        lines = _render_plain_table_lines(rows)
        return lines + ([""] if lines else [])

    width = max(len(row) for row in rows)
    normalized_rows = [row + [""] * (width - len(row)) for row in rows]
    header = normalized_rows[0]
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join(["---"] * width) + " |"]
    for row in normalized_rows[1:]:
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")
    return lines


def _render_table_html(
    table_unit: dict[str, Any],
    units_by_parent: dict[str, list[dict[str, Any]]],
    emitted_unit_ids: set[str],
) -> str:
    table_id = _string_value(table_unit.get("unit_id"))
    if not table_id:
        return ""
    rows = _table_rows(table_id, units_by_parent, emitted_unit_ids)
    if not rows:
        return ""

    if _table_has_structure_warning(table_unit):
        row_blocks = "".join(
            f'<div class="table-plain-row">{_html_with_breaks(line)}</div>' for line in _render_plain_table_lines(rows)
        )
        return f'<div class="table-wrap table-plain">{row_blocks}</div>' if row_blocks else ""

    width = max(len(row) for row in rows)
    normalized_rows = [row + [""] * (width - len(row)) for row in rows]
    header = normalized_rows[0]
    thead = "".join(f"<th>{_html_with_breaks(cell)}</th>" for cell in header)
    body_rows = []
    for row in normalized_rows[1:]:
        body_rows.append("<tr>" + "".join(f"<td>{_html_with_breaks(cell)}</td>" for cell in row) + "</tr>")
    tbody = "\n".join(body_rows)
    return f"<div class=\"table-wrap\"><table><thead><tr>{thead}</tr></thead><tbody>{tbody}</tbody></table></div>"


def _table_rows(
    table_id: str,
    units_by_parent: dict[str, list[dict[str, Any]]],
    emitted_unit_ids: set[str],
) -> list[list[str]]:
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
    return rows


def _table_has_structure_warning(table_unit: dict[str, Any]) -> bool:
    quality = table_unit.get("quality")
    if not isinstance(quality, dict):
        return False
    flags = quality.get("flags")
    return isinstance(flags, list) and any(_string_value(flag) == "table_structure_warning" for flag in flags)


def _render_plain_table_lines(rows: list[list[str]]) -> list[str]:
    lines: list[str] = []
    for row in rows:
        line = " ".join(cell.strip() for cell in row if cell and cell.strip()).strip()
        if line:
            lines.append(line)
    return lines


def _formula_number(text: str) -> str | None:
    match = re.search(r"\(([0-9]+(?:\.[0-9]+)*)\),?\s*$", text)
    return match.group(1) if match is not None else None


def _escape_table_cell(value: str) -> str:
    return value.replace("|", r"\|").replace("\r\n", "<br>").replace("\n", "<br>")


def _html_with_breaks(value: str) -> str:
    return escape(value).replace("\r\n", "<br>").replace("\n", "<br>")


def _href_value(value: str) -> str:
    return quote(value.replace("\\", "/"), safe="/:()[]#%")


def _relative_href(root: Path, path: Path) -> str:
    return _href_value(path.resolve().relative_to(root.resolve()).as_posix())


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _string_value(value: Any) -> str:
    return value if isinstance(value, str) else ""