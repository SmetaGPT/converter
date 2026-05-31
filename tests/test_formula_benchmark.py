from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

import doc_converter.formula_benchmark as formula_benchmark_module

from doc_converter.formula_benchmark import (
    build_formula_gold_payload,
    collect_formula_units,
    compare_formula_units_to_gold,
    evaluate_threshold_policy,
    main,
    run_benchmark_manifest,
    summarize_formula_units,
)


class FormulaBenchmarkTests(unittest.TestCase):
    def test_summarize_formula_units_tracks_native_low_confidence_and_provider(self) -> None:
        payload = _document_payload(
            [
                _formula_unit(
                    unit_id="u_000001",
                    order=1,
                    text="n = 1 ÷ N",
                    source_format="mathtype_wmf_text_records",
                    calc_expr=None,
                    confidence="high",
                ),
                _formula_unit(
                    unit_id="u_000002",
                    order=2,
                    text="S = A + B",
                    source_format="docx_text_linearized",
                    calc_expr="S = A + B",
                    confidence="low",
                    warnings=["formula_calc_expr_is_heuristic"],
                    quality_warnings=["formula_recognition_model_generated"],
                ),
            ]
        )

        formula_units = collect_formula_units(payload)
        summary = summarize_formula_units(payload, formula_units)

        self.assertEqual(summary["formula_units"], 2)
        self.assertEqual(summary["calc_expr_units"], 1)
        self.assertEqual(summary["native_units"], 1)
        self.assertEqual(summary["heuristic_units"], 1)
        self.assertEqual(summary["low_confidence_units"], 1)
        self.assertEqual(summary["provider_generated_units"], 1)
        self.assertEqual(summary["source_format_counts"], {"docx_text_linearized": 1, "mathtype_wmf_text_records": 1})
        self.assertEqual(summary["confidence_counts"], {"high": 1, "low": 1})

    def test_compare_formula_units_to_gold_reports_mismatch(self) -> None:
        payload = _document_payload(
            [
                _formula_unit(
                    unit_id="u_000001",
                    order=1,
                    text="S = A + B",
                    source_format="docx_text_linearized",
                    calc_expr="S = A + B",
                    confidence="high",
                )
            ]
        )

        gold_payload = build_formula_gold_payload(payload, document_label="sample")
        gold_payload["unit_expectations"][0]["calc_expr"] = "S = A - B"
        comparison = compare_formula_units_to_gold(collect_formula_units(payload), gold_payload)

        self.assertEqual(comparison["status"], "failed")
        self.assertEqual(comparison["mismatches"][0]["field"], "calc_expr")

    def test_run_benchmark_manifest_reads_document_json_and_writes_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            document_path = root / "document.v1.json"
            gold_path = root / "gold.json"
            manifest_path = root / "manifest.jsonl"
            output_root = root / "output"

            payload = _document_payload(
                [
                    _formula_unit(
                        unit_id="u_000001",
                        order=1,
                        text="R = A + B",
                        source_format="docx_text_linearized",
                        calc_expr="R = A + B",
                        confidence="high",
                    )
                ]
            )
            document_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            gold_path.write_text(
                json.dumps(build_formula_gold_payload(payload, document_label="sample"), ensure_ascii=False, indent=2)
                + "\n",
                encoding="utf-8",
            )
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": "formula-benchmark.manifest-entry.v1",
                        "benchmark_id": "sample-doc",
                        "tier": "anchor",
                        "label": "Sample doc",
                        "required": True,
                        "input_kind": "document_json",
                        "input_path": str(document_path),
                        "gold_path": str(gold_path),
                        "tags": ["unit-test"],
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )

            report = run_benchmark_manifest(manifest_path, output_root=output_root)

            self.assertEqual(report["status"], "ok")
            self.assertEqual(report["totals"]["gold_passed_entries"], 1)
            self.assertEqual(report["totals"]["calc_expr_coverage"], 1.0)
            benchmark_run_dir = Path(report["benchmark_run_dir"])
            self.assertTrue((benchmark_run_dir / "benchmark-report.json").exists())
            self.assertTrue((benchmark_run_dir / "benchmark-report.md").exists())
            formula_summary_path = benchmark_run_dir / "formula-summary.json"
            self.assertTrue(formula_summary_path.exists())
            self.assertTrue((benchmark_run_dir / "formula-summary.md").exists())
            formula_summary = json.loads(formula_summary_path.read_text(encoding="utf-8"))
            self.assertEqual(formula_summary["schema_version"], "formula-summary.v1")
            self.assertEqual(formula_summary["totals"]["unresolved_formula_units"], 0)
            self.assertEqual(formula_summary["documents"][0]["calc_expr_coverage"], 1.0)
            self.assertEqual(report["entries"][0]["cache_status"], "miss")

    def test_run_benchmark_manifest_evaluates_threshold_policy(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            anchor_document_path = root / "anchor-document.v1.json"
            anchor_gold_path = root / "anchor-gold.json"
            control_document_path = root / "control-document.v1.json"
            manifest_path = root / "manifest.jsonl"
            thresholds_path = root / "thresholds.json"
            output_root = root / "output"

            anchor_payload = _document_payload(
                [
                    _formula_unit(
                        unit_id="u_000001",
                        order=1,
                        text="R = A + B",
                        source_format="docx_text_linearized",
                        calc_expr="R = A + B",
                        confidence="high",
                    )
                ]
            )
            control_payload = _document_payload([])

            anchor_document_path.write_text(
                json.dumps(anchor_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            anchor_gold_path.write_text(
                json.dumps(build_formula_gold_payload(anchor_payload, document_label="anchor"), ensure_ascii=False, indent=2)
                + "\n",
                encoding="utf-8",
            )
            control_document_path.write_text(
                json.dumps(control_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            manifest_path.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "schema_version": "formula-benchmark.manifest-entry.v1",
                                "benchmark_id": "anchor-doc",
                                "tier": "anchor",
                                "label": "Anchor doc",
                                "required": True,
                                "input_kind": "document_json",
                                "input_path": str(anchor_document_path),
                                "gold_path": str(anchor_gold_path),
                                "tags": ["unit-test"],
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "schema_version": "formula-benchmark.manifest-entry.v1",
                                "benchmark_id": "control-doc",
                                "tier": "control",
                                "label": "Control doc",
                                "required": True,
                                "input_kind": "document_json",
                                "input_path": str(control_document_path),
                                "tags": ["unit-test"],
                            },
                            ensure_ascii=False,
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            thresholds_path.write_text(
                json.dumps(
                    {
                        "schema_version": "formula-benchmark-thresholds.v1",
                        "baseline_run_id": "unit-test",
                        "checks": [
                            {
                                "label": "Anchor gold stays green",
                                "scope": "anchor",
                                "metric": "gold_pass_rate",
                                "op": ">=",
                                "value": 1.0,
                            },
                            {
                                "label": "Overall calc_expr coverage stays usable",
                                "scope": "overall",
                                "metric": "calc_expr_coverage",
                                "op": ">=",
                                "value": 1.0,
                            },
                            {
                                "label": "Control stays false-positive free",
                                "scope": "control",
                                "metric": "false_positive_rate",
                                "op": "<=",
                                "value": 0.0,
                            },
                        ],
                        "monitor_only_scopes": ["rolling"],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            report = run_benchmark_manifest(
                manifest_path,
                output_root=output_root,
                thresholds_path=thresholds_path,
            )

            self.assertEqual(report["status"], "ok")
            self.assertEqual(report["required_gate"]["status"], "passed")
            self.assertEqual(report["tier_summaries"]["anchor"]["gold_pass_rate"], 1.0)
            self.assertEqual(report["tier_summaries"]["control"]["false_positive_rate"], 0.0)
            markdown = (Path(report["benchmark_run_dir"]) / "benchmark-report.md").read_text(encoding="utf-8")
            self.assertIn("## Required Gate", markdown)

    def test_run_benchmark_manifest_reuses_cached_entry_and_recomputes_required_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            document_path = root / "document.v1.json"
            gold_path = root / "gold.json"
            manifest_path = root / "manifest.jsonl"
            thresholds_path = root / "thresholds.json"
            output_root = root / "output"

            payload = _document_payload(
                [
                    _formula_unit(
                        unit_id="u_000001",
                        order=1,
                        text="R = A + B",
                        source_format="docx_text_linearized",
                        calc_expr="R = A + B",
                        confidence="high",
                    )
                ]
            )
            document_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            gold_path.write_text(
                json.dumps(build_formula_gold_payload(payload, document_label="sample"), ensure_ascii=False, indent=2)
                + "\n",
                encoding="utf-8",
            )
            _write_manifest_entries(
                manifest_path,
                [
                    {
                        "schema_version": "formula-benchmark.manifest-entry.v1",
                        "benchmark_id": "sample-doc",
                        "tier": "anchor",
                        "label": "Sample doc",
                        "required": True,
                        "input_kind": "document_json",
                        "input_path": str(document_path),
                        "gold_path": str(gold_path),
                        "tags": ["unit-test"],
                    }
                ],
            )
            thresholds_path.write_text(
                json.dumps(_threshold_policy_payload(), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            with patch("doc_converter.formula_benchmark._timestamp_slug", return_value="20260531T010101Z"):
                first_report = run_benchmark_manifest(
                    manifest_path,
                    output_root=output_root,
                    thresholds_path=thresholds_path,
                )

            self.assertEqual(first_report["entries"][0]["cache_status"], "miss")

            with patch("doc_converter.formula_benchmark._timestamp_slug", return_value="20260531T010102Z"):
                with patch(
                    "doc_converter.formula_benchmark._load_benchmark_payload",
                    side_effect=AssertionError("Benchmark payload should be reused from cache."),
                ):
                    second_report = run_benchmark_manifest(
                        manifest_path,
                        output_root=output_root,
                        thresholds_path=thresholds_path,
                    )

            self.assertEqual(second_report["status"], "ok")
            self.assertEqual(second_report["required_gate"]["status"], "passed")
            self.assertEqual(second_report["entries"][0]["cache_status"], "hit")
            self.assertTrue(Path(second_report["entries"][0]["document_path"]).exists())

    def test_run_benchmark_manifest_invalidates_cache_when_manifest_entry_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            document_path = root / "document.v1.json"
            gold_path = root / "gold.json"
            manifest_path = root / "manifest.jsonl"
            output_root = root / "output"

            payload = _document_payload(
                [
                    _formula_unit(
                        unit_id="u_000001",
                        order=1,
                        text="R = A + B",
                        source_format="docx_text_linearized",
                        calc_expr="R = A + B",
                        confidence="high",
                    )
                ]
            )
            document_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            gold_path.write_text(
                json.dumps(build_formula_gold_payload(payload, document_label="sample"), ensure_ascii=False, indent=2)
                + "\n",
                encoding="utf-8",
            )
            _write_manifest_entries(
                manifest_path,
                [
                    {
                        "schema_version": "formula-benchmark.manifest-entry.v1",
                        "benchmark_id": "sample-doc",
                        "tier": "anchor",
                        "label": "Sample doc",
                        "required": True,
                        "input_kind": "document_json",
                        "input_path": str(document_path),
                        "gold_path": str(gold_path),
                        "tags": ["unit-test"],
                    }
                ],
            )

            with patch("doc_converter.formula_benchmark._timestamp_slug", return_value="20260531T020101Z"):
                first_report = run_benchmark_manifest(manifest_path, output_root=output_root)

            _write_manifest_entries(
                manifest_path,
                [
                    {
                        "schema_version": "formula-benchmark.manifest-entry.v1",
                        "benchmark_id": "sample-doc",
                        "tier": "anchor",
                        "label": "Sample doc",
                        "required": True,
                        "input_kind": "document_json",
                        "input_path": str(document_path),
                        "gold_path": str(gold_path),
                        "tags": ["unit-test", "changed-entry"],
                    }
                ],
            )

            with patch("doc_converter.formula_benchmark._timestamp_slug", return_value="20260531T020102Z"):
                with patch(
                    "doc_converter.formula_benchmark._load_benchmark_payload",
                    wraps=formula_benchmark_module._load_benchmark_payload,
                ) as mocked_load_payload:
                    second_report = run_benchmark_manifest(manifest_path, output_root=output_root)

            mocked_load_payload.assert_called_once()
            self.assertEqual(second_report["entries"][0]["cache_status"], "miss")
            self.assertNotEqual(first_report["entries"][0]["cache_key"], second_report["entries"][0]["cache_key"])

    def test_run_benchmark_manifest_invalidates_cache_when_gold_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            document_path = root / "document.v1.json"
            gold_path = root / "gold.json"
            manifest_path = root / "manifest.jsonl"
            output_root = root / "output"

            payload = _document_payload(
                [
                    _formula_unit(
                        unit_id="u_000001",
                        order=1,
                        text="R = A + B",
                        source_format="docx_text_linearized",
                        calc_expr="R = A + B",
                        confidence="high",
                    )
                ]
            )
            document_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            gold_payload = build_formula_gold_payload(payload, document_label="sample")
            gold_path.write_text(json.dumps(gold_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            _write_manifest_entries(
                manifest_path,
                [
                    {
                        "schema_version": "formula-benchmark.manifest-entry.v1",
                        "benchmark_id": "sample-doc",
                        "tier": "anchor",
                        "label": "Sample doc",
                        "required": True,
                        "input_kind": "document_json",
                        "input_path": str(document_path),
                        "gold_path": str(gold_path),
                        "tags": ["unit-test"],
                    }
                ],
            )

            with patch("doc_converter.formula_benchmark._timestamp_slug", return_value="20260531T030101Z"):
                first_report = run_benchmark_manifest(manifest_path, output_root=output_root)

            gold_payload["unit_expectations"][0]["calc_expr"] = "R = A - B"
            gold_path.write_text(json.dumps(gold_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            with patch("doc_converter.formula_benchmark._timestamp_slug", return_value="20260531T030102Z"):
                with patch(
                    "doc_converter.formula_benchmark._load_benchmark_payload",
                    wraps=formula_benchmark_module._load_benchmark_payload,
                ) as mocked_load_payload:
                    second_report = run_benchmark_manifest(manifest_path, output_root=output_root)

            mocked_load_payload.assert_called_once()
            self.assertEqual(second_report["status"], "failed")
            self.assertEqual(second_report["entries"][0]["cache_status"], "miss")
            self.assertEqual(second_report["entries"][0]["gold_comparison"]["status"], "failed")
            self.assertNotEqual(first_report["entries"][0]["cache_key"], second_report["entries"][0]["cache_key"])

    def test_main_can_run_without_thresholds(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            document_path = root / "document.v1.json"
            gold_path = root / "gold.json"
            manifest_path = root / "manifest.jsonl"
            output_root = root / "output"

            payload = _document_payload(
                [
                    _formula_unit(
                        unit_id="u_000001",
                        order=1,
                        text="R = A + B",
                        source_format="docx_text_linearized",
                        calc_expr="R = A + B",
                        confidence="high",
                    )
                ]
            )
            document_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            gold_path.write_text(
                json.dumps(build_formula_gold_payload(payload, document_label="sample"), ensure_ascii=False, indent=2)
                + "\n",
                encoding="utf-8",
            )
            manifest_path.write_text(
                json.dumps(
                    {
                        "schema_version": "formula-benchmark.manifest-entry.v1",
                        "benchmark_id": "sample-doc",
                        "tier": "anchor",
                        "label": "Sample doc",
                        "required": True,
                        "input_kind": "document_json",
                        "input_path": str(document_path),
                        "gold_path": str(gold_path),
                        "tags": ["unit-test"],
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )

            exit_code = main(
                [
                    str(manifest_path),
                    "--output-root",
                    str(output_root),
                    "--no-thresholds",
                ]
            )

            self.assertEqual(exit_code, 0)
            benchmark_run_dir = next((output_root / "runs").iterdir())
            report = json.loads((benchmark_run_dir / "benchmark-report.json").read_text(encoding="utf-8"))
            self.assertIsNone(report["thresholds_path"])
            self.assertIsNone(report["required_gate"])

    def test_evaluate_threshold_policy_rejects_missing_scope_metric(self) -> None:
        required_gate = evaluate_threshold_policy(
            {
                "schema_version": "formula-benchmark-thresholds.v1",
                "checks": [
                    {
                        "scope": "gate",
                        "metric": "calc_expr_coverage",
                        "op": ">=",
                        "value": 0.5,
                    }
                ],
            },
            overall_summary={"calc_expr_coverage": 1.0},
            tier_summaries={"anchor": {"gold_pass_rate": 1.0}},
        )

        self.assertEqual(required_gate["status"], "failed")
        self.assertEqual(required_gate["checks"][0]["status"], "failed")


def _document_payload(units: list[dict[str, Any]]) -> dict[str, Any]:
    document_id = "sha256:" + ("0" * 64)
    return {
        "schema_version": "document.v1",
        "document_id": document_id,
        "source": {
            "original_path": "input.docx",
            "relative_input_path": None,
            "filename": "input.docx",
            "format": "docx",
            "sha256": "0" * 64,
            "size_bytes": 0,
        },
        "processing": {
            "route": "docx_native",
            "status": "success",
            "warnings": [],
        },
        "metadata": {
            "title": "Тестовый документ",
            "document_type": "приказ",
            "short_summary": "Тестовый документ с формулами",
            "confidence": "high",
            "method": "filename_fallback",
        },
        "units": [
            {
                "unit_id": "u_000000",
                "parent_id": None,
                "type": "document",
                "order": 0,
                "text": None,
                "asset_ref": None,
                "formula": None,
                "cell": None,
                "source_ref": {
                    "document_id": document_id,
                    "page": None,
                    "bbox": None,
                    "docx_path": "/word/document.xml",
                    "coordinate_system": None,
                    "page_width": None,
                    "page_height": None,
                },
                "quality": {"flags": [], "warnings": []},
            },
            *units,
        ],
        "assets": [],
        "quality": {"flags": [], "warnings": []},
    }


def _formula_unit(
    *,
    unit_id: str,
    order: int,
    text: str,
    source_format: str,
    calc_expr: str | None,
    confidence: str,
    warnings: list[str] | None = None,
    quality_warnings: list[str] | None = None,
) -> dict[str, Any]:
    document_id = "sha256:" + ("0" * 64)
    return {
        "unit_id": unit_id,
        "parent_id": "u_000000",
        "type": "formula",
        "order": order,
        "text": text,
        "asset_ref": None,
        "formula": {
            "source_format": source_format,
            "linear_text": text,
            "display_latex": text,
            "calc_expr": calc_expr,
            "variables": {},
            "confidence": confidence,
            "warnings": warnings or [],
        },
        "cell": None,
        "source_ref": {
            "document_id": document_id,
            "page": None,
            "bbox": None,
            "docx_path": "/word/document.xml/body/p[1]",
            "coordinate_system": None,
            "page_width": None,
            "page_height": None,
        },
        "quality": {"flags": [], "warnings": quality_warnings or []},
    }


def _write_manifest_entries(manifest_path: Path, entries: list[dict[str, Any]]) -> None:
    manifest_path.write_text(
        "\n".join(json.dumps(entry, ensure_ascii=False) for entry in entries) + "\n",
        encoding="utf-8",
    )


def _threshold_policy_payload() -> dict[str, Any]:
    return {
        "schema_version": "formula-benchmark-thresholds.v1",
        "baseline_run_id": "unit-test",
        "checks": [
            {
                "label": "Anchor gold stays green",
                "scope": "anchor",
                "metric": "gold_pass_rate",
                "op": ">=",
                "value": 1.0,
            },
            {
                "label": "Overall calc_expr coverage stays usable",
                "scope": "overall",
                "metric": "calc_expr_coverage",
                "op": ">=",
                "value": 1.0,
            },
        ],
        "monitor_only_scopes": ["rolling"],
    }
