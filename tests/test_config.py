from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from doc_converter.config import ConverterOptions, load_formula_recognition_config


class FormulaRecognitionConfigTests(unittest.TestCase):
    def test_load_formula_recognition_from_env_local(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".env.local").write_text(
                "FORMULA_RECOGNITION_PROVIDER=mathpix\n"
                "FORMULA_RECOGNITION_MODEL=mathpix-ocr-v3\n"
                "FORMULA_RECOGNITION_API_KEY=local-secret\n",
                encoding="utf-8",
            )

            with patch("doc_converter.config.Path.cwd", return_value=root):
                config = load_formula_recognition_config()

            self.assertEqual(config.provider, "mathpix")
            self.assertEqual(config.model, "mathpix-ocr-v3")
            self.assertEqual(config.api_key, "local-secret")
            self.assertTrue(config.is_configured())

    def test_load_formula_recognition_from_openrouter_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".env.local").write_text(
                "LLM_PROVIDER=openrouter\n"
                "OPENROUTER_MODEL=deepseek/deepseek-v4-pro\n"
                "FORMULA_MODEL=openai/gpt-4o\n"
                "OPENROUTER_API_KEY=router-secret\n",
                encoding="utf-8",
            )

            with patch("doc_converter.config.Path.cwd", return_value=root):
                config = load_formula_recognition_config()

            self.assertEqual(config.provider, "openrouter")
            self.assertEqual(config.model, "openai/gpt-4o")
            self.assertEqual(config.api_key, "router-secret")
            self.assertTrue(config.is_configured())

    def test_load_formula_recognition_from_mathpix_and_openrouter(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".env.local").write_text(
                "FORMULA_RECOGNITION_MODE=mathpix_first\n"
                "FORMULA_RECOGNITION_PROMPT_VERSION=mathpix-v2\n"
                "FORMULA_RECOGNITION_MAX_FORMULAS_PER_RUN=12\n"
                "FORMULA_RECOGNITION_MAX_PROVIDER_CALLS=8\n"
                "FORMULA_RECOGNITION_MAX_ESTIMATED_COST_USD=0.5\n"
                "MATHPIX_APP_ID=mathpix-id\n"
                "MATHPIX_APP_KEY=mathpix-key\n"
                "OPENROUTER_API_KEY=router-secret\n",
                encoding="utf-8",
            )

            with patch("doc_converter.config.Path.cwd", return_value=root):
                config = load_formula_recognition_config()

            self.assertEqual(config.mode, "mathpix_first")
            self.assertEqual(config.prompt_version, "mathpix-v2")
            self.assertEqual(config.mathpix_app_id, "mathpix-id")
            self.assertEqual(config.mathpix_app_key, "mathpix-key")
            self.assertEqual(config.provider, "openrouter")
            self.assertEqual(config.model, "openai/gpt-4o")
            self.assertEqual(config.api_key, "router-secret")
            self.assertEqual(config.max_formulas_per_run, 12)
            self.assertEqual(config.max_provider_calls, 8)
            self.assertEqual(config.max_estimated_cost_usd, 0.5)
            self.assertTrue(config.mathpix_is_configured())
            self.assertTrue(config.is_configured())

    def test_load_formula_recognition_defaults_to_formula_model_when_openrouter_key_present(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".env.local").write_text(
                "OPENROUTER_API_KEY=router-secret\n",
                encoding="utf-8",
            )

            with patch("doc_converter.config.Path.cwd", return_value=root):
                config = load_formula_recognition_config()

            self.assertEqual(config.provider, "openrouter")
            self.assertEqual(config.model, "openai/gpt-4o")
            self.assertEqual(config.api_key, "router-secret")
            self.assertTrue(config.is_configured())

    def test_load_formula_recognition_from_executable_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            exe_dir = root / "dist" / "DocumentConverter"
            exe_dir.mkdir(parents=True)
            (exe_dir / ".env.local").write_text(
                "OPENROUTER_API_KEY=router-secret\n",
                encoding="utf-8",
            )
            unrelated_cwd = root / "outside"
            unrelated_cwd.mkdir()

            with patch("doc_converter.config.Path.cwd", return_value=unrelated_cwd), patch(
                "doc_converter.config.sys.executable",
                str(exe_dir / "DocumentConverter.exe"),
            ):
                config = load_formula_recognition_config()

            self.assertEqual(config.provider, "openrouter")
            self.assertEqual(config.model, "openai/gpt-4o")
            self.assertEqual(config.api_key, "router-secret")
            self.assertTrue(config.is_configured())

    def test_general_openrouter_model_does_not_override_default_formula_model(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".env.local").write_text(
                "LLM_PROVIDER=openrouter\n"
                "OPENROUTER_MODEL=deepseek/deepseek-v4-pro\n"
                "OPENROUTER_API_KEY=router-secret\n",
                encoding="utf-8",
            )

            with patch("doc_converter.config.Path.cwd", return_value=root):
                config = load_formula_recognition_config()

            self.assertEqual(config.provider, "openrouter")
            self.assertEqual(config.model, "openai/gpt-4o")
            self.assertEqual(config.api_key, "router-secret")
            self.assertTrue(config.is_configured())

    def test_load_formula_recognition_local_backend_without_provider(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".env.local").write_text(
                "FORMULA_RECOGNITION_LOCAL_BACKEND=tesseract\n",
                encoding="utf-8",
            )

            with patch("doc_converter.config.Path.cwd", return_value=root):
                config = load_formula_recognition_config()

            self.assertIsNone(config.provider)
            self.assertIsNone(config.model)
            self.assertIsNone(config.api_key)
            self.assertEqual(config.local_backend, "tesseract")
            self.assertTrue(config.is_configured())

    def test_converter_options_treat_placeholder_api_key_as_unconfigured(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".env.local").write_text(
                "LLM_PROVIDER=openrouter\n"
                "OPENROUTER_MODEL=deepseek/deepseek-v4-pro\n"
                "OPENROUTER_API_KEY=paste-api-key-here\n",
                encoding="utf-8",
            )

            with patch("doc_converter.config.Path.cwd", return_value=root):
                options = ConverterOptions()

            self.assertEqual(options.formula_recognition.provider, "openrouter")
            self.assertEqual(options.formula_recognition.model, "openai/gpt-4o")
            self.assertIsNone(options.formula_recognition.api_key)
            self.assertFalse(options.formula_recognition.is_configured())

    def test_load_formula_recognition_ignores_invalid_limits(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".env.local").write_text(
                "FORMULA_RECOGNITION_MAX_FORMULAS_PER_RUN=-1\n"
                "FORMULA_RECOGNITION_MAX_PROVIDER_CALLS=oops\n"
                "FORMULA_RECOGNITION_MAX_ESTIMATED_COST_USD=-0.1\n",
                encoding="utf-8",
            )

            with patch("doc_converter.config.Path.cwd", return_value=root):
                config = load_formula_recognition_config()

            self.assertIsNone(config.max_formulas_per_run)
            self.assertIsNone(config.max_provider_calls)
            self.assertIsNone(config.max_estimated_cost_usd)

    def test_converter_options_default_to_ocrmypdf_and_both_catalog_writers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            with patch("doc_converter.config.Path.cwd", return_value=root):
                options = ConverterOptions()

            self.assertEqual(options.ocr_backend, "ocrmypdf")
            self.assertEqual(options.catalog_writers, ("json", "xlsx"))
