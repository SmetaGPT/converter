from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from doc_converter.canonical import SourceRef, StructuralUnit, document_id_from_sha256, minimal_document, unit_id
from doc_converter.document_metadata import build_document_metadata
from doc_converter.quality import quality_payload, text_quality_flags
from doc_converter.schema_validation import validate_payload


@dataclass(frozen=True)
class PdfTextConversionResult:
    status: str
    pages: int
    units_count: int
    text_chars: int
    warnings: tuple[str, ...] = ()


def convert_pdf_text(
    source_path: Path,
    output_dir: Path,
    sha256: str,
    *,
    relative_source_path: str | None = None,
) -> PdfTextConversionResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    reader = PdfReader(str(source_path))
    doc_id = document_id_from_sha256(sha256)
    units: list[StructuralUnit] = [
        StructuralUnit(
            unit_id=unit_id(0),
            type="document",
            order=0,
            source_ref=SourceRef(document_id=doc_id),
        )
    ]
    page_payloads = [_extract_page_payload(page, page_index) for page_index, page in enumerate(reader.pages, start=1)]
    header_candidates, footer_candidates = _detect_repeated_edge_paragraphs(page_payloads)

    search_parts: list[str] = []
    order = 1

    for page_payload in page_payloads:
        page_index = page_payload["page_index"]
        page_unit_id = unit_id(order)
        units.append(
            StructuralUnit(
                unit_id=page_unit_id,
                parent_id=unit_id(0),
                type="page",
                order=order,
                source_ref=SourceRef(
                    document_id=doc_id,
                    page=page_index,
                    bbox=(0.0, 0.0, page_payload["page_width"], page_payload["page_height"]),
                    coordinate_system="pdf_points_bottom_left",
                    page_width=page_payload["page_width"],
                    page_height=page_payload["page_height"],
                ),
            )
        )
        order += 1
        page_paragraphs = page_payload["paragraphs"]
        if not page_paragraphs:
            continue
        for paragraph_index, paragraph in enumerate(page_paragraphs):
            unit_type = "paragraph"
            if paragraph_index == 0 and paragraph in header_candidates:
                unit_type = "header"
            elif paragraph_index == len(page_paragraphs) - 1 and paragraph in footer_candidates:
                unit_type = "footer"
            units.append(
                StructuralUnit(
                    unit_id=unit_id(order),
                    parent_id=page_unit_id,
                    type=unit_type,
                    order=order,
                    text=paragraph,
                    source_ref=SourceRef(
                        document_id=doc_id,
                        page=page_index,
                        coordinate_system="pdf_points_bottom_left",
                        page_width=page_payload["page_width"],
                        page_height=page_payload["page_height"],
                    ),
                    quality=quality_payload(["repeated_edge_block"] if unit_type in {"header", "footer"} else []),
                )
            )
            if unit_type == "paragraph":
                search_parts.append(paragraph)
            order += 1

    search_text = "\n\n".join(search_parts)
    flags = text_quality_flags(search_text, size_bytes=source_path.stat().st_size, route="pdf_text")
    if any(int(page_payload.get("rotation", 0)) % 360 != 0 for page_payload in page_payloads):
        flags.append("rotated_text")
    status = "success" if search_text else "partial_success"
    payload = minimal_document(
        source_path=source_path,
        source_format="pdf",
        sha256=sha256,
        route="pdf_text",
        status=status,
        units=units,
        assets=[],
        quality=quality_payload(flags),
        relative_source_path=relative_source_path,
        metadata=build_document_metadata(filename=source_path.name, units=units, search_text=search_text),
    )
    payload["processing"]["ocr_applied"] = False
    _write_validated_json(output_dir / "document.v1.json", payload, "document.v1.schema.json")
    _write_json(
        output_dir / "extractor_raw.json",
        {
            "extractor": "pypdf",
            "extraction_mode": "layout_first",
            "pages": len(reader.pages),
            "text_chars": len(search_text),
        },
    )
    (output_dir / "search_text.txt").write_text(search_text, encoding="utf-8")

    return PdfTextConversionResult(
        status=status,
        pages=len(reader.pages),
        units_count=len(units),
        text_chars=len(search_text),
    )


def _split_pdf_text(text: str) -> list[str]:
    paragraphs: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        current.append(stripped)
    if current:
        paragraphs.append(" ".join(current))
    return paragraphs


def _extract_page_payload(page: Any, page_index: int) -> dict[str, Any]:
    layout_text = _extract_page_text(page)
    media_box = page.mediabox
    page_width = float(media_box.right) - float(media_box.left)
    page_height = float(media_box.top) - float(media_box.bottom)
    rotation = int(getattr(page, "rotation", 0) or 0)
    return {
        "page_index": page_index,
        "page_width": page_width,
        "page_height": page_height,
        "rotation": rotation,
        "paragraphs": _split_pdf_text(layout_text),
    }


def _extract_page_text(page: Any) -> str:
    try:
        text = page.extract_text(extraction_mode="layout") or ""
    except TypeError:
        text = ""
    if text.strip():
        return text.strip()
    return (page.extract_text() or "").strip()


def _detect_repeated_edge_paragraphs(page_payloads: list[dict[str, Any]]) -> tuple[set[str], set[str]]:
    header_counts: dict[str, int] = {}
    footer_counts: dict[str, int] = {}
    for page_payload in page_payloads:
        paragraphs = page_payload["paragraphs"]
        if not paragraphs:
            continue
        header_counts[paragraphs[0]] = header_counts.get(paragraphs[0], 0) + 1
        footer_counts[paragraphs[-1]] = footer_counts.get(paragraphs[-1], 0) + 1
    headers = {text for text, count in header_counts.items() if count >= 2}
    footers = {text for text, count in footer_counts.items() if count >= 2}
    return headers, footers


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_validated_json(path: Path, payload: dict[str, Any], schema_filename: str) -> None:
    validate_payload(payload, schema_filename)
    _write_json(path, payload)