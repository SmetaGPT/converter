from __future__ import annotations

import json
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from docx import Document

from doc_converter.canonical import SourceRef, StructuralUnit, document_id_from_sha256, minimal_document, unit_id
from doc_converter.quality import quality_payload, text_quality_flags


@dataclass(frozen=True)
class ConversionResult:
    status: str
    units_count: int
    assets_count: int
    search_text_chars: int
    warnings: tuple[str, ...] = ()


def convert_docx(source_path: Path, output_dir: Path, sha256: str) -> ConversionResult:
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

    for paragraph_index, paragraph in enumerate(document.paragraphs, start=1):
        text = paragraph.text.strip()
        if not text:
            continue
        paragraph_unit = StructuralUnit(
            unit_id=unit_id(order),
            parent_id=unit_id(0),
            type="paragraph",
            order=order,
            text=text,
            source_ref=SourceRef(document_id=doc_id, docx_path=f"/word/document.xml/body/p[{paragraph_index}]"),
        )
        units.append(paragraph_unit)
        search_parts.append(text)
        order += 1

    for table_index, table in enumerate(document.tables, start=1):
        table_id = unit_id(order)
        units.append(
            StructuralUnit(
                unit_id=table_id,
                parent_id=unit_id(0),
                type="table",
                order=order,
                source_ref=SourceRef(document_id=doc_id, docx_path=f"/word/document.xml/body/tbl[{table_index}]"),
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
                        docx_path=f"/word/document.xml/body/tbl[{table_index}]/tr[{row_index}]",
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
                                f"/word/document.xml/body/tbl[{table_index}]/"
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

    extracted_assets = _extract_docx_media(source_path, assets_dir)
    for asset_index, asset_path in enumerate(extracted_assets, start=1):
        figure_unit_id = unit_id(order)
        rel_asset_path = asset_path.relative_to(output_dir).as_posix()
        units.append(
            StructuralUnit(
                unit_id=figure_unit_id,
                parent_id=unit_id(0),
                type="figure",
                order=order,
                asset_ref=rel_asset_path,
                source_ref=SourceRef(document_id=doc_id, docx_path=f"/word/media/{asset_path.name}"),
            )
        )
        assets.append(
            {
                "asset_id": f"asset_{asset_index:06d}",
                "type": "figure",
                "path": rel_asset_path,
                "unit_id": figure_unit_id,
                "sha256": None,
            }
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
    )
    _write_json(output_dir / "document.v1.json", payload)
    _write_json(
        output_dir / "extractor_raw.json",
        {
            "extractor": "python-docx",
            "paragraphs": len(document.paragraphs),
            "tables": len(document.tables),
            "inline_shapes": len(document.inline_shapes),
            "assets": len(extracted_assets),
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


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")