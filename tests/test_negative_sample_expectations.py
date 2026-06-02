from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

from doc_converter.sample_expectations import validate_sample_expectations


class NegativeSampleExpectationTests(unittest.TestCase):
    def test_negative_sample_fixtures_validate_review_and_false_positive_contours(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir) / "run"
            run_dir.mkdir()
            manifest_records = [
                _write_document(
                    run_dir,
                    sha256="1" * 64,
                    output_name="negative_no_tables",
                    route="pdf_text",
                    status="success",
                    source_filename="negative_no_tables.pdf",
                    quality_flags=[],
                    processing_warnings=[],
                    units=[
                        _unit("u_000000", "document", 0, "1" * 64),
                        _unit("u_000001", "page", 1, "1" * 64, parent_id="u_000000", page=1),
                        _unit("u_000002", "paragraph", 2, "1" * 64, parent_id="u_000001", page=1, text="Обычный текст без таблиц."),
                    ],
                ),
                _write_document(
                    run_dir,
                    sha256="2" * 64,
                    output_name="negative_broken_wmf",
                    route="docx_native",
                    status="partial_success",
                    source_filename="negative_broken_wmf.docx",
                    quality_flags=["review_required", "formula_recognition_required"],
                    processing_warnings=["WMF formula parsing failed."],
                    units=[
                        _unit("u_000000", "document", 0, "2" * 64),
                        _unit("u_000001", "section", 1, "2" * 64, parent_id="u_000000"),
                        _unit("u_000002", "formula", 2, "2" * 64, parent_id="u_000001", text="[BROKEN_WMF_FORMULA]"),
                    ],
                ),
                _write_document(
                    run_dir,
                    sha256="3" * 64,
                    output_name="negative_protected_pdf",
                    route="pdf_text",
                    status="failed",
                    source_filename="negative_protected_pdf.pdf",
                    quality_flags=["review_required", "encrypted_pdf", "empty_text"],
                    processing_warnings=["PDF is encrypted or password protected."],
                    units=[_unit("u_000000", "document", 0, "3" * 64)],
                ),
            ]
            (run_dir / "manifest.jsonl").write_text(
                "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in manifest_records),
                encoding="utf-8",
            )

            summary = validate_sample_expectations(
                run_dir=run_dir,
                sample_manifest_path=Path("samples/manifest.negative.jsonl"),
                expected_dir=Path("samples/expected/negative"),
            )

            self.assertEqual(summary["status"], "ok")
            self.assertEqual(summary["samples_checked"], 3)


def _write_document(
    run_dir: Path,
    *,
    sha256: str,
    output_name: str,
    route: str,
    status: str,
    source_filename: str,
    quality_flags: list[str],
    processing_warnings: list[str],
    units: list[dict[str, Any]],
) -> dict[str, Any]:
    output_dir = Path("documents") / output_name
    document_dir = run_dir / output_dir
    document_dir.mkdir(parents=True)
    document_payload = {
        "schema_version": "document.v1",
        "document_id": f"sha256:{sha256}",
        "source": {
            "filename": source_filename,
            "relative_input_path": source_filename,
            "format": Path(source_filename).suffix.lstrip("."),
            "sha256": sha256,
            "original_path": f"D:/input/{source_filename}",
            "size_bytes": 10,
        },
        "processing": {"route": route, "status": status, "ocr_applied": False, "warnings": processing_warnings},
        "metadata": {
            "title": source_filename,
            "document_type": "negative-sample",
            "short_summary": "Synthetic negative sample fixture.",
            "confidence": "medium",
            "method": "synthetic_fixture",
        },
        "units": units,
        "assets": [],
        "quality": {"flags": quality_flags, "warnings": []},
    }
    (document_dir / "document.v1.json").write_text(
        json.dumps(document_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return {"sha256": sha256, "route": route, "status": status, "output_dir": output_dir.as_posix()}


def _unit(
    unit_id: str,
    unit_type: str,
    order: int,
    sha256: str,
    *,
    parent_id: str | None = None,
    page: int | None = None,
    text: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "unit_id": unit_id,
        "type": unit_type,
        "order": order,
        "source_ref": {"document_id": f"sha256:{sha256}"},
    }
    if parent_id is not None:
        payload["parent_id"] = parent_id
    if page is not None:
        payload["source_ref"]["page"] = page
    if text is not None:
        payload["text"] = text
    return payload


if __name__ == "__main__":
    unittest.main()