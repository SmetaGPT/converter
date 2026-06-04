from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "build_state_snapshot.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("build_state_snapshot_test_module", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BuildStateSnapshotTests(unittest.TestCase):
    def test_build_state_snapshot_payload_reads_current_state_sources(self) -> None:
        module = _load_module()

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            docs_dir = root / "docs"
            docs_dir.mkdir()
            (docs_dir / "current-status.md").write_text(
                "# Current Status\n\n"
                "Последнее обновление: 2026-06-03\n"
                "Статус контура: W9 closed; S10.1 gate active\n\n"
                "## 1. Краткий снимок состояния\n\n"
                "- state layer получил lightweight entry point.\n",
                encoding="utf-8",
            )
            (docs_dir / "current-sprint.md").write_text(
                "# Current Sprint\n\n"
                "Последнее обновление: 2026-06-02\n"
                "Активный спринт: S10.1 — v1.0 gate\n"
                "Статус: blocked_external_time\n\n"
                "## 4. Validation targets текущего состояния\n\n"
                "1. validate_harness_assets\n"
                "2. refresh_agent_eval\n"
                "3. narrow unittest\n\n"
                "## 5. Риски и blocker\n\n"
                "- Главный blocker теперь time-based GA criteria.\n",
                encoding="utf-8",
            )
            (docs_dir / "release-status.md").write_text(
                "# Release Status\n\n"
                "Последнее обновление: 2026-06-01\n"
                "Релизный контур: Windows Document Converter v0.3.0\n"
                "Статус: production-ready within declared scope\n",
                encoding="utf-8",
            )
            (docs_dir / "agent-feature-spine.json").write_text(
                json.dumps(
                    {
                        "features": [
                            {
                                "feature_id": "state-layer",
                                "behavior": "Cold-start begins with docs/state-snapshot.md first.",
                            },
                            {
                                "feature_id": "bootstrap-contract",
                                "behavior": "A new session can reacquire release scope and next validation path.",
                            },
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            payload = module.build_state_snapshot_payload(root)
            markdown = module.build_state_snapshot_markdown(payload)

        self.assertEqual(payload["last_updated"], "2026-06-03")
        self.assertEqual(payload["active_gate"], "S10.1 — v1.0 gate")
        self.assertEqual(payload["current_blocker"], "Главный blocker теперь time-based GA criteria.")
        self.assertEqual(payload["validation_anchors"], [
            "1. validate_harness_assets",
            "2. refresh_agent_eval",
            "3. narrow unittest",
        ])
        self.assertIn("- Продукт: Windows Document Converter v0.3.0.", markdown)
        self.assertIn("- Текущий active gate: S10.1 — v1.0 gate.", markdown)
        self.assertIn("1. validate_harness_assets", markdown)


if __name__ == "__main__":
    unittest.main()