from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from .. import __version__
from ..config import AgentRunMetadata, ConverterConfig, serialize_converter_options
from ..converters.docx import ConversionResult, convert_docx
from ..converters.pdf_scan import PdfScanConversionResult, convert_pdf_scan
from ..converters.pdf_text import PdfTextConversionResult, convert_pdf_text
from ..converters.xlsx import XlsxConversionResult, convert_xlsx
from ..inventory import build_inventory
from ..schema_validation import validate_payload
from .catalog import _write_processed_documents_catalog
from .paths import ConverterError, _allocate_run_dir, _document_output_path, _new_run_id, validate_run_directories
from .postprocess import (
    _build_review_required_records,
    _count_reason_map,
    _merge_formula_recognition_manifest_data,
    _queue_state_status,
    _run_formula_recognition_stage,
    _summary_status,
)
from .resume import _copy_result_metadata, _load_resume_index, _reuse_document_dir


@dataclass(frozen=True)
class RunResult:
    run_id: str
    run_dir: Path
    discovered_files: int
    supported_files: int
    status: str


def run_convert_folder(
    config: ConverterConfig,
    *,
    progress_callback: Callable[[dict[str, object]], None] | None = None,
    should_cancel: Callable[[], bool] | None = None,
) -> RunResult:
    input_dir, output_dir = validate_run_directories(config.input_dir, config.output_dir)

    run_id = _new_run_id()
    run_dir = _allocate_run_dir(output_dir / "runs", run_id)
    documents_dir = run_dir / "documents"
    documents_dir.mkdir(parents=True, exist_ok=False)

    run_metadata = _build_run_metadata(run_id, input_dir, output_dir, config)
    _write_validated_json(run_dir / "run.json", run_metadata, "run.v1.schema.json")

    inventory = build_inventory(input_dir)
    inventory_records = inventory.supported_records
    unsupported_records = inventory.unsupported_records

    manifest_path = run_dir / "manifest.jsonl"
    log_path = run_dir / "processing-log.jsonl"
    errors_path = run_dir / "errors.jsonl"
    queue_state_path = run_dir / "queue-state.json"
    review_required_path = run_dir / "review-required.jsonl"

    _write_text(manifest_path, "")
    _write_text(errors_path, "")
    _write_text(review_required_path, "")
    _append_jsonl(log_path, {"event": "run_started", "run_id": run_id, "status": "ok"})

    resume_index = _load_resume_index(output_dir / "runs", run_dir)
    total_files = len(inventory_records)
    error_details_by_relative_path: dict[str, str] = {}
    for unsupported_record in unsupported_records:
        _append_jsonl(
            log_path,
            {
                "event": "document_skipped_unsupported",
                "run_id": run_id,
                "relative_path": unsupported_record.relative_path,
                "filename": unsupported_record.filename,
                "format": unsupported_record.format,
                "size_bytes": unsupported_record.size_bytes,
                "warnings": list(unsupported_record.warnings),
                "status": "skipped_unsupported",
            },
        )
    _emit_progress(
        progress_callback,
        {
            "event": "inventory_built",
            "run_id": run_id,
            "total_files": total_files,
            "processed_files": 0,
        },
    )

    completed: list[str] = []
    partial: list[str] = []
    failed: list[str] = []
    final_manifest_records: list[dict[str, object]] = []
    manifest_by_relative_path: dict[str, dict[str, object]] = {}
    cancelled = False

    for record in inventory_records:
        if should_cancel is not None and should_cancel():
            cancelled = True
            _append_jsonl(
                log_path,
                {
                    "event": "run_cancelled",
                    "run_id": run_id,
                    "status": "cancelled",
                    "processed_files": len(completed) + len(partial) + len(failed),
                },
            )
            _emit_progress(
                progress_callback,
                {
                    "event": "run_cancelled",
                    "run_id": run_id,
                    "total_files": total_files,
                    "processed_files": len(completed) + len(partial) + len(failed),
                },
            )
            break

        manifest_record = record.to_manifest_record(run_id)
        if record.route in {"docx_native", "pdf_text", "pdf_scan", "xlsx_native"}:
            document_dir = _document_output_path(documents_dir, record.sha256)
            _emit_progress(
                progress_callback,
                {
                    "event": "document_started",
                    "run_id": run_id,
                    "relative_path": record.relative_path,
                    "total_files": total_files,
                    "processed_files": len(completed) + len(partial) + len(failed),
                },
            )
            if record.duplicate_of is not None:
                primary_manifest = manifest_by_relative_path.get(record.duplicate_of)
                if primary_manifest is None:
                    raise ConverterError(f"Primary duplicate record was not processed first: {record.duplicate_of}")
                manifest_record["status"] = "skipped_duplicate"
                if "output_dir" in primary_manifest:
                    manifest_record["output_dir"] = primary_manifest["output_dir"]
                _copy_result_metadata(primary_manifest, manifest_record)
                if config.options.include_originals and "output_dir" in manifest_record:
                    _copy_original_file(
                        input_dir / record.relative_path,
                        run_dir / str(manifest_record["output_dir"]),
                        record.relative_path,
                    )
                completed.append(record.relative_path)
                _append_jsonl(
                    log_path,
                    {
                        "event": "document_skipped_duplicate",
                        "run_id": run_id,
                        "relative_path": record.relative_path,
                        "duplicate_of": record.duplicate_of,
                        "status": "skipped_duplicate",
                    },
                )
                _emit_progress(
                    progress_callback,
                    {
                        "event": "document_finished",
                        "run_id": run_id,
                        "relative_path": record.relative_path,
                        "status": "skipped_duplicate",
                        "total_files": total_files,
                        "processed_files": len(completed) + len(partial) + len(failed),
                    },
                )
                final_manifest_records.append(manifest_record)
                manifest_by_relative_path[record.relative_path] = manifest_record
                continue

            resume_hit = resume_index.get((record.sha256, record.relative_path))
            if resume_hit is not None:
                source_document_dir = (output_dir / "runs" / resume_hit.run_id / resume_hit.output_dir).resolve()
                _reuse_document_dir(source_document_dir, document_dir)
                manifest_record["status"] = resume_hit.status
                manifest_record["output_dir"] = document_dir.relative_to(run_dir).as_posix()
                manifest_record["resumed_from_run_id"] = resume_hit.run_id
                manifest_record["reused_previous_output"] = True
                _copy_result_metadata(resume_hit.manifest_record, manifest_record)
                if config.options.include_originals:
                    _copy_original_file(input_dir / record.relative_path, document_dir, record.relative_path)
                if resume_hit.status == "partial_success":
                    partial.append(record.relative_path)
                else:
                    completed.append(record.relative_path)
                _append_jsonl(
                    log_path,
                    {
                        "event": "document_reused",
                        "run_id": run_id,
                        "relative_path": record.relative_path,
                        "route": record.route,
                        "status": resume_hit.status,
                        "resumed_from_run_id": resume_hit.run_id,
                    },
                )
                _emit_progress(
                    progress_callback,
                    {
                        "event": "document_finished",
                        "run_id": run_id,
                        "relative_path": record.relative_path,
                        "status": resume_hit.status,
                        "total_files": total_files,
                        "processed_files": len(completed) + len(partial) + len(failed),
                    },
                )
                final_manifest_records.append(manifest_record)
                manifest_by_relative_path[record.relative_path] = manifest_record
                continue

            try:
                result: ConversionResult | PdfTextConversionResult | PdfScanConversionResult | XlsxConversionResult
                if record.route == "docx_native":
                    result = convert_docx(
                        input_dir / record.relative_path,
                        document_dir,
                        record.sha256,
                        relative_source_path=record.relative_path,
                    )
                    manifest_record["assets_count"] = result.assets_count
                    manifest_record["search_text_chars"] = result.search_text_chars
                elif record.route == "pdf_text":
                    result = convert_pdf_text(
                        input_dir / record.relative_path,
                        document_dir,
                        record.sha256,
                        relative_source_path=record.relative_path,
                    )
                    manifest_record["pages"] = result.pages
                    manifest_record["search_text_chars"] = result.text_chars
                elif record.route == "xlsx_native":
                    result = convert_xlsx(
                        input_dir / record.relative_path,
                        document_dir,
                        record.sha256,
                        relative_source_path=record.relative_path,
                    )
                    manifest_record["sheets"] = result.sheets
                    manifest_record["search_text_chars"] = result.text_chars
                    manifest_record["formula_cells"] = result.formula_cells
                    manifest_record["warnings"] = list(result.warnings)
                else:
                    result = convert_pdf_scan(
                        input_dir / record.relative_path,
                        document_dir,
                        record.sha256,
                        config.options.ocr_languages,
                        relative_source_path=record.relative_path,
                    )
                    manifest_record["pages"] = result.pages
                    manifest_record["search_text_chars"] = result.text_chars
                    manifest_record["warnings"] = list(result.warnings)
                manifest_record["status"] = result.status
                manifest_record["output_dir"] = document_dir.relative_to(run_dir).as_posix()
                manifest_record["units_count"] = result.units_count
                formula_result = _run_formula_recognition_stage(document_dir, config)
                _merge_formula_recognition_manifest_data(manifest_record, formula_result)
                if config.options.include_originals:
                    manifest_record["original_copy_path"] = _copy_original_file(
                        input_dir / record.relative_path,
                        document_dir,
                        record.relative_path,
                    )
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
                _emit_progress(
                    progress_callback,
                    {
                        "event": "document_finished",
                        "run_id": run_id,
                        "relative_path": record.relative_path,
                        "status": result.status,
                        "total_files": total_files,
                        "processed_files": len(completed) + len(partial) + len(failed),
                    },
                )
            except Exception as exc:  # noqa: BLE001 - batch run records per-document failures.
                manifest_record["status"] = "failed"
                manifest_record["error"] = type(exc).__name__
                error_details_by_relative_path[record.relative_path] = str(exc)
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
                _emit_progress(
                    progress_callback,
                    {
                        "event": "document_finished",
                        "run_id": run_id,
                        "relative_path": record.relative_path,
                        "status": "failed",
                        "total_files": total_files,
                        "processed_files": len(completed) + len(partial) + len(failed),
                    },
                )
        manifest_by_relative_path[record.relative_path] = manifest_record
        final_manifest_records.append(manifest_record)

    for manifest_record in final_manifest_records:
        _append_validated_jsonl(manifest_path, manifest_record, "manifest.v1.schema.json")

    review_required_records = _build_review_required_records(run_dir, run_id, final_manifest_records)
    for review_required_record in review_required_records:
        _append_validated_jsonl(review_required_path, review_required_record, "review-required.v1.schema.json")

    _write_processed_documents_catalog(
        run_dir=run_dir,
        run_id=run_id,
        inventory_records=inventory_records,
        unsupported_records=unsupported_records,
        manifest_records=final_manifest_records,
        error_details_by_relative_path=error_details_by_relative_path,
        write_validated_json=_write_validated_json,
    )

    duplicate_groups = sorted({record.duplicate_group_id for record in inventory_records if record.duplicate_group_id})
    queue_state = {
        "schema_version": "queue-state.v1",
        "run_id": run_id,
        "status": _queue_state_status(cancelled, completed, partial, failed),
        "queued": [
            record.relative_path
            for record in inventory_records
            if record.relative_path not in completed and record.relative_path not in partial and record.relative_path not in failed
        ],
        "completed": completed,
        "partial": partial,
        "failed": failed,
    }
    _write_validated_json(queue_state_path, queue_state, "queue-state.v1.schema.json")

    summary = {
        "schema_version": "summary.v1",
        "run_id": run_id,
        "status": _summary_status(cancelled, completed, partial, failed),
        "input_dir": str(input_dir),
        "output_dir": str(output_dir),
        "run_dir": str(run_dir),
        "discovered_files": inventory.scanned_files,
        "supported_files": len(inventory_records),
        "unsupported_files": len(unsupported_records),
        "duplicate_groups": len(duplicate_groups),
        "processed_files": len(completed) + len(partial),
        "partial_files": len(partial),
        "failed_files": len(failed),
        "review_required_files": len(review_required_records),
        "review_required_reasons": _count_reason_map(record["flags"] for record in review_required_records),
        "partial_reasons": _count_reason_map(
            record["flags"] for record in review_required_records if record["status"] == "partial_success"
        ),
        "failed_reasons": _count_reason_map(
            [str(record["error_type"])]
            for record in review_required_records
            if record["status"] == "failed" and record.get("error_type")
        ),
    }
    _write_validated_json(run_dir / "summary.json", summary, "summary.v1.schema.json")
    final_status = _summary_status(cancelled, completed, partial, failed)
    _append_jsonl(log_path, {"event": "run_completed", "run_id": run_id, "status": final_status})
    _emit_progress(
        progress_callback,
        {
            "event": "run_completed",
            "run_id": run_id,
            "status": final_status,
            "total_files": total_files,
            "processed_files": len(completed) + len(partial) + len(failed),
        },
    )

    return RunResult(
        run_id=run_id,
        run_dir=run_dir,
        discovered_files=inventory.scanned_files,
        supported_files=len(inventory_records),
        status=final_status,
    )


def _build_run_metadata(
    run_id: str,
    input_dir: Path,
    output_dir: Path,
    config: ConverterConfig,
) -> dict[str, Any]:
    return {
        "schema_version": "run.v1",
        "run_id": run_id,
        "converter_version": __version__,
        "created_at": datetime.now(UTC).isoformat(),
        "input_dir": str(input_dir),
        "output_dir": str(output_dir),
        "options": serialize_converter_options(config.options),
        "agent_run_metadata": _agent_run_metadata_payload(config.agent_run_metadata, run_id),
    }


def _agent_run_metadata_payload(metadata: AgentRunMetadata | None, run_id: str) -> dict[str, str]:
    agent_id = _nonempty_string(metadata.agent_id) if metadata is not None else None
    agent_version = _nonempty_string(metadata.agent_version) if metadata is not None else None
    task_id = _nonempty_string(metadata.task_id) if metadata is not None else None
    parent_run_id = _nonempty_string(metadata.parent_run_id) if metadata is not None else None

    payload = {
        "agent_id": agent_id or "manual",
        "agent_version": agent_version or __version__,
        "task_id": task_id or run_id,
    }
    if parent_run_id is not None:
        payload["parent_run_id"] = parent_run_id
    return payload


def _nonempty_string(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _emit_progress(
    progress_callback: Callable[[dict[str, object]], None] | None,
    payload: dict[str, object],
) -> None:
    if progress_callback is not None:
        progress_callback(payload)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_validated_json(path: Path, payload: dict[str, Any], schema_filename: str) -> None:
    validate_payload(payload, schema_filename)
    _write_json(path, payload)


def _append_validated_jsonl(path: Path, payload: dict[str, Any], schema_filename: str) -> None:
    validate_payload(payload, schema_filename)
    _append_jsonl(path, payload)


def _copy_original_file(source_path: Path, document_dir: Path, relative_path: str) -> str:
    target = document_dir / "originals" / Path(relative_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, target)
    return target.relative_to(document_dir).as_posix()


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")