from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "run_sample_pilot.py"


def _load_run_sample_pilot_module():
    spec = importlib.util.spec_from_file_location("run_sample_pilot_test_module", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RunSamplePilotTests(unittest.TestCase):
    def test_stage_records_resolves_source_root_relative_to_manifest(self) -> None:
        module = _load_run_sample_pilot_module()

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_dir = root / "manifests"
            source_dir = manifest_dir / "fixtures"
            input_dir = root / "input"
            source_dir.mkdir(parents=True)
            input_dir.mkdir(parents=True)

            source_path = source_dir / "sample.pdf"
            source_path.write_text("fixture", encoding="utf-8")

            staged_records = module._stage_records(
                [
                    {
                        "sample_id": "sample_009",
                        "source_root": "fixtures",
                        "relative_path": "sample.pdf",
                    }
                ],
                input_dir,
                manifest_dir=manifest_dir,
            )

            staged_path = input_dir / "sample_009__sample.pdf"
            self.assertTrue(staged_path.exists())
            self.assertEqual(staged_path.read_text(encoding="utf-8"), "fixture")
            self.assertEqual(Path(staged_records[0]["source_path"]).resolve(), source_path.resolve())
            self.assertEqual(staged_records[0]["staged_relative_path"], "sample_009__sample.pdf")


if __name__ == "__main__":
    unittest.main()