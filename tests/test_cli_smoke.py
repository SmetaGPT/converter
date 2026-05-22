from __future__ import annotations

import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from doc_converter.cli import build_parser, main
from doc_converter.config import ConverterConfig
from doc_converter.ocr_runtime import find_ocrmypdf_executable
from doc_converter.runner import ConverterError, run_convert_folder


class CliSmokeTests(unittest.TestCase):
    def test_help_parser_contains_convert_folder(self) -> None:
        help_text = build_parser().format_help()
        self.assertIn("convert-folder", help_text)
        self.assertIn("check-ocr", help_text)

    def test_check_ocr_outputs_machine_readable_status(self) -> None:
        buffer = StringIO()
        with redirect_stdout(buffer):
            exit_code = main(["check-ocr"])

        self.assertIn(exit_code, {0, 1})
        payload = json.loads(buffer.getvalue())
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
                    self.assertEqual(find_ocrmypdf_executable(), str(ocrmypdf_path))

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

            summary = json.loads((result.run_dir / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["status"], "success")
            self.assertEqual(summary["supported_files"], 0)

    def test_missing_input_directory_fails(self) -> None:
        with tempfile.TemporaryDirectory() as output_dir:
            missing = Path(output_dir) / "missing"
            with self.assertRaises(ConverterError):
                run_convert_folder(ConverterConfig(input_dir=missing, output_dir=Path(output_dir)))


if __name__ == "__main__":
    unittest.main()