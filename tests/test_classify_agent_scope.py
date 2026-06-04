from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "classify_agent_scope.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("classify_agent_scope_test_module", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ClassifyAgentScopeTests(unittest.TestCase):
    def test_local_fast_path_prefers_test_anchor_validation(self) -> None:
        module = _load_module()

        payload = module.classify_scope(
            "Исправь падение узкого теста вокруг release notes.",
            ["tests/test_release_notes.py"],
        )

        self.assertEqual(payload["scope"], "local-fast-path")
        self.assertFalse(payload["state_strategy"]["read_full_state"])
        self.assertEqual(
            payload["first_validation"],
            ".\\.venv\\Scripts\\python.exe -m unittest tests.test_release_notes -v",
        )
        self.assertFalse(payload["feature_id_required"])

    def test_release_scope_reads_full_state(self) -> None:
        module = _load_module()

        payload = module.classify_scope(
            "Проверь nightly workflow и release blocker.",
            [".github/workflows/windows-ci.yml"],
        )

        self.assertEqual(payload["scope"], "release")
        self.assertTrue(payload["state_strategy"]["read_full_state"])
        self.assertIn("docs/agent-working-state.v1.json", payload["first_reads"])
        self.assertIn("docs/state-snapshot.md", payload["first_reads"])
        self.assertTrue(payload["feature_id_required"])

    def test_resume_scope_detects_resume_keywords(self) -> None:
        module = _load_module()

        payload = module.classify_scope(
            "Продолжи вчерашний tranche по formula benchmark.",
            ["src/doc_converter/formula_benchmark.py"],
        )

        self.assertEqual(payload["scope"], "resume")
        self.assertTrue(payload["state_strategy"]["read_full_state"])
        self.assertIn("docs/agent-working-state.v1.json", payload["first_reads"])
        self.assertIn("docs/current-status.md", payload["first_reads"])

    def test_cross_module_scope_detects_process_anchor(self) -> None:
        module = _load_module()

        payload = module.classify_scope(
            "Обнови startup contract и bootstrap behavior.",
            ["AGENTS.md", "docs/agent-bootstrap-contract.md"],
        )

        self.assertEqual(payload["scope"], "cross-module")
        self.assertFalse(payload["state_strategy"]["read_full_state"])
        self.assertTrue(payload["state_strategy"]["read_working_state_first"])
        self.assertEqual(
            payload["first_validation"],
            ".\\.venv\\Scripts\\python.exe scripts\\validate_harness_assets.py",
        )
        self.assertTrue(payload["feature_id_required"])


if __name__ == "__main__":
    unittest.main()
