from __future__ import annotations

import json
import shutil
import zipfile
from dataclasses import dataclass, replace
from pathlib import Path, PurePosixPath
from typing import Any, cast
from xml.etree import ElementTree

from docx import Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph

from doc_converter.canonical import (
    SourceRef,
    StructuralUnit,
    build_asset_record,
    document_id_from_sha256,
    minimal_document,
    unit_id,
)
from doc_converter.document_metadata import build_document_metadata
from doc_converter.quality import quality_payload, text_quality_flags
from doc_converter.schema_validation import validate_payload

from .formulas.text import (
    _formula_representation_from_text,
    _looks_like_formula_continuation,
    _looks_like_formula_text,
    _merge_formula_text,
    _trailing_formula_operator,
)
from .inline_glyph import _inline_drawing_placeholders

WORD_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
MAX_DOCX_ARCHIVE_ENTRIES = 4096
MAX_DOCX_UNCOMPRESSED_BYTES = 128 * 1024 * 1024


class DocxSecurityError(RuntimeError):
    """Raised when an untrusted DOCX archive violates admission limits."""


@dataclass(frozen=True)
class ConversionResult:
    status: str
    units_count: int
    assets_count: int
    search_text_chars: int
    warnings: tuple[str, ...] = ()


def convert_docx(
    source_path: Path,
    output_dir: Path,
    sha256: str,
    *,
    relative_source_path: str | None = None,
) -> ConversionResult:
    _validate_docx_archive(source_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = output_dir / "assets"
    assets_dir.mkdir(exist_ok=True)

    document = Document(str(source_path))
    doc_id = document_id_from_sha256(sha256)
    units: list[StructuralUnit] = [
        StructuralUnit(
            unit_id=unit_id(0),
            type="document",
            order=0,
            source_ref=SourceRef(document_id=doc_id, docx_path="/word/document.xml"),
            text=None,
        )
    ]
    assets: list[dict[str, Any]] = []
    search_parts: list[str] = []
    order = 1

    for block_kind, block, block_index in _iter_body_blocks(document):
        if block_kind == "paragraph":
            paragraph = cast(Paragraph, block)
            text = _paragraph_semantic_text(paragraph)
            if not text:
                continue
            if _merge_formula_continuation_into_previous_unit(units=units, search_parts=search_parts, text=text):
                continue
            paragraph_type = _classify_paragraph_type(paragraph)
            paragraph_unit = StructuralUnit(
                unit_id=unit_id(order),
                parent_id=unit_id(0),
                type=paragraph_type,
                order=order,
                text=text,
                formula=_formula_representation_from_text(text) if paragraph_type == "formula" else None,
                source_ref=SourceRef(document_id=doc_id, docx_path=f"/word/document.xml/body/p[{block_index}]"),
                quality=quality_payload(_quality_flags_for_docx_unit(paragraph_type)),
            )
            units.append(paragraph_unit)
            search_parts.append(text)
            order += 1
            continue

        table = cast(Table, block)
        table_id = unit_id(order)
        units.append(
            StructuralUnit(
                unit_id=table_id,
                parent_id=unit_id(0),
                type="table",
                order=order,
                source_ref=SourceRef(document_id=doc_id, docx_path=f"/word/document.xml/body/tbl[{block_index}]"),
            )
        )
        order += 1
        table_text_rows: list[str] = []
        for row_index, row in enumerate(table.rows, start=1):
            row_id = unit_id(order)
            units.append(
                StructuralUnit(
                    unit_id=row_id,
                    parent_id=table_id,
                    type="table_row",
                    order=order,
                    source_ref=SourceRef(
                        document_id=doc_id,
                        docx_path=f"/word/document.xml/body/tbl[{block_index}]/tr[{row_index}]",
                    ),
                )
            )
            order += 1
            row_cells: list[str] = []
            for cell_index, cell in enumerate(row.cells, start=1):
                cell_text = _table_cell_semantic_text(cell)
                units.append(
                    StructuralUnit(
                        unit_id=unit_id(order),
                        parent_id=row_id,
                        type="table_cell",
                        order=order,
                        text=cell_text,
                        formula=_table_cell_formula(cell_text),
                        source_ref=SourceRef(
                            document_id=doc_id,
                            docx_path=(
                                f"/word/document.xml/body/tbl[{block_index}]/"
                                f"tr[{row_index}]/tc[{cell_index}]"
                            ),
                        ),
                    )
                )
                row_cells.append(cell_text.replace("\n", " "))
                order += 1
            table_text_rows.append(" | ".join(row_cells))
        if table_text_rows:
            search_parts.append("\n".join(table_text_rows))

    for unit_type, text, docx_path in _iter_header_footer_units(document):
        units.append(
            StructuralUnit(
                unit_id=unit_id(order),
                parent_id=unit_id(0),
                type=unit_type,
                order=order,
                text=text,
                source_ref=SourceRef(document_id=doc_id, docx_path=docx_path),
                quality=quality_payload(["semantic_structure_inferred"]),
            )
        )
        order += 1

    for footnote_id, footnote_text in _extract_docx_footnotes(source_path):
        units.append(
            StructuralUnit(
                unit_id=unit_id(order),
                parent_id=unit_id(0),
                type="footnote",
                order=order,
                text=footnote_text,
                source_ref=SourceRef(document_id=doc_id, docx_path=f"/word/footnotes.xml/footnote[{footnote_id}]"),
                quality=quality_payload(["semantic_structure_inferred"]),
            )
        )
        search_parts.append(footnote_text)
        order += 1

    extracted_assets = _extract_docx_media(source_path, assets_dir)
    for asset_index, asset_path in enumerate(extracted_assets, start=1):
        figure_unit_id = unit_id(order)
        rel_asset_path = asset_path.relative_to(output_dir).as_posix()
        asset_type = _classify_docx_media_asset(asset_path)
        units.append(
            StructuralUnit(
                unit_id=figure_unit_id,
                parent_id=unit_id(0),
                type="formula_image" if asset_type == "formula_image" else "figure",
                order=order,
                asset_ref=rel_asset_path,
                source_ref=SourceRef(document_id=doc_id, docx_path=f"/word/media/{asset_path.name}"),
            )
        )
        assets.append(
            build_asset_record(
                asset_id=f"asset_{asset_index:06d}",
                asset_type=asset_type,
                asset_path=asset_path,
                output_dir=output_dir,
                unit_id=figure_unit_id,
            )
        )
        order += 1

    search_text = "\n\n".join(search_parts)
    payload = minimal_document(
        source_path=source_path,
        source_format="docx",
        sha256=sha256,
        route="docx_native",
        status="success",
        units=units,
        assets=assets,
        quality=quality_payload(text_quality_flags(search_text, size_bytes=source_path.stat().st_size, route="docx_native")),
        relative_source_path=relative_source_path,
        metadata=build_document_metadata(filename=source_path.name, units=units, search_text=search_text),
    )
    _write_validated_json(output_dir / "document.v1.json", payload, "document.v1.schema.json")
    _write_json(
        output_dir / "extractor_raw.json",
        {
            "extractor": "python-docx",
            "paragraphs": len(document.paragraphs),
            "tables": len(document.tables),
            "inline_shapes": len(document.inline_shapes),
            "assets": len(extracted_assets),
            "headers_footers": len(_iter_header_footer_units(document)),
            "footnotes": len(_extract_docx_footnotes(source_path)),
        },
    )
    (output_dir / "search_text.txt").write_text(search_text, encoding="utf-8")

    return ConversionResult(
        status="success",
        units_count=len(units),
        assets_count=len(assets),
        search_text_chars=len(search_text),
    )


def _extract_docx_media(source_path: Path, assets_dir: Path) -> list[Path]:
    extracted: list[Path] = []
    try:
        with _open_validated_docx_archive(source_path) as archive:
            media_names = sorted(name for name in archive.namelist() if name.startswith("word/media/"))
            for index, media_name in enumerate(media_names, start=1):
                suffix = Path(media_name).suffix.lower() or ".bin"
                target = assets_dir / f"figure_{index:06d}{suffix}"
                with archive.open(media_name) as source, target.open("wb") as destination:
                    shutil.copyfileobj(source, destination)
                extracted.append(target)
    except DocxSecurityError:
        raise
    except zipfile.BadZipFile:
        return extracted
    return extracted


def _classify_docx_media_asset(asset_path: Path) -> str:
    normalized = asset_path.stem.lower()
    if any(marker in normalized for marker in ("formula", "equation", "math")):
        return "formula_image"
    return "figure"


def _iter_body_blocks(document: Any) -> list[tuple[str, Paragraph | Table, int]]:
    blocks: list[tuple[str, Paragraph | Table, int]] = []
    paragraph_index = 0
    table_index = 0
    for child in document.element.body.iterchildren():
        if isinstance(child, CT_P):
            paragraph_index += 1
            blocks.append(("paragraph", Paragraph(child, document), paragraph_index))
        elif isinstance(child, CT_Tbl):
            table_index += 1
            blocks.append(("table", Table(child, document), table_index))
    return blocks


def _classify_paragraph_type(paragraph: Paragraph) -> str:
    text = _paragraph_semantic_text(paragraph)
    if _paragraph_has_omml(paragraph) or _looks_like_formula_text(text):
        return "formula"
    style = paragraph.style
    style_name = ((style.name if style is not None else "") or "").strip().lower()
    if "heading" in style_name or style_name.startswith("заголов"):
        return "section"
    if "caption" in style_name or "подпись" in style_name:
        return "caption"
    numbering = getattr(getattr(paragraph._p, "pPr", None), "numPr", None)
    if numbering is not None or style_name.startswith("list"):
        return "list_item"
    return "paragraph"


def _quality_flags_for_docx_unit(unit_type: str) -> list[str]:
    if unit_type == "paragraph":
        return []
    if unit_type == "formula":
        return ["semantic_structure_inferred"]
    return ["semantic_style_inferred"]


def _merge_formula_continuation_into_previous_unit(
    *,
    units: list[StructuralUnit],
    search_parts: list[str],
    text: str,
) -> bool:
    if not units:
        return False

    previous_unit = units[-1]
    previous_text = previous_unit.text or ""
    if previous_unit.type != "formula" or not previous_text:
        return False

    trailing_operator = _trailing_formula_operator(previous_text)
    if trailing_operator is None:
        return False

    stripped_continuation = text.lstrip()
    if not stripped_continuation or not _looks_like_formula_continuation(stripped_continuation, trailing_operator):
        return False

    merged_text = _merge_formula_text(previous_text, stripped_continuation, trailing_operator)
    units[-1] = replace(
        previous_unit,
        text=merged_text,
        formula=_formula_representation_from_text(merged_text),
    )
    if search_parts:
        search_parts[-1] = merged_text
    return True


def _paragraph_semantic_text(paragraph: Paragraph) -> str:
    text_parts: list[str] = []
    has_text_content = False
    for run in paragraph.runs:
        run_text, run_has_text = _run_semantic_text(paragraph, run)
        if run_text:
            text_parts.append(run_text)
        if run_has_text:
            has_text_content = True
    text = "".join(text_parts).strip()
    if text and (has_text_content or _looks_like_formula_text(text)):
        return text

    text = paragraph.text.strip()
    if text:
        return text
    math_text = " ".join(
        str(element.text).strip()
        for element in paragraph._p.iter()
        if element.tag.endswith("}t") and element.text and str(element.text).strip()
    )
    return math_text.strip()


def _table_cell_semantic_text(cell: Any) -> str:
    text_parts: list[str] = []
    for paragraph in cell.paragraphs:
        paragraph_text = _paragraph_semantic_text(paragraph)
        if paragraph_text:
            text_parts.append(paragraph_text)
    return "\n".join(text_parts)


def _table_cell_formula(text: str) -> dict[str, Any] | None:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines:
        if _looks_like_formula_text(line):
            return _formula_representation_from_text(line)
    return None


def _run_semantic_text(paragraph: Paragraph, run: Any) -> tuple[str, bool]:
    parts: list[str] = []
    has_text_content = False
    for child in run._r:
        if child.tag.endswith("}t") and child.text:
            parts.append(str(child.text))
            has_text_content = True
            continue
        if child.tag.endswith("}tab"):
            parts.append("\t")
            has_text_content = True
            continue
        if child.tag.endswith("}br"):
            parts.append("\n")
            has_text_content = True
            continue
        if child.tag.endswith("}drawing"):
            parts.extend(_inline_drawing_placeholders(paragraph, child))

    text = "".join(parts)
    if not text:
        return "", False

    if run.font.subscript:
        return f"_({text})", has_text_content
    if run.font.superscript:
        return f"^({text})", has_text_content
    return text, has_text_content


def _paragraph_has_omml(paragraph: Paragraph) -> bool:
    return any(element.tag.endswith("}oMath") or element.tag.endswith("}oMathPara") for element in paragraph._p.iter())


def _iter_header_footer_units(document: Any) -> list[tuple[str, str, str]]:
    units: list[tuple[str, str, str]] = []
    seen: set[tuple[str, str]] = set()
    for section_index, section in enumerate(document.sections, start=1):
        for unit_type, story in (("header", section.header), ("footer", section.footer)):
            for paragraph_index, paragraph in enumerate(story.paragraphs, start=1):
                text = _paragraph_semantic_text(paragraph)
                if not text:
                    continue
                key = (unit_type, text)
                if key in seen:
                    continue
                seen.add(key)
                units.append((unit_type, text, f"/word/section[{section_index}]/{unit_type}/p[{paragraph_index}]"))
    return units


def _extract_docx_footnotes(source_path: Path) -> list[tuple[str, str]]:
    footnotes: list[tuple[str, str]] = []
    try:
        with _open_validated_docx_archive(source_path) as archive:
            if "word/footnotes.xml" not in archive.namelist():
                return footnotes
            root = ElementTree.fromstring(archive.read("word/footnotes.xml"))
    except DocxSecurityError:
        raise
    except (zipfile.BadZipFile, ElementTree.ParseError):
        return footnotes

    for footnote in root.findall(f"{WORD_NS}footnote"):
        footnote_id = str(footnote.attrib.get(f"{WORD_NS}id", ""))
        footnote_type = str(footnote.attrib.get(f"{WORD_NS}type", ""))
        if footnote_type or footnote_id in {"", "-1", "0"}:
            continue
        text = " ".join(
            str(node.text).strip()
            for node in footnote.iter(f"{WORD_NS}t")
            if node.text and str(node.text).strip()
        ).strip()
        if text:
            footnotes.append((footnote_id, text))
    return footnotes


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_validated_json(path: Path, payload: dict[str, Any], schema_filename: str) -> None:
    validate_payload(payload, schema_filename)
    _write_json(path, payload)


def _open_validated_docx_archive(source_path: Path) -> zipfile.ZipFile:
    _validate_docx_archive(source_path)
    return zipfile.ZipFile(source_path)


def _validate_docx_archive(source_path: Path) -> None:
    try:
        with zipfile.ZipFile(source_path) as archive:
            entries = archive.infolist()
    except zipfile.BadZipFile as exc:
        raise DocxSecurityError(f"Invalid DOCX archive: {source_path}") from exc

    if len(entries) > MAX_DOCX_ARCHIVE_ENTRIES:
        raise DocxSecurityError(
            "DOCX archive exceeds the maximum allowed entry count: "
            f"entries={len(entries)}, limit={MAX_DOCX_ARCHIVE_ENTRIES}, source={source_path}"
        )

    total_uncompressed_bytes = 0
    for entry in entries:
        _validate_docx_archive_member_name(entry.filename, source_path)
        total_uncompressed_bytes += entry.file_size
        if total_uncompressed_bytes > MAX_DOCX_UNCOMPRESSED_BYTES:
            raise DocxSecurityError(
                "DOCX archive exceeds the maximum allowed uncompressed size: "
                f"bytes={total_uncompressed_bytes}, limit={MAX_DOCX_UNCOMPRESSED_BYTES}, source={source_path}"
            )


def _validate_docx_archive_member_name(member_name: str, source_path: Path) -> None:
    normalized = PurePosixPath(member_name)
    if not member_name or normalized.is_absolute() or "\\" in member_name:
        raise DocxSecurityError(f"DOCX archive contains an invalid member path: {member_name!r} in {source_path}")
    if any(part in {"", ".", ".."} for part in normalized.parts):
        raise DocxSecurityError(f"DOCX archive contains a traversal-like member path: {member_name!r} in {source_path}")
    if normalized.parts and ":" in normalized.parts[0]:
        raise DocxSecurityError(f"DOCX archive contains a drive-qualified member path: {member_name!r} in {source_path}")
