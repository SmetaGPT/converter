from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from doc_converter.config import ConverterConfig
from doc_converter.converters.pdf_text import convert_pdf_text
from doc_converter.runner import run_convert_folder
from doc_converter.schema_validation import validate_payload


class PdfTextConverterTests(unittest.TestCase):
    def test_pdf_text_infers_table_formula_and_figure_units(self) -> None:
        class FakeMediaBox:
            left = 0
            bottom = 0
            right = 595
            top = 842

        class FakePage:
            def __init__(self, layout_text: str) -> None:
                self._layout_text = layout_text
                self.mediabox = FakeMediaBox()
                self.rotation = 0

            def extract_text(self, *args: object, **kwargs: object) -> str:
                if kwargs.get("extraction_mode") == "layout":
                    return self._layout_text
                return self._layout_text

        fake_reader = type(
            "FakeReader",
            (),
            {
                "pages": [
                    FakePage(
                        "Показатель  Значение\n"
                        "A  10\n"
                        "B  20\n\n"
                        "S = a * b\n\n"
                        "Рисунок 1 - Схема процесса"
                    )
                ]
            },
        )()

        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = Path(temp_dir) / "semantic.pdf"
            output_dir = Path(temp_dir) / "out"
            source_path.write_bytes(b"%PDF-1.4\n%stub\n")

            with patch("doc_converter.converters.pdf_text.PdfReader", return_value=fake_reader):
                result = convert_pdf_text(source_path, output_dir, "2" * 64)

            payload = json.loads((output_dir / "document.v1.json").read_text(encoding="utf-8"))
            validate_payload(payload, "document.v1.schema.json")
            unit_types = [unit["type"] for unit in payload["units"]]
            table_cells = [unit for unit in payload["units"] if unit["type"] == "table_cell"]
            formula_units = [unit for unit in payload["units"] if unit["type"] == "formula"]
            figure_units = [unit for unit in payload["units"] if unit["type"] == "figure"]

            self.assertEqual(result.status, "success")
            self.assertIn("table", unit_types)
            self.assertIn("table_row", unit_types)
            self.assertEqual([unit["text"] for unit in table_cells[:2]], ["Показатель", "Значение"])
            self.assertEqual(formula_units[0]["text"], "S = a * b")
            self.assertIn("semantic_structure_inferred", formula_units[0]["quality"]["flags"])
            self.assertEqual(figure_units[0]["text"], "Рисунок 1 - Схема процесса")
            self.assertIn("A | 10", (output_dir / "search_text.txt").read_text(encoding="utf-8"))

    def test_pdf_text_uses_layout_mode_and_marks_repeated_edge_blocks(self) -> None:
        class FakeMediaBox:
            left = 0
            bottom = 0
            right = 595
            top = 842

        class FakePage:
            def __init__(self, layout_text: str, rotation: int = 0) -> None:
                self._layout_text = layout_text
                self.mediabox = FakeMediaBox()
                self.rotation = rotation

            def extract_text(self, *args: object, **kwargs: object) -> str:
                if kwargs.get("extraction_mode") == "layout":
                    return self._layout_text
                return self._layout_text

        fake_reader = type(
            "FakeReader",
            (),
            {
                "pages": [
                    FakePage("СП 123\n\nОсновной текст 1\n\nМинстрой России"),
                    FakePage("СП 123\n\nОсновной текст 2\n\nМинстрой России", rotation=90),
                ]
            },
        )()

        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = Path(temp_dir) / "sample.pdf"
            output_dir = Path(temp_dir) / "out"
            source_path.write_bytes(b"%PDF-1.4\n%stub\n")

            with patch("doc_converter.converters.pdf_text.PdfReader", return_value=fake_reader):
                result = convert_pdf_text(
                    source_path,
                    output_dir,
                    "1" * 64,
                    relative_source_path="nested/sample.pdf",
                )

            payload = json.loads((output_dir / "document.v1.json").read_text(encoding="utf-8"))
            validate_payload(payload, "document.v1.schema.json")
            page_units = [unit for unit in payload["units"] if unit["type"] == "page"]
            header_units = [unit for unit in payload["units"] if unit["type"] == "header"]
            footer_units = [unit for unit in payload["units"] if unit["type"] == "footer"]
            paragraph_units = [unit for unit in payload["units"] if unit["type"] == "paragraph"]

            self.assertEqual(result.status, "success")
            self.assertEqual(payload["source"]["relative_input_path"], "nested/sample.pdf")
            self.assertEqual(len(page_units), 2)
            self.assertEqual(page_units[0]["source_ref"]["coordinate_system"], "pdf_points_bottom_left")
            self.assertEqual(page_units[0]["source_ref"]["bbox"], [0.0, 0.0, 595.0, 842.0])
            self.assertEqual(len(header_units), 2)
            self.assertEqual(len(footer_units), 2)
            self.assertIn("repeated_edge_block", header_units[0]["quality"]["flags"])
            self.assertIn("repeated_edge_block", footer_units[0]["quality"]["flags"])
            self.assertIn("rotated_text", payload["quality"]["flags"])
            self.assertIn("review_required", payload["quality"]["flags"])
            self.assertEqual([unit["text"] for unit in paragraph_units], ["Основной текст 1", "Основной текст 2"])
            self.assertNotIn("СП 123", (output_dir / "search_text.txt").read_text(encoding="utf-8"))

    def test_runner_converts_real_pdf_text_sample_when_available(self) -> None:
        source_root = Path(r"D:\ФСНБ\Документы\Загрузка НПА\SP")
        sample = source_root / "SP_481.pdf"
        if not sample.exists():
            self.skipTest("ФСНБ PDF sample is not available on this machine")

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
            validate_payload(manifest_records[0], "manifest.v1.schema.json")
            document_dir = result.run_dir / manifest_records[0]["output_dir"]
            payload = json.loads((document_dir / "document.v1.json").read_text(encoding="utf-8"))
            validate_payload(payload, "document.v1.schema.json")

            self.assertEqual(payload["processing"]["route"], "pdf_text")
            self.assertFalse(payload["processing"]["ocr_applied"])
            self.assertIn("page", {unit["type"] for unit in payload["units"]})
            self.assertGreater(manifest_records[0]["search_text_chars"], 1000)


if __name__ == "__main__":
    unittest.main()