from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from doc_converter.config import ConverterConfig, ConverterOptions, FormulaRecognitionConfig
from doc_converter.converters import REGISTERED_CONVERTERS
from doc_converter.converters.txt import TXT_DUMMY_CONVERTER
from doc_converter.runner import run_convert_folder


class ConverterRegistryTests(unittest.TestCase):
    def test_dummy_txt_converter_registers_without_runner_changes(self) -> None:
        with tempfile.TemporaryDirectory() as input_dir, tempfile.TemporaryDirectory() as output_dir:
            source_path = Path(input_dir) / "sample.txt"
            source_path.write_text("registry works", encoding="utf-8")

            with patch(
                "doc_converter.converters.REGISTERED_CONVERTERS",
                REGISTERED_CONVERTERS + (TXT_DUMMY_CONVERTER,),
            ), patch("doc_converter.converters.txt.validate_payload"), patch("doc_converter.run.orchestration.validate_payload"):
                result = run_convert_folder(
                    ConverterConfig(
                        input_dir=Path(input_dir),
                        output_dir=Path(output_dir),
                        options=ConverterOptions(formula_recognition=FormulaRecognitionConfig()),
                    )
                )

            manifest = [
                json.loads(line)
                for line in (result.run_dir / "manifest.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            document_path = result.run_dir / str(manifest[0]["output_dir"]) / "document.v1.json"
            payload = json.loads(document_path.read_text(encoding="utf-8"))

            self.assertEqual(result.status, "success")
            self.assertEqual(result.supported_files, 1)
            self.assertEqual(manifest[0]["format"], "txt")
            self.assertEqual(manifest[0]["route"], "txt_dummy")
            self.assertEqual(manifest[0]["search_text_chars"], len("registry works"))
            self.assertEqual(payload["processing"]["route"], "txt_dummy")
            self.assertEqual(payload["units"][1]["text"], "registry works")


if __name__ == "__main__":
    unittest.main()