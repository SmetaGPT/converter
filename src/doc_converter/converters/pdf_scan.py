from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from doc_converter.canonical import (
    SourceRef,
    StructuralUnit,
    build_asset_record,
    document_id_from_sha256,
    minimal_document,
    unit_id,
)
from doc_converter.converters.pdf_text import (
    _is_figure_caption,
    _is_formula_block,
    _is_table_block,
    _parse_table_rows,
    _quality_flags_for_pdf_unit,
    _split_pdf_text,
)
from doc_converter.document_metadata import build_document_metadata
from doc_converter.ocr_runtime import find_ocrmypdf_executable
from doc_converter.quality import quality_payload
from doc_converter.schema_validation import validate_payload


@dataclass(frozen=True)
class PdfScanConversionResult:
    status: str
    pages: int
    units_count: int
    text_chars: int
    warnings: tuple[str, ...]


def convert_pdf_scan(
    source_path: Path,
    output_dir: Path,
    sha256: str,
    ocr_languages: tuple[str, ...],
    *,
    relative_source_path: str | None = None,
) -> PdfScanConversionResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    ocr_dir = output_dir / "ocr"
    ocr_dir.mkdir(exist_ok=True)
    searchable_pdf = ocr_dir / "searchable.pdf"
    sidecar_text = ocr_dir / "sidecar.txt"
    status_path = ocr_dir / "ocr-status.json"

    ocrmypdf = find_ocrmypdf_executable()
    if ocrmypdf is None:
        return _write_unavailable_result(source_path, output_dir, status_path, sha256, relative_source_path=relative_source_path)

    command = [
        ocrmypdf,
        "--mode",
        "skip",
        "--deskew",
        "--sidecar",
        str(sidecar_text),
        "-l",
        "+".join(ocr_languages),
        str(source_path),
        str(searchable_pdf),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=900, check=False)
    status_payload = {
        "engine": "ocrmypdf",
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout[-4000:],
        "stderr": completed.stderr[-4000:],
    }
    _write_json(status_path, status_payload)
    if completed.returncode != 0:
        return _write_ocr_failed_result(
            source_path,
            output_dir,
            status_path,
            sha256,
            completed.stderr,
            relative_source_path=relative_source_path,
        )

    return _write_ocr_success_result(
        source_path,
        searchable_pdf,
        sidecar_text,
        output_dir,
        sha256,
        relative_source_path=relative_source_path,
    )


def _write_unavailable_result(
    source_path: Path,
    output_dir: Path,
    status_path: Path,
    sha256: str,
    *,
    relative_source_path: str | None = None,
) -> PdfScanConversionResult:
    reader = PdfReader(str(source_path))
    pages = len(reader.pages)
    _write_json(
        status_path,
        {
            "engine": "ocrmypdf",
            "available": False,
            "status": "unavailable",
        },
    )
    return _write_scan_payload(
        source_path=source_path,
        output_dir=output_dir,
        sha256=sha256,
        pages=pages,
        search_text="",
        status="partial_success",
        flags=["ocr_required", "ocr_unavailable", "empty_text", "review_required"],
        warnings=["OCRmyPDF is not available in the current runtime."],
        ocr_applied=False,
        assets=[
            build_asset_record(
                asset_id="ocr_status",
                asset_type="other",
                asset_path=status_path,
                output_dir=output_dir,
                unit_id=None,
            )
        ],
        relative_source_path=relative_source_path,
    )


def _write_ocr_failed_result(
    source_path: Path,
    output_dir: Path,
    status_path: Path,
    sha256: str,
    stderr: str,
    *,
    relative_source_path: str | None = None,
) -> PdfScanConversionResult:
    reader = PdfReader(str(source_path))
    pages = len(reader.pages)
    return _write_scan_payload(
        source_path=source_path,
        output_dir=output_dir,
        sha256=sha256,
        pages=pages,
        search_text="",
        status="partial_success",
        flags=["ocr_required", "ocr_failed", "empty_text", "review_required"],
        warnings=[stderr.strip()[:1000] or "OCRmyPDF failed."],
        ocr_applied=False,
        assets=[
            build_asset_record(
                asset_id="ocr_status",
                asset_type="other",
                asset_path=status_path,
                output_dir=output_dir,
                unit_id=None,
            )
        ],
        relative_source_path=relative_source_path,
    )


def _write_ocr_success_result(
    source_path: Path,
    searchable_pdf: Path,
    sidecar_text: Path,
    output_dir: Path,
    sha256: str,
    *,
    relative_source_path: str | None = None,
) -> PdfScanConversionResult:
    reader = PdfReader(str(searchable_pdf))
    page_texts = [(page.extract_text() or "").strip() for page in reader.pages]
    search_text = "\f".join(page_texts)
    has_text = any(page_texts)
    flags = ["ocr_required", "ocr_applied"]
    if not has_text:
        flags.extend(["empty_text", "review_required"])
    assets = [
        build_asset_record(
            asset_id="ocr_pdf",
            asset_type="ocr_pdf",
            asset_path=searchable_pdf,
            output_dir=output_dir,
            unit_id=None,
        ),
        build_asset_record(
            asset_id="ocr_sidecar",
            asset_type="ocr_sidecar",
            asset_path=sidecar_text,
            output_dir=output_dir,
            unit_id=None,
        ),
    ]
    return _write_scan_payload(
        source_path=source_path,
        output_dir=output_dir,
        sha256=sha256,
        pages=len(reader.pages),
        search_text=search_text,
        status="success" if has_text else "partial_success",
        flags=flags,
        warnings=[],
        ocr_applied=True,
        assets=assets,
        relative_source_path=relative_source_path,
    )


def _write_scan_payload(
    *,
    source_path: Path,
    output_dir: Path,
    sha256: str,
    pages: int,
    search_text: str,
    status: str,
    flags: list[str],
    warnings: list[str],
    ocr_applied: bool,
    assets: list[dict[str, Any]],
    relative_source_path: str | None = None,
) -> PdfScanConversionResult:
    doc_id = document_id_from_sha256(sha256)
    units: list[StructuralUnit] = [
        StructuralUnit(unit_id=unit_id(0), type="document", order=0, source_ref=SourceRef(document_id=doc_id))
    ]
    order = 1
    page_texts = search_text.split("\f") if search_text else []
    for page_index in range(1, pages + 1):
        page_unit_id = unit_id(order)
        units.append(
            StructuralUnit(
                unit_id=page_unit_id,
                parent_id=unit_id(0),
                type="page",
                order=order,
                source_ref=SourceRef(document_id=doc_id, page=page_index),
            )
        )
        order += 1
        page_text = page_texts[page_index - 1] if page_index <= len(page_texts) else ""
        for paragraph in _split_pdf_text(page_text):
            order = _append_pdf_scan_text_units(
                units=units,
                order=order,
                paragraph=paragraph,
                doc_id=doc_id,
                page_unit_id=page_unit_id,
                page_index=page_index,
            )

    payload = minimal_document(
        source_path=source_path,
        source_format="pdf",
        sha256=sha256,
        route="pdf_scan",
        status=status,
        units=units,
        assets=assets,
        quality=quality_payload(flags, warnings),
        relative_source_path=relative_source_path,
        metadata=build_document_metadata(filename=source_path.name, units=units, search_text=search_text),
    )
    payload["processing"]["ocr_applied"] = ocr_applied
    payload["processing"]["warnings"] = warnings
    _write_validated_json(output_dir / "document.v1.json", payload, "document.v1.schema.json")
    _write_json(
        output_dir / "extractor_raw.json",
        {
            "extractor": "ocrmypdf+pypdf",
            "pages": pages,
            "text_chars": len(search_text),
            "ocr_applied": ocr_applied,
        },
    )
    (output_dir / "search_text.txt").write_text(search_text, encoding="utf-8")
    return PdfScanConversionResult(
        status=status,
        pages=pages,
        units_count=len(units),
        text_chars=len(search_text),
        warnings=tuple(warnings),
    )


def _append_pdf_scan_text_units(
    *,
    units: list[StructuralUnit],
    order: int,
    paragraph: str,
    doc_id: str,
    page_unit_id: str,
    page_index: int,
) -> int:
    if _is_table_block(paragraph):
        table_id = unit_id(order)
        units.append(
            StructuralUnit(
                unit_id=table_id,
                parent_id=page_unit_id,
                type="table",
                order=order,
                source_ref=SourceRef(document_id=doc_id, page=page_index),
                quality=quality_payload(["semantic_structure_inferred"]),
            )
        )
        order += 1
        for row_cells in _parse_table_rows(paragraph):
            row_id = unit_id(order)
            units.append(
                StructuralUnit(
                    unit_id=row_id,
                    parent_id=table_id,
                    type="table_row",
                    order=order,
                    source_ref=SourceRef(document_id=doc_id, page=page_index),
                )
            )
            order += 1
            for cell_text in row_cells:
                units.append(
                    StructuralUnit(
                        unit_id=unit_id(order),
                        parent_id=row_id,
                        type="table_cell",
                        order=order,
                        text=cell_text,
                        source_ref=SourceRef(document_id=doc_id, page=page_index),
                    )
                )
                order += 1
        return order

    if _is_figure_caption(paragraph):
        unit_type = "figure"
    elif _is_formula_block(paragraph):
        unit_type = "formula"
    else:
        unit_type = "paragraph"
    units.append(
        StructuralUnit(
            unit_id=unit_id(order),
            parent_id=page_unit_id,
            type=unit_type,
            order=order,
            text=paragraph,
            source_ref=SourceRef(document_id=doc_id, page=page_index),
            quality=quality_payload(_quality_flags_for_pdf_unit(unit_type)),
        )
    )
    return order + 1


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_validated_json(path: Path, payload: dict[str, Any], schema_filename: str) -> None:
    validate_payload(payload, schema_filename)
    _write_json(path, payload)