from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from doc_converter.config import ConverterConfig
from doc_converter.runner import run_convert_folder


class PdfScanConverterTests(unittest.TestCase):
    def test_runner_handles_real_pdf_scan_sample_when_available(self) -> None:
        sample = Path(r"D:\ФСНБ\Документы\Загрузка НПА\sub_law\PPRF_680.pdf")
        if not sample.exists():
            self.skipTest("ФСНБ PDF scan sample is not available on this machine")

        with tempfile.TemporaryDirectory() as input_dir, tempfile.TemporaryDirectory() as output_dir:
            input_path = Path(input_dir) / sample.name
            input_path.write_bytes(sample.read_bytes())

            result = run_convert_folder(ConverterConfig(input_dir=Path(input_dir), output_dir=Path(output_dir)))

            self.assertIn(result.status, {"success", "partial_success"})
            manifest_records = [
                json.loads(line)
                for line in (result.run_dir / "manifest.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(manifest_records[0]["route"], "pdf_scan")
            document_dir = result.run_dir / manifest_records[0]["output_dir"]
            payload = json.loads((document_dir / "document.v1.json").read_text(encoding="utf-8"))

            self.assertEqual(payload["processing"]["route"], "pdf_scan")
            self.assertTrue((document_dir / "ocr" / "ocr-status.json").exists())
            self.assertIn("page", {unit["type"] for unit in payload["units"]})
            self.assertIn("ocr_required", payload["quality"]["flags"])


if __name__ == "__main__":
    unittest.main()