from __future__ import annotations

import os
import sys
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

_FORMULA_RECOGNITION_ENV_KEYS = {
    "provider": "FORMULA_RECOGNITION_PROVIDER",
    "model": "FORMULA_RECOGNITION_MODEL",
    "api_key": "FORMULA_RECOGNITION_API_KEY",
    "local_backend": "FORMULA_RECOGNITION_LOCAL_BACKEND",
    "mode": "FORMULA_RECOGNITION_MODE",
    "prompt_version": "FORMULA_RECOGNITION_PROMPT_VERSION",
    "max_formulas_per_run": "FORMULA_RECOGNITION_MAX_FORMULAS_PER_RUN",
    "max_provider_calls": "FORMULA_RECOGNITION_MAX_PROVIDER_CALLS",
    "max_estimated_cost_usd": "FORMULA_RECOGNITION_MAX_ESTIMATED_COST_USD",
}
_GENERAL_PROVIDER_ENV_KEY = "LLM_PROVIDER"
_GENERAL_API_KEY_ENV_KEY = "LLM_API_KEY"
_FORMULA_MODEL_ALIAS_ENV_KEY = "FORMULA_MODEL"
_MATHPIX_APP_ID_ENV_KEY = "MATHPIX_APP_ID"
_MATHPIX_APP_KEY_ENV_KEY = "MATHPIX_APP_KEY"
_PROVIDER_MODEL_ENV_KEYS = {
    "openrouter": "OPENROUTER_MODEL",
    "openai": "OPENAI_MODEL",
}
_PROVIDER_API_KEY_ENV_KEYS = {
    "openrouter": "OPENROUTER_API_KEY",
    "openai": "OPENAI_API_KEY",
}
_PLACEHOLDER_VALUES = {
    "",
    "paste-api-key-here",
    "your-api-key-here",
    "change-me",
}
_DEFAULT_FORMULA_PROVIDER = "openrouter"
_DEFAULT_FORMULA_MODEL_BY_PROVIDER = {
    "openrouter": "openai/gpt-4o",
}
_DEFAULT_FORMULA_PROMPT_VERSION = "v1"


@dataclass(frozen=True)
class FormulaRecognitionConfig:
    provider: str | None = None
    model: str | None = None
    api_key: str | None = None
    local_backend: str | None = None
    mode: str = "fallback"
    prompt_version: str = _DEFAULT_FORMULA_PROMPT_VERSION
    mathpix_app_id: str | None = None
    mathpix_app_key: str | None = None
    max_formulas_per_run: int | None = None
    max_provider_calls: int | None = None
    max_estimated_cost_usd: float | None = None

    def provider_is_configured(self) -> bool:
        return bool(self.provider and self.model and self.api_key)

    def local_backend_is_configured(self) -> bool:
        return bool(self.local_backend)

    def mathpix_is_configured(self) -> bool:
        return bool(self.mathpix_app_id and self.mathpix_app_key)

    def is_configured(self) -> bool:
        return self.mode != "off" and (
            self.provider_is_configured() or self.local_backend_is_configured() or self.mathpix_is_configured()
        )

    def public_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {"configured": self.is_configured(), "mode": self.mode}
        if self.prompt_version:
            payload["prompt_version"] = self.prompt_version
        if self.provider is not None:
            payload["provider"] = self.provider
        if self.model is not None:
            payload["model"] = self.model
        if self.local_backend is not None:
            payload["local_backend"] = self.local_backend
        if self.mathpix_is_configured():
            payload["mathpix"] = {"configured": True}
        limits: dict[str, object] = {}
        if self.max_formulas_per_run is not None:
            limits["max_formulas_per_run"] = self.max_formulas_per_run
        if self.max_provider_calls is not None:
            limits["max_provider_calls"] = self.max_provider_calls
        if self.max_estimated_cost_usd is not None:
            limits["max_estimated_cost_usd"] = self.max_estimated_cost_usd
        if limits:
            payload["limits"] = limits
        return payload


def load_formula_recognition_config(
    *,
    start_dir: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> FormulaRecognitionConfig:
    resolved: dict[str, str] = {}
    env_dir = _discover_env_dir(start_dir)
    if env_dir is not None:
        resolved.update(_parse_env_file(env_dir / ".env"))
        resolved.update(_parse_env_file(env_dir / ".env.local"))

    source_environ = os.environ if environ is None else environ
    for key in _relevant_env_keys():
        value = source_environ.get(key)
        if value is not None:
            resolved[key] = value

    provider = _normalize_env_value(
        _first_resolved_value(
            resolved,
            _FORMULA_RECOGNITION_ENV_KEYS["provider"],
            _GENERAL_PROVIDER_ENV_KEY,
        )
    )
    if provider is None:
        provider = _infer_formula_provider(resolved)

    model = _normalize_env_value(
        _first_resolved_value(
            resolved,
            _FORMULA_RECOGNITION_ENV_KEYS["model"],
            _FORMULA_MODEL_ALIAS_ENV_KEY,
        )
    )
    if model is None:
        model = _default_formula_model(provider)
    if model is None:
        model = _normalize_env_value(_first_resolved_value(resolved, _provider_model_env_key(provider)))

    api_key = _normalize_env_value(
        _first_resolved_value(
            resolved,
            _FORMULA_RECOGNITION_ENV_KEYS["api_key"],
            _provider_api_key_env_key(provider),
            _GENERAL_API_KEY_ENV_KEY,
        )
    )
    local_backend = _normalize_local_formula_backend(
        _normalize_env_value(_first_resolved_value(resolved, _FORMULA_RECOGNITION_ENV_KEYS["local_backend"]))
    )
    mode = _normalize_formula_recognition_mode(
        _normalize_env_value(_first_resolved_value(resolved, _FORMULA_RECOGNITION_ENV_KEYS["mode"]))
    )
    prompt_version = _normalize_formula_recognition_prompt_version(
        _normalize_env_value(_first_resolved_value(resolved, _FORMULA_RECOGNITION_ENV_KEYS["prompt_version"]))
    )
    mathpix_app_id = _normalize_env_value(_first_resolved_value(resolved, _MATHPIX_APP_ID_ENV_KEY))
    mathpix_app_key = _normalize_env_value(_first_resolved_value(resolved, _MATHPIX_APP_KEY_ENV_KEY))
    max_formulas_per_run = _normalize_nonnegative_int(
        _normalize_env_value(_first_resolved_value(resolved, _FORMULA_RECOGNITION_ENV_KEYS["max_formulas_per_run"]))
    )
    max_provider_calls = _normalize_nonnegative_int(
        _normalize_env_value(_first_resolved_value(resolved, _FORMULA_RECOGNITION_ENV_KEYS["max_provider_calls"]))
    )
    max_estimated_cost_usd = _normalize_nonnegative_float(
        _normalize_env_value(_first_resolved_value(resolved, _FORMULA_RECOGNITION_ENV_KEYS["max_estimated_cost_usd"]))
    )

    return FormulaRecognitionConfig(
        provider=provider,
        model=model,
        api_key=api_key,
        local_backend=local_backend,
        mode=mode,
        prompt_version=prompt_version,
        mathpix_app_id=mathpix_app_id,
        mathpix_app_key=mathpix_app_key,
        max_formulas_per_run=max_formulas_per_run,
        max_provider_calls=max_provider_calls,
        max_estimated_cost_usd=max_estimated_cost_usd,
    )


def serialize_converter_options(options: ConverterOptions) -> dict[str, object]:
    payload: dict[str, object] = {
        "ocr_languages": list(options.ocr_languages),
        "include_originals": options.include_originals,
        "duplicate_policy": options.duplicate_policy,
        "ocr_backend": options.ocr_backend,
        "catalog_writers": list(options.catalog_writers),
    }
    formula_payload = options.formula_recognition.public_payload()
    if len(formula_payload) > 1 or bool(formula_payload.get("configured")):
        payload["formula_recognition"] = formula_payload
    return payload


def _discover_env_dir(start_dir: Path | None) -> Path | None:
    search_roots: list[Path] = []
    if start_dir is not None:
        search_roots.append(start_dir.resolve())
    cwd = Path.cwd().resolve()
    if cwd not in search_roots:
        search_roots.append(cwd)
    executable_dir = Path(sys.executable).resolve().parent
    if executable_dir not in search_roots:
        search_roots.append(executable_dir)

    seen: set[Path] = set()
    for root in search_roots:
        for directory in (root, *root.parents):
            if directory in seen:
                continue
            seen.add(directory)
            if (directory / ".env").exists() or (directory / ".env.local").exists():
                return directory
    return None


def _relevant_env_keys() -> tuple[str, ...]:
    return (
        *_FORMULA_RECOGNITION_ENV_KEYS.values(),
        _GENERAL_PROVIDER_ENV_KEY,
        _GENERAL_API_KEY_ENV_KEY,
        _FORMULA_MODEL_ALIAS_ENV_KEY,
        _MATHPIX_APP_ID_ENV_KEY,
        _MATHPIX_APP_KEY_ENV_KEY,
        *_PROVIDER_MODEL_ENV_KEYS.values(),
        *_PROVIDER_API_KEY_ENV_KEYS.values(),
    )


def _first_resolved_value(resolved: Mapping[str, str], *keys: str | None) -> str | None:
    for key in keys:
        if key is None:
            continue
        value = resolved.get(key)
        if value is not None:
            return value
    return None


def _provider_model_env_key(provider: str | None) -> str | None:
    if provider is None:
        return None
    return _PROVIDER_MODEL_ENV_KEYS.get(provider.lower())


def _provider_api_key_env_key(provider: str | None) -> str | None:
    if provider is None:
        return None
    return _PROVIDER_API_KEY_ENV_KEYS.get(provider.lower())


def _infer_formula_provider(resolved: Mapping[str, str]) -> str | None:
    openrouter_api_key = _normalize_env_value(resolved.get(_PROVIDER_API_KEY_ENV_KEYS["openrouter"]))
    openrouter_model = _normalize_env_value(resolved.get(_PROVIDER_MODEL_ENV_KEYS["openrouter"]))
    if openrouter_api_key is not None or openrouter_model is not None:
        return _DEFAULT_FORMULA_PROVIDER
    return None


def _default_formula_model(provider: str | None) -> str | None:
    if provider is None:
        return None
    return _DEFAULT_FORMULA_MODEL_BY_PROVIDER.get(provider.lower())


def _parse_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        key, separator, value = line.partition("=")
        if not separator:
            continue
        values[key.strip()] = _strip_quotes(value.strip())
    return values


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _normalize_env_value(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if normalized.lower() in _PLACEHOLDER_VALUES:
        return None
    return normalized


def _normalize_formula_recognition_mode(value: str | None) -> str:
    if value is None:
        return "fallback"
    normalized = value.strip().lower().replace("-", "_")
    if normalized in {"off", "fallback", "llm_first", "mathpix_first"}:
        return normalized
    return "fallback"


def _normalize_formula_recognition_prompt_version(value: str | None) -> str:
    if value is None:
        return _DEFAULT_FORMULA_PROMPT_VERSION
    normalized = value.strip()
    return normalized or _DEFAULT_FORMULA_PROMPT_VERSION


def _normalize_local_formula_backend(value: str | None) -> str | None:
    normalized = _normalize_env_value(value)
    if normalized is None:
        return None
    return normalized.strip().lower()


def _normalize_nonnegative_int(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        parsed = int(value)
    except ValueError:
        return None
    if parsed < 0:
        return None
    return parsed


def _normalize_nonnegative_float(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        parsed = float(value)
    except ValueError:
        return None
    if parsed < 0:
        return None
    return parsed


@dataclass(frozen=True)
class ConverterOptions:
    ocr_languages: tuple[str, ...] = ("rus", "eng")
    include_originals: bool = False
    duplicate_policy: str = "record_provenance"
    ocr_backend: str = "ocrmypdf"
    catalog_writers: tuple[str, ...] = ("json", "xlsx")
    formula_recognition: FormulaRecognitionConfig = field(default_factory=load_formula_recognition_config)


@dataclass(frozen=True)
class AgentRunMetadata:
    agent_id: str | None = None
    agent_version: str | None = None
    task_id: str | None = None
    parent_run_id: str | None = None


@dataclass(frozen=True)
class ConverterConfig:
    input_dir: Path
    output_dir: Path
    options: ConverterOptions = ConverterOptions()
    agent_run_metadata: AgentRunMetadata | None = None
