from __future__ import annotations

import hashlib
import mimetypes
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from doc_converter.document_metadata import fallback_document_metadata


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def document_id_from_sha256(sha256: str) -> str:
    normalized = sha256.strip().lower()
    if len(normalized) != 64 or any(char not in "0123456789abcdef" for char in normalized):
        raise ValueError("sha256 must be a 64-character lowercase hexadecimal string")
    return f"sha256:{normalized}"


def unit_id(order: int) -> str:
    if order < 0:
        raise ValueError("order must be non-negative")
    return f"u_{order:06d}"


def build_asset_record(
    *,
    asset_id: str,
    asset_type: str,
    asset_path: Path,
    output_dir: Path,
    unit_id: str | None,
) -> dict[str, Any]:
    media_type, _ = mimetypes.guess_type(asset_path.name)
    return {
        "asset_id": asset_id,
        "type": asset_type,
        "path": asset_path.relative_to(output_dir).as_posix(),
        "unit_id": unit_id,
        "sha256": sha256_file(asset_path),
        "filename": asset_path.name,
        "size_bytes": asset_path.stat().st_size,
        "media_type": media_type,
    }


@dataclass(frozen=True)
class SourceRef:
    document_id: str
    page: int | None = None
    bbox: tuple[float, float, float, float] | None = None
    docx_path: str | None = None
    coordinate_system: str | None = None
    page_width: float | None = None
    page_height: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "page": self.page,
            "bbox": list(self.bbox) if self.bbox is not None else None,
            "docx_path": self.docx_path,
            "coordinate_system": self.coordinate_system,
            "page_width": self.page_width,
            "page_height": self.page_height,
        }


@dataclass(frozen=True)
class StructuralUnit:
    unit_id: str
    type: str
    order: int
    source_ref: SourceRef
    parent_id: str | None = None
    text: str | None = None
    asset_ref: str | None = None
    formula: dict[str, Any] | None = None
    cell: dict[str, Any] | None = None
    quality: dict[str, Any] = field(default_factory=lambda: {"flags": [], "warnings": []})

    def to_dict(self) -> dict[str, Any]:
        return {
            "unit_id": self.unit_id,
            "parent_id": self.parent_id,
            "type": self.type,
            "order": self.order,
            "text": self.text,
            "asset_ref": self.asset_ref,
            "formula": self.formula,
            "cell": self.cell,
            "source_ref": self.source_ref.to_dict(),
            "quality": self.quality,
        }


def minimal_document(
    *,
    source_path: Path,
    source_format: str,
    sha256: str,
    route: str,
    status: str,
    units: list[StructuralUnit],
    assets: list[dict[str, Any]] | None = None,
    quality: dict[str, Any] | None = None,
    relative_source_path: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    document_id = document_id_from_sha256(sha256)
    return {
        "schema_version": "document.v1",
        "document_id": document_id,
        "source": {
            "original_path": str(source_path),
            "relative_input_path": relative_source_path,
            "filename": source_path.name,
            "format": source_format,
            "sha256": sha256,
            "size_bytes": source_path.stat().st_size if source_path.exists() else 0,
        },
        "processing": {
            "route": route,
            "status": status,
            "warnings": [],
        },
        "metadata": metadata or fallback_document_metadata(source_path.name),
        "units": [item.to_dict() for item in units],
        "assets": assets or [],
        "quality": quality or {"flags": [], "warnings": []},
    }