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