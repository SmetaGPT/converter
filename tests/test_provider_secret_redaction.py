from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from docx import Document

from doc_converter.config import AgentRunMetadata, ConverterConfig, ConverterOptions, FormulaRecognitionConfig
from doc_converter.formula_recognition import run_formula_recognition_postprocess
from doc_converter.runner import run_convert_folder


class ProviderSecretRedactionTests(unittest.TestCase):
    def test_run_artifacts_redact_env_secret_values(self) -> None:
        run_secret = "agent-secret-123456"
        error_secret = "failure-secret-ABCDEF"

        with patch.dict(
            os.environ,
            {
                "RUN_AGENT_SECRET": run_secret,
                "RUN_ERROR_SECRET": error_secret,
            },
            clear=False,
        ):
            with tempfile.TemporaryDirectory() as input_dir, tempfile.TemporaryDirectory() as output_dir:
                source_path = Path(input_dir) / "sample.docx"
                document = Document()
                document.add_paragraph("secret redaction smoke")
                document.save(str(source_path))

                converter = Mock()
                converter.convert.side_effect = RuntimeError(f"converter failed with {error_secret}")
                with patch("doc_converter.run.orchestration.get_converter", return_value=converter):
                    result = run_convert_folder(
                        ConverterConfig(
                            input_dir=Path(input_dir),
                            output_dir=Path(output_dir),
                            options=ConverterOptions(formula_recognition=FormulaRecognitionConfig()),
                            agent_run_metadata=AgentRunMetadata(agent_id=run_secret, agent_version="test", task_id=run_secret),
                        )
                    )

                self.assertEqual(result.status, "failed")
                run_payload = (result.run_dir / "run.json").read_text(encoding="utf-8")
                self.assertIn("[REDACTED_ENV:RUN_AGENT_SECRET]", run_payload)
                self.assert_run_artifacts_do_not_contain_secrets(result.run_dir, run_secret, error_secret)

    def test_formula_recognition_artifact_redacts_env_secret_values(self) -> None:
        provider_secret = "provider-secret-UVWXYZ"

        with patch.dict(os.environ, {"OPENROUTER_API_KEY": provider_secret}, clear=False):
            with tempfile.TemporaryDirectory() as temp_dir:
                document_dir = Path(temp_dir)
                assets_dir = document_dir / "assets"
                assets_dir.mkdir()
                asset_path = assets_dir / "formula.png"
                asset_path.write_bytes(b"png")

                payload = _minimal_formula_document_payload(asset_path)
                (document_dir / "document.v1.json").write_text(payload, encoding="utf-8")

                with patch(
                    "doc_converter.formulas.providers._request_openrouter_completion",
                    side_effect=RuntimeError(f"provider failed with {provider_secret}"),
                ):
                    result = run_formula_recognition_postprocess(
                        document_dir,
                        FormulaRecognitionConfig(provider="openrouter", model="openai/gpt-4o", api_key="placeholder"),
                    )

                self.assertEqual(result.attempted, 1)
                self.assertEqual(result.recognized, 0)
                artifact_text = (document_dir / "formula-recognition.jsonl").read_text(encoding="utf-8")
                self.assertIn("[REDACTED_ENV:OPENROUTER_API_KEY]", artifact_text)
                self.assertNotIn(provider_secret, artifact_text)
                self.assert_run_artifacts_do_not_contain_secrets(document_dir, provider_secret)

    def assert_run_artifacts_do_not_contain_secrets(self, root: Path, *secrets: str) -> None:
        secret_bytes = [secret.encode("utf-8") for secret in secrets]
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            payload = path.read_bytes()
            for secret in secret_bytes:
                self.assertNotIn(secret, payload, msg=f"Secret leaked into artifact {path}")


def _minimal_formula_document_payload(asset_path: Path) -> str:
    return """{
  "schema_version": "document.v1",
  "document_id": "sha256:%s",
  "source": {
    "original_path": "%s",
    "relative_input_path": null,
    "filename": "sample.docx",
    "format": "docx",
    "sha256": "%s",
    "size_bytes": 1
  },
  "processing": {
    "route": "docx_native",
    "status": "success",
    "warnings": []
  },
  "metadata": {
    "title": "sample",
    "document_type": "приказ",
    "short_summary": "sample",
    "confidence": "low",
    "method": "filename_fallback"
  },
  "units": [
    {
      "unit_id": "u_000000",
      "parent_id": null,
      "type": "document",
      "order": 0,
      "text": null,
      "asset_ref": null,
      "formula": null,
      "cell": null,
      "source_ref": {
        "document_id": "sha256:%s",
        "page": null,
        "bbox": null,
        "docx_path": null,
        "coordinate_system": null,
        "page_width": null,
        "page_height": null
      },
      "quality": {
        "flags": [],
        "warnings": []
      }
    },
    {
      "unit_id": "u_000001",
      "parent_id": "u_000000",
      "type": "formula_image",
      "order": 1,
      "text": "placeholder",
      "asset_ref": "assets/formula.png",
      "formula": null,
      "cell": null,
      "source_ref": {
        "document_id": "sha256:%s",
        "page": null,
        "bbox": null,
        "docx_path": null,
        "coordinate_system": null,
        "page_width": null,
        "page_height": null
      },
      "quality": {
        "flags": [],
        "warnings": []
      }
    }
  ],
  "assets": [
    {
      "asset_id": "asset_000001",
      "type": "formula_image",
      "path": "assets/formula.png",
      "unit_id": "u_000001",
      "sha256": null,
      "filename": "formula.png",
      "size_bytes": %d,
      "media_type": "image/png"
    }
  ],
  "quality": {
    "flags": [],
    "warnings": []
  }
}
""" % (
        "0" * 64,
        asset_path.as_posix(),
        "0" * 64,
        "0" * 64,
        "0" * 64,
        asset_path.stat().st_size,
    )
