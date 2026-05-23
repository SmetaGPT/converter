from __future__ import annotations

import json
import re
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path
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


WORD_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
FORMULA_RE = re.compile(r"(^|\s)[A-Za-zА-Яа-я][\wА-Яа-я]*\s*=|[=∑√≤≥±×÷≈]|\b(sum|sqrt|frac)\b", re.IGNORECASE)


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
            paragraph_type = _classify_paragraph_type(paragraph)
            paragraph_unit = StructuralUnit(
                unit_id=unit_id(order),
                parent_id=unit_id(0),
                type=paragraph_type,
                order=order,
                text=text,
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
                cell_text = "\n".join(paragraph.text.strip() for paragraph in cell.paragraphs if paragraph.text.strip())
                units.append(
                    StructuralUnit(
                        unit_id=unit_id(order),
                        parent_id=row_id,
                        type="table_cell",
                        order=order,
                        text=cell_text,
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
        with zipfile.ZipFile(source_path) as archive:
            media_names = sorted(name for name in archive.namelist() if name.startswith("word/media/"))
            for index, media_name in enumerate(media_names, start=1):
                suffix = Path(media_name).suffix.lower() or ".bin"
                target = assets_dir / f"figure_{index:06d}{suffix}"
                with archive.open(media_name) as source, target.open("wb") as destination:
                    shutil.copyfileobj(source, destination)
                extracted.append(target)
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


def _paragraph_semantic_text(paragraph: Paragraph) -> str:
    text = paragraph.text.strip()
    if text:
        return text
    math_text = " ".join(
        str(element.text).strip()
        for element in paragraph._p.iter()
        if element.tag.endswith("}t") and element.text and str(element.text).strip()
    )
    return math_text.strip()


def _paragraph_has_omml(paragraph: Paragraph) -> bool:
    return any(element.tag.endswith("}oMath") or element.tag.endswith("}oMathPara") for element in paragraph._p.iter())


def _looks_like_formula_text(text: str) -> bool:
    stripped = text.strip()
    if len(stripped) > 180:
        return False
    return bool(FORMULA_RE.search(stripped))


def _iter_header_footer_units(document: Any) -> list[tuple[str, str, str]]:
    units: list[tuple[str, str, str]] = []
    seen: set[tuple[str, str]] = set()
    for section_index, section in enumerate(document.sections, start=1):
        for unit_type, story in (("header", section.header), ("footer", section.footer)):
            for paragraph_index, paragraph in enumerate(story.paragraphs, start=1):
                text = paragraph.text.strip()
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
        with zipfile.ZipFile(source_path) as archive:
            if "word/footnotes.xml" not in archive.namelist():
                return footnotes
            root = ElementTree.fromstring(archive.read("word/footnotes.xml"))
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