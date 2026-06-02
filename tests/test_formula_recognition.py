from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from doc_converter.config import FormulaRecognitionConfig
from doc_converter.formula_recognition import run_formula_recognition_postprocess
from doc_converter.formulas.providers import (
    FormulaProviderContext,
    FormulaRecognitionAsset,
    LocalTesseractProvider,
    MathpixProvider,
    NullProvider,
    OpenRouterProvider,
    _request_openrouter_completion,
    build_formula_provider_chain,
)
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
                "doc_converter.formulas.providers._request_openrouter_completion",
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
                    "cache_hits": 0,
                    "estimated_cost_usd": 0.001203,
                    "review_required_units": 0,
                    "prompt_version": "v1",
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
            self.assertEqual(artifact_record["cache_status"], "miss")
            self.assertFalse(artifact_record["review_required"])

    def test_formula_recognition_uses_mathpix_hint_before_openrouter(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            document_dir = Path(temp_dir)
            assets_dir = document_dir / "assets"
            assets_dir.mkdir()
            asset_path = assets_dir / "formula.png"
            asset_path.write_bytes(b"png")

            payload = _minimal_document_payload(asset_path)
            (document_dir / "document.v1.json").write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            captured_prompt: dict[str, str] = {}

            def _fake_openrouter(*, api_key: str, model: str, image_url: str | None, prompt: str) -> dict[str, object]:
                captured_prompt["prompt"] = prompt
                return {
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
                }

            with patch(
                "doc_converter.formulas.providers._request_mathpix_text",
                return_value={
                    "text": r"\( C = A + B \)",
                    "confidence": 0.99,
                    "data": [{"type": "latex", "value": r"C = A + B"}],
                },
            ) as mocked_mathpix, patch(
                "doc_converter.formulas.providers._request_openrouter_completion",
                side_effect=_fake_openrouter,
            ) as mocked_openrouter:
                result = run_formula_recognition_postprocess(
                    document_dir,
                    FormulaRecognitionConfig(
                        mode="mathpix_first",
                        mathpix_app_id="mathpix-id",
                        mathpix_app_key="mathpix-key",
                        provider="openrouter",
                        model="openai/gpt-4o",
                        api_key="router-secret",
                    ),
                )

            mocked_mathpix.assert_called_once()
            mocked_openrouter.assert_called_once()
            self.assertEqual(result.attempted, 1)
            self.assertEqual(result.recognized, 1)
            self.assertEqual(result.provider_calls, 2)
            self.assertIn("mathpix_latex: C = A + B", captured_prompt["prompt"])

            updated_payload = json.loads((document_dir / "document.v1.json").read_text(encoding="utf-8"))
            formula_unit = updated_payload["units"][1]
            self.assertEqual(formula_unit["formula"]["calc_expr"], "C = A + B")
            self.assertEqual(updated_payload["processing"]["formula_recognition"]["mathpix"], {"configured": True})
            self.assertEqual(updated_payload["processing"]["formula_recognition"]["cache_hits"], 0)
            artifact_lines = (document_dir / "formula-recognition.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual(json.loads(artifact_lines[0])["status"], "recognized_mathpix_partial")
            self.assertEqual(json.loads(artifact_lines[1])["status"], "recognized_provider")
            self.assertEqual(result.artifact_path, "formula-recognition.jsonl")

    def test_openrouter_request_uses_strict_json_schema(self) -> None:
        captured: dict[str, object] = {}

        class _FakeResponse:
            def __enter__(self) -> _FakeResponse:
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

        with patch("doc_converter.formulas.providers.urllib.request.urlopen", side_effect=_fake_urlopen):
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
                "doc_converter.formulas.providers._request_openrouter_completion",
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
            self.assertEqual(result.review_required_units, 0)
            updated_payload = json.loads((document_dir / "document.v1.json").read_text(encoding="utf-8"))
            formula_unit = updated_payload["units"][1]
            self.assertEqual(formula_unit["formula"]["confidence"], "high")
            self.assertEqual(formula_unit["formula"]["calc_expr"], "Z_ch = t_i * Z_chj")
            artifact_record = json.loads((document_dir / "formula-recognition.jsonl").read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(artifact_record["candidate_kind"], "formula_text")

    def test_formula_recognition_skips_low_confidence_formula_with_existing_calc_expr(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            document_dir = Path(temp_dir)
            payload = _minimal_formula_text_document_payload(
                calc_expr="Z_ch = t_rab_mes",
                confidence="low",
                source_format="docx_text_linearized",
                warnings=["formula_calc_expr_is_heuristic"],
            )
            (document_dir / "document.v1.json").write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            with patch("doc_converter.formulas.providers._request_openrouter_completion") as mocked_provider:
                result = run_formula_recognition_postprocess(
                    document_dir,
                    FormulaRecognitionConfig(provider="openrouter", model="openai/gpt-4o", api_key="secret"),
                )

            mocked_provider.assert_not_called()
            self.assertEqual(result.attempted, 0)
            self.assertEqual(result.recognized, 0)
            self.assertEqual(result.provider_calls, 0)
            self.assertFalse((document_dir / "formula-recognition.jsonl").exists())

    def test_formula_recognition_attempts_formula_without_calc_expr_even_if_confidence_high(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            document_dir = Path(temp_dir)
            payload = _minimal_formula_text_document_payload(
                calc_expr=None,
                confidence="high",
                source_format="mathtype_wmf_text_records",
                warnings=[],
            )
            (document_dir / "document.v1.json").write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            with patch(
                "doc_converter.formulas.providers._request_openrouter_completion",
                return_value={
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(
                                    {
                                        "linear_text": "З_ч = t_i * З_чj",
                                        "display_latex": r"З_{ч} = t_{i} \\times З_{чj}",
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
            ) as mocked_provider:
                result = run_formula_recognition_postprocess(
                    document_dir,
                    FormulaRecognitionConfig(provider="openrouter", model="openai/gpt-4o", api_key="secret"),
                )

            mocked_provider.assert_called_once()
            self.assertEqual(result.attempted, 1)
            self.assertEqual(result.recognized, 1)
            self.assertEqual(result.provider_calls, 1)

    def test_formula_recognition_uses_local_backend_without_provider(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            document_dir = Path(temp_dir)
            assets_dir = document_dir / "assets"
            assets_dir.mkdir()
            asset_path = assets_dir / "formula.png"
            asset_path.write_bytes(b"png")

            payload = _minimal_document_payload(asset_path)
            (document_dir / "document.v1.json").write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            with patch(
                "doc_converter.formulas.providers._recognize_formula_with_tesseract",
                return_value={
                    "source_format": "heuristic_latex",
                    "linear_text": "C = A + B",
                    "display_latex": r"C = A + B",
                    "calc_expr": "C = A + B",
                    "confidence": "low",
                    "warnings": ["formula_local_backend_tesseract"],
                },
            ) as mocked_local_backend, patch(
                "doc_converter.formulas.providers._request_openrouter_completion"
            ) as mocked_provider:
                result = run_formula_recognition_postprocess(
                    document_dir,
                    FormulaRecognitionConfig(local_backend="tesseract"),
                )

            mocked_local_backend.assert_called_once()
            mocked_provider.assert_not_called()
            self.assertEqual(result.attempted, 1)
            self.assertEqual(result.recognized, 1)
            self.assertEqual(result.provider_calls, 0)
            updated_payload = json.loads((document_dir / "document.v1.json").read_text(encoding="utf-8"))
            formula_unit = updated_payload["units"][1]
            self.assertEqual(formula_unit["formula"]["calc_expr"], "C = A + B")
            self.assertIn("formula_recognition_local_backend_generated", formula_unit["quality"]["warnings"])
            self.assertEqual(
                updated_payload["processing"]["formula_recognition"],
                {
                    "attempted": 1,
                    "recognized": 1,
                    "provider_calls": 0,
                    "cache_hits": 0,
                    "estimated_cost_usd": 0.0,
                    "review_required_units": 1,
                    "prompt_version": "v1",
                    "results_path": "formula-recognition.jsonl",
                    "local_backend": "tesseract",
                },
            )
            artifact_record = json.loads((document_dir / "formula-recognition.jsonl").read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(artifact_record["status"], "recognized_local_backend")
            self.assertEqual(artifact_record["local_backend"], "tesseract")
            self.assertIn("review_required", updated_payload["quality"]["flags"])

    def test_formula_recognition_falls_back_to_provider_after_local_backend_miss(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            document_dir = Path(temp_dir)
            assets_dir = document_dir / "assets"
            assets_dir.mkdir()
            asset_path = assets_dir / "formula.png"
            asset_path.write_bytes(b"png")

            payload = _minimal_document_payload(asset_path)
            (document_dir / "document.v1.json").write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            with patch(
                "doc_converter.formulas.providers._recognize_formula_with_tesseract",
                return_value=None,
            ) as mocked_local_backend, patch(
                "doc_converter.formulas.providers._request_openrouter_completion",
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
            ) as mocked_provider:
                result = run_formula_recognition_postprocess(
                    document_dir,
                    FormulaRecognitionConfig(local_backend="tesseract", provider="openrouter", model="openai/gpt-4o", api_key="secret"),
                )

            mocked_local_backend.assert_called_once()
            mocked_provider.assert_called_once()
            self.assertEqual(result.recognized, 1)
            self.assertEqual(result.provider_calls, 1)

    def test_formula_recognition_reuses_provider_cache_within_shared_run_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            document_dir = Path(temp_dir)
            assets_dir = document_dir / "assets"
            assets_dir.mkdir()
            asset_path = assets_dir / "formula.png"
            asset_path.write_bytes(b"png")

            payload = _minimal_duplicate_formula_image_document_payload(asset_path)
            (document_dir / "document.v1.json").write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            with patch(
                "doc_converter.formulas.providers._request_openrouter_completion",
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
            ) as mocked_provider:
                result = run_formula_recognition_postprocess(
                    document_dir,
                    FormulaRecognitionConfig(provider="openrouter", model="openai/gpt-4o", api_key="secret"),
                    run_state=None,
                )

            mocked_provider.assert_called_once()
            self.assertEqual(result.attempted, 2)
            self.assertEqual(result.recognized, 2)
            self.assertEqual(result.provider_calls, 1)
            self.assertEqual(result.cache_hits, 1)
            artifact_records = [
                json.loads(line)
                for line in (document_dir / "formula-recognition.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(artifact_records[0]["cache_status"], "miss")
            self.assertEqual(artifact_records[1]["cache_status"], "hit")

    def test_formula_recognition_budget_breach_marks_review_required_without_provider_call(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            document_dir = Path(temp_dir)
            assets_dir = document_dir / "assets"
            assets_dir.mkdir()
            asset_path = assets_dir / "formula.png"
            asset_path.write_bytes(b"png")

            payload = _minimal_document_payload(asset_path)
            (document_dir / "document.v1.json").write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            with patch("doc_converter.formulas.providers._request_openrouter_completion") as mocked_provider:
                result = run_formula_recognition_postprocess(
                    document_dir,
                    FormulaRecognitionConfig(
                        provider="openrouter",
                        model="openai/gpt-4o",
                        api_key="secret",
                        max_provider_calls=0,
                    ),
                )

            mocked_provider.assert_not_called()
            self.assertEqual(result.attempted, 1)
            self.assertEqual(result.recognized, 0)
            self.assertEqual(result.provider_calls, 0)
            self.assertEqual(result.review_required_units, 1)
            updated_payload = json.loads((document_dir / "document.v1.json").read_text(encoding="utf-8"))
            self.assertIn("review_required", updated_payload["quality"]["flags"])
            self.assertIn("formula_recognition_budget_max_provider_calls", updated_payload["quality"]["warnings"])
            artifact_record = json.loads((document_dir / "formula-recognition.jsonl").read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(artifact_record["status"], "budget_skipped")
            self.assertTrue(artifact_record["review_required"])

    def test_formula_recognition_low_confidence_provider_result_marks_review_required(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            document_dir = Path(temp_dir)
            assets_dir = document_dir / "assets"
            assets_dir.mkdir()
            asset_path = assets_dir / "formula.png"
            asset_path.write_bytes(b"png")

            payload = _minimal_document_payload(asset_path)
            (document_dir / "document.v1.json").write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            with patch(
                "doc_converter.formulas.providers._request_openrouter_completion",
                return_value={
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(
                                    {
                                        "linear_text": "C = A + B",
                                        "display_latex": r"C = A + B",
                                        "calc_expr": "C = A + B",
                                        "confidence": "low",
                                        "warnings": ["ambiguous"],
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

            self.assertEqual(result.recognized, 1)
            self.assertEqual(result.review_required_units, 1)
            updated_payload = json.loads((document_dir / "document.v1.json").read_text(encoding="utf-8"))
            self.assertIn("review_required", updated_payload["quality"]["flags"])
            self.assertIn("formula_recognition_low_confidence", updated_payload["quality"]["warnings"])
            formula_unit = updated_payload["units"][1]
            self.assertIn("review_required", formula_unit["quality"]["flags"])
            artifact_record = json.loads((document_dir / "formula-recognition.jsonl").read_text(encoding="utf-8").splitlines()[0])
            self.assertTrue(artifact_record["review_required"])

    def test_build_formula_provider_chain_returns_null_provider_when_unconfigured(self) -> None:
        providers = build_formula_provider_chain(FormulaRecognitionConfig())

        self.assertEqual(len(providers), 1)
        self.assertIsInstance(providers[0], NullProvider)

    def test_build_formula_provider_chain_orders_mathpix_before_openrouter(self) -> None:
        providers = build_formula_provider_chain(
            FormulaRecognitionConfig(
                mathpix_app_id="mathpix-id",
                mathpix_app_key="mathpix-key",
                provider="openrouter",
                model="openai/gpt-4o",
                api_key="router-secret",
            )
        )

        self.assertEqual([provider.provider_id for provider in providers], ["mathpix", "openrouter"])

    def test_local_tesseract_provider_returns_prediction(self) -> None:
        provider = LocalTesseractProvider(backend="tesseract")
        asset = FormulaRecognitionAsset(path=Path("formula.png"), blob=b"png")
        context = FormulaProviderContext(
            candidate_kind="formula_image",
            asset_name="formula.png",
            local_hint_text=None,
            source_text=None,
        )

        with patch(
            "doc_converter.formulas.providers._recognize_formula_with_tesseract",
            return_value={
                "source_format": "heuristic_latex",
                "linear_text": "C = A + B",
                "display_latex": r"C = A + B",
                "calc_expr": "C = A + B",
                "confidence": "high",
                "warnings": [],
            },
        ) as mocked_backend:
            prediction = provider.predict(asset, context)

        mocked_backend.assert_called_once()
        assert prediction is not None
        self.assertEqual(prediction.origin, "local_backend")
        self.assertEqual(prediction.formula["calc_expr"], "C = A + B")

    def test_openrouter_provider_returns_prediction(self) -> None:
        provider = OpenRouterProvider(provider="openrouter", model="openai/gpt-4o", api_key="secret")
        asset = FormulaRecognitionAsset(path=None, blob=None)
        context = FormulaProviderContext(
            candidate_kind="formula_text",
            asset_name=None,
            local_hint_text=None,
            source_text="C = A + B",
        )

        with patch(
            "doc_converter.formulas.providers._request_openrouter_completion",
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
        ) as mocked_request:
            prediction = provider.predict(asset, context)

        mocked_request.assert_called_once()
        assert prediction is not None
        self.assertEqual(prediction.origin, "provider")
        self.assertEqual(prediction.formula["display_latex"], r"C = A + B")

    def test_mathpix_provider_returns_display_only_prediction(self) -> None:
        provider = MathpixProvider(app_id="mathpix-id", app_key="mathpix-key")
        asset = FormulaRecognitionAsset(path=Path("formula.png"), blob=b"png")
        context = FormulaProviderContext(
            candidate_kind="formula_image",
            asset_name="formula.png",
            local_hint_text=None,
            source_text=None,
        )

        with patch(
            "doc_converter.formulas.providers._request_mathpix_text",
            return_value={
                "text": r"\( C = A + B \)",
                "confidence": 0.99,
                "data": [
                    {"type": "asciimath", "value": "C = A + B"},
                    {"type": "latex", "value": r"C = A + B"},
                ],
            },
        ) as mocked_request:
            prediction = provider.predict(asset, context)

        mocked_request.assert_called_once()
        assert prediction is not None
        self.assertEqual(prediction.origin, "mathpix")
        self.assertEqual(prediction.formula["display_latex"], r"C = A + B")
        self.assertIsNone(prediction.formula["calc_expr"])
        self.assertIn("formula_mathpix_display_only", prediction.formula["warnings"])

    def test_formula_recognition_postprocess_accepts_explicit_null_provider(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            document_dir = Path(temp_dir)
            assets_dir = document_dir / "assets"
            assets_dir.mkdir()
            asset_path = assets_dir / "formula.png"
            asset_path.write_bytes(b"png")

            payload = _minimal_document_payload(asset_path)
            (document_dir / "document.v1.json").write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            result = run_formula_recognition_postprocess(
                document_dir,
                FormulaRecognitionConfig(),
                providers=(NullProvider(),),
            )

            self.assertEqual(result.attempted, 1)
            self.assertEqual(result.recognized, 0)
            self.assertEqual(result.provider_calls, 0)
            artifact_record = json.loads((document_dir / "formula-recognition.jsonl").read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(artifact_record["status"], "unresolved_without_provider")
            self.assertEqual(artifact_record["provider"], "null")


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


def _minimal_formula_text_document_payload(
    *,
    calc_expr: str | None = None,
    confidence: str = "low",
    source_format: str = "docx_text_linearized",
    warnings: list[str] | None = None,
) -> dict[str, object]:
    sha256 = "1" * 64
    document_id = f"sha256:{sha256}"
    formula_warnings = ["formula_display_latex_is_heuristic"] if warnings is None else warnings
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
                    "source_format": source_format,
                    "linear_text": "З_ч = (ч. раб.мес.)",
                    "display_latex": r"З_ч = (ч. раб.мес.)",
                    "calc_expr": calc_expr,
                    "confidence": confidence,
                    "warnings": formula_warnings,
                },
                "cell": None,
                "source_ref": _source_ref_payload(document_id=document_id, docx_path="/word/document.xml/body/p[1]"),
                "quality": _quality_payload(),
            },
        ],
        "assets": [],
        "quality": {"flags": [], "warnings": []},
    }


def _minimal_duplicate_formula_image_document_payload(asset_path: Path) -> dict[str, object]:
    payload = _minimal_document_payload(asset_path)
    units = payload["units"]
    document_id = payload["document_id"]
    if not isinstance(units, list) or not isinstance(document_id, str):
        raise TypeError("Minimal duplicate formula payload is malformed")
    units.append(
        {
            "unit_id": "u_000002",
            "parent_id": "u_000000",
            "type": "formula_image",
            "order": 2,
            "text": None,
            "asset_ref": "assets/formula.png",
            "formula": None,
            "cell": None,
            "source_ref": _source_ref_payload(document_id=document_id, docx_path="/word/media/formula-copy.png"),
            "quality": _quality_payload(),
        }
    )
    return payload
