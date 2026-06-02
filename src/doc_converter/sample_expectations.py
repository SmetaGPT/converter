from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

UNIT_ID_RE = re.compile(r"^u_[0-9]{6}$")
WINDOWS_ABSOLUTE_PATH_RE = re.compile(r"^(?:[A-Za-z]:[\\/]|\\\\)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate representative sample expectations against a converter run.")
    parser.add_argument("run_dir", type=Path, help="Path to converter run directory")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("samples") / "manifest.sample.jsonl",
        help="Path to representative sample manifest JSONL",
    )
    parser.add_argument(
        "--expected-dir",
        type=Path,
        default=Path("samples") / "expected",
        help="Directory with sample_*.expected-units.json fixtures",
    )
    parser.add_argument(
        "--sample-id",
        action="append",
        default=[],
        help="Validate only a specific representative sample_id. Can be passed multiple times.",
    )
    args = parser.parse_args(argv)

    summary = validate_sample_expectations(
        run_dir=args.run_dir.expanduser().resolve(),
        sample_manifest_path=args.manifest.expanduser().resolve(),
        expected_dir=args.expected_dir.expanduser().resolve(),
        sample_ids=set(args.sample_id) or None,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["status"] == "ok" else 1


def validate_sample_expectations(
    *,
    run_dir: Path,
    sample_manifest_path: Path,
    expected_dir: Path,
    sample_ids: set[str] | None = None,
) -> dict[str, Any]:
    manifest_records = _read_jsonl(sample_manifest_path)
    expected_specs = _load_expected_specs(expected_dir)
    run_manifest = _read_jsonl(run_dir / "manifest.jsonl")

    manifest_by_sample_id = {str(record["sample_id"]): record for record in manifest_records}
    run_by_sha = {str(record["sha256"]): record for record in run_manifest}

    results: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    checked_samples = 0

    for sample_id, expected in sorted(expected_specs.items()):
        if sample_ids is not None and sample_id not in sample_ids:
            continue
        sample_record = manifest_by_sample_id.get(sample_id)
        issues: list[str] = []
        metrics: dict[str, Any] = {}
        checked_samples += 1

        if sample_record is None:
            issues.append(f"sample manifest record missing for {sample_id}")
            result = {"sample_id": sample_id, "issues": issues, "table_metrics": metrics}
            results.append(result)
            failures.append(result)
            continue

        run_record = run_by_sha.get(str(sample_record["sha256"]))
        if run_record is None:
            issues.append(f"run manifest record missing for sha256 {sample_record['sha256']}")
            missing_run_result: dict[str, Any] = {"sample_id": sample_id, "issues": issues, "table_metrics": metrics}
            results.append(missing_run_result)
            failures.append(missing_run_result)
            continue

        document_path = run_dir / str(run_record["output_dir"]) / "document.v1.json"
        if not document_path.exists():
            issues.append(f"missing document artifact: {document_path}")
            missing_document_result: dict[str, Any] = {"sample_id": sample_id, "issues": issues, "table_metrics": metrics}
            results.append(missing_document_result)
            failures.append(missing_document_result)
            continue

        document_payload = _read_json(document_path)
        metrics = _compute_table_metrics(document_payload)
        issues.extend(_validate_sample(sample_id, sample_record, run_record, document_payload, expected, metrics))

        sample_result: dict[str, Any] = {
            "sample_id": sample_id,
            "route": run_record.get("route"),
            "status": run_record.get("status"),
            "table_metrics": metrics,
            "issues": issues,
        }
        results.append(sample_result)
        if issues:
            failures.append(sample_result)

    return {
        "status": "ok" if not failures else "failed",
        "samples_checked": checked_samples,
        "samples_failed": len(failures),
        "results": results,
    }


def _validate_sample(
    sample_id: str,
    sample_record: dict[str, Any],
    run_record: dict[str, Any],
    document_payload: dict[str, Any],
    expected: dict[str, Any],
    table_metrics: dict[str, Any],
) -> list[str]:
    issues: list[str] = []
    unit_counts = Counter(_unit.get("type") for _unit in document_payload.get("units", []))
    doc_quality_flags = set(_quality_flags(document_payload))
    expected_units = expected.get("expected_units") or {}
    references = expected.get("required_references") or {}
    quality_expectations = expected.get("quality_expectations") or {}
    processing_expectations = expected.get("processing_expectations") or {}
    table_expectations = expected.get("table_expectations") or {}

    if expected.get("route") != run_record.get("route"):
        issues.append(
            f"route mismatch for {sample_id}: expected {expected.get('route')}, got {run_record.get('route')}"
        )

    if processing_expectations.get("status") != run_record.get("status") and processing_expectations.get("status") is not None:
        issues.append(
            f"status mismatch for {sample_id}: expected {processing_expectations.get('status')}, got {run_record.get('status')}"
        )

    processing_payload = document_payload.get("processing") or {}
    if processing_expectations.get("ocr_applied") is not None and bool(processing_payload.get("ocr_applied")) != bool(
        processing_expectations.get("ocr_applied")
    ):
        issues.append(
            f"ocr_applied mismatch for {sample_id}: expected {processing_expectations.get('ocr_applied')}, got {processing_payload.get('ocr_applied')}"
        )

    expected_warnings = processing_expectations.get("warnings_include") or []
    actual_warnings = {str(warning) for warning in processing_payload.get("warnings", [])}
    for warning in expected_warnings:
        if warning not in actual_warnings:
            issues.append(f"missing processing warning for {sample_id}: {warning}")

    for required_type in expected_units.get("required_types", []):
        if unit_counts.get(required_type, 0) <= 0:
            issues.append(f"missing required unit type for {sample_id}: {required_type}")

    for unit_type, minimum in (expected_units.get("minimum_counts") or {}).items():
        actual = unit_counts.get(unit_type, 0)
        if actual < int(minimum):
            issues.append(f"minimum count failed for {sample_id}: {unit_type} {actual} < {minimum}")

    forbidden_regression = expected_units.get("forbidden_regression") or {}
    if forbidden_regression.get("table_count_must_not_be_fabricated") and unit_counts.get("table", 0) != 0:
        issues.append(f"forbidden regression for {sample_id}: fabricated table units detected")
    if forbidden_regression.get("figure_count_must_not_be_fabricated") and unit_counts.get("figure", 0) != 0:
        issues.append(f"forbidden regression for {sample_id}: fabricated figure units detected")

    if references.get("stable_document_id"):
        expected_document_id = f"sha256:{sample_record['sha256']}"
        if document_payload.get("document_id") != expected_document_id:
            issues.append(
                f"document_id mismatch for {sample_id}: {document_payload.get('document_id')} != {expected_document_id}"
            )

    if references.get("stable_unit_ids"):
        unit_ids = [str(unit.get("unit_id")) for unit in document_payload.get("units", []) if unit.get("unit_id")]
        if len(unit_ids) != len(set(unit_ids)):
            issues.append(f"duplicate unit_id detected for {sample_id}")
        if any(UNIT_ID_RE.fullmatch(unit_id) is None for unit_id in unit_ids):
            issues.append(f"non-stable unit_id format detected for {sample_id}")

    if references.get("preserve_reading_order"):
        orders = [int(unit.get("order")) for unit in document_payload.get("units", []) if unit.get("order") is not None]
        if orders != sorted(orders) or len(orders) != len(set(orders)):
            issues.append(f"reading order drift detected for {sample_id}")

    if references.get("page_refs"):
        for unit in document_payload.get("units", []):
            if unit.get("type") == "document":
                continue
            source_ref = unit.get("source_ref") or {}
            if source_ref.get("page") is None:
                issues.append(f"missing page reference for {sample_id} unit {unit.get('unit_id')}")
                break

    if references.get("bbox_refs_when_available"):
        page_units = [unit for unit in document_payload.get("units", []) if unit.get("type") == "page"]
        if any((unit.get("source_ref") or {}).get("bbox") is None for unit in page_units):
            issues.append(f"missing page bbox for {sample_id}")

    if references.get("asset_refs_relative"):
        for asset in document_payload.get("assets", []):
            path = str(asset.get("path") or "")
            if WINDOWS_ABSOLUTE_PATH_RE.match(path):
                issues.append(f"absolute asset path detected for {sample_id}: {path}")
                break

    if references.get("ocr_artifact_refs"):
        asset_types = {str(asset.get("type")) for asset in document_payload.get("assets", [])}
        missing = {"ocr_pdf", "ocr_sidecar"} - asset_types
        if missing:
            issues.append(f"missing OCR artifact refs for {sample_id}: {', '.join(sorted(missing))}")

    if references.get("preserve_original_pdf"):
        source = document_payload.get("source") or {}
        source_name = str(source.get("relative_input_path") or source.get("filename") or "")
        if not source_name.endswith(str(sample_record.get("filename") or "")):
            issues.append(f"source filename drift detected for {sample_id}")

    for flag_name, expected_value in quality_expectations.items():
        if not isinstance(expected_value, bool):
            continue
        has_flag = flag_name in doc_quality_flags
        if expected_value and not has_flag:
            issues.append(f"missing quality flag for {sample_id}: {flag_name}")
        if not expected_value and has_flag:
            issues.append(f"unexpected quality flag for {sample_id}: {flag_name}")

    for metric_name, comparator in table_expectations.items():
        metric_value = table_metrics.get(metric_name)
        if metric_value is None:
            issues.append(f"unknown table metric for {sample_id}: {metric_name}")
            continue
        if not _table_metric_matches(float(metric_value), comparator):
            issues.append(
                f"table metric check failed for {sample_id}: {metric_name} actual={metric_value} expected={comparator}"
            )

    return issues


def _table_metric_matches(actual: float, comparator: Any) -> bool:
    if isinstance(comparator, (int, float)):
        return actual >= float(comparator)
    if not isinstance(comparator, dict):
        return False
    minimum = comparator.get("min")
    maximum = comparator.get("max")
    exact = comparator.get("equals")
    if exact is not None and actual != float(exact):
        return False
    if minimum is not None and actual < float(minimum):
        return False
    return not (maximum is not None and actual > float(maximum))


def _compute_table_metrics(document_payload: dict[str, Any]) -> dict[str, Any]:
    units = document_payload.get("units", [])
    units_by_parent: dict[str, list[dict[str, Any]]] = {}
    for unit in units:
        parent_id = unit.get("parent_id")
        if parent_id is None:
            continue
        units_by_parent.setdefault(str(parent_id), []).append(unit)

    table_units = [unit for unit in units if unit.get("type") == "table"]
    table_row_units = [unit for unit in units if unit.get("type") == "table_row"]
    table_cell_units = [unit for unit in units if unit.get("type") == "table_cell"]
    rows_with_two_plus_cells = 0
    single_cell_rows = 0
    warning_tables = 0
    maximum_cells_per_row = 0

    for table in table_units:
        if "table_structure_warning" in _quality_flags(table):
            warning_tables += 1

    for row in table_row_units:
        row_id = str(row.get("unit_id") or "")
        cell_count = len(units_by_parent.get(row_id, []))
        maximum_cells_per_row = max(maximum_cells_per_row, cell_count)
        if cell_count >= 2:
            rows_with_two_plus_cells += 1
        elif cell_count == 1:
            single_cell_rows += 1

    total_rows = len(table_row_units)
    average_cells_per_row = round(len(table_cell_units) / total_rows, 4) if total_rows else 0.0
    wide_row_ratio = round(rows_with_two_plus_cells / total_rows, 4) if total_rows else 0.0
    single_cell_row_ratio = round(single_cell_rows / total_rows, 4) if total_rows else 0.0

    return {
        "table_units": len(table_units),
        "table_rows": total_rows,
        "table_cells": len(table_cell_units),
        "rows_with_two_plus_cells": rows_with_two_plus_cells,
        "single_cell_rows": single_cell_rows,
        "maximum_cells_per_row": maximum_cells_per_row,
        "average_cells_per_row": average_cells_per_row,
        "wide_row_ratio": wide_row_ratio,
        "single_cell_row_ratio": single_cell_row_ratio,
        "warning_tables": warning_tables,
    }


def _quality_flags(payload: dict[str, Any]) -> list[str]:
    quality = payload.get("quality")
    if not isinstance(quality, dict):
        return []
    flags = quality.get("flags")
    if not isinstance(flags, list):
        return []
    return [str(flag) for flag in flags]


def _load_expected_specs(expected_dir: Path) -> dict[str, dict[str, Any]]:
    specs: dict[str, dict[str, Any]] = {}
    for path in sorted(expected_dir.glob("*.expected-units.json")):
        payload = _read_json(path)
        sample_id = str(payload["sample_id"])
        specs[sample_id] = payload
    return specs


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


if __name__ == "__main__":
    raise SystemExit(main())
