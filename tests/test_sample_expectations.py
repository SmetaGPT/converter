from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from doc_converter.sample_expectations import validate_sample_expectations


DOCUMENT_ID = "sha256:" + ("a" * 64)


class SampleExpectationsTests(unittest.TestCase):
    def test_validate_sample_expectations_accepts_table_metrics_and_references(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = root / "manifest.sample.jsonl"
            expected_dir = root / "expected"
            run_dir = root / "run"
            documents_dir = run_dir / "documents" / "sha_a"
            expected_dir.mkdir(parents=True)
            documents_dir.mkdir(parents=True)

            manifest_path.write_text(
                json.dumps(
                    {
                        "sample_id": "sample_009",
                        "route": "pdf_text",
                        "filename": "SP_332.pdf",
                        "sha256": "a" * 64,
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            (run_dir / "manifest.jsonl").write_text(
                json.dumps(
                    {
                        "sha256": "a" * 64,
                        "route": "pdf_text",
                        "status": "success",
                        "output_dir": "documents/sha_a",
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )

            document_payload = {
                "schema_version": "document.v1",
                "document_id": DOCUMENT_ID,
                "source": {
                    "filename": "SP_332.pdf",
                    "format": "pdf",
                    "sha256": "a" * 64,
                    "original_path": "D:/input/SP_332.pdf",
                    "size_bytes": 10,
                },
                "processing": {"route": "pdf_text", "status": "success", "ocr_applied": False},
                "metadata": {
                    "title": "Тест",
                    "document_type": "свод правил",
                    "short_summary": "summary",
                    "confidence": "high",
                    "method": "rule_based_title_extraction",
                },
                "units": [
                    {"unit_id": "u_000000", "type": "document", "order": 0, "source_ref": {"document_id": DOCUMENT_ID}},
                    {
                        "unit_id": "u_000001",
                        "parent_id": "u_000000",
                        "type": "page",
                        "order": 1,
                        "source_ref": {"document_id": DOCUMENT_ID, "page": 1, "bbox": [0.0, 0.0, 10.0, 10.0]},
                    },
                    {
                        "unit_id": "u_000002",
                        "parent_id": "u_000001",
                        "type": "table",
                        "order": 2,
                        "source_ref": {"document_id": DOCUMENT_ID, "page": 1},
                        "quality": {"flags": ["semantic_structure_inferred"], "warnings": []},
                    },
                    {
                        "unit_id": "u_000003",
                        "parent_id": "u_000002",
                        "type": "table_row",
                        "order": 3,
                        "source_ref": {"document_id": DOCUMENT_ID, "page": 1},
                    },
                    {
                        "unit_id": "u_000004",
                        "parent_id": "u_000003",
                        "type": "table_cell",
                        "order": 4,
                        "text": "A",
                        "source_ref": {"document_id": DOCUMENT_ID, "page": 1},
                    },
                    {
                        "unit_id": "u_000005",
                        "parent_id": "u_000003",
                        "type": "table_cell",
                        "order": 5,
                        "text": "B",
                        "source_ref": {"document_id": DOCUMENT_ID, "page": 1},
                    },
                    {
                        "unit_id": "u_000006",
                        "parent_id": "u_000001",
                        "type": "paragraph",
                        "order": 6,
                        "text": "paragraph",
                        "source_ref": {"document_id": DOCUMENT_ID, "page": 1},
                    },
                ],
                "assets": [],
                "quality": {"flags": [], "warnings": []},
            }
            (documents_dir / "document.v1.json").write_text(
                json.dumps(document_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            expected_payload = {
                "sample_id": "sample_009",
                "route": "pdf_text",
                "expected_units": {
                    "required_types": ["document", "page", "table", "table_row", "table_cell", "paragraph"],
                    "minimum_counts": {"page": 1, "table": 1, "table_cell": 2},
                },
                "required_references": {
                    "stable_document_id": True,
                    "stable_unit_ids": True,
                    "preserve_reading_order": True,
                    "page_refs": True,
                    "bbox_refs_when_available": True,
                },
                "quality_expectations": {"empty_text": False, "review_required": False},
                "table_expectations": {
                    "table_units": 1,
                    "table_rows": 1,
                    "table_cells": 2,
                    "rows_with_two_plus_cells": 1,
                    "warning_tables": {"max": 0},
                },
            }
            (expected_dir / "sample_009.expected-units.json").write_text(
                json.dumps(expected_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            summary = validate_sample_expectations(
                run_dir=run_dir,
                sample_manifest_path=manifest_path,
                expected_dir=expected_dir,
            )

            self.assertEqual(summary["status"], "ok")
            self.assertEqual(summary["samples_failed"], 0)
            self.assertEqual(summary["results"][0]["table_metrics"]["rows_with_two_plus_cells"], 1)

    def test_validate_sample_expectations_reports_warning_table_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = root / "manifest.sample.jsonl"
            expected_dir = root / "expected"
            run_dir = root / "run"
            documents_dir = run_dir / "documents" / "sha_b"
            expected_dir.mkdir(parents=True)
            documents_dir.mkdir(parents=True)

            manifest_path.write_text(
                json.dumps(
                    {
                        "sample_id": "sample_018",
                        "route": "pdf_text",
                        "filename": "SP_433.pdf",
                        "sha256": "b" * 64,
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            (run_dir / "manifest.jsonl").write_text(
                json.dumps(
                    {
                        "sha256": "b" * 64,
                        "route": "pdf_text",
                        "status": "success",
                        "output_dir": "documents/sha_b",
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )

            document_payload = {
                "schema_version": "document.v1",
                "document_id": "sha256:" + ("b" * 64),
                "source": {
                    "filename": "SP_433.pdf",
                    "format": "pdf",
                    "sha256": "b" * 64,
                    "original_path": "D:/input/SP_433.pdf",
                    "size_bytes": 10,
                },
                "processing": {"route": "pdf_text", "status": "success", "ocr_applied": False},
                "metadata": {
                    "title": "Тест",
                    "document_type": "свод правил",
                    "short_summary": "summary",
                    "confidence": "high",
                    "method": "rule_based_title_extraction",
                },
                "units": [
                    {"unit_id": "u_000000", "type": "document", "order": 0, "source_ref": {"document_id": "sha256:" + ("b" * 64)}},
                    {
                        "unit_id": "u_000001",
                        "parent_id": "u_000000",
                        "type": "page",
                        "order": 1,
                        "source_ref": {"document_id": "sha256:" + ("b" * 64), "page": 1, "bbox": [0.0, 0.0, 10.0, 10.0]},
                    },
                    {
                        "unit_id": "u_000002",
                        "parent_id": "u_000001",
                        "type": "table",
                        "order": 2,
                        "source_ref": {"document_id": "sha256:" + ("b" * 64), "page": 1},
                        "quality": {"flags": ["semantic_structure_inferred", "table_structure_warning"], "warnings": []},
                    },
                ],
                "assets": [],
                "quality": {"flags": [], "warnings": []},
            }
            (documents_dir / "document.v1.json").write_text(
                json.dumps(document_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            expected_payload = {
                "sample_id": "sample_018",
                "route": "pdf_text",
                "expected_units": {"required_types": ["document", "page", "table"]},
                "required_references": {
                    "stable_document_id": True,
                    "stable_unit_ids": True,
                    "preserve_reading_order": True,
                    "page_refs": True,
                    "bbox_refs_when_available": True,
                },
                "table_expectations": {"warning_tables": {"max": 0}},
            }
            (expected_dir / "sample_018.expected-units.json").write_text(
                json.dumps(expected_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            summary = validate_sample_expectations(
                run_dir=run_dir,
                sample_manifest_path=manifest_path,
                expected_dir=expected_dir,
            )

            self.assertEqual(summary["status"], "failed")
            self.assertIn("warning_tables", summary["results"][0]["issues"][0])

    def test_validate_sample_expectations_can_filter_sample_ids_and_check_processing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = root / "manifest.sample.jsonl"
            expected_dir = root / "expected"
            run_dir = root / "run"
            documents_dir = run_dir / "documents" / "sha_c"
            expected_dir.mkdir(parents=True)
            documents_dir.mkdir(parents=True)

            manifest_path.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "sample_id": "sample_009",
                                "route": "pdf_text",
                                "filename": "SP_332.pdf",
                                "sha256": "a" * 64,
                            },
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            {
                                "sample_id": "sample_020",
                                "route": "pdf_scan",
                                "filename": "PPRF1315.pdf",
                                "sha256": "c" * 64,
                            },
                            ensure_ascii=False,
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (run_dir / "manifest.jsonl").write_text(
                json.dumps(
                    {
                        "sha256": "c" * 64,
                        "route": "pdf_scan",
                        "status": "partial_success",
                        "output_dir": "documents/sha_c",
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )

            document_payload = {
                "schema_version": "document.v1",
                "document_id": "sha256:" + ("c" * 64),
                "source": {
                    "filename": "sample_020__PPRF1315.pdf",
                    "relative_input_path": "sample_020__PPRF1315.pdf",
                    "format": "pdf",
                    "sha256": "c" * 64,
                    "original_path": "D:/input/sample_020__PPRF1315.pdf",
                    "size_bytes": 10,
                },
                "processing": {
                    "route": "pdf_scan",
                    "status": "partial_success",
                    "ocr_applied": False,
                    "warnings": ["OCRmyPDF failed."],
                },
                "metadata": {
                    "title": "Тест",
                    "document_type": "unknown",
                    "short_summary": "summary",
                    "confidence": "medium",
                    "method": "rule_based_title_extraction",
                },
                "units": [
                    {"unit_id": "u_000000", "type": "document", "order": 0, "source_ref": {"document_id": "sha256:" + ("c" * 64)}},
                    {
                        "unit_id": "u_000001",
                        "parent_id": "u_000000",
                        "type": "page",
                        "order": 1,
                        "source_ref": {"document_id": "sha256:" + ("c" * 64), "page": 1, "bbox": None},
                    },
                ],
                "assets": [],
                "quality": {"flags": ["ocr_required", "ocr_failed", "empty_text", "review_required"], "warnings": []},
            }
            (documents_dir / "document.v1.json").write_text(
                json.dumps(document_payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            (expected_dir / "sample_009.expected-units.json").write_text(
                json.dumps({"sample_id": "sample_009", "route": "pdf_text"}, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (expected_dir / "sample_020.expected-units.json").write_text(
                json.dumps(
                    {
                        "sample_id": "sample_020",
                        "route": "pdf_scan",
                        "required_references": {"stable_document_id": True, "stable_unit_ids": True, "preserve_original_pdf": True},
                        "quality_expectations": {
                            "ocr_required": True,
                            "ocr_failed": True,
                            "empty_text": True,
                            "review_required": True,
                        },
                        "processing_expectations": {
                            "status": "partial_success",
                            "ocr_applied": False,
                            "warnings_include": ["OCRmyPDF failed."],
                        },
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            summary = validate_sample_expectations(
                run_dir=run_dir,
                sample_manifest_path=manifest_path,
                expected_dir=expected_dir,
                sample_ids={"sample_020"},
            )

            self.assertEqual(summary["status"], "ok")
            self.assertEqual(summary["samples_checked"], 1)


if __name__ == "__main__":
    unittest.main()