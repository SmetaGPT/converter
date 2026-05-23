from __future__ import annotations

from typing import Any


CHUNKABLE_TYPES = {"section", "paragraph", "list_item", "caption", "header", "footer", "table_cell", "formula", "figure"}


def build_chunks_from_document(document_payload: dict[str, Any], *, max_chars: int = 1200) -> list[dict[str, Any]]:
    document_id = str(document_payload["document_id"])
    chunks: list[dict[str, Any]] = []
    current_unit_refs: list[str] = []
    current_parts: list[str] = []
    current_pages: set[int] = set()
    current_asset_refs: set[str] = set()
    current_section_path: list[str] = []

    def flush() -> None:
        if not current_unit_refs:
            return
        chunks.append(
            {
                "schema_version": "chunks.v1",
                "chunk_id": f"c_{len(chunks) + 1:06d}",
                "document_id": document_id,
                "unit_refs": list(current_unit_refs),
                "section_path": list(current_section_path),
                "pages": sorted(current_pages),
                "text": "\n\n".join(current_parts),
                "asset_refs": sorted(current_asset_refs),
            }
        )
        current_unit_refs.clear()
        current_parts.clear()
        current_pages.clear()
        current_asset_refs.clear()

    for unit in document_payload.get("units", []):
        unit_type = str(unit.get("type", ""))
        text = str(unit.get("text") or "").strip()
        if unit_type == "section" and text:
            flush()
            current_section_path = [text]
        if unit_type not in CHUNKABLE_TYPES or not text:
            continue

        projected_text = "\n\n".join(current_parts + [text])
        if current_unit_refs and len(projected_text) > max_chars:
            flush()

        current_unit_refs.append(str(unit["unit_id"]))
        current_parts.append(text)
        asset_ref = unit.get("asset_ref")
        if isinstance(asset_ref, str) and asset_ref:
            current_asset_refs.add(asset_ref)
        page = unit.get("source_ref", {}).get("page")
        if isinstance(page, int):
            current_pages.add(page)

    flush()
    return chunks