from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "create_nightly_failure_issue.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("nightly_failure_issue_test_module", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class NightlyFailureIssueTests(unittest.TestCase):
    def test_infer_agent_id_prefers_pr_body_field(self) -> None:
        module = _load_module()

        agent_id, source = module.infer_agent_id(
            {
                "body": "- tranche / sprint: S9.2\n- agent_id: roadmap-agent\n- feature_id(s): ci-nightly-e2e\n",
                "head": {"ref": "agent/s9-2-nightly"},
                "user": {"login": "copilot"},
            }
        )

        self.assertEqual(agent_id, "roadmap-agent")
        self.assertEqual(source, "pr_body")

    def test_infer_agent_id_falls_back_to_head_ref(self) -> None:
        module = _load_module()

        agent_id, source = module.infer_agent_id(
            {
                "body": "- tranche / sprint: S9.2\n- agent_id: -\n",
                "head": {"ref": "agent/s9-2-nightly"},
                "user": {"login": "copilot"},
            }
        )

        self.assertEqual(agent_id, "agent/s9-2-nightly")
        self.assertEqual(source, "head_ref")

    def test_build_issue_body_includes_last_merge_and_failed_jobs(self) -> None:
        module = _load_module()

        body = module.build_issue_body(
            workflow_name="nightly-full-e2e",
            run_payload={
                "id": 123,
                "event": "schedule",
                "conclusion": "failure",
                "head_sha": "abc123",
            },
            run_url="https://example.invalid/run/123",
            jobs=[
                {"name": "nightly-full-e2e", "conclusion": "failure"},
                {"name": "upload-artifacts", "conclusion": "success"},
            ],
            latest_pull_request={
                "number": 45,
                "title": "Seed nightly workflow",
                "merged_at": "2026-05-30T18:00:00Z",
                "merge_commit_sha": "deadbeef",
                "body": "- agent_id: roadmap-agent\n",
                "head": {"ref": "agent/s9-2-nightly"},
                "user": {"login": "copilot"},
            },
        )

        self.assertIn("<!-- nightly-full-e2e -->", body)
        self.assertIn("- number: #45", body)
        self.assertIn("- agent_id: roadmap-agent", body)
        self.assertIn("- nightly-full-e2e: failure", body)


if __name__ == "__main__":
    unittest.main()