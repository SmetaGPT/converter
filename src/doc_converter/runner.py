from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Union

from . import __version__
from .config import ConverterConfig
from .converters.docx import ConversionResult, convert_docx
from .converters.pdf_scan import PdfScanConversionResult, convert_pdf_scan
from .converters.pdf_text import PdfTextConversionResult, convert_pdf_text
from .inventory import build_inventory


class ConverterError(RuntimeError):
    """Raised when a conversion run cannot be started."""


@dataclass(frozen=True)
class RunResult:
    run_id: str
    run_dir: Path
    discovered_files: int
    supported_files: int
    status: str


def run_convert_folder(config: ConverterConfig) -> RunResult:
    input_dir = config.input_dir.expanduser().resolve()
    output_dir = config.output_dir.expanduser().resolve()

    _validate_startup_paths(input_dir, output_dir)

    run_id = _new_run_id()
    run_dir = _allocate_run_dir(output_dir / "runs", run_id)
    documents_dir = run_dir / "documents"
    documents_dir.mkdir(parents=True, exist_ok=False)

    run_metadata = _build_run_metadata(run_id, input_dir, output_dir, config)
    _write_json(run_dir / "run.json", run_metadata)

    inventory_records = build_inventory(input_dir)

    manifest_path = run_dir / "manifest.jsonl"
    log_path = run_dir / "processing-log.jsonl"
    errors_path = run_dir / "errors.jsonl"
    queue_state_path = run_dir / "queue-state.json"

    _write_text(manifest_path, "")
    _write_text(errors_path, "")
    _append_jsonl(log_path, {"event": "run_started", "run_id": run_id, "status": "ok"})

    completed: list[str] = []
    partial: list[str] = []
    failed: list[str] = []
    final_manifest_records: list[dict[str, object]] = []

    for record in inventory_records:
        manifest_record = record.to_manifest_record(run_id)
        if record.route in {"docx_native", "pdf_text", "pdf_scan"}:
            try:
                document_dir = _document_output_dir(documents_dir, record.sha256)
                result: Union[ConversionResult, PdfTextConversionResult, PdfScanConversionResult]
                if record.route == "docx_native":
                    result = convert_docx(input_dir / record.relative_path, document_dir, record.sha256)
                    manifest_record["assets_count"] = result.assets_count
                    manifest_record["search_text_chars"] = result.search_text_chars
                elif record.route == "pdf_text":
                    result = convert_pdf_text(input_dir / record.relative_path, document_dir, record.sha256)
                    manifest_record["pages"] = result.pages
                    manifest_record["search_text_chars"] = result.text_chars
                else:
                    result = convert_pdf_scan(
                        input_dir / record.relative_path,
                        document_dir,
                        record.sha256,
                        config.options.ocr_languages,
                    )
                    manifest_record["pages"] = result.pages
                    manifest_record["search_text_chars"] = result.text_chars
                    manifest_record["warnings"] = list(result.warnings)
                manifest_record["status"] = result.status
                manifest_record["output_dir"] = document_dir.relative_to(run_dir).as_posix()
                manifest_record["units_count"] = result.units_count
                if result.status == "partial_success":
                    partial.append(record.relative_path)
                else:
                    completed.append(record.relative_path)
                _append_jsonl(
                    log_path,
                    {
                        "event": "document_converted",
                        "run_id": run_id,
                        "relative_path": record.relative_path,
                        "route": record.route,
                        "status": result.status,
                    },
                )
            except Exception as exc:  # noqa: BLE001 - batch run records per-document failures.
                manifest_record["status"] = "failed"
                manifest_record["error"] = type(exc).__name__
                failed.append(record.relative_path)
                _append_jsonl(
                    errors_path,
                    {
                        "event": "document_failed",
                        "run_id": run_id,
                        "relative_path": record.relative_path,
                        "route": record.route,
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    },
                )
        final_manifest_records.append(manifest_record)

    for manifest_record in final_manifest_records:
        _append_jsonl(manifest_path, manifest_record)

    duplicate_groups = sorted({record.duplicate_group_id for record in inventory_records if record.duplicate_group_id})
    _write_json(
        queue_state_path,
        {
            "schema_version": "queue-state.v1",
            "run_id": run_id,
            "status": "completed" if not failed and not partial else "partial_success",
            "queued": [
                record.relative_path
                for record in inventory_records
                if record.relative_path not in completed and record.relative_path not in partial and record.relative_path not in failed
            ],
            "completed": completed,
            "partial": partial,
            "failed": failed,
        },
    )

    summary = {
        "run_id": run_id,
        "status": "success" if not failed and not partial else "partial_success",
        "input_dir": str(input_dir),
        "output_dir": str(output_dir),
        "run_dir": str(run_dir),
        "discovered_files": len(inventory_records),
        "supported_files": len(inventory_records),
        "unsupported_files": 0,
        "duplicate_groups": len(duplicate_groups),
        "processed_files": len(completed) + len(partial),
        "partial_files": len(partial),
        "failed_files": len(failed),
    }
    _write_json(run_dir / "summary.json", summary)
    final_status = "success" if not failed and not partial else "partial_success"
    _append_jsonl(log_path, {"event": "run_completed", "run_id": run_id, "status": final_status})

    return RunResult(
        run_id=run_id,
        run_dir=run_dir,
        discovered_files=len(inventory_records),
        supported_files=len(inventory_records),
        status=final_status,
    )


def _validate_startup_paths(input_dir: Path, output_dir: Path) -> None:
    if not input_dir.exists():
        raise ConverterError(f"Input directory does not exist: {input_dir}")
    if not input_dir.is_dir():
        raise ConverterError(f"Input path is not a directory: {input_dir}")
    if output_dir.exists() and not output_dir.is_dir():
        raise ConverterError(f"Output path is not a directory: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)


def _new_run_id() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _allocate_run_dir(runs_dir: Path, base_run_id: str) -> Path:
    runs_dir.mkdir(parents=True, exist_ok=True)
    candidate = runs_dir / base_run_id
    if not candidate.exists():
        candidate.mkdir()
        return candidate

    for index in range(1, 1000):
        candidate = runs_dir / f"{base_run_id}-{index:03d}"
        if not candidate.exists():
            candidate.mkdir()
            return candidate

    raise ConverterError(f"Unable to allocate run directory under: {runs_dir}")


def _build_run_metadata(
    run_id: str,
    input_dir: Path,
    output_dir: Path,
    config: ConverterConfig,
) -> dict[str, Any]:
    options = asdict(config.options)
    options["ocr_languages"] = list(config.options.ocr_languages)
    return {
        "schema_version": "run.v1",
        "run_id": run_id,
        "converter_version": __version__,
        "created_at": datetime.now(UTC).isoformat(),
        "input_dir": str(input_dir),
        "output_dir": str(output_dir),
        "options": options,
    }


def _document_output_dir(documents_dir: Path, sha256: str) -> Path:
    document_dir = documents_dir / f"sha256_{sha256}"
    document_dir.mkdir(parents=True, exist_ok=True)
    return document_dir


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")