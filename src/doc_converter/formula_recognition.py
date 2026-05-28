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
from typing import Any

from doc_converter.config import FormulaRecognitionConfig
from doc_converter.converters.docx import (
    INLINE_GLYPH_METAFILE_SUFFIXES,
    INLINE_GLYPH_RASTER_SUFFIXES,
    _extract_formula_text_from_asset,
    _formula_representation_from_text,
    _render_windows_metafile,
)
from doc_converter.schema_validation import validate_payload

OPENROUTER_CHAT_COMPLETIONS_URL = "https://openrouter.ai/api/v1/chat/completions"
FORMULA_RECOGNITION_RESULTS_FILENAME = "formula-recognition.jsonl"
FORMULA_RECOGNITION_TIMEOUT_SECONDS = 90
FORMULA_LOCAL_BACKEND_TIMEOUT_SECONDS = 30
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
class FormulaRecognitionPostprocessResult:
    attempted: int = 0
    recognized: int = 0
    provider_calls: int = 0
    warnings: tuple[str, ...] = ()
    artifact_path: str | None = None


def run_formula_recognition_postprocess(
    document_dir: Path,
    config: FormulaRecognitionConfig,
) -> FormulaRecognitionPostprocessResult:
    if not config.is_configured():
        return FormulaRecognitionPostprocessResult()

    document_path = document_dir / "document.v1.json"
    if not document_path.exists():
        return FormulaRecognitionPostprocessResult(warnings=("formula_recognition_document_missing",))

    payload = json.loads(document_path.read_text(encoding="utf-8"))
    units = payload.get("units")
    if not isinstance(units, list):
        return FormulaRecognitionPostprocessResult(warnings=("formula_recognition_units_missing",))

    records: list[dict[str, Any]] = []
    attempted = 0
    recognized = 0
    provider_calls = 0
    warning_set: set[str] = set()

    for unit in units:
        candidate = _formula_recognition_candidate(unit)
        if candidate is None:
            continue

        attempted += 1
        asset_ref = candidate.get("asset_ref")
        source_text = candidate.get("source_text")
        local_hint_text = None
        if isinstance(asset_ref, str) and asset_ref:
            asset_path = document_dir / asset_ref
            if not asset_path.exists():
                warning_set.add("formula_recognition_asset_missing")
                records.append(
                    {
                        "unit_id": unit.get("unit_id"),
                        "asset_ref": asset_ref,
                        "status": "asset_missing",
                    }
                )
                continue

            blob = asset_path.read_bytes()
            local_hint_text = _extract_formula_text_from_asset(blob, asset_path.name)
            local_formula = _formula_representation_from_text(local_hint_text) if local_hint_text else None
            if _local_formula_is_sufficient(local_formula):
                assert local_formula is not None
                _apply_formula_to_unit(unit, local_formula)
                recognized += 1
                records.append(
                    {
                        "unit_id": unit.get("unit_id"),
                        "asset_ref": asset_ref,
                        "status": "recognized_local",
                        "source_format": local_formula.get("source_format"),
                        "confidence": local_formula.get("confidence"),
                    }
                )
                continue
        else:
            asset_path = None
            blob = None

        try:
            local_backend_formula = _recognize_formula_with_local_backend(
                asset_path=asset_path,
                blob=blob,
                config=config,
                local_hint_text=local_hint_text,
                source_text=source_text,
            )
        except Exception as exc:  # noqa: BLE001 - best-effort local backend should not fail the document.
            warning_set.add("formula_recognition_local_backend_failed")
            records.append(
                {
                    "unit_id": unit.get("unit_id"),
                    "asset_ref": asset_ref,
                    "status": "local_backend_failed",
                    "candidate_kind": candidate.get("kind"),
                    "local_backend": config.local_backend,
                    "error": type(exc).__name__,
                    "message": str(exc),
                }
            )
            local_backend_formula = None

        if _local_backend_formula_is_sufficient(local_backend_formula):
            assert local_backend_formula is not None
            _apply_formula_to_unit(unit, local_backend_formula, origin="local_backend")
            recognized += 1
            records.append(
                {
                    "unit_id": unit.get("unit_id"),
                    "asset_ref": asset_ref,
                    "status": "recognized_local_backend",
                    "candidate_kind": candidate.get("kind"),
                    "local_backend": config.local_backend,
                    "source_format": local_backend_formula.get("source_format"),
                    "confidence": local_backend_formula.get("confidence"),
                }
            )
            continue

        if not config.provider_is_configured():
            records.append(
                {
                    "unit_id": unit.get("unit_id"),
                    "asset_ref": asset_ref,
                    "status": "unresolved_without_provider",
                    "candidate_kind": candidate.get("kind"),
                    "local_backend": config.local_backend,
                }
            )
            continue

        provider_calls += 1
        try:
            provider_formula = _recognize_formula_with_openrouter(
                asset_path=asset_path,
                blob=blob,
                config=config,
                local_hint_text=local_hint_text,
                source_text=source_text,
            )
            _apply_formula_to_unit(unit, provider_formula, origin="provider")
            recognized += 1
            records.append(
                {
                    "unit_id": unit.get("unit_id"),
                    "asset_ref": asset_ref,
                    "status": "recognized_provider",
                    "candidate_kind": candidate.get("kind"),
                    "provider": config.provider,
                    "model": config.model,
                    "confidence": provider_formula.get("confidence"),
                }
            )
        except Exception as exc:  # noqa: BLE001 - best-effort post-processing should not fail the whole document.
            warning_set.add("formula_recognition_provider_failed")
            records.append(
                {
                    "unit_id": unit.get("unit_id"),
                    "asset_ref": asset_ref,
                    "status": "provider_failed",
                    "candidate_kind": candidate.get("kind"),
                    "provider": config.provider,
                    "model": config.model,
                    "error": type(exc).__name__,
                    "message": str(exc),
                }
            )

    if attempted == 0:
        return FormulaRecognitionPostprocessResult()

    processing = payload.setdefault("processing", {})
    processing_warnings = processing.setdefault("warnings", [])
    if isinstance(processing_warnings, list):
        if recognized > 0:
            _append_unique(processing_warnings, "formula_recognition_applied")
        for warning in sorted(warning_set):
            _append_unique(processing_warnings, warning)

    artifact_path = document_dir / FORMULA_RECOGNITION_RESULTS_FILENAME
    artifact_path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )
    processing_payload: dict[str, Any] = {
        "attempted": attempted,
        "recognized": recognized,
        "provider_calls": provider_calls,
        "results_path": artifact_path.name,
    }
    if config.provider is not None:
        processing_payload["provider"] = config.provider
    if config.model is not None:
        processing_payload["model"] = config.model
    if config.local_backend is not None:
        processing_payload["local_backend"] = config.local_backend
    processing["formula_recognition"] = processing_payload

    validate_payload(payload, "document.v1.schema.json")
    document_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return FormulaRecognitionPostprocessResult(
        attempted=attempted,
        recognized=recognized,
        provider_calls=provider_calls,
        warnings=tuple(sorted(warning_set)),
        artifact_path=artifact_path.name,
    )


def _formula_recognition_candidate(unit: object) -> dict[str, Any] | None:
    if not isinstance(unit, dict):
        return None

    unit_type = unit.get("type")
    asset_ref = unit.get("asset_ref")
    formula = unit.get("formula") if isinstance(unit.get("formula"), dict) else None
    text = unit.get("text") if isinstance(unit.get("text"), str) else None

    if unit_type == "formula_image" and isinstance(asset_ref, str) and asset_ref:
        if _formula_needs_provider_review(formula):
            return {"kind": "formula_image", "asset_ref": asset_ref, "source_text": text}

    if unit_type == "formula" and text and _formula_needs_provider_review(formula):
        return {"kind": "formula_text", "asset_ref": None, "source_text": text}

    return None


def _formula_needs_provider_review(formula: dict[str, Any] | None) -> bool:
    if formula is None:
        return True
    if not _formula_has_machine_readable_contract(formula):
        return True
    return False


def _formula_has_machine_readable_contract(formula: dict[str, Any]) -> bool:
    calc_expr = formula.get("calc_expr")
    return isinstance(calc_expr, str) and bool(calc_expr.strip())


def _local_formula_is_sufficient(formula: dict[str, Any] | None) -> bool:
    if formula is None:
        return False
    return str(formula.get("confidence")) in {"high", "medium"}


def _local_backend_formula_is_sufficient(formula: dict[str, Any] | None) -> bool:
    if formula is None:
        return False
    if str(formula.get("confidence")) in {"high", "medium"}:
        return True
    calc_expr = formula.get("calc_expr")
    return isinstance(calc_expr, str) and bool(calc_expr.strip())


def _apply_formula_to_unit(unit: dict[str, Any], formula: dict[str, Any], *, origin: str | None = None) -> None:
    unit["formula"] = formula
    unit["text"] = formula.get("linear_text")
    quality = unit.setdefault("quality", {"flags": [], "warnings": []})
    warnings = quality.setdefault("warnings", [])
    if isinstance(warnings, list):
        if origin == "provider":
            _append_unique(warnings, "formula_recognition_model_generated")
        if origin == "local_backend":
            _append_unique(warnings, "formula_recognition_local_backend_generated")


def _recognize_formula_with_local_backend(
    *,
    asset_path: Path | None,
    blob: bytes | None,
    config: FormulaRecognitionConfig,
    local_hint_text: str | None,
    source_text: str | None,
) -> dict[str, Any] | None:
    backend = (config.local_backend or "").strip().lower()
    if not backend:
        return None
    if backend != "tesseract":
        raise RuntimeError(f"Unsupported local formula backend: {config.local_backend}")
    if asset_path is None or blob is None:
        return None
    return _recognize_formula_with_tesseract(asset_path=asset_path, blob=blob, local_hint_text=local_hint_text, source_text=source_text)


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

    raster_bytes, suffix = _prepare_formula_asset_payload(asset_path, blob)
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

    formula = _formula_representation_from_text(recognized_text)
    if formula is None:
        return {
            "source_format": "heuristic_latex",
            "linear_text": recognized_text,
            "display_latex": recognized_text,
            "calc_expr": None,
            "confidence": "low",
            "warnings": ["formula_local_backend_tesseract", "formula_local_backend_unparsed"],
        }

    patched_formula = dict(formula)
    warnings = list(patched_formula.get("warnings", []))
    if local_hint_text:
        _append_unique(warnings, "formula_local_backend_used_local_hint")
    if source_text:
        _append_unique(warnings, "formula_local_backend_used_source_text")
    _append_unique(warnings, "formula_local_backend_tesseract")
    patched_formula["warnings"] = warnings
    return patched_formula


def _recognize_formula_with_openrouter(
    *,
    asset_path: Path | None,
    blob: bytes | None,
    config: FormulaRecognitionConfig,
    local_hint_text: str | None,
    source_text: str | None,
) -> dict[str, Any]:
    if (config.provider or "").lower() != "openrouter":
        raise RuntimeError(f"Unsupported formula recognition provider: {config.provider}")

    image_url = _build_image_data_url(asset_path, blob) if asset_path is not None and blob is not None else None
    prompt = _formula_recognition_prompt(asset_name=asset_path.name if asset_path is not None else None, local_hint_text=local_hint_text, source_text=source_text)
    response_payload = _request_openrouter_completion(
        api_key=str(config.api_key),
        model=str(config.model),
        image_url=image_url,
        prompt=prompt,
    )
    return _normalize_openrouter_formula_response(response_payload)


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


def _formula_recognition_prompt(asset_name: str | None, local_hint_text: str | None, source_text: str | None) -> str:
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


def _normalized_optional_string(value: object) -> str | None:
    normalized = _normalized_nonempty_string(value)
    if normalized in {None, "null"}:
        return None
    return normalized


def _append_unique(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)