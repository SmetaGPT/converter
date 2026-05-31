from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, cast

from doc_converter.canonical import sha256_file
from doc_converter.config import ConverterConfig, ConverterOptions, FormulaRecognitionConfig, load_formula_recognition_config
from doc_converter.runner import run_convert_folder
from doc_converter.schema_validation import validate_json_file


ROOT = Path(__file__).resolve().parents[2]

_FORMULA_UNIT_TYPES = {"formula", "formula_image"}
_FORMULA_SOURCE_FORMATS = {
    "docx_text_linearized",
    "mathtype_wmf_text_records",
    "heuristic_latex",
}
_FORMULA_CONFIDENCE = {"high", "medium", "low"}
_INPUT_KINDS = {"source_file", "document_json"}
_BENCHMARK_CACHE_VERSION = "formula-benchmark-incremental-v1"
_AGGREGATE_COUNT_FIELDS = (
    "formula_units",
    "calc_expr_units",
    "low_confidence_units",
    "provider_generated_units",
    "native_units",
    "heuristic_units",
)
_TIER_ORDER = {"anchor": 0, "gate": 1, "control": 2, "rolling": 3}


class FormulaBenchmarkError(ValueError):
    pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a formula benchmark manifest and write machine-readable benchmark artifacts."
    )
    parser.add_argument("manifest", type=Path, help="Path to formula benchmark manifest JSONL.")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=ROOT / "runs" / "formula-benchmark",
        help="Root folder for formula benchmark runs.",
    )
    parser.add_argument(
        "--keep-case-inputs",
        action="store_true",
        help="Keep copied per-case input files under the benchmark run directory.",
    )
    parser.add_argument(
        "--thresholds",
        type=Path,
        default=ROOT / "samples" / "formula-benchmark.thresholds.json",
        help="Optional threshold policy JSON used to evaluate the required benchmark gate.",
    )
    parser.add_argument(
        "--no-thresholds",
        action="store_true",
        help="Disable threshold evaluation and run the manifest in monitor-only mode.",
    )
    args = parser.parse_args(argv)

    report = run_benchmark_manifest(
        args.manifest,
        output_root=args.output_root,
        keep_case_inputs=args.keep_case_inputs,
        thresholds_path=None if args.no_thresholds else args.thresholds,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "ok" else 1


def run_benchmark_manifest(
    manifest_path: Path,
    *,
    output_root: Path | None = None,
    keep_case_inputs: bool = False,
    thresholds_path: Path | None = None,
) -> dict[str, Any]:
    manifest_path = manifest_path.expanduser().resolve()
    manifest_dir = manifest_path.parent
    thresholds_path = thresholds_path.expanduser().resolve() if thresholds_path is not None else None
    entries = _load_manifest(manifest_path)

    benchmark_root = (output_root or ROOT / "runs" / "formula-benchmark").expanduser().resolve()
    benchmark_run_dir = benchmark_root / "runs" / _timestamp_slug()
    cache_root = benchmark_root / "cache"
    benchmark_run_dir.mkdir(parents=True, exist_ok=True)
    cache_root.mkdir(parents=True, exist_ok=True)

    case_reports: list[dict[str, Any]] = []
    totals: dict[str, Any] = {
        "entries": 0,
        "available_entries": 0,
        "required_failures": 0,
        "gold_entries": 0,
        "gold_passed_entries": 0,
        "gold_failed_entries": 0,
        "formula_units": 0,
        "calc_expr_units": 0,
        "low_confidence_units": 0,
        "provider_generated_units": 0,
        "native_units": 0,
        "heuristic_units": 0,
        "source_format_counts": {},
        "confidence_counts": {},
    }

    for entry in entries:
        case_report = benchmark_manifest_entry(
            entry,
            manifest_dir=manifest_dir,
            benchmark_run_dir=benchmark_run_dir,
            keep_case_inputs=keep_case_inputs,
            cache_root=cache_root,
        )
        case_reports.append(case_report)
        totals["entries"] += 1

        if case_report["status"] == "skipped_missing_input":
            if case_report["required"]:
                totals["required_failures"] += 1
            continue

        if case_report["status"] not in {"ok", "gold_failed"}:
            if case_report["required"]:
                totals["required_failures"] += 1
            continue

        totals["available_entries"] += 1
        summary = case_report["summary"]
        totals["formula_units"] += summary["formula_units"]
        totals["calc_expr_units"] += summary["calc_expr_units"]
        totals["low_confidence_units"] += summary["low_confidence_units"]
        totals["provider_generated_units"] += summary["provider_generated_units"]
        totals["native_units"] += summary["native_units"]
        totals["heuristic_units"] += summary["heuristic_units"]
        _merge_counter(totals["source_format_counts"], summary["source_format_counts"])
        _merge_counter(totals["confidence_counts"], summary["confidence_counts"])

        gold_comparison = case_report.get("gold_comparison")
        if isinstance(gold_comparison, dict) and gold_comparison.get("status") != "no_gold":
            totals["gold_entries"] += 1
            if gold_comparison["status"] == "passed":
                totals["gold_passed_entries"] += 1
            else:
                totals["gold_failed_entries"] += 1
                if case_report["required"]:
                    totals["required_failures"] += 1

    _finalize_aggregate_metrics(totals)
    tier_summaries = _build_tier_summaries(case_reports)

    status = "ok" if totals["required_failures"] == 0 else "failed"
    threshold_policy = _load_threshold_policy(thresholds_path) if thresholds_path is not None else None
    required_gate = None
    if threshold_policy is not None:
        required_gate = evaluate_threshold_policy(
            threshold_policy,
            overall_summary=totals,
            tier_summaries=tier_summaries,
        )
        if required_gate["status"] != "passed":
            status = "failed"

    report: dict[str, Any] = {
        "schema_version": "formula-benchmark-report.v1",
        "generated_at": _iso_timestamp(),
        "status": status,
        "manifest_path": str(manifest_path),
        "benchmark_run_dir": str(benchmark_run_dir),
        "thresholds_path": str(thresholds_path) if threshold_policy is not None else None,
        "tier_summaries": tier_summaries,
        "required_gate": required_gate,
        "entries": case_reports,
        "totals": totals,
    }

    report_path = benchmark_run_dir / "benchmark-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path = benchmark_run_dir / "benchmark-report.md"
    markdown_path.write_text(render_benchmark_markdown(report), encoding="utf-8")
    formula_summary = build_formula_summary(report)
    formula_summary_path = benchmark_run_dir / "formula-summary.json"
    formula_summary_path.write_text(json.dumps(formula_summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    formula_summary_markdown_path = benchmark_run_dir / "formula-summary.md"
    formula_summary_markdown_path.write_text(render_formula_summary_markdown(formula_summary), encoding="utf-8")
    return report


def benchmark_manifest_entry(
    entry: Mapping[str, Any],
    *,
    manifest_dir: Path,
    benchmark_run_dir: Path,
    keep_case_inputs: bool,
    cache_root: Path | None = None,
) -> dict[str, Any]:
    benchmark_id = str(entry["benchmark_id"])
    case_dir = benchmark_run_dir / "cases" / _safe_slug(benchmark_id)
    case_dir.mkdir(parents=True, exist_ok=True)

    required = bool(entry.get("required", True))
    input_kind = str(entry["input_kind"])
    input_path = _resolve_path(str(entry["input_path"]), base_dir=manifest_dir)
    gold_path = _resolve_optional_path(entry.get("gold_path"), base_dir=manifest_dir)

    base_report: dict[str, Any] = {
        "benchmark_id": benchmark_id,
        "tier": str(entry["tier"]),
        "label": str(entry["label"]),
        "required": required,
        "input_kind": input_kind,
        "input_path": str(input_path),
        "gold_path": str(gold_path) if gold_path is not None else None,
        "tags": [str(tag) for tag in entry.get("tags", []) if isinstance(tag, str)],
        "enable_formula_recognition": bool(entry.get("enable_formula_recognition", False)),
        "status": "ok",
    }

    if not input_path.exists():
        base_report["status"] = "skipped_missing_input"
        base_report["error"] = f"Input path does not exist: {input_path}"
        return base_report

    cache_key = _build_case_cache_key(entry, input_path=input_path, gold_path=gold_path)
    if cache_root is not None:
        cached_report = _load_cached_case_report(cache_root / cache_key, case_dir=case_dir, cache_key=cache_key)
        if cached_report is not None:
            return cached_report

    try:
        payload, run_context = _load_benchmark_payload(
            input_kind,
            input_path,
            case_dir=case_dir,
            keep_case_inputs=keep_case_inputs,
            enable_formula_recognition=bool(entry.get("enable_formula_recognition", False)),
        )
    except Exception as exc:
        base_report["status"] = "failed_runtime"
        base_report["error"] = str(exc)
        return base_report

    formula_units = collect_formula_units(payload)
    summary = summarize_formula_units(payload, formula_units)
    base_report["summary"] = summary
    base_report.update(run_context)
    base_report["cache_key"] = cache_key
    base_report["cache_status"] = "miss"

    gold_payload = _load_gold_payload(gold_path) if gold_path is not None and gold_path.exists() else None
    gold_comparison = compare_formula_units_to_gold(formula_units, gold_payload)
    base_report["gold_comparison"] = gold_comparison
    if gold_comparison["status"] == "failed":
        base_report["status"] = "gold_failed"

    if cache_root is not None:
        _store_cached_case_report(cache_root / cache_key, report=base_report, payload=payload)

    return base_report


def collect_formula_units(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw_units = payload.get("units")
    if not isinstance(raw_units, list):
        raise FormulaBenchmarkError("Document payload must contain a units array.")

    formula_units: list[dict[str, Any]] = []
    for raw_unit in raw_units:
        if not isinstance(raw_unit, dict):
            continue
        formula = raw_unit.get("formula")
        if not isinstance(formula, dict):
            continue

        unit_type = raw_unit.get("type")
        if not isinstance(unit_type, str) or unit_type not in _FORMULA_UNIT_TYPES:
            continue

        formula_index = len(formula_units)
        text = _optional_string(raw_unit.get("text"))
        source_format = _optional_string(formula.get("source_format"))
        linear_text = _optional_string(formula.get("linear_text"))
        display_latex = _optional_string(formula.get("display_latex"))
        calc_expr = _optional_string(formula.get("calc_expr"))
        confidence = _optional_string(formula.get("confidence"))
        formula_warnings = _string_list(formula.get("warnings"))
        quality = raw_unit.get("quality")
        quality_warnings = []
        if isinstance(quality, dict):
            quality_warnings = _string_list(quality.get("warnings"))

        formula_units.append(
            {
                "formula_index": formula_index,
                "unit_id": _optional_string(raw_unit.get("unit_id")),
                "type": unit_type,
                "order": raw_unit.get("order") if isinstance(raw_unit.get("order"), int) else 0,
                "text": text,
                "source_format": source_format,
                "linear_text": linear_text,
                "display_latex": display_latex,
                "calc_expr": calc_expr,
                "confidence": confidence,
                "warnings": formula_warnings,
                "quality_warnings": quality_warnings,
                "provider_generated": "formula_recognition_model_generated" in quality_warnings,
                "review_required": (
                    confidence in {"low", "medium"}
                    or bool(formula_warnings)
                    or bool(quality_warnings)
                ),
            }
        )

    return formula_units


def summarize_formula_units(
    payload: Mapping[str, Any],
    formula_units: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    units = formula_units if formula_units is not None else collect_formula_units(payload)
    source_format_counts: Counter[str] = Counter()
    confidence_counts: Counter[str] = Counter()

    calc_expr_units = 0
    low_confidence_units = 0
    provider_generated_units = 0
    native_units = 0
    heuristic_units = 0
    review_required_units = 0

    for unit in units:
        source_format = unit.get("source_format")
        confidence = unit.get("confidence")
        if isinstance(source_format, str) and source_format:
            source_format_counts[source_format] += 1
            if source_format == "mathtype_wmf_text_records":
                native_units += 1
            else:
                heuristic_units += 1
        if isinstance(confidence, str) and confidence:
            confidence_counts[confidence] += 1
            if confidence != "high":
                low_confidence_units += 1
        if isinstance(unit.get("calc_expr"), str) and unit["calc_expr"]:
            calc_expr_units += 1
        if unit.get("provider_generated"):
            provider_generated_units += 1
        if unit.get("review_required"):
            review_required_units += 1

    return {
        "formula_units": len(units),
        "calc_expr_units": calc_expr_units,
        "low_confidence_units": low_confidence_units,
        "provider_generated_units": provider_generated_units,
        "native_units": native_units,
        "heuristic_units": heuristic_units,
        "review_required_units": review_required_units,
        "native_coverage": _ratio(native_units, len(units)),
        "calc_expr_coverage": _ratio(calc_expr_units, len(units)),
        "low_confidence_rate": _ratio(low_confidence_units, len(units)),
        "provider_dependency_rate": _ratio(provider_generated_units, len(units)),
        "source_format_counts": dict(sorted(source_format_counts.items())),
        "confidence_counts": dict(sorted(confidence_counts.items())),
        "page_units": _count_page_units(payload),
    }


def compare_formula_units_to_gold(
    formula_units: list[dict[str, Any]],
    gold_payload: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if gold_payload is None:
        return {"status": "no_gold", "mismatches": []}

    document_expectations = gold_payload.get("document_expectations")
    if not isinstance(document_expectations, dict):
        raise FormulaBenchmarkError("Formula gold payload must contain document_expectations.")

    unit_expectations = gold_payload.get("unit_expectations")
    if not isinstance(unit_expectations, list):
        raise FormulaBenchmarkError("Formula gold payload must contain unit_expectations.")

    mismatches: list[dict[str, Any]] = []

    expected_formula_units = document_expectations.get("formula_units")
    if isinstance(expected_formula_units, int) and len(formula_units) != expected_formula_units:
        mismatches.append(
            {
                "scope": "document",
                "field": "formula_units",
                "expected": expected_formula_units,
                "actual": len(formula_units),
            }
        )

    expected_calc_expr_units = document_expectations.get("calc_expr_units")
    actual_calc_expr_units = sum(1 for item in formula_units if item.get("calc_expr"))
    if isinstance(expected_calc_expr_units, int) and actual_calc_expr_units != expected_calc_expr_units:
        mismatches.append(
            {
                "scope": "document",
                "field": "calc_expr_units",
                "expected": expected_calc_expr_units,
                "actual": actual_calc_expr_units,
            }
        )

    banned_substrings = document_expectations.get("banned_substrings_absent")
    if isinstance(banned_substrings, list):
        all_text = "\n".join(
            filter(
                None,
                [
                    value
                    for unit in formula_units
                    for value in (unit.get("text"), unit.get("linear_text"), unit.get("display_latex"))
                    if isinstance(value, str)
                ],
            )
        )
        for substring in banned_substrings:
            if isinstance(substring, str) and substring and substring in all_text:
                mismatches.append(
                    {
                        "scope": "document",
                        "field": "banned_substrings_absent",
                        "expected": f"substring absent: {substring}",
                        "actual": substring,
                    }
                )

    for unit_expectation in unit_expectations:
        if not isinstance(unit_expectation, dict):
            continue
        formula_index = unit_expectation.get("formula_index")
        if not isinstance(formula_index, int):
            raise FormulaBenchmarkError("Each gold unit expectation must contain an integer formula_index.")
        if formula_index >= len(formula_units):
            mismatches.append(
                {
                    "scope": f"formula[{formula_index}]",
                    "field": "exists",
                    "expected": True,
                    "actual": False,
                }
            )
            continue

        actual_unit = formula_units[formula_index]
        for field in (
            "type",
            "order",
            "text",
            "source_format",
            "linear_text",
            "display_latex",
            "calc_expr",
            "confidence",
        ):
            if field not in unit_expectation:
                continue
            expected_value = unit_expectation.get(field)
            actual_value = actual_unit.get(field)
            if actual_value != expected_value:
                mismatches.append(
                    {
                        "scope": f"formula[{formula_index}]",
                        "field": field,
                        "expected": expected_value,
                        "actual": actual_value,
                    }
                )

        for field in ("warnings", "quality_warnings"):
            if field not in unit_expectation:
                continue
            expected_list = _string_list(unit_expectation.get(field))
            actual_list = _string_list(actual_unit.get(field))
            if sorted(actual_list) != sorted(expected_list):
                mismatches.append(
                    {
                        "scope": f"formula[{formula_index}]",
                        "field": field,
                        "expected": expected_list,
                        "actual": actual_list,
                    }
                )

    return {
        "status": "passed" if not mismatches else "failed",
        "checked_units": len(unit_expectations),
        "mismatches": mismatches,
    }


def build_formula_gold_payload(
    payload: Mapping[str, Any],
    *,
    document_label: str,
    banned_substrings_absent: list[str] | None = None,
) -> dict[str, Any]:
    formula_units = collect_formula_units(payload)
    return {
        "schema_version": "formula-gold.v1",
        "document_label": document_label,
        "document_expectations": {
            "formula_units": len(formula_units),
            "calc_expr_units": sum(1 for item in formula_units if item.get("calc_expr")),
            "banned_substrings_absent": banned_substrings_absent or [],
        },
        "unit_expectations": [
            {
                "formula_index": item["formula_index"],
                "type": item["type"],
                "order": item["order"],
                "text": item["text"],
                "source_format": item["source_format"],
                "linear_text": item["linear_text"],
                "display_latex": item["display_latex"],
                "calc_expr": item["calc_expr"],
                "confidence": item["confidence"],
                "warnings": item["warnings"],
                "quality_warnings": item["quality_warnings"],
            }
            for item in formula_units
        ],
    }


def render_benchmark_markdown(report: Mapping[str, Any]) -> str:
    totals = report["totals"]
    lines = [
        "# Formula Benchmark Report",
        "",
        f"- generated_at: {report['generated_at']}",
        f"- status: {report['status']}",
        f"- manifest_path: {report['manifest_path']}",
        f"- benchmark_run_dir: {report['benchmark_run_dir']}",
        "",
        "## Totals",
        "",
        f"- entries: {totals['entries']}",
        f"- available_entries: {totals['available_entries']}",
        f"- required_failures: {totals['required_failures']}",
        f"- gold_entries: {totals['gold_entries']}",
        f"- gold_passed_entries: {totals['gold_passed_entries']}",
        f"- gold_failed_entries: {totals['gold_failed_entries']}",
        f"- formula_units: {totals['formula_units']}",
        f"- calc_expr_units: {totals['calc_expr_units']}",
        f"- low_confidence_units: {totals['low_confidence_units']}",
        f"- provider_generated_units: {totals['provider_generated_units']}",
        f"- native_units: {totals['native_units']}",
        f"- heuristic_units: {totals['heuristic_units']}",
        f"- native_coverage: {totals['native_coverage']}",
        f"- calc_expr_coverage: {totals['calc_expr_coverage']}",
        f"- low_confidence_rate: {totals['low_confidence_rate']}",
        f"- provider_dependency_rate: {totals['provider_dependency_rate']}",
        f"- gold_pass_rate: {totals['gold_pass_rate']}",
        "",
    ]

    tier_summaries = report.get("tier_summaries")
    if isinstance(tier_summaries, dict) and tier_summaries:
        lines.extend(["## Tier Summaries", ""])
        for tier_name, summary in tier_summaries.items():
            lines.append(f"### {tier_name}")
            lines.append("")
            lines.append(f"- entries: {summary['entries']}")
            lines.append(f"- available_entries: {summary['available_entries']}")
            lines.append(f"- formula_units: {summary['formula_units']}")
            lines.append(f"- calc_expr_coverage: {summary['calc_expr_coverage']}")
            lines.append(f"- native_coverage: {summary['native_coverage']}")
            lines.append(f"- low_confidence_rate: {summary['low_confidence_rate']}")
            lines.append(f"- provider_dependency_rate: {summary['provider_dependency_rate']}")
            if summary.get("gold_pass_rate") is not None:
                lines.append(f"- gold_pass_rate: {summary['gold_pass_rate']}")
            if summary.get("false_positive_rate") is not None:
                lines.append(f"- false_positive_rate: {summary['false_positive_rate']}")
            lines.append("")

    required_gate = report.get("required_gate")
    if isinstance(required_gate, dict):
        lines.extend([
            "## Required Gate",
            "",
            f"- status: {required_gate['status']}",
        ])
        thresholds_path = report.get("thresholds_path")
        if isinstance(thresholds_path, str) and thresholds_path:
            lines.append(f"- thresholds_path: {thresholds_path}")
        baseline_run_id = required_gate.get("baseline_run_id")
        if isinstance(baseline_run_id, str) and baseline_run_id:
            lines.append(f"- baseline_run_id: {baseline_run_id}")
        monitor_only_scopes = required_gate.get("monitor_only_scopes")
        if isinstance(monitor_only_scopes, list) and monitor_only_scopes:
            lines.append(f"- monitor_only_scopes: {', '.join(str(item) for item in monitor_only_scopes)}")
        lines.append("")
        for check in required_gate.get("checks", []):
            if not isinstance(check, dict):
                continue
            label = check.get("label") or f"{check.get('scope')}.{check.get('metric')}"
            lines.append(
                f"- {label}: {check.get('status')} (actual={check.get('actual')}, expected {check.get('op')} {check.get('value')})"
            )
        lines.append("")

    lines.extend([
        "## Entries",
        "",
    ])

    for entry in report["entries"]:
        lines.append(f"### {entry['benchmark_id']} ({entry['status']})")
        lines.append("")
        lines.append(f"- tier: {entry['tier']}")
        lines.append(f"- label: {entry['label']}")
        lines.append(f"- input_kind: {entry['input_kind']}")
        lines.append(f"- input_path: {entry['input_path']}")
        if entry.get("gold_path"):
            lines.append(f"- gold_path: {entry['gold_path']}")
        if "summary" in entry:
            summary = entry["summary"]
            lines.append(f"- formula_units: {summary['formula_units']}")
            lines.append(f"- calc_expr_units: {summary['calc_expr_units']}")
            lines.append(f"- native_coverage: {summary['native_coverage']}")
            lines.append(f"- calc_expr_coverage: {summary['calc_expr_coverage']}")
            lines.append(f"- low_confidence_rate: {summary['low_confidence_rate']}")
            lines.append(f"- provider_dependency_rate: {summary['provider_dependency_rate']}")
        gold_comparison = entry.get("gold_comparison")
        if isinstance(gold_comparison, dict) and gold_comparison.get("status") == "failed":
            lines.append("- gold_mismatches:")
            for mismatch in gold_comparison["mismatches"][:20]:
                lines.append(
                    f"  - {mismatch['scope']} {mismatch['field']}: expected={mismatch['expected']} actual={mismatch['actual']}"
                )
        if entry.get("error"):
            lines.append(f"- error: {entry['error']}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def build_formula_summary(report: Mapping[str, Any]) -> dict[str, Any]:
    raw_totals = report.get("totals")
    totals: dict[str, Any] = dict(raw_totals) if isinstance(raw_totals, dict) else {}
    total_formula_units = int(totals.get("formula_units", 0))
    total_calc_expr_units = int(totals.get("calc_expr_units", 0))
    totals["unresolved_formula_units"] = max(0, total_formula_units - total_calc_expr_units)

    documents: list[dict[str, Any]] = []
    for entry in report.get("entries", []):
        if not isinstance(entry, dict):
            continue
        summary = cast(dict[str, Any], entry.get("summary")) if isinstance(entry.get("summary"), dict) else {}
        formula_units = int(summary.get("formula_units", 0))
        calc_expr_units = int(summary.get("calc_expr_units", 0))
        unresolved_units = max(0, formula_units - calc_expr_units)
        gold_comparison = entry.get("gold_comparison") if isinstance(entry.get("gold_comparison"), dict) else None
        mismatches = gold_comparison.get("mismatches", []) if gold_comparison is not None else []

        document_summary = {
            "benchmark_id": entry.get("benchmark_id"),
            "tier": entry.get("tier"),
            "label": entry.get("label"),
            "status": entry.get("status"),
            "input_kind": entry.get("input_kind"),
            "document_path": entry.get("document_path"),
            "run_dir": entry.get("run_dir"),
            "formula_units": formula_units,
            "calc_expr_units": calc_expr_units,
            "unresolved_formula_units": unresolved_units,
            "native_units": int(summary.get("native_units", 0)),
            "heuristic_units": int(summary.get("heuristic_units", 0)),
            "low_confidence_units": int(summary.get("low_confidence_units", 0)),
            "provider_generated_units": int(summary.get("provider_generated_units", 0)),
            "review_required_units": int(summary.get("review_required_units", 0)),
            "calc_expr_coverage": summary.get("calc_expr_coverage"),
            "native_coverage": summary.get("native_coverage"),
            "low_confidence_rate": summary.get("low_confidence_rate"),
            "provider_dependency_rate": summary.get("provider_dependency_rate"),
            "source_format_counts": summary.get("source_format_counts", {}),
            "confidence_counts": summary.get("confidence_counts", {}),
            "gold_status": gold_comparison.get("status") if gold_comparison is not None else "no_gold",
            "gold_mismatch_count": len(mismatches) if isinstance(mismatches, list) else 0,
            "backlog_reasons": _formula_summary_backlog_reasons(entry, summary, unresolved_units),
        }
        documents.append(document_summary)

    return {
        "schema_version": "formula-summary.v1",
        "generated_at": report.get("generated_at"),
        "status": report.get("status"),
        "manifest_path": report.get("manifest_path"),
        "benchmark_run_dir": report.get("benchmark_run_dir"),
        "thresholds_path": report.get("thresholds_path"),
        "totals": totals,
        "tier_summaries": report.get("tier_summaries", {}),
        "required_gate": report.get("required_gate"),
        "documents": documents,
    }


def render_formula_summary_markdown(summary: Mapping[str, Any]) -> str:
    raw_totals = summary.get("totals")
    totals: Mapping[str, Any] = raw_totals if isinstance(raw_totals, Mapping) else {}
    lines = [
        "# Formula Summary",
        "",
        f"- generated_at: {summary.get('generated_at')}",
        f"- status: {summary.get('status')}",
        f"- manifest_path: {summary.get('manifest_path')}",
        f"- benchmark_run_dir: {summary.get('benchmark_run_dir')}",
        "",
        "## Totals",
        "",
        f"- entries: {totals.get('entries')}",
        f"- available_entries: {totals.get('available_entries')}",
        f"- formula_units: {totals.get('formula_units')}",
        f"- calc_expr_units: {totals.get('calc_expr_units')}",
        f"- unresolved_formula_units: {totals.get('unresolved_formula_units')}",
        f"- native_units: {totals.get('native_units')}",
        f"- low_confidence_units: {totals.get('low_confidence_units')}",
        f"- provider_generated_units: {totals.get('provider_generated_units')}",
        f"- calc_expr_coverage: {totals.get('calc_expr_coverage')}",
        f"- native_coverage: {totals.get('native_coverage')}",
        f"- low_confidence_rate: {totals.get('low_confidence_rate')}",
        f"- provider_dependency_rate: {totals.get('provider_dependency_rate')}",
        "",
        "## Documents",
        "",
        "| benchmark_id | tier | status | formulas | calc_expr | unresolved | native | low_confidence | backlog_reasons |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for document in summary.get("documents", []):
        if not isinstance(document, dict):
            continue
        reasons = document.get("backlog_reasons", [])
        reason_text = ", ".join(str(reason) for reason in reasons) if isinstance(reasons, list) else ""
        lines.append(
            "| "
            + " | ".join(
                [
                    str(document.get("benchmark_id", "")),
                    str(document.get("tier", "")),
                    str(document.get("status", "")),
                    str(document.get("formula_units", 0)),
                    str(document.get("calc_expr_units", 0)),
                    str(document.get("unresolved_formula_units", 0)),
                    str(document.get("native_units", 0)),
                    str(document.get("low_confidence_units", 0)),
                    reason_text,
                ]
            )
            + " |"
        )
    return "\n".join(lines).rstrip() + "\n"


def _formula_summary_backlog_reasons(
    entry: Mapping[str, Any],
    summary: Mapping[str, Any],
    unresolved_units: int,
) -> list[str]:
    reasons: list[str] = []
    if unresolved_units > 0:
        reasons.append("calc_expr gap")
    if int(summary.get("low_confidence_units", 0)) > 0:
        reasons.append("review load")
    if int(summary.get("provider_generated_units", 0)) > 0:
        reasons.append("provider-only")
    if int(summary.get("heuristic_units", 0)) > int(summary.get("native_units", 0)):
        reasons.append("native parser gap")
    if str(entry.get("tier")) == "control" and _is_false_positive_control_case(entry):
        reasons.append("false positive")
    if int(summary.get("low_confidence_units", 0)) > 0 and int(summary.get("provider_generated_units", 0)) == 0:
        reasons.append("local OCR candidate")
    return reasons


def _load_manifest(manifest_path: Path) -> list[dict[str, Any]]:
    if not manifest_path.exists():
        raise FileNotFoundError(f"Formula benchmark manifest does not exist: {manifest_path}")

    entries: list[dict[str, Any]] = []
    for line_number, line in enumerate(manifest_path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise FormulaBenchmarkError(f"Manifest entry at line {line_number} must be an object.")
        _validate_manifest_entry(payload, line_number=line_number)
        entries.append(payload)

    if not entries:
        raise FormulaBenchmarkError("Formula benchmark manifest must contain at least one entry.")
    return entries


def _validate_manifest_entry(entry: Mapping[str, Any], *, line_number: int) -> None:
    if entry.get("schema_version") != "formula-benchmark.manifest-entry.v1":
        raise FormulaBenchmarkError(
            f"Manifest entry at line {line_number} has unsupported schema_version: {entry.get('schema_version')}"
        )

    for field in ("benchmark_id", "tier", "label", "input_kind", "input_path"):
        if not isinstance(entry.get(field), str) or not str(entry[field]).strip():
            raise FormulaBenchmarkError(f"Manifest entry at line {line_number} must contain a non-empty {field}.")

    input_kind = str(entry["input_kind"])
    if input_kind not in _INPUT_KINDS:
        raise FormulaBenchmarkError(
            f"Manifest entry at line {line_number} has unsupported input_kind: {input_kind}"
        )


def _load_gold_payload(gold_path: Path) -> dict[str, Any]:
    payload = json.loads(gold_path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise FormulaBenchmarkError(f"Formula gold file must be an object: {gold_path}")
    if payload.get("schema_version") != "formula-gold.v1":
        raise FormulaBenchmarkError(
            f"Formula gold file has unsupported schema_version {payload.get('schema_version')}: {gold_path}"
        )
    return payload


def _load_benchmark_payload(
    input_kind: str,
    input_path: Path,
    *,
    case_dir: Path,
    keep_case_inputs: bool,
    enable_formula_recognition: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if input_kind == "document_json":
        payload = validate_json_file(input_path, "document.v1.schema.json")
        return payload, {"document_path": str(input_path), "run_dir": None}

    if input_kind != "source_file":
        raise FormulaBenchmarkError(f"Unsupported input_kind: {input_kind}")

    if not input_path.is_file():
        raise FileNotFoundError(f"Benchmark source file does not exist: {input_path}")

    input_dir = case_dir / "input"
    output_dir = case_dir / "output"
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    staged_input_path = input_dir / input_path.name
    shutil.copy2(input_path, staged_input_path)

    result = run_convert_folder(
        ConverterConfig(
            input_dir=input_dir,
            output_dir=output_dir,
            options=ConverterOptions(
                formula_recognition=(
                    load_formula_recognition_config(start_dir=input_path.parent)
                    if enable_formula_recognition
                    else FormulaRecognitionConfig()
                )
            ),
        )
    )
    document_paths = sorted((result.run_dir / "documents").glob("*/document.v1.json"))
    if len(document_paths) != 1:
        raise FormulaBenchmarkError(
            f"Expected exactly one document.v1.json for benchmark case {input_path}, got {len(document_paths)}"
        )

    payload = validate_json_file(document_paths[0], "document.v1.schema.json")
    if not keep_case_inputs and staged_input_path.exists():
        staged_input_path.unlink()
    return payload, {"document_path": str(document_paths[0]), "run_dir": str(result.run_dir)}


def _build_case_cache_key(entry: Mapping[str, Any], *, input_path: Path, gold_path: Path | None) -> str:
    asset_sha256 = sha256_file(input_path)
    manifest_entry_sha256 = hashlib.sha256(
        _canonical_json(_cache_manifest_entry(entry, gold_path=gold_path)).encode("utf-8")
    ).hexdigest()
    return hashlib.sha256(
        f"{asset_sha256}:{manifest_entry_sha256}:{_BENCHMARK_CACHE_VERSION}".encode("utf-8")
    ).hexdigest()


def _store_cached_case_report(cache_dir: Path, *, report: Mapping[str, Any], payload: Mapping[str, Any]) -> None:
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    stored_report = dict(report)
    run_dir = _optional_string(report.get("run_dir"))
    document_path = Path(str(report["document_path"])).resolve()

    if run_dir is None:
        cached_document_path = cache_dir / "document.v1.json"
        cached_document_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        stored_report["document_path"] = cached_document_path.name
        stored_report["run_dir"] = None
    else:
        run_dir_path = Path(run_dir).resolve()
        cached_run_dir = cache_dir / "run"
        shutil.copytree(run_dir_path, cached_run_dir)
        relative_document_path = document_path.relative_to(run_dir_path)
        stored_report["document_path"] = (Path("run") / relative_document_path).as_posix()
        stored_report["run_dir"] = cached_run_dir.name

    (cache_dir / "case-report.json").write_text(
        json.dumps(stored_report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _load_cached_case_report(cache_dir: Path, *, case_dir: Path, cache_key: str) -> dict[str, Any] | None:
    report_path = cache_dir / "case-report.json"
    if not report_path.exists():
        return None

    try:
        stored_report = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(stored_report, dict):
        return None

    stored_document_path = _optional_string(stored_report.get("document_path"))
    if stored_document_path is None:
        return None
    stored_document_source = cache_dir / stored_document_path
    if not stored_document_source.exists():
        return None

    stored_run_dir = _optional_string(stored_report.get("run_dir"))
    if stored_run_dir is not None:
        stored_run_source = cache_dir / stored_run_dir
        if not stored_run_source.exists():
            return None
        shutil.copytree(stored_run_source, case_dir / stored_run_dir)
        stored_report["run_dir"] = str((case_dir / stored_run_dir).resolve())
    else:
        target_document_path = case_dir / "document.v1.json"
        shutil.copy2(stored_document_source, target_document_path)
        stored_report["document_path"] = str(target_document_path.resolve())
        stored_report["cache_key"] = cache_key
        stored_report["cache_status"] = "hit"
        return stored_report

    stored_report["document_path"] = str((case_dir / stored_document_path).resolve())
    stored_report["cache_key"] = cache_key
    stored_report["cache_status"] = "hit"
    return stored_report


def _resolve_path(raw_path: str, *, base_dir: Path) -> Path:
    candidate = Path(raw_path).expanduser()
    if not candidate.is_absolute():
        candidate = (base_dir / candidate).resolve()
    else:
        candidate = candidate.resolve()
    return candidate


def _resolve_optional_path(raw_path: Any, *, base_dir: Path) -> Path | None:
    if not isinstance(raw_path, str) or not raw_path.strip():
        return None
    return _resolve_path(raw_path, base_dir=base_dir)


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _cache_manifest_entry(entry: Mapping[str, Any], *, gold_path: Path | None) -> dict[str, Any]:
    cached_entry = dict(entry)
    cached_entry["gold_path_sha256"] = sha256_file(gold_path) if gold_path is not None and gold_path.exists() else None
    return cached_entry


def _optional_string(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


def _count_page_units(payload: Mapping[str, Any]) -> int:
    raw_units = payload.get("units")
    if not isinstance(raw_units, list):
        return 0
    return sum(1 for unit in raw_units if isinstance(unit, dict) and unit.get("type") == "page")


def _finalize_aggregate_metrics(summary: dict[str, Any], *, include_false_positive_rate: bool = False) -> None:
    formula_units = int(summary.get("formula_units", 0))
    summary["calc_expr_coverage"] = _ratio(int(summary.get("calc_expr_units", 0)), formula_units)
    summary["native_coverage"] = _ratio(int(summary.get("native_units", 0)), formula_units)
    summary["low_confidence_rate"] = _ratio(int(summary.get("low_confidence_units", 0)), formula_units)
    summary["provider_dependency_rate"] = _ratio(int(summary.get("provider_generated_units", 0)), formula_units)

    gold_entries = int(summary.get("gold_entries", 0))
    summary["gold_pass_rate"] = _ratio(int(summary.get("gold_passed_entries", 0)), gold_entries) if gold_entries else None

    if include_false_positive_rate:
        available_entries = int(summary.get("available_entries", 0))
        summary["false_positive_rate"] = (
            _ratio(int(summary.get("false_positive_entries", 0)), available_entries)
            if available_entries
            else None
        )


def _build_tier_summaries(case_reports: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    tier_summaries: dict[str, dict[str, Any]] = {}
    for case_report in case_reports:
        tier = str(case_report["tier"])
        tier_summary = tier_summaries.setdefault(
            tier,
            {
                "entries": 0,
                "available_entries": 0,
                "required_failures": 0,
                "gold_entries": 0,
                "gold_passed_entries": 0,
                "gold_failed_entries": 0,
                "false_positive_entries": 0,
                "formula_units": 0,
                "calc_expr_units": 0,
                "low_confidence_units": 0,
                "provider_generated_units": 0,
                "native_units": 0,
                "heuristic_units": 0,
            },
        )
        tier_summary["entries"] += 1

        if case_report["status"] == "skipped_missing_input":
            if case_report["required"]:
                tier_summary["required_failures"] += 1
            continue

        if case_report["status"] not in {"ok", "gold_failed"}:
            if case_report["required"]:
                tier_summary["required_failures"] += 1
            continue

        tier_summary["available_entries"] += 1
        summary = case_report.get("summary")
        if isinstance(summary, dict):
            for field in _AGGREGATE_COUNT_FIELDS:
                tier_summary[field] += int(summary.get(field, 0))

        gold_comparison = case_report.get("gold_comparison")
        if isinstance(gold_comparison, dict) and gold_comparison.get("status") != "no_gold":
            tier_summary["gold_entries"] += 1
            if gold_comparison.get("status") == "passed":
                tier_summary["gold_passed_entries"] += 1
            else:
                tier_summary["gold_failed_entries"] += 1

        if tier == "control" and _is_false_positive_control_case(case_report):
            tier_summary["false_positive_entries"] += 1

    finalized: dict[str, dict[str, Any]] = {}
    for tier_name in sorted(tier_summaries, key=lambda item: (_TIER_ORDER.get(item, 99), item)):
        summary = tier_summaries[tier_name]
        _finalize_aggregate_metrics(summary, include_false_positive_rate=tier_name == "control")
        finalized[tier_name] = summary
    return finalized


def _is_false_positive_control_case(case_report: Mapping[str, Any]) -> bool:
    gold_comparison = case_report.get("gold_comparison")
    if isinstance(gold_comparison, dict) and gold_comparison.get("status") == "failed":
        return True
    if isinstance(gold_comparison, dict) and gold_comparison.get("status") == "passed":
        return False
    summary = case_report.get("summary")
    if not isinstance(summary, dict):
        return False
    return int(summary.get("formula_units", 0)) > 0


def evaluate_threshold_policy(
    threshold_policy: Mapping[str, Any],
    *,
    overall_summary: Mapping[str, Any],
    tier_summaries: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    checks = threshold_policy.get("checks")
    if not isinstance(checks, list):
        raise FormulaBenchmarkError("Threshold policy must contain a checks array.")

    results: list[dict[str, Any]] = []
    failures = 0
    for raw_check in checks:
        if not isinstance(raw_check, dict):
            raise FormulaBenchmarkError("Each threshold policy check must be an object.")

        scope = _optional_string(raw_check.get("scope"))
        metric = _optional_string(raw_check.get("metric"))
        operator = _optional_string(raw_check.get("op"))
        value = raw_check.get("value")
        if scope is None or metric is None or operator is None or not isinstance(value, (int, float)):
            raise FormulaBenchmarkError("Each threshold policy check must contain scope, metric, op and numeric value.")

        summary = overall_summary if scope == "overall" else tier_summaries.get(scope)
        actual = summary.get(metric) if isinstance(summary, Mapping) else None
        passed = _compare_threshold(actual, operator, float(value))
        if not passed:
            failures += 1

        results.append(
            {
                "label": _optional_string(raw_check.get("label")) or f"{scope}.{metric}",
                "scope": scope,
                "metric": metric,
                "op": operator,
                "value": float(value),
                "actual": actual,
                "status": "passed" if passed else "failed",
            }
        )

    monitor_only_scopes = threshold_policy.get("monitor_only_scopes")
    return {
        "status": "passed" if failures == 0 else "failed",
        "baseline_run_id": _optional_string(threshold_policy.get("baseline_run_id")),
        "monitor_only_scopes": _string_list(monitor_only_scopes),
        "checks": results,
    }


def _compare_threshold(actual: Any, operator: str, expected: float) -> bool:
    if not isinstance(actual, (int, float)):
        return False
    if operator == ">=":
        return float(actual) >= expected
    if operator == "<=":
        return float(actual) <= expected
    if operator == "==":
        return float(actual) == expected
    raise FormulaBenchmarkError(f"Unsupported threshold operator: {operator}")


def _load_threshold_policy(thresholds_path: Path) -> dict[str, Any]:
    if not thresholds_path.exists():
        raise FileNotFoundError(f"Formula benchmark threshold policy does not exist: {thresholds_path}")

    payload = json.loads(thresholds_path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise FormulaBenchmarkError("Formula benchmark threshold policy must be an object.")
    if payload.get("schema_version") != "formula-benchmark-thresholds.v1":
        raise FormulaBenchmarkError(
            f"Unsupported threshold policy schema_version: {payload.get('schema_version')}"
        )
    return payload


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 4)


def _timestamp_slug() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _iso_timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _safe_slug(value: str) -> str:
    cleaned = [char.lower() if char.isalnum() else "-" for char in value]
    compact = "".join(cleaned).strip("-")
    while "--" in compact:
        compact = compact.replace("--", "-")
    return compact or "formula-benchmark-case"


def _merge_counter(target: dict[str, int], source: Mapping[str, Any]) -> None:
    for key, value in source.items():
        if isinstance(key, str) and isinstance(value, int):
            target[key] = target.get(key, 0) + value
