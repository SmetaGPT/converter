from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "estimate_context_tokens.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("estimate_context_tokens_test_module", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EstimateContextTokensTests(unittest.TestCase):
    def test_estimate_text_tokens_counts_words_and_symbols(self) -> None:
        module = _load_module()

        self.assertEqual(module.estimate_text_tokens("abc def,()"), 5)
        self.assertEqual(module.estimate_text_tokens("привет мир"), 3)

    def test_build_report_includes_startup_bundles(self) -> None:
        module = _load_module()

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            docs_dir = root / "docs"
            docs_dir.mkdir()
            (docs_dir / "agent-working-state.v1.json").write_text('{"state":"hot"}\n', encoding="utf-8")
            (docs_dir / "state-snapshot.md").write_text("Snapshot line\n", encoding="utf-8")
            (docs_dir / "current-status.md").write_text("Status line\nMore status\n", encoding="utf-8")
            (docs_dir / "current-sprint.md").write_text("Sprint line\n", encoding="utf-8")
            (docs_dir / "release-status.md").write_text("Release line\n", encoding="utf-8")

            payload = module.build_report(root, path_specs=[], inline_texts=[], include_startup_bundles=True, excerpt_lines=0)

        self.assertEqual(payload["summary"]["items"], 2)
        self.assertEqual(payload["summary"]["bundles"], 4)
        bundle_map = {bundle["label"]: bundle for bundle in payload["bundles"]}
        self.assertIn("hot-state startup", bundle_map)
        self.assertIn("snapshot-only startup", bundle_map)
        self.assertIn("hot+snapshot startup", bundle_map)
        self.assertIn("full-state startup", bundle_map)
        self.assertGreater(bundle_map["hot+snapshot startup"]["estimated_tokens"], bundle_map["snapshot-only startup"]["estimated_tokens"])
        self.assertGreater(bundle_map["full-state startup"]["estimated_tokens"], bundle_map["snapshot-only startup"]["estimated_tokens"])

    def test_build_report_excerpt_mode_uses_first_n_lines_only(self) -> None:
        module = _load_module()

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            docs_dir = root / "docs"
            docs_dir.mkdir()
            sample_path = docs_dir / "sample.md"
            sample_path.write_text("line one\nline two\nline three\n", encoding="utf-8")

            payload = module.build_report(
                root,
                path_specs=["docs/sample.md"],
                inline_texts=[],
                include_startup_bundles=False,
                excerpt_lines=2,
            )

        item = payload["items"][0]
        self.assertEqual(item["lines"], 2)
        self.assertEqual(item["total_lines"], 3)
        self.assertEqual(item["mode"], "excerpt:first_2_lines")
        self.assertLess(item["estimated_tokens"], module.estimate_text_tokens("line one\nline two\nline three\n"))


if __name__ == "__main__":
    unittest.main()
