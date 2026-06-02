from __future__ import annotations

import unittest

from hypothesis import given, settings

from doc_converter.converters.docx.formulas.text import _formula_symbol_key, _linear_formula_text_to_calc_expr
from doc_converter.tables import parse_table_block
from tests.fixtures.docx_factories import formula_assignment_texts, rectangular_table_texts, table_cell_texts


class PropertyBasedRegressionTests(unittest.TestCase):
    @settings(max_examples=40, deadline=None, database=None)
    @given(formula_assignment_texts())
    def test_formula_assignments_emit_machine_readable_calc_expr(self, formula_case: tuple[str, str, str]) -> None:
        formula_text, target_symbol, left_symbol = formula_case

        result = _linear_formula_text_to_calc_expr(formula_text)

        self.assertIsNotNone(result)
        calc_expr, variables = result or ("", {})
        self.assertIn(" = ", calc_expr)
        self.assertIn(_formula_symbol_key(target_symbol), variables)
        self.assertIn(_formula_symbol_key(left_symbol), variables)
        self.assertNotIn("×", calc_expr)
        self.assertNotIn("÷", calc_expr)

    @settings(max_examples=40, deadline=None, database=None)
    @given(rectangular_table_texts(max_width=4, max_rows=4))
    def test_rectangular_table_blocks_stay_rectangular(self, table_case: tuple[str, int, int]) -> None:
        table_text, expected_width, expected_rows = table_case

        parsed = parse_table_block(table_text)

        self.assertEqual(parsed.dominant_width, expected_width)
        self.assertEqual(len(parsed.rows), expected_rows)
        self.assertTrue(all(len(row) == expected_width for row in parsed.rows))
        self.assertNotIn("table_structure_warning", parsed.flags)

    @settings(max_examples=40, deadline=None, database=None)
    @given(rectangular_table_texts(max_width=4, max_rows=4), table_cell_texts())
    def test_single_cell_table_continuations_merge_into_previous_row(self, table_case: tuple[str, int, int], continuation: str) -> None:
        table_text, expected_width, expected_rows = table_case
        first_line, *remaining_lines = table_text.splitlines()
        table_with_continuation = "\n".join([first_line, continuation, *remaining_lines])

        parsed = parse_table_block(table_with_continuation)

        self.assertEqual(parsed.dominant_width, expected_width)
        self.assertEqual(len(parsed.rows), expected_rows)
        self.assertTrue(all(len(row) == expected_width for row in parsed.rows))
        self.assertTrue(parsed.rows[0][-1].endswith(f"\n{continuation}"))
        self.assertNotIn("table_structure_warning", parsed.flags)


if __name__ == "__main__":
    unittest.main()
