from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from docx import Document

from doc_converter.config import ConverterConfig, ConverterOptions
from doc_converter.runner import run_convert_folder
from doc_converter.schema_validation import validate_payload


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
            document.save(str(source_path))

            result = run_convert_folder(ConverterConfig(input_dir=Path(input_dir), output_dir=Path(output_dir)))

            self.assertEqual(result.status, "success")
            manifest_records = [
                json.loads(line)
                for line in (result.run_dir / "manifest.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(len(manifest_records), 1)
            self.assertEqual(manifest_records[0]["status"], "success")
            validate_payload(manifest_records[0], "manifest.v1.schema.json")
            document_dir = result.run_dir / manifest_records[0]["output_dir"]
            payload = json.loads((document_dir / "document.v1.json").read_text(encoding="utf-8"))
            search_text = (document_dir / "search_text.txt").read_text(encoding="utf-8")

            validate_payload(payload, "document.v1.schema.json")
            self.assertEqual(payload["schema_version"], "document.v1")
            self.assertEqual(payload["processing"]["route"], "docx_native")
            self.assertEqual(payload["source"]["relative_input_path"], "sample.docx")
            self.assertIn("Первый абзац", search_text)
            self.assertIn("paragraph", {unit["type"] for unit in payload["units"]})
            self.assertIn("table", {unit["type"] for unit in payload["units"]})
            self.assertIn("table_cell", {unit["type"] for unit in payload["units"]})

    def test_docx_preserves_body_order_and_basic_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as input_dir, tempfile.TemporaryDirectory() as output_dir:
            source_path = Path(input_dir) / "ordered.docx"
            document = Document()
            document.add_heading("Раздел 1", level=1)
            document.add_paragraph("Абзац до таблицы")
            table = document.add_table(rows=1, cols=2)
            table.rows[0].cells[0].text = "A"
            table.rows[0].cells[1].text = "B"
            document.add_paragraph("Пункт списка", style="List Bullet")
            document.add_paragraph("Абзац после таблицы")
            document.save(str(source_path))

            result = run_convert_folder(ConverterConfig(input_dir=Path(input_dir), output_dir=Path(output_dir)))

            self.assertEqual(result.status, "success")
            manifest_records = [
                json.loads(line)
                for line in (result.run_dir / "manifest.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            document_dir = result.run_dir / manifest_records[0]["output_dir"]
            payload = json.loads((document_dir / "document.v1.json").read_text(encoding="utf-8"))
            semantic_units = [
                unit
                for unit in payload["units"]
                if unit["type"] in {"section", "paragraph", "table", "list_item"}
            ]

            self.assertEqual(semantic_units[0]["type"], "section")
            self.assertEqual(semantic_units[0]["text"], "Раздел 1")
            self.assertIn("semantic_style_inferred", semantic_units[0]["quality"]["flags"])
            self.assertEqual(semantic_units[1]["text"], "Абзац до таблицы")
            self.assertEqual(semantic_units[2]["type"], "table")
            self.assertEqual(semantic_units[3]["type"], "list_item")
            self.assertIn("semantic_style_inferred", semantic_units[3]["quality"]["flags"])
            self.assertEqual(semantic_units[4]["text"], "Абзац после таблицы")
            self.assertLess(semantic_units[2]["order"], semantic_units[4]["order"])

    def test_runner_skips_duplicate_docx_and_can_copy_originals(self) -> None:
        with tempfile.TemporaryDirectory() as input_dir, tempfile.TemporaryDirectory() as output_dir:
            first_path = Path(input_dir) / "a.docx"
            second_path = Path(input_dir) / "nested" / "b.docx"
            second_path.parent.mkdir(parents=True, exist_ok=True)

            document = Document()
            document.add_paragraph("Одинаковый текст")
            document.save(str(first_path))
            second_path.write_bytes(first_path.read_bytes())

            result = run_convert_folder(
                ConverterConfig(
                    input_dir=Path(input_dir),
                    output_dir=Path(output_dir),
                    options=ConverterOptions(include_originals=True),
                )
            )

            manifest_records = [
                json.loads(line)
                for line in (result.run_dir / "manifest.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual([record["status"] for record in manifest_records], ["success", "skipped_duplicate"])
            shared_output_dir = manifest_records[0]["output_dir"]
            self.assertEqual(manifest_records[1]["output_dir"], shared_output_dir)
            document_dir = result.run_dir / shared_output_dir
            self.assertTrue((document_dir / "originals" / "a.docx").exists())
            self.assertTrue((document_dir / "originals" / "nested" / "b.docx").exists())


if __name__ == "__main__":
    unittest.main()