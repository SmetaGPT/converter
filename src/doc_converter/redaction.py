from __future__ import annotations

import os
from typing import Mapping

_SECRET_ENV_MARKERS = ("API_KEY", "TOKEN", "SECRET")
_PLACEHOLDER_VALUES = {
    "",
    "paste-api-key-here",
    "your-api-key-here",
    "change-me",
}


def redact_secrets(value: object, env: Mapping[str, str] | None = None) -> object:
    replacements = _secret_replacements(os.environ if env is None else env)
    return _redact(value, replacements)


def _redact(value: object, replacements: tuple[tuple[str, str], ...]) -> object:
    if isinstance(value, str):
        return _redact_string(value, replacements)
    if isinstance(value, dict):
        return {key: _redact(item, replacements) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact(item, replacements) for item in value]
    if isinstance(value, tuple):
        return tuple(_redact(item, replacements) for item in value)
    return value


def _redact_string(text: str, replacements: tuple[tuple[str, str], ...]) -> str:
    redacted = text
    for secret_value, env_key in replacements:
        if secret_value in redacted:
            redacted = redacted.replace(secret_value, f"[REDACTED_ENV:{env_key}]")
    return redacted


def _secret_replacements(env: Mapping[str, str]) -> tuple[tuple[str, str], ...]:
    candidates: list[tuple[str, str]] = []
    seen_values: set[str] = set()
    for key, raw_value in env.items():
        if not any(marker in key.upper() for marker in _SECRET_ENV_MARKERS):
            continue
        value = raw_value.strip()
        if len(value) < 4 or value.lower() in _PLACEHOLDER_VALUES or value in seen_values:
            continue
        seen_values.add(value)
        candidates.append((value, key))
    candidates.sort(key=lambda item: len(item[0]), reverse=True)
    return tuple(candidates)


__all__ = ["redact_secrets"]
