from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from docx import Document

from doc_converter.config import ConverterConfig
from doc_converter.runner import run_convert_folder


class DocxConverterTests(unittest.TestCase):
    def test_runner_converts_docx_to_document_package(self) -> None:
        with tempfile.TemporaryDirectory() as input_dir, tempfile.TemporaryDirectory() as output_dir:
            source_path = Path(input_dir) / "sample.docx"
            document = Document()
            document.add_paragraph("Заголовок")
            document.add_paragraph("Первый абзац")
            table = document.add_table(rows=1, cols=2)
            table.rows[0].cells[0].text = "A"
            table.rows[0].cells[1].text = "B"
            document.save(source_path)

            result = run_convert_folder(ConverterConfig(input_dir=Path(input_dir), output_dir=Path(output_dir)))

            self.assertEqual(result.status, "success")
            manifest_records = [
                json.loads(line)
                for line in (result.run_dir / "manifest.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(len(manifest_records), 1)
            self.assertEqual(manifest_records[0]["status"], "success")
            document_dir = result.run_dir / manifest_records[0]["output_dir"]
            payload = json.loads((document_dir / "document.v1.json").read_text(encoding="utf-8"))
            search_text = (document_dir / "search_text.txt").read_text(encoding="utf-8")

            self.assertEqual(payload["schema_version"], "document.v1")
            self.assertEqual(payload["processing"]["route"], "docx_native")
            self.assertIn("Первый абзац", search_text)
            self.assertIn("paragraph", {unit["type"] for unit in payload["units"]})
            self.assertIn("table", {unit["type"] for unit in payload["units"]})
            self.assertIn("table_cell", {unit["type"] for unit in payload["units"]})


if __name__ == "__main__":
    unittest.main()