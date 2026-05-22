from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from doc_converter.canonical import SourceRef, StructuralUnit, document_id_from_sha256, minimal_document, unit_id
from doc_converter.quality import quality_payload, text_quality_flags


@dataclass(frozen=True)
class PdfTextConversionResult:
    status: str
    pages: int
    units_count: int
    text_chars: int
    warnings: tuple[str, ...] = ()


def convert_pdf_text(source_path: Path, output_dir: Path, sha256: str) -> PdfTextConversionResult:
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
    search_parts: list[str] = []
    order = 1

    for page_index, page in enumerate(reader.pages, start=1):
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
        page_text = (page.extract_text() or "").strip()
        if not page_text:
            continue
        page_paragraphs = _split_pdf_text(page_text)
        for paragraph in page_paragraphs:
            units.append(
                StructuralUnit(
                    unit_id=unit_id(order),
                    parent_id=page_unit_id,
                    type="paragraph",
                    order=order,
                    text=paragraph,
                    source_ref=SourceRef(document_id=doc_id, page=page_index),
                )
            )
            search_parts.append(paragraph)
            order += 1

    search_text = "\n\n".join(search_parts)
    flags = text_quality_flags(search_text, size_bytes=source_path.stat().st_size, route="pdf_text")
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
    )
    payload["processing"]["ocr_applied"] = False
    _write_json(output_dir / "document.v1.json", payload)
    _write_json(
        output_dir / "extractor_raw.json",
        {
            "extractor": "pypdf",
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


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")