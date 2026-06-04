from __future__ import annotations

import base64
import io
import json
import mimetypes
import re
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from doc_converter.config import FormulaRecognitionConfig
from doc_converter.converters.docx import (
    INLINE_GLYPH_METAFILE_SUFFIXES,
    INLINE_GLYPH_RASTER_SUFFIXES,
    _render_windows_metafile,
)

OPENROUTER_CHAT_COMPLETIONS_URL = "https://openrouter.ai/api/v1/chat/completions"
MATHPIX_TEXT_URL = "https://api.mathpix.com/v3/text"
FORMULA_RECOGNITION_TIMEOUT_SECONDS = 90
FORMULA_LOCAL_BACKEND_TIMEOUT_SECONDS = 30
_PADDLEOCR_FORMULA_MODEL: Any | None = None
FORMULA_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "linear_text": {
            "type": ["string", "null"],
            "description": "Human-readable linear formula text with original symbols where possible.",
        },
        "display_latex": {
            "type": ["string", "null"],
            "description": "Display LaTeX for rendering the formula.",
        },
        "calc_expr": {
            "type": ["string", "null"],
            "description": "Python-like machine-readable expression for calculation, or null when ambiguous.",
        },
        "confidence": {
            "type": "string",
            "enum": ["high", "medium", "low"],
        },
        "warnings": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": ["linear_text", "display_latex", "calc_expr", "confidence", "warnings"],
    "additionalProperties": False,
}


@dataclass(frozen=True)
class FormulaRecognitionAsset:
    path: Path | None
    blob: bytes | None


@dataclass(frozen=True)
class FormulaProviderContext:
    candidate_kind: str
    asset_name: str | None
    local_hint_text: str | None
    source_text: str | None
    mathpix_text: str | None = None
    mathpix_latex: str | None = None
    mathpix_asciimath: str | None = None


@dataclass(frozen=True)
class FormulaPrediction:
    formula: dict[str, Any]
    origin: str


class FormulaProvider(Protocol):
    @property
    def provider_id(self) -> str: ...

    @property
    def stage(self) -> str: ...

    def predict(
        self,
        asset: FormulaRecognitionAsset,
        context: FormulaProviderContext,
    ) -> FormulaPrediction | None: ...


@dataclass(frozen=True)
class NullProvider:
    provider_id: str = "null"
    stage: str = "null"

    def predict(
        self,
        asset: FormulaRecognitionAsset,
        context: FormulaProviderContext,
    ) -> FormulaPrediction | None:
        return None


@dataclass(frozen=True)
class LocalTesseractProvider:
    backend: str
    provider_id: str = "tesseract"
    stage: str = "local_backend"

    def predict(
        self,
        asset: FormulaRecognitionAsset,
        context: FormulaProviderContext,
    ) -> FormulaPrediction | None:
        backend = self.backend.strip().lower()
        if backend != "tesseract":
            raise RuntimeError(f"Unsupported local formula backend: {self.backend}")
        if asset.path is None or asset.blob is None:
            return None
        formula = _recognize_formula_with_tesseract(
            asset_path=asset.path,
            blob=asset.blob,
            local_hint_text=context.local_hint_text,
            source_text=context.source_text,
        )
        if formula is None:
            return None
        return FormulaPrediction(formula=formula, origin="local_backend")


@dataclass(frozen=True)
class LocalPaddleOCRProvider:
    backend: str
    provider_id: str = "paddleocr"
    stage: str = "local_backend"

    def predict(
        self,
        asset: FormulaRecognitionAsset,
        context: FormulaProviderContext,
    ) -> FormulaPrediction | None:
        backend = self.backend.strip().lower()
        if backend != "paddleocr":
            raise RuntimeError(f"Unsupported local formula backend: {self.backend}")
        if asset.path is None or asset.blob is None:
            return None
        formula = _recognize_formula_with_paddleocr(
            asset_path=asset.path,
            blob=asset.blob,
            local_hint_text=context.local_hint_text,
            source_text=context.source_text,
        )
        if formula is None:
            return None
        return FormulaPrediction(formula=formula, origin="local_backend")


@dataclass(frozen=True)
class OpenRouterProvider:
    provider: str
    model: str
    api_key: str
    provider_id: str = "openrouter"
    stage: str = "provider"

    def predict(
        self,
        asset: FormulaRecognitionAsset,
        context: FormulaProviderContext,
    ) -> FormulaPrediction | None:
        if self.provider.strip().lower() != "openrouter":
            raise RuntimeError(f"Unsupported formula recognition provider: {self.provider}")

        image_url = _build_image_data_url(asset.path, asset.blob) if asset.path is not None and asset.blob is not None else None
        prompt = _formula_recognition_prompt(
            asset_name=context.asset_name,
            local_hint_text=context.local_hint_text,
            source_text=context.source_text,
            mathpix_text=context.mathpix_text,
            mathpix_latex=context.mathpix_latex,
            mathpix_asciimath=context.mathpix_asciimath,
        )
        response_payload = _request_openrouter_completion(
            api_key=self.api_key,
            model=self.model,
            image_url=image_url,
            prompt=prompt,
        )
        return FormulaPrediction(
            formula=_normalize_openrouter_formula_response(response_payload),
            origin="provider",
        )


@dataclass(frozen=True)
class MathpixProvider:
    app_id: str
    app_key: str
    provider_id: str = "mathpix"
    stage: str = "provider"

    def predict(
        self,
        asset: FormulaRecognitionAsset,
        context: FormulaProviderContext,
    ) -> FormulaPrediction | None:
        if asset.path is None or asset.blob is None:
            return None
        image_url = _build_image_data_url(asset.path, asset.blob)
        response_payload = _request_mathpix_text(app_id=self.app_id, app_key=self.app_key, image_url=image_url)
        return FormulaPrediction(
            formula=_normalize_mathpix_formula_response(response_payload),
            origin="mathpix",
        )


def build_formula_provider_chain(config: FormulaRecognitionConfig) -> tuple[FormulaProvider, ...]:
    providers: list[FormulaProvider] = []
    if config.mode == "off":
        return (NullProvider(),)
    if config.local_backend_is_configured():
        local_backend = str(config.local_backend).strip().lower()
        if local_backend == "paddleocr":
            providers.append(LocalPaddleOCRProvider(backend=str(config.local_backend)))
        else:
            providers.append(LocalTesseractProvider(backend=str(config.local_backend)))
    if config.mathpix_is_configured():
        providers.append(MathpixProvider(app_id=str(config.mathpix_app_id), app_key=str(config.mathpix_app_key)))
    if config.provider_is_configured():
        providers.append(
            OpenRouterProvider(
                provider=str(config.provider),
                model=str(config.model),
                api_key=str(config.api_key),
            )
        )
    if not providers:
        providers.append(NullProvider())
    return tuple(providers)


def _recognize_formula_with_tesseract(
    *,
    asset_path: Path,
    blob: bytes,
    local_hint_text: str | None,
    source_text: str | None,
) -> dict[str, Any] | None:
    tesseract = shutil.which("tesseract") or shutil.which("tesseract.exe")
    if tesseract is None:
        raise RuntimeError("Tesseract executable not found")

    raster_bytes, media_type = _prepare_formula_asset_payload(asset_path, blob)
    suffix = mimetypes.guess_extension(media_type) or ".png"
    with tempfile.TemporaryDirectory(prefix="formula-local-backend-") as temp_dir:
        input_path = Path(temp_dir) / f"formula{suffix}"
        output_base = Path(temp_dir) / "formula-ocr"
        input_path.write_bytes(raster_bytes)

        completed = subprocess.run(
            [
                tesseract,
                str(input_path),
                str(output_base),
                "-l",
                "rus+eng",
                "--psm",
                "7",
                "--oem",
                "1",
                "-c",
                "preserve_interword_spaces=1",
            ],
            capture_output=True,
            text=True,
            timeout=FORMULA_LOCAL_BACKEND_TIMEOUT_SECONDS,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError((completed.stderr or completed.stdout).strip() or "Tesseract formula OCR failed")

        text_path = output_base.with_suffix(".txt")
        if not text_path.exists():
            return None
        recognized_text = _normalize_local_backend_formula_text(text_path.read_text(encoding="utf-8-sig"))

    if not recognized_text:
        return None

    return _formula_from_local_backend_text(
        recognized_text,
        local_hint_text=local_hint_text,
        source_text=source_text,
        backend_warning="formula_local_backend_tesseract",
        fallback_confidence="low",
    )


def _recognize_formula_with_paddleocr(
    *,
    asset_path: Path,
    blob: bytes,
    local_hint_text: str | None,
    source_text: str | None,
) -> dict[str, Any] | None:
    model = _get_paddleocr_formula_model()

    raster_bytes, media_type = _prepare_formula_asset_payload(asset_path, blob)
    suffix = mimetypes.guess_extension(media_type) or ".png"
    with tempfile.TemporaryDirectory(prefix="formula-local-backend-") as temp_dir:
        input_path = Path(temp_dir) / f"formula{suffix}"
        input_path.write_bytes(raster_bytes)
        try:
            predictions = model.predict(input=str(input_path), batch_size=1)
        except TypeError:
            predictions = model.predict(str(input_path), batch_size=1)

    recognized_text, raw_confidence = _extract_paddleocr_formula_prediction(predictions)
    if not recognized_text:
        return None

    return _formula_from_local_backend_text(
        recognized_text,
        local_hint_text=local_hint_text,
        source_text=source_text,
        backend_warning="formula_local_backend_paddleocr",
        fallback_confidence=_paddleocr_confidence(raw_confidence),
    )


def _get_paddleocr_formula_model() -> Any:
    global _PADDLEOCR_FORMULA_MODEL
    if _PADDLEOCR_FORMULA_MODEL is None:
        try:
            from paddleocr import FormulaRecognition
        except ImportError as exc:
            raise RuntimeError(
                "PaddleOCR formula backend requires paddleocr and paddlepaddle to be installed"
            ) from exc
        _PADDLEOCR_FORMULA_MODEL = FormulaRecognition(model_name="PP-FormulaNet_plus-M")
    return _PADDLEOCR_FORMULA_MODEL


def _extract_paddleocr_formula_prediction(predictions: object) -> tuple[str | None, float | None]:
    for candidate in _iter_paddleocr_prediction_candidates(predictions):
        recognized_text = _paddleocr_prediction_text(candidate)
        if recognized_text:
            return recognized_text, _paddleocr_prediction_score(candidate)
    return None, None


def _iter_paddleocr_prediction_candidates(predictions: object) -> list[object]:
    if predictions is None:
        return []
    if isinstance(predictions, list | tuple):
        items = list(predictions)
    else:
        try:
            items = list(predictions)
        except TypeError:
            items = [predictions]

    candidates: list[object] = []
    pending = list(items)
    while pending:
        item = pending.pop(0)
        if item is None:
            continue
        candidates.append(item)
        if isinstance(item, list | tuple):
            pending[:0] = list(item)
            continue
        if isinstance(item, dict):
            nested_res = item.get("res")
            if nested_res is not None:
                pending.append(nested_res)
            nested_result = item.get("result")
            if nested_result is not None:
                pending.append(nested_result)
            continue
        nested = getattr(item, "res", None)
        if nested is not None:
            pending.append(nested)
    return candidates


def _paddleocr_prediction_text(candidate: object) -> str | None:
    if isinstance(candidate, str):
        stripped = candidate.strip()
        return stripped or None
    if isinstance(candidate, dict):
        for key in ("formula", "prunedResult", "rec_text", "text", "latex"):
            value = candidate.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None
    for attr in ("formula", "prunedResult", "rec_text", "text", "latex"):
        value = getattr(candidate, attr, None)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _paddleocr_prediction_score(candidate: object) -> float | None:
    if isinstance(candidate, dict):
        return _normalized_optional_float(candidate.get("confidence") or candidate.get("score") or candidate.get("rec_score"))
    return _normalized_optional_float(
        getattr(candidate, "confidence", None) or getattr(candidate, "score", None) or getattr(candidate, "rec_score", None)
    )


def _paddleocr_confidence(value: float | None) -> str:
    if value is None:
        return "low"
    if value >= 0.95:
        return "high"
    if value >= 0.80:
        return "medium"
    return "low"


def _formula_from_local_backend_text(
    recognized_text: str,
    *,
    local_hint_text: str | None,
    source_text: str | None,
    backend_warning: str,
    fallback_confidence: str,
) -> dict[str, Any]:
    from doc_converter.converters.docx import _formula_representation_from_text

    formula = _formula_representation_from_text(recognized_text)
    if formula is None:
        return {
            "source_format": "heuristic_latex",
            "linear_text": recognized_text,
            "display_latex": recognized_text,
            "calc_expr": None,
            "confidence": fallback_confidence,
            "warnings": [backend_warning, "formula_local_backend_unparsed"],
        }

    patched_formula = dict(formula)
    warnings = list(patched_formula.get("warnings", []))
    if local_hint_text:
        _append_unique(warnings, "formula_local_backend_used_local_hint")
    if source_text:
        _append_unique(warnings, "formula_local_backend_used_source_text")
    _append_unique(warnings, backend_warning)
    patched_formula["warnings"] = warnings
    return patched_formula


def _build_image_data_url(asset_path: Path, blob: bytes) -> str:
    payload, media_type = _prepare_formula_asset_payload(asset_path, blob)
    encoded = base64.b64encode(payload).decode("ascii")
    return f"data:{media_type};base64,{encoded}"


def _prepare_formula_asset_payload(asset_path: Path, blob: bytes) -> tuple[bytes, str]:
    suffix = asset_path.suffix.lower()
    if suffix in INLINE_GLYPH_RASTER_SUFFIXES:
        return blob, mimetypes.guess_type(asset_path.name)[0] or "image/png"
    if suffix in INLINE_GLYPH_METAFILE_SUFFIXES:
        image = _render_windows_metafile(blob, suffix)
        if image is None:
            raise RuntimeError(f"Unable to rasterize metafile asset: {asset_path.name}")
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue(), "image/png"
    raise RuntimeError(f"Unsupported formula asset format: {asset_path.suffix}")


def _normalize_local_backend_formula_text(value: str) -> str:
    normalized = value.replace("\x0c", " ")
    normalized = re.sub(r"(?<=[\)\]A-Za-zА-Яа-я0-9])\s*\*\s*(?=[\(\[A-Za-zА-Яа-я0-9])", " x ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def _formula_recognition_prompt(
    asset_name: str | None,
    local_hint_text: str | None,
    source_text: str | None,
    mathpix_text: str | None = None,
    mathpix_latex: str | None = None,
    mathpix_asciimath: str | None = None,
) -> str:
    lines = [
        "Распознай формулу на изображении и верни только JSON-объект.",
        "Сохраняй кириллические обозначения и индексы, если они есть на изображении.",
        "Поля JSON: linear_text, display_latex, calc_expr, confidence, warnings.",
        "Для calc_expr используй Python-like операторы: *, /, ** и круглые скобки; если формула неоднозначна, верни null.",
        "confidence должно быть одним из: high, medium, low.",
        "warnings должно быть массивом коротких snake_case строк.",
        "Не добавляй markdown, комментарии или поясняющий текст вне JSON.",
    ]
    if asset_name:
        lines.append(f"asset_name: {asset_name}")
    if local_hint_text:
        lines.append(f"partial_local_hint: {local_hint_text}")
    if mathpix_text:
        lines.append(f"mathpix_text: {mathpix_text}")
    if mathpix_latex:
        lines.append(f"mathpix_latex: {mathpix_latex}")
    if mathpix_asciimath:
        lines.append(f"mathpix_asciimath: {mathpix_asciimath}")
    if source_text:
        lines.append(f"raw_extracted_text: {source_text}")
    return "\n".join(lines)


def _request_openrouter_completion(*, api_key: str, model: str, image_url: str | None, prompt: str) -> dict[str, Any]:
    content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
    if image_url is not None:
        content.append({"type": "image_url", "image_url": {"url": image_url, "detail": "high"}})

    body = {
        "model": model,
        "temperature": 0,
        "max_tokens": 500,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "formula_extraction",
                "strict": True,
                "schema": FORMULA_RESPONSE_SCHEMA,
            },
        },
        "messages": [
            {
                "role": "system",
                "content": "You extract formulas from technical document images and reply with JSON only.",
            },
            {
                "role": "user",
                "content": content,
            },
        ],
    }
    request = urllib.request.Request(
        OPENROUTER_CHAT_COMPLETIONS_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-OpenRouter-Title": "DocumentConverter",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=FORMULA_RECOGNITION_TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenRouter request failed: {exc.code} {details}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"OpenRouter request failed: {exc.reason}") from exc


def _request_mathpix_text(*, app_id: str, app_key: str, image_url: str) -> dict[str, Any]:
    body = {
        "src": image_url,
        "formats": ["text", "data", "html"],
        "data_options": {
            "include_asciimath": True,
            "include_latex": True,
        },
        "math_inline_delimiters": ["$", "$"],
        "rm_spaces": True,
        "metadata": {
            "improve_mathpix": False,
        },
    }
    request = urllib.request.Request(
        MATHPIX_TEXT_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "app_id": app_id,
            "app_key": app_key,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=FORMULA_RECOGNITION_TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Mathpix request failed: {exc.code} {details}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Mathpix request failed: {exc.reason}") from exc


def _normalize_openrouter_formula_response(response_payload: dict[str, Any]) -> dict[str, Any]:
    content = _extract_openrouter_message_content(response_payload)
    model_payload = _parse_json_object(content)

    linear_text = _normalized_nonempty_string(model_payload.get("linear_text"))
    display_latex = _normalized_nonempty_string(model_payload.get("display_latex"))
    calc_expr = _normalized_optional_string(model_payload.get("calc_expr"))

    if linear_text is None and display_latex is None:
        raise RuntimeError("OpenRouter formula response did not contain linear_text or display_latex")
    if linear_text is None:
        linear_text = display_latex
    if display_latex is None:
        display_latex = linear_text

    confidence = _normalized_nonempty_string(model_payload.get("confidence"))
    if confidence not in {"high", "medium", "low"}:
        confidence = "low"

    warnings_value = model_payload.get("warnings")
    warnings = []
    if isinstance(warnings_value, list):
        warnings = [item.strip() for item in warnings_value if isinstance(item, str) and item.strip()]

    return {
        "source_format": "heuristic_latex",
        "linear_text": linear_text,
        "display_latex": display_latex,
        "calc_expr": calc_expr,
        "confidence": confidence,
        "warnings": warnings,
    }


def _normalize_mathpix_formula_response(response_payload: dict[str, Any]) -> dict[str, Any]:
    text = _normalized_optional_string(response_payload.get("text"))
    latex = _mathpix_data_value(response_payload, "latex") or _normalized_optional_string(response_payload.get("latex_styled"))
    asciimath = _mathpix_data_value(response_payload, "asciimath")

    linear_text = text or asciimath or latex
    display_latex = latex or text or asciimath
    if linear_text is None and display_latex is None:
        raise RuntimeError("Mathpix formula response did not contain text, latex or asciimath")
    if linear_text is None:
        linear_text = display_latex
    if display_latex is None:
        display_latex = linear_text

    confidence = _mathpix_confidence(response_payload.get("confidence"))
    warnings = ["formula_mathpix_ocr", "formula_mathpix_display_only"]
    if asciimath:
        warnings.append("formula_mathpix_asciimath_available")

    return {
        "source_format": "heuristic_latex",
        "linear_text": _strip_mathpix_delimiters(str(linear_text)),
        "display_latex": _strip_mathpix_delimiters(str(display_latex)),
        "calc_expr": None,
        "confidence": confidence,
        "warnings": warnings,
    }


def _mathpix_data_value(response_payload: dict[str, Any], value_type: str) -> str | None:
    data = response_payload.get("data")
    if not isinstance(data, list):
        return None
    for item in data:
        if not isinstance(item, dict):
            continue
        if item.get("type") == value_type:
            return _normalized_optional_string(item.get("value"))
    return None


def _mathpix_confidence(value: object) -> str:
    if isinstance(value, int | float):
        if value >= 0.95:
            return "high"
        if value >= 0.80:
            return "medium"
    return "low"


def _strip_mathpix_delimiters(value: str) -> str:
    stripped = value.strip()
    if stripped.startswith("\\(") and stripped.endswith("\\)"):
        return stripped[2:-2].strip()
    if stripped.startswith("\\[") and stripped.endswith("\\]"):
        return stripped[2:-2].strip()
    if stripped.startswith("$") and stripped.endswith("$") and len(stripped) > 1:
        return stripped[1:-1].strip()
    return stripped


def _extract_openrouter_message_content(response_payload: dict[str, Any]) -> str:
    choices = response_payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RuntimeError("OpenRouter response did not contain choices")
    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        raise RuntimeError("OpenRouter response choice is not an object")
    message = first_choice.get("message")
    if not isinstance(message, dict):
        raise RuntimeError("OpenRouter response did not contain message")
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("OpenRouter response content is empty")
    return content


def _parse_json_object(content: str) -> dict[str, Any]:
    stripped = content.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", stripped, flags=re.DOTALL)
        if match is None:
            raise RuntimeError("OpenRouter response is not valid JSON") from None
        parsed = json.loads(match.group(0))
    if not isinstance(parsed, dict):
        raise RuntimeError("OpenRouter response JSON is not an object")
    return parsed


def _normalized_nonempty_string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _normalized_optional_float(value: object) -> float | None:
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            return float(stripped)
        except ValueError:
            return None
    return None


def _normalized_optional_string(value: object) -> str | None:
    normalized = _normalized_nonempty_string(value)
    if normalized in {None, "null"}:
        return None
    return normalized


def _append_unique(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)
