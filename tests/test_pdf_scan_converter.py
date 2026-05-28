from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from doc_converter.config import ConverterConfig
from doc_converter.converters.pdf_scan import _write_ocr_success_result
from doc_converter.runner import run_convert_folder
from doc_converter.schema_validation import validate_payload


class PdfScanConverterTests(unittest.TestCase):
    def test_ocr_success_preserves_page_boundaries_for_paragraph_units(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source_path = temp_path / "scan.pdf"
            output_dir = temp_path / "out"
            ocr_dir = output_dir / "ocr"
            searchable_pdf = ocr_dir / "searchable.pdf"
            sidecar_text = ocr_dir / "sidecar.txt"

            source_path.write_bytes(b"%PDF-1.4\n%stub\n")
            ocr_dir.mkdir(parents=True)
            searchable_pdf.write_bytes(b"%PDF-1.4\n%ocr\n")
            sidecar_text.write_text("page 1\fpage 2\n", encoding="utf-8")

            fake_pages = [Mock(extract_text=Mock(return_value="Первая страница\n\nАбзац 1")), Mock(extract_text=Mock(return_value="Вторая страница"))]
            fake_reader = Mock(pages=fake_pages)

            with patch("doc_converter.converters.pdf_scan.PdfReader", return_value=fake_reader):
                result = _write_ocr_success_result(
                    source_path=source_path,
                    searchable_pdf=searchable_pdf,
                    sidecar_text=sidecar_text,
                    output_dir=output_dir,
                    sha256="0" * 64,
                )

            payload = json.loads((output_dir / "document.v1.json").read_text(encoding="utf-8"))
            validate_payload(payload, "document.v1.schema.json")
            page_units = [unit for unit in payload["units"] if unit["type"] == "page"]
            paragraph_units = [unit for unit in payload["units"] if unit["type"] == "paragraph"]

            self.assertEqual(result.status, "success")
            self.assertEqual(len(page_units), 2)
            self.assertEqual(len(paragraph_units), 3)
            self.assertEqual(paragraph_units[0]["source_ref"]["page"], 1)
            self.assertEqual(paragraph_units[1]["source_ref"]["page"], 1)
            self.assertEqual(paragraph_units[2]["source_ref"]["page"], 2)
            self.assertEqual(paragraph_units[2]["parent_id"], page_units[1]["unit_id"])
            self.assertIn("\f", (output_dir / "search_text.txt").read_text(encoding="utf-8"))
            self.assertEqual(payload["assets"][0]["filename"], "searchable.pdf")
            self.assertIsNotNone(payload["assets"][0]["sha256"])
            self.assertGreater(payload["assets"][1]["size_bytes"], 0)

    def test_ocr_success_infers_table_formula_and_figure_units(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source_path = temp_path / "scan.pdf"
            output_dir = temp_path / "out"
            ocr_dir = output_dir / "ocr"
            searchable_pdf = ocr_dir / "searchable.pdf"
            sidecar_text = ocr_dir / "sidecar.txt"

            source_path.write_bytes(b"%PDF-1.4\n%stub\n")
            ocr_dir.mkdir(parents=True)
            searchable_pdf.write_bytes(b"%PDF-1.4\n%ocr\n")
            sidecar_text.write_text("page 1\n", encoding="utf-8")

            fake_pages = [
                Mock(
                    extract_text=Mock(
                        return_value=(
                            "Показатель  Значение\n"
                            "A  10\n"
                            "B  20\n\n"
                            "S = a * b\n\n"
                            "Рисунок 1 - Схема процесса"
                        )
                    )
                )
            ]
            fake_reader = Mock(pages=fake_pages)

            with patch("doc_converter.converters.pdf_scan.PdfReader", return_value=fake_reader):
                result = _write_ocr_success_result(
                    source_path=source_path,
                    searchable_pdf=searchable_pdf,
                    sidecar_text=sidecar_text,
                    output_dir=output_dir,
                    sha256="3" * 64,
                )

            payload = json.loads((output_dir / "document.v1.json").read_text(encoding="utf-8"))
            validate_payload(payload, "document.v1.schema.json")
            unit_types = [unit["type"] for unit in payload["units"]]
            self.assertEqual(result.status, "success")
            self.assertIn("table", unit_types)
            self.assertIn("table_cell", unit_types)
            self.assertIn("formula", unit_types)
            self.assertIn("figure", unit_types)

    def test_ocr_success_merges_table_continuation_lines(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source_path = temp_path / "scan.pdf"
            output_dir = temp_path / "out"
            ocr_dir = output_dir / "ocr"
            searchable_pdf = ocr_dir / "searchable.pdf"
            sidecar_text = ocr_dir / "sidecar.txt"

            source_path.write_bytes(b"%PDF-1.4\n%stub\n")
            ocr_dir.mkdir(parents=True)
            searchable_pdf.write_bytes(b"%PDF-1.4\n%ocr\n")
            sidecar_text.write_text("page 1\n", encoding="utf-8")

            fake_pages = [
                Mock(
                    extract_text=Mock(
                        return_value=(
                            "Показатель  Значение  Примечание\n"
                            "A  10  длинное описание\n"
                            "продолжение строки\n"
                            "B  20  короткое описание"
                        )
                    )
                )
            ]
            fake_reader = Mock(pages=fake_pages)

            with patch("doc_converter.converters.pdf_scan.PdfReader", return_value=fake_reader):
                _write_ocr_success_result(
                    source_path=source_path,
                    searchable_pdf=searchable_pdf,
                    sidecar_text=sidecar_text,
                    output_dir=output_dir,
                    sha256="6" * 64,
                )

            payload = json.loads((output_dir / "document.v1.json").read_text(encoding="utf-8"))
            validate_payload(payload, "document.v1.schema.json")
            table_cells = [unit for unit in payload["units"] if unit["type"] == "table_cell"]
            table_unit = next(unit for unit in payload["units"] if unit["type"] == "table")

            self.assertIn(
                "длинное описание\nпродолжение строки",
                [unit["text"] for unit in table_cells],
            )
            self.assertNotIn("table_structure_warning", table_unit["quality"]["flags"])

    def test_ocr_success_marks_ragged_table_warning_and_pads_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source_path = temp_path / "scan.pdf"
            output_dir = temp_path / "out"
            ocr_dir = output_dir / "ocr"
            searchable_pdf = ocr_dir / "searchable.pdf"
            sidecar_text = ocr_dir / "sidecar.txt"

            source_path.write_bytes(b"%PDF-1.4\n%stub\n")
            ocr_dir.mkdir(parents=True)
            searchable_pdf.write_bytes(b"%PDF-1.4\n%ocr\n")
            sidecar_text.write_text("page 1\n", encoding="utf-8")

            fake_pages = [
                Mock(
                    extract_text=Mock(
                        return_value=(
                            "Показатель  Значение  Примечание\n"
                            "A  10\n"
                            "B  20  короткое описание"
                        )
                    )
                )
            ]
            fake_reader = Mock(pages=fake_pages)

            with patch("doc_converter.converters.pdf_scan.PdfReader", return_value=fake_reader):
                _write_ocr_success_result(
                    source_path=source_path,
                    searchable_pdf=searchable_pdf,
                    sidecar_text=sidecar_text,
                    output_dir=output_dir,
                    sha256="7" * 64,
                )

            payload = json.loads((output_dir / "document.v1.json").read_text(encoding="utf-8"))
            validate_payload(payload, "document.v1.schema.json")
            table_unit = next(unit for unit in payload["units"] if unit["type"] == "table")
            row_units = [unit for unit in payload["units"] if unit["type"] == "table_row"]
            row_cells = [unit for unit in payload["units"] if unit.get("parent_id") == row_units[1]["unit_id"]]

            self.assertIn("table_structure_warning", table_unit["quality"]["flags"])
            self.assertEqual([unit["text"] for unit in row_cells], ["A", "10", ""])

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
            validate_payload(manifest_records[0], "manifest.v1.schema.json")
            document_dir = result.run_dir / manifest_records[0]["output_dir"]
            payload = json.loads((document_dir / "document.v1.json").read_text(encoding="utf-8"))
            validate_payload(payload, "document.v1.schema.json")

            self.assertEqual(payload["processing"]["route"], "pdf_scan")
            self.assertTrue((document_dir / "ocr" / "ocr-status.json").exists())
            self.assertIn("page", {unit["type"] for unit in payload["units"]})
            self.assertIn("ocr_required", payload["quality"]["flags"])


if __name__ == "__main__":
    unittest.main()