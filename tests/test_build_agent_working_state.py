from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "build_agent_working_state.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("build_agent_working_state_test_module", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BuildAgentWorkingStateTests(unittest.TestCase):
    def test_build_working_state_payload_compacts_latest_state(self) -> None:
        module = _load_module()

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            docs_dir = root / "docs"
            docs_dir.mkdir()
            (docs_dir / "state-snapshot.md").write_text(
                "# State Snapshot\n\n"
                "## 2. Текущий контур\n\n"
                "- Текущий blocker: external time window.\n"
                "- Release status: blocked on GA evidence.\n\n"
                "## 6. Ближайшие validation anchors\n\n"
                "1. validate_harness_assets\n"
                "2. focused unittest\n",
                encoding="utf-8",
            )
            (docs_dir / "agent-telemetry.v1.jsonl").write_text(
                json.dumps(
                    {
                        "schema_version": "agent-telemetry-entry.v1",
                        "date": "2026-06-04",
                        "task": "Compact working state",
                        "task_type": "harness",
                        "touched_areas": ["scripts/build_agent_working_state.py"],
                        "feature_ids": ["compact-working-state"],
                        "validation_targets": ["unit tests"],
                        "validation_result": "passed",
                        "state_update": True,
                        "note": "Generated a compact state overlay.",
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            (docs_dir / "agent-feature-spine.json").write_text(
                json.dumps(
                    {
                        "last_updated": "2026-06-03",
                        "features": [
                            {"feature_id": "release-v1", "status": "active"},
                            {"feature_id": "state-layer", "status": "validated"},
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            payload = module.build_working_state_payload(root)

        self.assertEqual(payload["schema_version"], "agent-working-state.v1")
        self.assertEqual(payload["last_updated"], "2026-06-04")
        self.assertEqual(payload["current_goal"], "Compact working state")
        self.assertIn("release-v1", payload["active_feature_ids"])
        self.assertIn("compact-working-state", payload["active_feature_ids"])
        self.assertEqual(payload["blockers"], ["external time window"])
        self.assertIn("unit tests", payload["validation_targets"])
        self.assertIn("hot", payload["memory_tiers"])

    def test_dump_working_state_json_is_stable(self) -> None:
        module = _load_module()

        dumped = module.dump_working_state_json({"b": 1, "a": 2})

        self.assertEqual(dumped, '{\n  "a": 2,\n  "b": 1\n}\n')


if __name__ == "__main__":
    unittest.main()
