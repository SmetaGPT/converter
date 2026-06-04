from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from doc_converter.human_readable import (
    build_human_readable_html,
    build_human_readable_markdown,
    export_document_html,
    export_run_human_readable_html,
)

DOCUMENT_ID = "sha256:" + ("a" * 64)
SOURCE_SHA = "a" * 64


def _sample_payload() -> dict[str, object]:
    return {
        "schema_version": "document.v1",
        "document_id": DOCUMENT_ID,
        "source": {
            "original_path": "D:/input/example.docx",
            "filename": "example.docx",
            "format": "docx",
            "sha256": SOURCE_SHA,
            "size_bytes": 42,
        },
        "processing": {"route": "docx_native", "status": "success"},
        "metadata": {
            "title": "Тестовый документ",
            "document_type": "приказ",
            "short_summary": "Краткое описание",
            "confidence": "high",
            "method": "rule_based_title_extraction",
        },
        "units": [
            {
                "unit_id": "u_000001",
                "type": "section",
                "order": 0,
                "text": "Раздел 1",
                "source_ref": {"document_id": DOCUMENT_ID},
                "quality": {"flags": [], "warnings": []},
            },
            {
                "unit_id": "u_000002",
                "type": "formula",
                "order": 1,
                "text": "С = А + Б (1)",
                "formula": {
                    "source_format": "heuristic_latex",
                    "linear_text": "С = А + Б",
                    "display_latex": r"C = A + B",
                    "calc_expr": "C = A + B",
                    "confidence": "high",
                    "warnings": [],
                },
                "source_ref": {"document_id": DOCUMENT_ID},
                "quality": {"flags": [], "warnings": []},
            },
            {
                "unit_id": "u_000003",
                "type": "table",
                "order": 2,
                "source_ref": {"document_id": DOCUMENT_ID},
                "quality": {"flags": [], "warnings": []},
            },
            {
                "unit_id": "u_000004",
                "parent_id": "u_000003",
                "type": "table_row",
                "order": 3,
                "source_ref": {"document_id": DOCUMENT_ID},
                "quality": {"flags": [], "warnings": []},
            },
            {
                "unit_id": "u_000005",
                "parent_id": "u_000004",
                "type": "table_cell",
                "order": 4,
                "text": "Колонка",
                "source_ref": {"document_id": DOCUMENT_ID},
                "quality": {"flags": [], "warnings": []},
            },
            {
                "unit_id": "u_000006",
                "parent_id": "u_000004",
                "type": "table_cell",
                "order": 5,
                "text": "Значение",
                "source_ref": {"document_id": DOCUMENT_ID},
                "quality": {"flags": [], "warnings": []},
            },
        ],
        "assets": [],
        "quality": {"flags": [], "warnings": []},
    }


def _low_confidence_formula_payload() -> dict[str, object]:
    payload = _sample_payload()
    payload["units"] = [
        {
            "unit_id": "u_000001",
            "type": "paragraph",
            "order": 0,
            "text": "Абзац перед формулой",
            "source_ref": {"document_id": DOCUMENT_ID},
            "quality": {"flags": [], "warnings": []},
        },
        {
            "unit_id": "u_000002",
            "type": "formula",
            "order": 1,
            "text": "k_з.п - коэффициент, устанавливающий долю зарплаты",
            "formula": {
                "source_format": "docx_text_linearized",
                "linear_text": "k_з.п - коэффициент, устанавливающий долю зарплаты",
                "display_latex": r"k_з.п - коэффициент, устанавливающий долю зарплаты",
                "calc_expr": None,
                "confidence": "low",
                "warnings": ["formula_display_latex_is_heuristic"],
            },
            "source_ref": {"document_id": DOCUMENT_ID},
            "quality": {"flags": [], "warnings": []},
        },
        {
            "unit_id": "u_000003",
            "type": "formula_image",
            "order": 2,
            "text": "C = A + B",
            "asset_ref": "assets/formula.png",
            "formula": {
                "source_format": "heuristic_latex",
                "linear_text": "C = A + B",
                "display_latex": r"C = A + B",
                "calc_expr": "C = A + B",
                "confidence": "high",
                "warnings": [],
            },
            "source_ref": {"document_id": DOCUMENT_ID},
            "quality": {"flags": [], "warnings": []},
        },
    ]
    return payload


def _table_warning_payload() -> dict[str, object]:
    payload = _sample_payload()
    payload["units"] = [
        {
            "unit_id": "u_000001",
            "type": "table",
            "order": 0,
            "source_ref": {"document_id": DOCUMENT_ID},
            "quality": {"flags": ["semantic_structure_inferred", "table_structure_warning"], "warnings": []},
        },
        {
            "unit_id": "u_000002",
            "parent_id": "u_000001",
            "type": "table_row",
            "order": 1,
            "source_ref": {"document_id": DOCUMENT_ID},
            "quality": {"flags": [], "warnings": []},
        },
        {
            "unit_id": "u_000003",
            "parent_id": "u_000002",
            "type": "table_cell",
            "order": 2,
            "text": "МИНИСТЕРСТВО СТРОИТЕЛЬСТВА",
            "source_ref": {"document_id": DOCUMENT_ID},
            "quality": {"flags": [], "warnings": []},
        },
        {
            "unit_id": "u_000004",
            "parent_id": "u_000002",
            "type": "table_cell",
            "order": 3,
            "text": "РОССИЙСКОЙ ФЕДЕРАЦИИ",
            "source_ref": {"document_id": DOCUMENT_ID},
            "quality": {"flags": [], "warnings": []},
        },
    ]
    return payload


class HumanReadableExportTests(unittest.TestCase):
    def test_build_markdown_renders_formula_and_table(self) -> None:
        markdown = build_human_readable_markdown(_sample_payload())

        self.assertIn("# Тестовый документ", markdown)
        self.assertIn("$$", markdown)
        self.assertIn("C = A + B", markdown)
        self.assertIn("```python", markdown)
        self.assertIn("| Колонка | Значение |", markdown)

    def test_build_html_renders_mathjax_and_table(self) -> None:
        html = build_human_readable_html(_sample_payload())

        self.assertIn("MathJax", html)
        self.assertIn("<div class=\"formula-block\">", html)
        self.assertIn("inlineMath: []", html)
        self.assertIn("C = A + B", html)
        self.assertIn("<table>", html)
        self.assertIn("Тестовый документ", html)

    def test_build_markdown_renders_table_warning_as_plain_text(self) -> None:
        markdown = build_human_readable_markdown(_table_warning_payload())

        self.assertIn("МИНИСТЕРСТВО СТРОИТЕЛЬСТВА РОССИЙСКОЙ ФЕДЕРАЦИИ", markdown)
        self.assertNotIn("| МИНИСТЕРСТВО СТРОИТЕЛЬСТВА |", markdown)

    def test_build_html_renders_table_warning_as_plain_text_block(self) -> None:
        html = build_human_readable_html(_table_warning_payload())

        self.assertIn('class="table-wrap table-plain"', html)
        self.assertIn("МИНИСТЕРСТВО СТРОИТЕЛЬСТВА РОССИЙСКОЙ ФЕДЕРАЦИИ", html)
        self.assertNotIn("<table>", html)

    def test_build_html_renders_low_confidence_formula_as_plain_text(self) -> None:
        html = build_human_readable_html(_low_confidence_formula_payload())

        self.assertIn("text-indent:1.6em", html)
        self.assertIn("formula-plain", html)
        self.assertIn("k_з.п - коэффициент", html)
        self.assertNotIn("$$\nk_з.п - коэффициент", html)

    def test_build_html_renders_recognized_formula_image_as_formula_block(self) -> None:
        html = build_human_readable_html(_low_confidence_formula_payload())

        self.assertIn("assets/formula.png", html)
        self.assertIn("C = A + B", html)

    def test_export_document_html_writes_next_to_document(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            document_dir = Path(temp_dir)
            document_path = document_dir / "document.v1.json"
            document_path.write_text(json.dumps(_sample_payload(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            html_path = export_document_html(document_path)

            self.assertEqual(html_path, (document_dir / "human-readable.html").resolve())
            self.assertTrue(html_path.exists())
            self.assertIn("MathJax", html_path.read_text(encoding="utf-8"))

    def test_export_run_html_creates_index_and_document_html(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            run_dir = Path(temp_dir)
            document_dir = run_dir / "documents" / "sha256_demo"
            document_dir.mkdir(parents=True)
            document_path = document_dir / "document.v1.json"
            document_path.write_text(json.dumps(_sample_payload(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            (document_dir / "search_text.txt").write_text("search text", encoding="utf-8")
            (run_dir / "processed-documents-catalog.json").write_text(
                json.dumps(
                    {
                        "schema_version": "processed-documents-catalog.v1",
                        "run_id": "run-1",
                        "documents": [
                            {
                                "relative_input_path": "example.docx",
                                "original_filename": "example.docx",
                                "output_dir": "documents/sha256_demo",
                                "output_folder_name": "sha256_demo",
                                "status": "success",
                                "status_label": "Успешная обработка",
                                "issue": None,
                            }
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (run_dir / "run.json").write_text("{}\n", encoding="utf-8")

            index_path = export_run_human_readable_html(run_dir)

            self.assertEqual(index_path, (run_dir / "human-readable-index.html").resolve())
            self.assertTrue(index_path.exists())
            self.assertTrue((document_dir / "human-readable.html").exists())
            index_html = index_path.read_text(encoding="utf-8")
            self.assertIn("HTML QC index", index_html)
            self.assertIn("example.docx", index_html)
            self.assertIn("human-readable.html", index_html)


if __name__ == "__main__":
    unittest.main()