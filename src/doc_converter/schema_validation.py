from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator


class SchemaValidationError(ValueError):
    """Raised when a JSON payload does not match its schema."""


_SCHEMAS_DIR = Path(__file__).resolve().parents[2] / "schemas"


@lru_cache(maxsize=None)
def _load_validator(schema_filename: str) -> Draft202012Validator:
    schema_path = _SCHEMAS_DIR / schema_filename
    if not schema_path.exists():
        raise SchemaValidationError(f"Schema file not found: {schema_path}")
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


def validate_payload(payload: Mapping[str, Any], schema_filename: str) -> None:
    validator = _load_validator(schema_filename)
    errors = sorted(validator.iter_errors(dict(payload)), key=lambda item: list(item.absolute_path))
    if not errors:
        return

    first_error = errors[0]
    location = ".".join(str(part) for part in first_error.absolute_path) or "$"
    raise SchemaValidationError(
        f"{schema_filename} validation failed at {location}: {first_error.message}"
    )


def validate_json_file(path: Path, schema_filename: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    validate_payload(payload, schema_filename)
    return payload