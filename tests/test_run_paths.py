from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from doc_converter.run.paths import ConverterError, validate_run_directories


class RunPathValidationTests(unittest.TestCase):
    def test_validate_run_directories_resolves_safe_paths(self) -> None:
        with tempfile.TemporaryDirectory() as input_dir, tempfile.TemporaryDirectory() as output_root:
            resolved_input, resolved_output = validate_run_directories(Path(input_dir), Path(output_root) / "safe-output")

            self.assertEqual(resolved_input, Path(input_dir).resolve())
            self.assertEqual(resolved_output, (Path(output_root) / "safe-output").resolve())
            self.assertTrue((resolved_output / "runs").parent == resolved_output)

    def test_validate_run_directories_rejects_symlinked_input_dir(self) -> None:
        with tempfile.TemporaryDirectory() as input_dir, tempfile.TemporaryDirectory() as output_dir, tempfile.TemporaryDirectory() as links_dir:
            symlink_path = Path(links_dir) / "input-link"
            try:
                symlink_path.symlink_to(Path(input_dir), target_is_directory=True)
            except OSError:
                self.skipTest("Directory symlinks are unavailable in this environment")

            with self.assertRaisesRegex(ConverterError, "Input directory must not include symlink components"):
                validate_run_directories(symlink_path, Path(output_dir))

    def test_validate_run_directories_rejects_symlinked_runs_dir(self) -> None:
        with tempfile.TemporaryDirectory() as input_dir, tempfile.TemporaryDirectory() as output_dir, tempfile.TemporaryDirectory() as other_dir:
            runs_link = Path(output_dir) / "runs"
            try:
                runs_link.symlink_to(Path(other_dir), target_is_directory=True)
            except OSError:
                self.skipTest("Directory symlinks are unavailable in this environment")

            with self.assertRaisesRegex(ConverterError, "Runs directory must not include symlink components"):
                validate_run_directories(Path(input_dir), Path(output_dir))

    def test_validate_run_directories_rejects_nested_output(self) -> None:
        with tempfile.TemporaryDirectory() as input_dir:
            output_dir = Path(input_dir) / "nested-output"

            with self.assertRaisesRegex(ConverterError, "must not be nested"):
                validate_run_directories(Path(input_dir), output_dir)