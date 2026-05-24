from __future__ import annotations

import unittest

from doc_converter.formula_eval import (
    FormulaEvaluationError,
    MissingFormulaVariablesError,
    evaluate_document_formulas,
    evaluate_formula_expression,
)


class FormulaEvaluationTests(unittest.TestCase):
    def test_evaluate_formula_expression_supports_power_and_percentage(self) -> None:
        result = evaluate_formula_expression("K_rost = ( 1 + P_rost / 100 ) ** 2", {"P_rost": 15})

        self.assertEqual(result.target, "K_rost")
        self.assertEqual(result.expression, "( 1 + P_rost / 100 ) ** 2")
        self.assertEqual(result.used_variables, {"P_rost": 15.0})
        self.assertAlmostEqual(result.value, 1.3225)

    def test_evaluate_formula_expression_reports_missing_variables(self) -> None:
        with self.assertRaises(MissingFormulaVariablesError) as raised:
            evaluate_formula_expression("R = A + B", {"A": 1})

        self.assertEqual(raised.exception.target, "R")
        self.assertEqual(raised.exception.missing_variables, ("B",))

    def test_evaluate_formula_expression_rejects_function_calls(self) -> None:
        with self.assertRaises(FormulaEvaluationError):
            evaluate_formula_expression("R = sum(A, B)", {"A": 1, "B": 2})

    def test_evaluate_document_formulas_returns_machine_readable_results(self) -> None:
        payload = _document_payload(
            [
                _formula_unit(unit_id="u_000001", order=1, text="R = A + B", calc_expr="R = A + B"),
                _formula_unit(unit_id="u_000002", order=2, text="S = R + C", calc_expr="S = R + C"),
            ]
        )

        result = evaluate_document_formulas(payload, {"A": 2, "B": 3})

        self.assertEqual(result.formula_units, 2)
        self.assertEqual(result.calc_expr_units, 2)
        self.assertEqual(result.evaluated_count, 1)
        self.assertEqual(result.missing_count, 1)
        self.assertEqual(result.error_count, 0)
        self.assertEqual(result.results[0].status, "ok")
        self.assertEqual(result.results[0].target, "R")
        self.assertAlmostEqual(result.results[0].value or 0.0, 5.0)
        self.assertEqual(result.results[1].status, "missing_variables")
        self.assertEqual(result.results[1].missing_variables, ("C",))

    def test_evaluate_document_formulas_resolves_formula_dependencies(self) -> None:
        payload = _document_payload(
            [
                _formula_unit(unit_id="u_000001", order=1, text="S = R * 2", calc_expr="S = R * 2"),
                _formula_unit(unit_id="u_000002", order=2, text="R = A + B", calc_expr="R = A + B"),
            ]
        )

        result = evaluate_document_formulas(payload, {"A": 2, "B": 3})

        self.assertEqual(result.evaluated_count, 2)
        self.assertEqual(result.missing_count, 0)
        self.assertEqual(result.error_count, 0)
        self.assertEqual(result.results[0].target, "S")
        self.assertAlmostEqual(result.results[0].value or 0.0, 10.0)
        self.assertEqual(result.results[0].used_variables, {"R": 5.0})
        self.assertEqual(result.results[1].target, "R")
        self.assertAlmostEqual(result.results[1].value or 0.0, 5.0)


def _document_payload(units: list[dict[str, object]]) -> dict[str, object]:
    document_id = "sha256:" + ("0" * 64)
    return {
        "schema_version": "document.v1",
        "document_id": document_id,
        "source": {
            "original_path": "input.docx",
            "relative_input_path": None,
            "filename": "input.docx",
            "format": "docx",
            "sha256": "0" * 64,
            "size_bytes": 0,
        },
        "processing": {
            "route": "docx_native",
            "status": "success",
            "ocr_applied": False,
            "warnings": [],
        },
        "metadata": {
            "title": "Тестовый документ",
            "document_type": "методика",
            "short_summary": "Тестовый документ с формулами",
            "confidence": "high",
            "method": "filename_fallback",
        },
        "units": units,
        "assets": [],
        "quality": {"flags": [], "warnings": []},
    }


def _formula_unit(*, unit_id: str, order: int, text: str, calc_expr: str) -> dict[str, object]:
    document_id = "sha256:" + ("0" * 64)
    return {
        "unit_id": unit_id,
        "parent_id": None,
        "type": "formula",
        "order": order,
        "text": text,
        "asset_ref": None,
        "formula": {
            "source_format": "docx_text_linearized",
            "linear_text": text,
            "display_latex": text,
            "calc_expr": calc_expr,
            "variables": {},
            "confidence": "low",
            "warnings": [],
        },
        "cell": None,
        "source_ref": {
            "document_id": document_id,
            "page": None,
            "bbox": None,
            "docx_path": "/w:document/w:body/w:p[1]",
            "coordinate_system": None,
            "page_width": None,
            "page_height": None,
        },
        "quality": {"flags": [], "warnings": []},
    }