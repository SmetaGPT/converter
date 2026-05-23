from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .canonical import sha256_file


SUPPORTED_SUFFIXES = {".docx", ".pdf"}


@dataclass(frozen=True)
class InventoryRecord:
    relative_path: str
    filename: str
    format: str
    size_bytes: int
    sha256: str
    route: str
    status: str
    duplicate_group_id: str | None = None
    duplicate_of: str | None = None
    warnings: tuple[str, ...] = ()

    def to_manifest_record(self, run_id: str) -> dict[str, object]:
        return {
            "run_id": run_id,
            "relative_path": self.relative_path,
            "filename": self.filename,
            "format": self.format,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
            "route": self.route,
            "status": self.status,
            "duplicate_group_id": self.duplicate_group_id,
            "duplicate_of": self.duplicate_of,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class UnsupportedInventoryRecord:
    relative_path: str
    filename: str
    format: str
    size_bytes: int
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class InventoryScanResult:
    scanned_files: int
    supported_records: list[InventoryRecord]
    unsupported_records: list[UnsupportedInventoryRecord]


def build_inventory(input_dir: Path) -> InventoryScanResult:
    supported_candidates: list[Path] = []
    unsupported_records: list[UnsupportedInventoryRecord] = []
    for item in _iter_input_files(input_dir):
        if item.suffix.lower() in SUPPORTED_SUFFIXES:
            supported_candidates.append(item)
            continue
        unsupported_records.append(_build_unsupported_record(input_dir, item))

    raw_records = [_build_record(input_dir, item) for item in supported_candidates]
    supported_records = _attach_duplicate_info(raw_records)
    return InventoryScanResult(
        scanned_files=len(supported_records) + len(unsupported_records),
        supported_records=supported_records,
        unsupported_records=unsupported_records,
    )


def classify_route(path: Path) -> tuple[str, tuple[str, ...]]:
    suffix = path.suffix.lower()
    if suffix == ".docx":
        return "docx_native", ()
    if suffix == ".pdf":
        return _classify_pdf_route(path)
    return "not_classified", ("unsupported_suffix",)


def _iter_input_files(input_dir: Path) -> list[Path]:
    files: list[Path] = []
    for item in input_dir.rglob("*"):
        if not item.is_file():
            continue
        if item.name.startswith("~$"):
            continue
        files.append(item)
    return sorted(files, key=lambda item: item.relative_to(input_dir).as_posix().lower())


def _build_record(input_dir: Path, path: Path) -> InventoryRecord:
    route, warnings = classify_route(path)
    digest = sha256_file(path)
    return InventoryRecord(
        relative_path=path.relative_to(input_dir).as_posix(),
        filename=path.name,
        format=path.suffix.lower().lstrip("."),
        size_bytes=path.stat().st_size,
        sha256=digest,
        route=route,
        status="queued",
        warnings=warnings,
    )


def _build_unsupported_record(input_dir: Path, path: Path) -> UnsupportedInventoryRecord:
    return UnsupportedInventoryRecord(
        relative_path=path.relative_to(input_dir).as_posix(),
        filename=path.name,
        format=path.suffix.lower().lstrip("."),
        size_bytes=path.stat().st_size,
        warnings=("unsupported_suffix",),
    )


def _classify_pdf_route(path: Path) -> tuple[str, tuple[str, ...]]:
    try:
        from pypdf import PdfReader
    except ImportError:
        return "pdf_scan", ("pypdf_not_available", "ocr_required")

    try:
        reader = PdfReader(str(path))
        pages = len(reader.pages)
        text_chars = 0
        for page in reader.pages[:5]:
            text_chars += len((page.extract_text() or "").strip())
        threshold = max(200, min(max(pages, 1), 5) * 40)
        if text_chars >= threshold:
            return "pdf_text", ()
        return "pdf_scan", ("ocr_required",)
    except Exception as exc:  # noqa: BLE001 - route detection must not stop inventory.
        return "pdf_scan", ("pdf_text_layer_check_failed", type(exc).__name__, "ocr_required")


def _attach_duplicate_info(records: list[InventoryRecord]) -> list[InventoryRecord]:
    by_hash: dict[str, list[InventoryRecord]] = {}
    for record in records:
        by_hash.setdefault(record.sha256, []).append(record)

    result: list[InventoryRecord] = []
    for record in records:
        group = by_hash[record.sha256]
        if len(group) == 1:
            result.append(record)
            continue
        duplicate_group_id = f"sha256:{record.sha256}"
        primary = group[0].relative_path
        result.append(
            InventoryRecord(
                relative_path=record.relative_path,
                filename=record.filename,
                format=record.format,
                size_bytes=record.size_bytes,
                sha256=record.sha256,
                route=record.route,
                status=record.status,
                duplicate_group_id=duplicate_group_id,
                duplicate_of=None if record.relative_path == primary else primary,
                warnings=record.warnings,
            )
        )
    return result