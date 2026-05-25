from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from doc_converter.config import FormulaRecognitionConfig
from doc_converter.formula_recognition import _request_openrouter_completion, run_formula_recognition_postprocess
from doc_converter.schema_validation import validate_payload


class FormulaRecognitionPostprocessTests(unittest.TestCase):
    def test_formula_recognition_updates_document_and_writes_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            document_dir = Path(temp_dir)
            assets_dir = document_dir / "assets"
            assets_dir.mkdir()
            asset_path = assets_dir / "formula.png"
            asset_path.write_bytes(b"not-a-real-png-but-good-enough-for-a-mocked-request")

            payload = _minimal_document_payload(asset_path)
            (document_dir / "document.v1.json").write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            with patch(
                "doc_converter.formula_recognition._request_openrouter_completion",
                return_value={
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(
                                    {
                                        "linear_text": "C = A + B",
                                        "display_latex": r"C = A + B",
                                        "calc_expr": "C = A + B",
                                        "confidence": "high",
                                        "warnings": [],
                                    },
                                    ensure_ascii=False,
                                )
                            }
                        }
                    ]
                },
            ):
                result = run_formula_recognition_postprocess(
                    document_dir,
                    FormulaRecognitionConfig(provider="openrouter", model="openai/gpt-4o", api_key="secret"),
                )

            self.assertEqual(result.attempted, 1)
            self.assertEqual(result.recognized, 1)
            self.assertEqual(result.provider_calls, 1)
            self.assertEqual(result.artifact_path, "formula-recognition.jsonl")

            updated_payload = json.loads((document_dir / "document.v1.json").read_text(encoding="utf-8"))
            validate_payload(updated_payload, "document.v1.schema.json")
            formula_unit = updated_payload["units"][1]
            self.assertEqual(formula_unit["text"], "C = A + B")
            self.assertEqual(formula_unit["formula"]["display_latex"], r"C = A + B")
            self.assertEqual(formula_unit["formula"]["calc_expr"], "C = A + B")
            self.assertIn("formula_recognition_model_generated", formula_unit["quality"]["warnings"])
            self.assertEqual(
                updated_payload["processing"]["formula_recognition"],
                {
                    "provider": "openrouter",
                    "model": "openai/gpt-4o",
                    "attempted": 1,
                    "recognized": 1,
                    "provider_calls": 1,
                    "results_path": "formula-recognition.jsonl",
                },
            )
            self.assertIn("formula_recognition_applied", updated_payload["processing"]["warnings"])
            self.assertNotIn("secret", json.dumps(updated_payload, ensure_ascii=False))

            artifact_lines = (document_dir / "formula-recognition.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(artifact_lines), 1)
            artifact_record = json.loads(artifact_lines[0])
            self.assertEqual(artifact_record["status"], "recognized_provider")
            self.assertEqual(artifact_record["unit_id"], "u_000001")

    def test_openrouter_request_uses_strict_json_schema(self) -> None:
        captured: dict[str, object] = {}

        class _FakeResponse:
            def __enter__(self) -> "_FakeResponse":
                return self

            def __exit__(self, exc_type, exc, tb) -> None:
                return None

            def read(self) -> bytes:
                return json.dumps(
                    {
                        "choices": [
                            {
                                "message": {
                                    "content": json.dumps(
                                        {
                                            "linear_text": "C = A + B",
                                            "display_latex": r"C = A + B",
                                            "calc_expr": "C = A + B",
                                            "confidence": "high",
                                            "warnings": [],
                                        },
                                        ensure_ascii=False,
                                    )
                                }
                            }
                        ]
                    },
                    ensure_ascii=False,
                ).encode("utf-8")

        def _fake_urlopen(request, timeout: int):
            captured["timeout"] = timeout
            captured["body"] = json.loads(request.data.decode("utf-8"))
            return _FakeResponse()

        with patch("doc_converter.formula_recognition.urllib.request.urlopen", side_effect=_fake_urlopen):
            _request_openrouter_completion(
                api_key="secret",
                model="openai/gpt-4o",
                image_url="data:image/png;base64,AAAA",
                prompt="extract formula",
            )

        request_body = captured["body"]
        assert isinstance(request_body, dict)
        self.assertEqual(request_body["model"], "openai/gpt-4o")
        self.assertEqual(request_body["response_format"]["type"], "json_schema")
        self.assertEqual(request_body["response_format"]["json_schema"]["name"], "formula_extraction")
        self.assertTrue(request_body["response_format"]["json_schema"]["strict"])
        self.assertEqual(request_body["messages"][1]["content"][1]["type"], "image_url")
        self.assertEqual(request_body["messages"][1]["content"][1]["image_url"]["url"], "data:image/png;base64,AAAA")

    def test_formula_recognition_updates_low_confidence_formula_text_unit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            document_dir = Path(temp_dir)
            payload = _minimal_formula_text_document_payload()
            (document_dir / "document.v1.json").write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            with patch(
                "doc_converter.formula_recognition._request_openrouter_completion",
                return_value={
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(
                                    {
                                        "linear_text": "З_ч = t_i * З_чj",
                                        "display_latex": r"З_{ч} = t_{i} \times З_{чj}",
                                        "calc_expr": "Z_ch = t_i * Z_chj",
                                        "confidence": "high",
                                        "warnings": [],
                                    },
                                    ensure_ascii=False,
                                )
                            }
                        }
                    ]
                },
            ):
                result = run_formula_recognition_postprocess(
                    document_dir,
                    FormulaRecognitionConfig(provider="openrouter", model="openai/gpt-4o", api_key="secret"),
                )

            self.assertEqual(result.attempted, 1)
            self.assertEqual(result.recognized, 1)
            self.assertEqual(result.provider_calls, 1)
            updated_payload = json.loads((document_dir / "document.v1.json").read_text(encoding="utf-8"))
            formula_unit = updated_payload["units"][1]
            self.assertEqual(formula_unit["formula"]["confidence"], "high")
            self.assertEqual(formula_unit["formula"]["calc_expr"], "Z_ch = t_i * Z_chj")
            artifact_record = json.loads((document_dir / "formula-recognition.jsonl").read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(artifact_record["candidate_kind"], "formula_text")


def _minimal_document_payload(asset_path: Path) -> dict[str, object]:
    sha256 = "0" * 64
    document_id = f"sha256:{sha256}"
    units: list[dict[str, object]] = [
        _document_unit_payload(document_id=document_id),
        _formula_image_unit_payload(document_id=document_id),
    ]
    return {
        "schema_version": "document.v1",
        "document_id": document_id,
        "source": {
            "original_path": str(asset_path),
            "relative_input_path": None,
            "filename": "sample.docx",
            "format": "docx",
            "sha256": sha256,
            "size_bytes": 1,
        },
        "processing": {
            "route": "docx_native",
            "status": "success",
            "warnings": [],
        },
        "metadata": {
            "title": "sample",
            "document_type": "приказ",
            "short_summary": "sample",
            "confidence": "low",
            "method": "filename_fallback",
        },
        "units": units,
        "assets": [
            {
                "asset_id": "asset_000001",
                "type": "formula_image",
                "path": "assets/formula.png",
                "unit_id": "u_000001",
                "sha256": None,
                "filename": "formula.png",
                "size_bytes": asset_path.stat().st_size,
                "media_type": "image/png",
            }
        ],
        "quality": {"flags": [], "warnings": []},
    }


def _document_unit_payload(*, document_id: str) -> dict[str, object]:
    return {
        "unit_id": "u_000000",
        "parent_id": None,
        "type": "document",
        "order": 0,
        "text": None,
        "asset_ref": None,
        "formula": None,
        "cell": None,
        "source_ref": _source_ref_payload(document_id=document_id, docx_path="/word/document.xml"),
        "quality": _quality_payload(),
    }


def _formula_image_unit_payload(*, document_id: str) -> dict[str, object]:
    return {
        "unit_id": "u_000001",
        "parent_id": "u_000000",
        "type": "formula_image",
        "order": 1,
        "text": None,
        "asset_ref": "assets/formula.png",
        "formula": None,
        "cell": None,
        "source_ref": _source_ref_payload(document_id=document_id, docx_path="/word/media/formula.png"),
        "quality": _quality_payload(),
    }


def _source_ref_payload(*, document_id: str, docx_path: str) -> dict[str, object]:
    return {
        "document_id": document_id,
        "page": None,
        "bbox": None,
        "docx_path": docx_path,
        "coordinate_system": None,
        "page_width": None,
        "page_height": None,
    }


def _quality_payload() -> dict[str, list[str]]:
    return {"flags": [], "warnings": []}


def _minimal_formula_text_document_payload() -> dict[str, object]:
    sha256 = "1" * 64
    document_id = f"sha256:{sha256}"
    return {
        "schema_version": "document.v1",
        "document_id": document_id,
        "source": {
            "original_path": "D:/input/example.docx",
            "relative_input_path": None,
            "filename": "sample.docx",
            "format": "docx",
            "sha256": sha256,
            "size_bytes": 1,
        },
        "processing": {"route": "docx_native", "status": "success", "warnings": []},
        "metadata": {
            "title": "sample",
            "document_type": "приказ",
            "short_summary": "sample",
            "confidence": "low",
            "method": "filename_fallback",
        },
        "units": [
            _document_unit_payload(document_id=document_id),
            {
                "unit_id": "u_000001",
                "parent_id": "u_000000",
                "type": "formula",
                "order": 1,
                "text": "З_ч = (ч. раб.мес.)",
                "asset_ref": None,
                "formula": {
                    "source_format": "docx_text_linearized",
                    "linear_text": "З_ч = (ч. раб.мес.)",
                    "display_latex": r"З_ч = (ч. раб.мес.)",
                    "calc_expr": None,
                    "confidence": "low",
                    "warnings": ["formula_display_latex_is_heuristic"],
                },
                "cell": None,
                "source_ref": _source_ref_payload(document_id=document_id, docx_path="/word/document.xml/body/p[1]"),
                "quality": _quality_payload(),
            },
        ],
        "assets": [],
        "quality": {"flags": [], "warnings": []},
    }