from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "build_agent_handoff.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("build_agent_handoff_test_module", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BuildAgentHandoffTests(unittest.TestCase):
    def test_parse_git_status_path_handles_rename_and_modified(self) -> None:
        module = _load_module()

        self.assertEqual(module.parse_git_status_path(" M docs/current-status.md"), "docs/current-status.md")
        self.assertEqual(module.parse_git_status_path("R  old/name.md -> new/name.md"), "new/name.md")

    def test_build_handoff_payload_prefers_changed_file_as_anchor(self) -> None:
        module = _load_module()

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            docs_dir = root / "docs"
            docs_dir.mkdir()
            (docs_dir / "state-snapshot.md").write_text(
                "# State Snapshot\n\n"
                "## 2. Текущий контур\n\n"
                "- Продукт: Demo Product.\n"
                "- Текущий blocker: external provider credentials missing.\n"
                "- Release status: blocked on external gate.\n\n"
                "## 6. Ближайшие validation anchors\n\n"
                "1. .\\.venv\\Scripts\\python.exe scripts\\validate_harness_assets.py\n",
                encoding="utf-8",
            )
            telemetry_entry = {
                "task": "One-command agent preflight",
                "note": "Added a local one-command preflight wrapper.",
                "validation_result": "passed",
                "validation_targets": [".\\.venv\\Scripts\\python.exe -m unittest tests.test_agent_preflight -v"],
                "touched_areas": ["scripts/agent_preflight.py", "tests/test_agent_preflight.py"],
            }
            payload = module.build_handoff_payload(
                root,
                validator_summary={"status": "ok", "detail": "status ok"},
                changed_files=["scripts/agent_preflight.py", "tests/test_agent_preflight.py"],
                latest_telemetry_entry=telemetry_entry,
                state_snapshot_text=(docs_dir / "state-snapshot.md").read_text(encoding="utf-8"),
            )

        self.assertEqual(payload["current_anchor"], "scripts/agent_preflight.py")
        self.assertEqual(payload["files_to_read_in_new_chat"][:2], ["docs/state-snapshot.md", "scripts/agent_preflight.py"])
        self.assertIn("working tree still has 2 changed paths", payload["blocker_or_residual_risk"])
        self.assertEqual(payload["approval_state"], "external approval or credentials still required")
        self.assertIn("rerun the latest focused check", payload["next_step"])

    def test_build_handoff_payload_handles_failed_validator(self) -> None:
        module = _load_module()

        payload = module.build_handoff_payload(
            ROOT,
            validator_summary={"status": "failed", "detail": "drift"},
            changed_files=[],
            latest_telemetry_entry={"task": "Generated state snapshot sync", "validation_result": "passed", "touched_areas": []},
            state_snapshot_text="# State Snapshot\n\n## 2. Текущий контур\n\n- Текущий blocker: none.\n- Release status: stable.\n",
        )

        self.assertEqual(payload["current_anchor"], "docs/state-snapshot.md")
        self.assertEqual(payload["approval_state"], "blocked by local validation failure")
        self.assertIn("repair validator drift", payload["next_step"])


if __name__ == "__main__":
    unittest.main()