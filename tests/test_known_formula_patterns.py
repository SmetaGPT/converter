"""Tests for known formula patterns data and loader."""

from __future__ import annotations

import unittest

from doc_converter.formulas import (
    get_known_formula_representation,
    get_mathtype_signature_rules,
    get_noisy_form_recovery,
)


class TestKnownFormulaPatternsData(unittest.TestCase):
    """Test known formula patterns data loading and structure."""

    def test_noisy_form_recovery_loads(self) -> None:
        """Noisy form recovery mapping loads successfully."""
        noisy_forms = get_noisy_form_recovery()
        self.assertIsInstance(noisy_forms, dict)
        self.assertGreater(len(noisy_forms), 0, "Should have at least one noisy form mapping")

        # Check that keys and values are strings
        for key, value in noisy_forms.items():
            self.assertIsInstance(key, str)
            self.assertIsInstance(value, str)
            self.assertGreater(len(key), 0)
            self.assertGreater(len(value), 0)

    def test_formula_representations_loads(self) -> None:
        """Formula representations load successfully."""
        # Test a known formula
        formula = get_known_formula_representation("k = 1 ÷ K")
        self.assertIsNone(formula, "Simple formula should not have full representation")

        # Test a formula with full representation
        formula = get_known_formula_representation("М_(тек) = sum_(j=1)^J P^(j) × См_(тек)^(j)")
        self.assertIsNotNone(formula)
        assert formula is not None
        self.assertEqual(formula["source_format"], "mathtype_wmf_text_records")
        self.assertIn("display_latex", formula)
        self.assertIn("calc_expr", formula)
        self.assertIn("variables", formula)
        self.assertIn("confidence", formula)
        self.assertIn("warnings", formula)

    def test_mathtype_signature_rules_loads(self) -> None:
        """MathType signature rules load successfully."""
        rules = get_mathtype_signature_rules()
        self.assertIsInstance(rules, list)
        self.assertGreater(len(rules), 0, "Should have at least one signature rule")

        # Check rule structure
        for rule in rules:
            self.assertIn("condition", rule)
            self.assertIn("linear_text", rule)
            self.assertIsInstance(rule["condition"], dict)
            self.assertIsInstance(rule["linear_text"], str)

    def test_loader_returns_copies(self) -> None:
        """Loader returns copies so caller cannot mutate cache."""
        # Get noisy forms twice
        forms1 = get_noisy_form_recovery()
        forms2 = get_noisy_form_recovery()

        # They should be equal but not the same object
        self.assertEqual(forms1, forms2)
        self.assertIsNot(forms1, forms2)

        # Mutating one should not affect the other
        forms1["test_key"] = "test_value"
        self.assertNotIn("test_key", forms2)

        # Get rules twice
        rules1 = get_mathtype_signature_rules()
        rules2 = get_mathtype_signature_rules()

        # They should be equal but not the same object
        self.assertEqual(rules1, rules2)
        self.assertIsNot(rules1, rules2)


class TestKnownFormulaPatternsBehavior(unittest.TestCase):
    """Test known formula patterns preserve existing behavior."""

    def test_noisy_form_recovery_known_cases(self) -> None:
        """Known noisy form cases recover correctly."""
        noisy_forms = get_noisy_form_recovery()

        # Test first known noisy form
        noisy1 = "ЗТЧ100Н[100(НН)]60=-+_(ВрИпзро)"
        expected1 = "Н_(ВрИ) = ЗТ_(Иср) × 100 / (Ч_(общ) × [100 - (Н_(пзр) + Н_(о))] × 60)"
        self.assertEqual(noisy_forms[noisy1], expected1)

        # Test second known noisy form
        noisy2 = "ЗТЧ100Н[100(НН)]60=-+_(ВрЭлпзро)"
        expected2 = "Н_(ВрЭл) = ЗТ_(эСРл) × 100 / (Ч_(общ) × [100 - (Н_(пзр) + Н_(о))] × 60)"
        self.assertEqual(noisy_forms[noisy2], expected2)

    def test_formula_representations_known_cases(self) -> None:
        """Known formula representations return expected data."""
        # Test a known formula with full representation
        formula = get_known_formula_representation("ОТ_(тек) = sum_(i=1)^I ЗТ_(i) × СЦ_(ЗТтек)^(i) × V_(i)")
        self.assertIsNotNone(formula)
        assert formula is not None
        self.assertEqual(formula["source_format"], "mathtype_wmf_text_records")
        self.assertIn("ЗТ", formula["display_latex"])
        self.assertIn("OT_tek", formula["calc_expr"])
        self.assertIn("ОТ_тек", formula["variables"])
        self.assertEqual(formula["confidence"], "medium")
        self.assertIsInstance(formula["warnings"], list)

        # Test unknown formula returns None
        unknown = get_known_formula_representation("unknown formula")
        self.assertIsNone(unknown)

    def test_mathtype_signature_rules_structure(self) -> None:
        """MathType signature rules have expected condition types."""
        rules = get_mathtype_signature_rules()

        condition_types = set()
        for rule in rules:
            condition = rule["condition"]
            if "signature_exact" in condition:
                condition_types.add("signature_exact")
            elif "signature_contains_all" in condition:
                condition_types.add("signature_contains_all")
            elif "signature_complex" in condition:
                condition_types.add("signature_complex")

        # Should have at least two types of conditions
        self.assertGreaterEqual(len(condition_types), 2)
        self.assertTrue(
            any(
                any(item.get("ends_with") == "|i" for item in rule["condition"].get("signature_complex", {}).get("contains_any", []))
                for rule in rules
            )
        )


if __name__ == "__main__":
    unittest.main()
