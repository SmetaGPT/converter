from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..config import ConverterConfig
from ..formula_recognition import (
    FormulaRecognitionPostprocessResult,
    FormulaRecognitionRunState,
    run_formula_recognition_postprocess,
)
from ..schema_validation import SchemaValidationError, validate_json_file


def _run_formula_recognition_stage(
    document_dir: Path,
    config: ConverterConfig,
    run_state: FormulaRecognitionRunState,
) -> FormulaRecognitionPostprocessResult:
    try:
        return run_formula_recognition_postprocess(document_dir, config.options.formula_recognition, run_state=run_state)
    except Exception:  # noqa: BLE001 - best-effort network stage must not fail document conversion.
        return FormulaRecognitionPostprocessResult(warnings=("formula_recognition_postprocess_failed",))


def _merge_formula_recognition_manifest_data(
    manifest_record: dict[str, object],
    formula_result: FormulaRecognitionPostprocessResult,
) -> None:
    if formula_result.attempted > 0:
        manifest_record["formula_recognition_attempted"] = formula_result.attempted
        manifest_record["formula_recognition_recognized"] = formula_result.recognized
        manifest_record["formula_recognition_provider_calls"] = formula_result.provider_calls
        manifest_record["formula_recognition_cache_hits"] = formula_result.cache_hits
        manifest_record["formula_recognition_estimated_cost_usd"] = formula_result.estimated_cost_usd
        manifest_record["formula_recognition_review_required_units"] = formula_result.review_required_units
    if formula_result.artifact_path is not None:
        manifest_record["formula_recognition_results_path"] = formula_result.artifact_path
    if formula_result.warnings:
        warnings = manifest_record.get("warnings")
        warning_list = [str(item) for item in warnings] if isinstance(warnings, list) else []
        for warning in formula_result.warnings:
            if warning not in warning_list:
                warning_list.append(warning)
        manifest_record["warnings"] = warning_list


def _summary_status(cancelled: bool, completed: list[str], partial: list[str], failed: list[str]) -> str:
    if cancelled:
        return "cancelled"
    if failed and not completed and not partial:
        return "failed"
    if failed or partial:
        return "partial_success"
    return "success"


def _queue_state_status(cancelled: bool, completed: list[str], partial: list[str], failed: list[str]) -> str:
    if cancelled:
        return "cancelled"
    if failed and not completed and not partial:
        return "failed"
    if failed or partial:
        return "partial_success"
    return "completed"


def _build_review_required_records(
    run_dir: Path,
    run_id: str,
    manifest_records: list[dict[str, object]],
) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for manifest_record in manifest_records:
        status = str(manifest_record.get("status", ""))
        output_dir = manifest_record.get("output_dir")
        flags: list[str] = []
        warnings: list[str] = []
        document_id: str | None = None
        if isinstance(output_dir, str):
            document_path = run_dir / output_dir / "document.v1.json"
            if document_path.exists():
                try:
                    payload = validate_json_file(document_path, "document.v1.schema.json")
                    document_id = str(payload.get("document_id"))
                    flags = [str(flag) for flag in payload.get("quality", {}).get("flags", [])]
                    warnings = [str(warning) for warning in payload.get("quality", {}).get("warnings", [])]
                except (OSError, json.JSONDecodeError, SchemaValidationError) as exc:
                    warnings.append(f"document_validation_failed:{type(exc).__name__}")
        error_type = str(manifest_record.get("error", "")) or None
        if status == "failed" and error_type is not None:
            warnings.append(error_type)
        if status in {"partial_success", "failed"} or "review_required" in flags or warnings:
            records.append(
                {
                    "schema_version": "review-required.v1",
                    "run_id": run_id,
                    "relative_path": str(manifest_record["relative_path"]),
                    "status": status,
                    "document_id": document_id,
                    "output_dir": output_dir if isinstance(output_dir, str) else None,
                    "flags": flags,
                    "warnings": warnings,
                    "error_type": error_type,
                }
            )
    return records


def _count_reason_map(reason_groups: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for reasons in reason_groups:
        for reason in reasons:
            normalized = str(reason).strip()
            if not normalized:
                continue
            counts[normalized] = counts.get(normalized, 0) + 1
    return dict(sorted(counts.items()))
