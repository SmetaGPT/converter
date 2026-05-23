from __future__ import annotations

import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from docx import Document

from doc_converter.cli import build_parser, main
from doc_converter.config import ConverterConfig, ConverterOptions
from doc_converter.ocr_runtime import find_ocrmypdf_executable
from doc_converter.runner import ConverterError, run_convert_folder
from doc_converter.schema_validation import validate_payload


class CliSmokeTests(unittest.TestCase):
    def test_help_parser_contains_convert_folder(self) -> None:
        help_text = build_parser().format_help()
        self.assertIn("convert-folder", help_text)
        self.assertIn("check-ocr", help_text)
        self.assertNotIn("--workers", help_text)

    def test_check_ocr_outputs_machine_readable_status(self) -> None:
        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["check-ocr"])

        self.assertIn(exit_code, {0, 1})
        payload = json.loads(buffer.getvalue())
        validate_payload(payload, "ocr-runtime.v1.schema.json")
        self.assertEqual(payload["schema_version"], "ocr-runtime.v1")
        self.assertIn(payload["status"], {"ready", "missing"})
        self.assertIn("tools", payload)
        self.assertIn("languages", payload)

    def test_find_ocrmypdf_prefers_active_python_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            scripts_dir = Path(temp_dir)
            executable_name = "ocrmypdf.exe" if os.name == "nt" else "ocrmypdf"
            python_name = "python.exe" if os.name == "nt" else "python"
            ocrmypdf_path = scripts_dir / executable_name
            ocrmypdf_path.write_text("", encoding="utf-8")

            with patch("doc_converter.ocr_runtime.sys.executable", str(scripts_dir / python_name)):
                with patch("doc_converter.ocr_runtime.shutil.which", return_value=None):
                    self.assertEqual(find_ocrmypdf_executable(), str(ocrmypdf_path.resolve()))

    def test_empty_folder_creates_run_package(self) -> None:
        with tempfile.TemporaryDirectory() as input_dir, tempfile.TemporaryDirectory() as output_dir:
            result = run_convert_folder(ConverterConfig(input_dir=Path(input_dir), output_dir=Path(output_dir)))

            self.assertEqual(result.status, "success")
            self.assertEqual(result.discovered_files, 0)
            self.assertEqual(result.supported_files, 0)
            self.assertTrue((result.run_dir / "run.json").exists())
            self.assertTrue((result.run_dir / "manifest.jsonl").exists())
            self.assertTrue((result.run_dir / "processing-log.jsonl").exists())
            self.assertTrue((result.run_dir / "summary.json").exists())
            self.assertTrue((result.run_dir / "errors.jsonl").exists())
            self.assertTrue((result.run_dir / "queue-state.json").exists())
            self.assertTrue((result.run_dir / "documents").is_dir())

            run_payload = json.loads((result.run_dir / "run.json").read_text(encoding="utf-8"))
            summary = json.loads((result.run_dir / "summary.json").read_text(encoding="utf-8"))
            queue_state = json.loads((result.run_dir / "queue-state.json").read_text(encoding="utf-8"))

            validate_payload(run_payload, "run.v1.schema.json")
            validate_payload(summary, "summary.v1.schema.json")
            validate_payload(queue_state, "queue-state.v1.schema.json")

            self.assertEqual(summary["schema_version"], "summary.v1")
            self.assertEqual(summary["status"], "success")
            self.assertEqual(summary["supported_files"], 0)
            self.assertNotIn("workers", run_payload["options"])

    def test_failed_document_writes_review_required_file_and_failed_reason(self) -> None:
        with tempfile.TemporaryDirectory() as input_dir, tempfile.TemporaryDirectory() as output_dir:
            source_path = Path(input_dir) / "sample.docx"
            document = Document()
            document.add_paragraph("boom")
            document.save(str(source_path))

            with patch("doc_converter.runner.convert_docx", side_effect=OSError("broken docx extractor")):
                result = run_convert_folder(
                    ConverterConfig(input_dir=Path(input_dir), output_dir=Path(output_dir), options=ConverterOptions())
                )

            summary = json.loads((result.run_dir / "summary.json").read_text(encoding="utf-8"))
            review_required_records = [
                json.loads(line)
                for line in (result.run_dir / "review-required.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

            self.assertEqual(result.status, "failed")
            self.assertEqual(summary["failed_files"], 1)
            self.assertEqual(summary["review_required_files"], 1)
            self.assertEqual(summary["failed_reasons"]["OSError"], 1)
            self.assertEqual(review_required_records[0]["status"], "failed")
            validate_payload(review_required_records[0], "review-required.v1.schema.json")

    def test_mixed_folder_reports_unsupported_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as input_dir, tempfile.TemporaryDirectory() as output_dir:
            document = Document()
            document.add_paragraph("supported")
            document.save(str(Path(input_dir) / "source.docx"))
            (Path(input_dir) / "ignored.txt").write_text("ignored", encoding="utf-8")

            result = run_convert_folder(ConverterConfig(input_dir=Path(input_dir), output_dir=Path(output_dir)))

            summary = json.loads((result.run_dir / "summary.json").read_text(encoding="utf-8"))
            log_records = [
                json.loads(line)
                for line in (result.run_dir / "processing-log.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

            self.assertEqual(result.discovered_files, 2)
            self.assertEqual(result.supported_files, 1)
            self.assertEqual(summary["discovered_files"], 2)
            self.assertEqual(summary["supported_files"], 1)
            self.assertEqual(summary["unsupported_files"], 1)
            unsupported_records = [
                record for record in log_records if record.get("event") == "document_skipped_unsupported"
            ]
            self.assertEqual(len(unsupported_records), 1)
            self.assertEqual(unsupported_records[0]["relative_path"], "ignored.txt")
            self.assertEqual(unsupported_records[0]["status"], "skipped_unsupported")

    def test_repeated_run_reuses_previous_output_for_unchanged_input(self) -> None:
        with tempfile.TemporaryDirectory() as input_dir, tempfile.TemporaryDirectory() as output_dir:
            source_path = Path(input_dir) / "sample.docx"
            document = Document()
            document.add_paragraph("Resume candidate")
            document.save(str(source_path))

            first_result = run_convert_folder(
                ConverterConfig(input_dir=Path(input_dir), output_dir=Path(output_dir), options=ConverterOptions())
            )
            first_manifest = [
                json.loads(line)
                for line in (first_result.run_dir / "manifest.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

            with patch("doc_converter.runner.convert_docx") as convert_docx:
                second_result = run_convert_folder(
                    ConverterConfig(input_dir=Path(input_dir), output_dir=Path(output_dir), options=ConverterOptions())
                )
                convert_docx.assert_not_called()

            second_manifest = [
                json.loads(line)
                for line in (second_result.run_dir / "manifest.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]

            self.assertEqual(first_manifest[0]["status"], "success")
            self.assertEqual(second_manifest[0]["status"], "success")
            self.assertTrue(second_manifest[0]["reused_previous_output"])
            self.assertEqual(second_manifest[0]["resumed_from_run_id"], first_result.run_id)

    def test_missing_input_directory_fails(self) -> None:
        with tempfile.TemporaryDirectory() as output_dir:
            missing = Path(output_dir) / "missing"
            with self.assertRaises(ConverterError):
                run_convert_folder(ConverterConfig(input_dir=missing, output_dir=Path(output_dir)))

    def test_equal_input_and_output_directory_fails_before_run_starts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            shared_dir = Path(temp_dir) / "shared"
            shared_dir.mkdir()

            with self.assertRaises(ConverterError):
                run_convert_folder(ConverterConfig(input_dir=shared_dir, output_dir=shared_dir))

            self.assertFalse((shared_dir / "runs").exists())

    def test_output_directory_inside_input_fails_before_run_starts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_dir = Path(temp_dir) / "input"
            input_dir.mkdir()
            output_dir = input_dir / "out"

            with self.assertRaises(ConverterError):
                run_convert_folder(ConverterConfig(input_dir=input_dir, output_dir=output_dir))

            self.assertFalse(output_dir.exists())

    def test_input_directory_inside_output_fails_before_run_starts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "output"
            input_dir = output_dir / "input"
            input_dir.mkdir(parents=True)

            with self.assertRaises(ConverterError):
                run_convert_folder(ConverterConfig(input_dir=input_dir, output_dir=output_dir))

            self.assertFalse((output_dir / "runs").exists())


if __name__ == "__main__":
    unittest.main()