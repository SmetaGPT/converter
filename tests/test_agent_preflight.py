from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "agent_preflight.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("agent_preflight_test_module", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AgentPreflightTests(unittest.TestCase):
    def test_local_fast_path_counts_anchor_budget(self) -> None:
        module = _load_module()

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            tests_dir = root / "tests"
            tests_dir.mkdir(parents=True)
            (tests_dir / "test_release_notes.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")

            payload = module.build_preflight_payload(
                root,
                task="Исправь падение узкого теста вокруг release notes.",
                anchors=["tests/test_release_notes.py"],
                excerpt_lines=40,
            )

        self.assertEqual(payload["scope"], "local-fast-path")
        self.assertFalse(payload["feature_id_required"])
        self.assertEqual(payload["first_validation"], ".\\.venv\\Scripts\\python.exe -m unittest tests.test_release_notes -v")
        self.assertEqual(payload["startup_budget"]["counted_reads"], ["tests/test_release_notes.py"])
        self.assertEqual(payload["startup_budget"]["skipped_reads"], [])
        self.assertEqual(payload["reference_bundles"], [])
        self.assertIsNone(payload["handoff_summary"])
        self.assertGreater(payload["startup_budget"]["estimated_tokens"], 0)

    def test_cross_module_preflight_includes_snapshot_and_reference_bundles(self) -> None:
        module = _load_module()

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            docs_dir = root / "docs"
            docs_dir.mkdir(parents=True)
            (root / "AGENTS.md").write_text("startup contract\n", encoding="utf-8")
            (docs_dir / "state-snapshot.md").write_text("snapshot\n", encoding="utf-8")
            (docs_dir / "agent-working-state.v1.json").write_text(
                '{"current_goal":"Hot state","current_status":"stable","active_feature_ids":["agent-preflight"],"next":["focused check"],"blockers":[],"validation_targets":["focused check"]}\n',
                encoding="utf-8",
            )
            (docs_dir / "current-status.md").write_text("status\n", encoding="utf-8")
            (docs_dir / "current-sprint.md").write_text("sprint\n", encoding="utf-8")
            (docs_dir / "release-status.md").write_text("release\n", encoding="utf-8")
            (docs_dir / "agent-bootstrap-contract.md").write_text("bootstrap\n", encoding="utf-8")
            (docs_dir / "agent-telemetry.v1.jsonl").write_text(
                '{"task":"One-command agent preflight","note":"Added unified preflight wrapper.","validation_result":"passed","validation_targets":[".\\\\.venv\\\\Scripts\\\\python.exe -m unittest tests.test_agent_preflight -v"],"touched_areas":["scripts/agent_preflight.py"]}\n',
                encoding="utf-8",
            )
            (docs_dir / "state-snapshot.md").write_text(
                "# State Snapshot\n\n"
                "## 2. Текущий контур\n\n"
                "- Продукт: Demo Product.\n"
                "- Текущий blocker: none.\n"
                "- Release status: stable.\n\n"
                "## 6. Ближайшие validation anchors\n\n"
                "1. .\\.venv\\Scripts\\python.exe -m unittest tests.test_agent_preflight -v\n",
                encoding="utf-8",
            )

            payload = module.build_preflight_payload(
                root,
                task="Обнови startup contract и bootstrap behavior.",
                anchors=["AGENTS.md", "docs/agent-bootstrap-contract.md"],
                excerpt_lines=80,
            )

        self.assertEqual(payload["scope"], "cross-module")
        self.assertTrue(payload["feature_id_required"])
        self.assertEqual(
            payload["first_reads"],
            ["docs/agent-working-state.v1.json", "docs/state-snapshot.md", "AGENTS.md", "docs/agent-bootstrap-contract.md"],
        )
        self.assertEqual(
            payload["startup_budget"]["counted_reads"],
            ["docs/agent-working-state.v1.json", "docs/state-snapshot.md", "AGENTS.md", "docs/agent-bootstrap-contract.md"],
        )
        self.assertEqual(payload["working_state"]["current_goal"], "Hot state")
        bundle_map = {bundle["label"]: bundle for bundle in payload["reference_bundles"]}
        self.assertIn("snapshot-only startup", bundle_map)
        self.assertIn("full-state startup", bundle_map)
        self.assertIsNotNone(payload["handoff_summary"])
        self.assertEqual(payload["handoff_summary"]["goal"], "One-command agent preflight")
        self.assertEqual(payload["handoff_summary"]["current_anchor"], "AGENTS.md")
        self.assertEqual(payload["handoff_summary"]["touched_surface"], ["AGENTS.md", "docs/agent-bootstrap-contract.md"])


if __name__ == "__main__":
    unittest.main()
