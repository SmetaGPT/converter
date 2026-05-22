from __future__ import annotations

import json
import unittest
from pathlib import Path

from doc_converter.config import ConverterConfig
from doc_converter.runner import run_convert_folder


class PdfTextConverterTests(unittest.TestCase):
    def test_runner_converts_real_pdf_text_sample_when_available(self) -> None:
        source_root = Path(r"D:\ФСНБ\Документы\Загрузка НПА\SP")
        sample = source_root / "SP_481.pdf"
        if not sample.exists():
            self.skipTest("ФСНБ PDF sample is not available on this machine")

        import tempfile

        with tempfile.TemporaryDirectory() as input_dir, tempfile.TemporaryDirectory() as output_dir:
            input_path = Path(input_dir) / sample.name
            input_path.write_bytes(sample.read_bytes())

            result = run_convert_folder(ConverterConfig(input_dir=Path(input_dir), output_dir=Path(output_dir)))

            self.assertEqual(result.status, "success")
            manifest_records = [
                json.loads(line)
                for line in (result.run_dir / "manifest.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(manifest_records[0]["route"], "pdf_text")
            document_dir = result.run_dir / manifest_records[0]["output_dir"]
            payload = json.loads((document_dir / "document.v1.json").read_text(encoding="utf-8"))

            self.assertEqual(payload["processing"]["route"], "pdf_text")
            self.assertFalse(payload["processing"]["ocr_applied"])
            self.assertIn("page", {unit["type"] for unit in payload["units"]})
            self.assertGreater(manifest_records[0]["search_text_chars"], 1000)


if __name__ == "__main__":
    unittest.main()