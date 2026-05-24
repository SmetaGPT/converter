from __future__ import annotations

import base64
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw
from PIL import ImageFont
from docx import Document

from doc_converter.converters.docx import WmfTextChunk, _assemble_mathtype_wmf_formula, _formula_representation_from_text
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
            self.assertEqual(payload["metadata"]["method"], "rule_based_title_extraction")
            self.assertIn("Заголовок", payload["metadata"]["title"])
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

    def test_docx_extracts_formula_header_footer_and_footnotes(self) -> None:
        with tempfile.TemporaryDirectory() as input_dir, tempfile.TemporaryDirectory() as output_dir:
            source_path = Path(input_dir) / "semantic.docx"
            document = Document()
            document.sections[0].header.paragraphs[0].text = "Верхний колонтитул"
            document.sections[0].footer.paragraphs[0].text = "Нижний колонтитул"
            document.add_paragraph("E = mc^2")
            document.add_paragraph("Основной текст")
            document.save(str(source_path))
            _add_footnotes_xml(source_path, "Текст сноски")

            result = run_convert_folder(ConverterConfig(input_dir=Path(input_dir), output_dir=Path(output_dir)))

            self.assertEqual(result.status, "success")
            manifest_records = [
                json.loads(line)
                for line in (result.run_dir / "manifest.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            document_dir = result.run_dir / manifest_records[0]["output_dir"]
            payload = json.loads((document_dir / "document.v1.json").read_text(encoding="utf-8"))
            validate_payload(payload, "document.v1.schema.json")

            units_by_type = {unit["type"]: unit for unit in payload["units"]}
            self.assertEqual(units_by_type["formula"]["text"], "E = mc^2")
            self.assertIn("semantic_structure_inferred", units_by_type["formula"]["quality"]["flags"])
            self.assertEqual(units_by_type["header"]["text"], "Верхний колонтитул")
            self.assertEqual(units_by_type["footer"]["text"], "Нижний колонтитул")
            self.assertEqual(units_by_type["footnote"]["text"], "Текст сноски")
            search_text = (document_dir / "search_text.txt").read_text(encoding="utf-8")
            self.assertIn("E = mc^2", search_text)
            self.assertIn("Текст сноски", search_text)

    def test_docx_preserves_subscript_superscript_and_inline_drawing_placeholders(self) -> None:
        with tempfile.TemporaryDirectory() as input_dir, tempfile.TemporaryDirectory() as output_dir:
            source_path = Path(input_dir) / "formula-markup.docx"
            image_path = Path(input_dir) / "inline.png"
            _write_tiny_png(image_path)

            document = Document()

            formula_with_subscripts = document.add_paragraph()
            formula_with_subscripts.add_run("С")
            run = formula_with_subscripts.add_run("НГ")
            run.font.subscript = True
            formula_with_subscripts.add_run(" = НГ x К")
            run = formula_with_subscripts.add_run("в")
            run.font.subscript = True
            formula_with_subscripts.add_run(" x L (6),")

            paragraph_with_superscript = document.add_paragraph()
            paragraph_with_superscript.add_run("P")
            run = paragraph_with_superscript.add_run("j")
            run.font.superscript = True
            paragraph_with_superscript.add_run(" - описание ресурса")

            formula_with_inline_drawing = document.add_paragraph()
            formula_with_inline_drawing.add_run("j = 1 ")
            formula_with_inline_drawing.add_run().add_picture(str(image_path))
            formula_with_inline_drawing.add_run(" J, где:")

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

            formula_units = [unit for unit in payload["units"] if unit["type"] == "formula"]
            paragraph_units = [unit for unit in payload["units"] if unit["type"] == "paragraph"]

            self.assertIn("С_(НГ) = НГ x К_(в) x L (6),", [unit["text"] for unit in formula_units])
            self.assertIn("P^(j) - описание ресурса", [unit["text"] for unit in paragraph_units])

            inline_formula = next(unit["text"] for unit in formula_units if unit["text"].startswith("j = 1 "))
            self.assertIn("[INLINE_DRAWING:", inline_formula)
            self.assertTrue(inline_formula.endswith(" J, где:"))

            search_text = (document_dir / "search_text.txt").read_text(encoding="utf-8")
            self.assertIn("С_(НГ) = НГ x К_(в) x L (6),", search_text)
            self.assertIn("P^(j) - описание ресурса", search_text)
            self.assertIn("[INLINE_DRAWING:", search_text)

    def test_docx_recognizes_inline_symbol_drawings(self) -> None:
        with tempfile.TemporaryDirectory() as input_dir, tempfile.TemporaryDirectory() as output_dir:
            source_path = Path(input_dir) / "formula-symbol.docx"
            image_path = Path(input_dir) / "division.png"
            _write_symbol_png(image_path, "÷")

            document = Document()
            formula = document.add_paragraph()
            formula.add_run("j = 1 ")
            formula.add_run().add_picture(str(image_path))
            formula.add_run(" J, где:")
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

            formula_texts = [unit["text"] for unit in payload["units"] if unit["type"] == "formula"]
            self.assertIn("j = 1 ÷ J, где:", formula_texts)

            search_text = (document_dir / "search_text.txt").read_text(encoding="utf-8")
            self.assertIn("j = 1 ÷ J, где:", search_text)

    def test_docx_merges_formula_continuation_lines_split_into_adjacent_paragraphs(self) -> None:
        with tempfile.TemporaryDirectory() as input_dir, tempfile.TemporaryDirectory() as output_dir:
            source_path = Path(input_dir) / "formula-continuation.docx"

            document = Document()
            document.add_paragraph("A = B +")
            document.add_paragraph("+ C (1),")
            document.add_paragraph("D = E x")
            document.add_paragraph("x (F - 1) (2),")
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

            formula_texts = [unit["text"] for unit in payload["units"] if unit["type"] == "formula"]
            paragraph_texts = [unit["text"] for unit in payload["units"] if unit["type"] == "paragraph"]

            self.assertIn("A = B + C (1),", formula_texts)
            self.assertIn("D = E x (F - 1) (2),", formula_texts)
            self.assertNotIn("+ C (1),", paragraph_texts)
            self.assertNotIn("x (F - 1) (2),", paragraph_texts)

            search_text = (document_dir / "search_text.txt").read_text(encoding="utf-8")
            self.assertIn("A = B + C (1),", search_text)
            self.assertIn("D = E x (F - 1) (2),", search_text)

    def test_docx_recognizes_additional_inline_math_symbol_drawings(self) -> None:
        with tempfile.TemporaryDirectory() as input_dir, tempfile.TemporaryDirectory() as output_dir:
            source_path = Path(input_dir) / "formula-extra-symbols.docx"
            symbols = ["∏", "∂", "∇", "∅", "∀", "∃", "<", ">", "+", "-", "="]

            document = Document()
            expected_texts: list[str] = []
            for index, symbol in enumerate(symbols, start=1):
                image_path = Path(input_dir) / f"symbol-{index}.png"
                _write_symbol_png(image_path, symbol)
                formula = document.add_paragraph()
                formula.add_run(f"k{index} = A ")
                formula.add_run().add_picture(str(image_path))
                formula.add_run(" B")
                expected_texts.append(f"k{index} = A {symbol} B")

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

            formula_texts = [unit["text"] for unit in payload["units"] if unit["type"] == "formula"]
            search_text = (document_dir / "search_text.txt").read_text(encoding="utf-8")
            for expected in expected_texts:
                with self.subTest(expected=expected):
                    self.assertIn(expected, formula_texts)
                    self.assertIn(expected, search_text)

    def test_mathtype_wmf_formula_assembly_interleaves_symbol_chunks(self) -> None:
        chunks = [
            WmfTextChunk(text="n1N", face="Times New Roman", charset=0, height=-384, order=0),
            WmfTextChunk(text="=÷", face="Symbol", charset=1, height=-384, order=1),
        ]

        self.assertEqual(_assemble_mathtype_wmf_formula(chunks), "n = 1 ÷ N")

    def test_mathtype_wmf_formula_assembly_restores_scripts(self) -> None:
        chunks = [
            WmfTextChunk(text="(", face="Times New Roman", charset=0, height=-384, order=0),
            WmfTextChunk(text="СЦ", face="Times New Roman", charset=204, height=-384, order=1),
            WmfTextChunk(text=")", face="Times New Roman", charset=0, height=-384, order=2),
            WmfTextChunk(text="тек", face="Times New Roman", charset=204, height=-222, order=3),
            WmfTextChunk(text="k", face="Times New Roman", charset=0, height=-222, order=4),
        ]

        self.assertEqual(_assemble_mathtype_wmf_formula(chunks), "(СЦ)_(тек)^(k)")

    def test_mathtype_wmf_formula_assembly_restores_double_sum_text(self) -> None:
        chunks = [
            WmfTextChunk(text="тек", face="Times New Roman", charset=204, height=-222, order=0),
            WmfTextChunk(text="11", face="Times New Roman", charset=0, height=-222, order=1),
            WmfTextChunk(text="ОТЗТСЦV", face="Times New Roman", charset=204, height=-384, order=2),
            WmfTextChunk(text="IN", face="Times New Roman", charset=0, height=-222, order=3),
            WmfTextChunk(text="nini", face="Times New Roman", charset=0, height=-222, order=4),
            WmfTextChunk(text="in", face="Times New Roman", charset=0, height=-222, order=5),
            WmfTextChunk(text="==", face="Symbol", charset=1, height=-222, order=6),
            WmfTextChunk(text="=", face="Symbol", charset=1, height=-384, order=7),
        ]

        self.assertEqual(
            _assemble_mathtype_wmf_formula(chunks),
            "ОТ_(тек) = sum_(i=1)^I sum_(n=1)^N ЗТ_(ni) × СЦ_(n) × V_(i)",
        )

    def test_mathtype_wmf_formula_assembly_restores_known_421pr_formulas(self) -> None:
        cases = [
            (
                [
                    WmfTextChunk(text="тек", face="Times New Roman", charset=204, height=-222, order=0),
                    WmfTextChunk(text="11", face="Times New Roman", charset=0, height=-222, order=1),
                    WmfTextChunk(text="ОТмЗТСЦV", face="Times New Roman", charset=204, height=-384, order=2),
                    WmfTextChunk(text="IK", face="Times New Roman", charset=0, height=-222, order=3),
                    WmfTextChunk(text="kiki", face="Times New Roman", charset=0, height=-222, order=4),
                    WmfTextChunk(text="ik", face="Times New Roman", charset=0, height=-222, order=5),
                    WmfTextChunk(text="==", face="Symbol", charset=1, height=-222, order=6),
                    WmfTextChunk(text="=", face="Symbol", charset=1, height=-384, order=7),
                ],
                "ОТм_(тек) = sum_(i=1)^I sum_(k=1)^K ЗТ_(ki) × СЦ_(k) × V_(i)",
            ),
            (
                [
                    WmfTextChunk(text="t", face="Times New Roman", charset=0, height=-222, order=0),
                    WmfTextChunk(text="1", face="Times New Roman", charset=0, height=-222, order=1),
                    WmfTextChunk(text="PPV", face="Times New Roman", charset=0, height=-384, order=2),
                    WmfTextChunk(text="T", face="Times New Roman", charset=0, height=-222, order=3),
                    WmfTextChunk(text="t", face="Times New Roman", charset=0, height=-222, order=4),
                    WmfTextChunk(text="ii", face="Times New Roman", charset=0, height=-222, order=5),
                    WmfTextChunk(text="t", face="Times New Roman", charset=0, height=-222, order=6),
                    WmfTextChunk(text="=", face="Symbol", charset=1, height=-222, order=7),
                    WmfTextChunk(text="=", face="Symbol", charset=1, height=-384, order=8),
                ],
                "P^(t) = sum_(i=1)^I P_(i)^(t) × V_(i)",
            ),
            (
                [
                    WmfTextChunk(text="с", face="Times New Roman", charset=204, height=-222, order=0),
                    WmfTextChunk(text="Ц", face="Times New Roman", charset=204, height=-384, order=1),
                    WmfTextChunk(text="С", face="Times New Roman", charset=204, height=-384, order=2),
                    WmfTextChunk(text="Т", face="Times New Roman", charset=204, height=-384, order=3),
                    WmfTextChunk(text="=", face="Symbol", charset=1, height=-384, order=4),
                ],
                "С_(маш.р) = Ц_(а) / Т_(с)",
            ),
            (
                [
                    WmfTextChunk(text="k1", face="Times New Roman", charset=0, height=-384, order=0),
                    WmfTextChunk(text="К", face="Times New Roman", charset=204, height=-384, order=1),
                    WmfTextChunk(text="=÷", face="Symbol", charset=1, height=-384, order=2),
                ],
                "k = 1 ÷ K",
            ),
        ]

        for chunks, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(_assemble_mathtype_wmf_formula(chunks), expected)

    def test_formula_representation_adds_latex_and_calc_expr_for_double_sum(self) -> None:
        representation = _formula_representation_from_text(
            "ОТ_(тек) = sum_(i=1)^I sum_(n=1)^N ЗТ_(ni) × СЦ_(n) × V_(i) (1.1),"
        )

        self.assertIsNotNone(representation)
        assert representation is not None
        self.assertEqual(representation["source_format"], "mathtype_wmf_text_records")
        self.assertIn(r"\sum_{i=1}^{I}", representation["display_latex"])
        self.assertIn("OT_tek = sum", representation["calc_expr"])

    def test_formula_representation_normalizes_known_sums_and_ranges(self) -> None:
        sum_representation = _formula_representation_from_text(
            "ОТм_(тек) = sum_(i=1)^I sum_(k=1)^K ЗТ_(ki) × СЦ_(k) × V_(i) (1.2)"
        )
        range_representation = _formula_representation_from_text("k = 1 ÷ K, где:")

        self.assertIsNotNone(sum_representation)
        assert sum_representation is not None
        self.assertIn(r"\sum_{i=1}^{I}", sum_representation["display_latex"])
        self.assertIn(r"\sum_{k=1}^{K}", sum_representation["display_latex"])
        self.assertIn("OTm_tek = sum", sum_representation["calc_expr"])

        self.assertIsNotNone(range_representation)
        assert range_representation is not None
        self.assertEqual(range_representation["linear_text"], "k = 1 ÷ K")
        self.assertEqual(range_representation["display_latex"], r"k = 1 \div K")

    def test_formula_representation_adds_calc_expr_for_linearized_assignment(self) -> None:
        representation = _formula_representation_from_text("С_(ИГДИ) = С_(П) + С_(К) (1),")

        self.assertIsNotNone(representation)
        assert representation is not None
        self.assertEqual(representation["display_latex"], r"\mathrm{С}_{\text{ИГДИ}} = \mathrm{С}_{\text{П}} + \mathrm{С}_{\text{К}}")
        self.assertEqual(representation["calc_expr"], "S_IGDI = S_P + S_K")
        self.assertEqual(
            representation["variables"],
            {
                "С_ИГДИ": "S_IGDI",
                "С_П": "S_P",
                "С_К": "S_K",
            },
        )
        self.assertIn("formula_calc_expr_is_heuristic", representation["warnings"])
        self.assertIn("calculation_expression_requires_domain_variable_binding", representation["warnings"])

    def test_formula_representation_adds_calc_expr_for_nested_linearized_formula(self) -> None:
        representation = _formula_representation_from_text(
            "ДЗ_(вП) = (С_(Ппз) + ДЗ_(НП) + ДЗ_(режим) + ДЗ_(ноч) + ДЗ_(орг)) x (Д_(ЗПП) x П_(ДЗвыс) + Д_(прочП) - 1) (9),"
        )

        self.assertIsNotNone(representation)
        assert representation is not None
        self.assertEqual(
            representation["calc_expr"],
            "DZ_vP = ( S_Ppz + DZ_NP + DZ_rezhim + DZ_noch + DZ_org ) * ( D_ZPP * P_DZvys + D_prochP - 1 )",
        )
        self.assertEqual(representation["variables"]["ДЗ_вП"], "DZ_vP")
        self.assertEqual(representation["variables"]["П_ДЗвыс"], "P_DZvys")

    def test_formula_representation_supports_identifiers_with_digits(self) -> None:
        representation = _formula_representation_from_text("С_(Свлс) = ПЗ1_(п) + ПЗ2_(п) x S_(влс) (18),")

        self.assertIsNotNone(representation)
        assert representation is not None
        self.assertEqual(
            representation["display_latex"],
            r"\mathrm{С}_{\text{Свлс}} = \mathrm{ПЗ1}_{\text{п}} + \mathrm{ПЗ2}_{\text{п}}  \times  S_{\text{влс}}",
        )
        self.assertEqual(representation["calc_expr"], "S_Svls = PZ1_p + PZ2_p * S_vls")
        self.assertEqual(representation["variables"]["ПЗ1_п"], "PZ1_p")
        self.assertEqual(representation["variables"]["ПЗ2_п"], "PZ2_p")

    def test_formula_representation_supports_percent_and_power(self) -> None:
        representation = _formula_representation_from_text("К_(рост) = (1 + П_(рост)%)^2 (5),")

        self.assertIsNotNone(representation)
        assert representation is not None
        self.assertEqual(representation["calc_expr"], "K_rost = ( 1 + P_rost / 100 ) ** 2")
        self.assertIn(r"\%", representation["display_latex"])
        self.assertEqual(representation["variables"]["П_рост"], "P_rost")

    def test_formula_representation_collapses_repeated_multiply_at_line_wrap(self) -> None:
        representation = _formula_representation_from_text(
            "С_(Свлс) = ПЗ1_(п) + ПЗ2_(п) x\n x S_(влс) (18),"
        )

        self.assertIsNotNone(representation)
        assert representation is not None
        self.assertEqual(representation["linear_text"], "С_(Свлс) = ПЗ1_(п) + ПЗ2_(п) x S_(влс)")
        self.assertEqual(representation["calc_expr"], "S_Svls = PZ1_p + PZ2_p * S_vls")
        self.assertEqual(
            representation["display_latex"],
            r"\mathrm{С}_{\text{Свлс}} = \mathrm{ПЗ1}_{\text{п}} + \mathrm{ПЗ2}_{\text{п}}  \times  S_{\text{влс}}",
        )

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


def _add_footnotes_xml(source_path: Path, footnote_text: str) -> None:
    temp_path = source_path.with_suffix(".tmp.docx")
    footnotes_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:footnotes xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:footnote w:type="separator" w:id="-1"><w:p><w:r><w:separator/></w:r></w:p></w:footnote>
  <w:footnote w:id="1"><w:p><w:r><w:t>{footnote_text}</w:t></w:r></w:p></w:footnote>
</w:footnotes>
"""
    with zipfile.ZipFile(source_path, "r") as source_archive, zipfile.ZipFile(temp_path, "w") as target_archive:
        for item in source_archive.infolist():
            target_archive.writestr(item, source_archive.read(item.filename))
        target_archive.writestr("word/footnotes.xml", footnotes_xml.encode("utf-8"))
    temp_path.replace(source_path)


def _write_tiny_png(path: Path) -> None:
    png_bytes = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+XlGQAAAAASUVORK5CYII="
    )
    path.write_bytes(png_bytes)


def _write_symbol_png(path: Path, symbol: str) -> None:
    image = Image.new("RGBA", (128, 128), (255, 255, 255, 0))
    draw = ImageDraw.Draw(image)
    font = _load_test_symbol_font(72)
    bbox = draw.textbbox((0, 0), symbol, font=font)
    x = (128 - (bbox[2] - bbox[0])) // 2 - bbox[0]
    y = (128 - (bbox[3] - bbox[1])) // 2 - bbox[1]
    draw.text((x, y), symbol, font=font, fill=(0, 0, 0, 255))
    image.save(path)


def _load_test_symbol_font(size: int) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
    for candidate in (
        "C:/Windows/Fonts/cambria.ttc",
        "C:/Windows/Fonts/cambriai.ttf",
        "C:/Windows/Fonts/seguisym.ttf",
        "C:/Windows/Fonts/times.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ):
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


if __name__ == "__main__":
    unittest.main()