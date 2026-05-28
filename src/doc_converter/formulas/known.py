"""Known formula patterns loader with schema validation and immutable caching."""

from __future__ import annotations

import copy
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from doc_converter.schema_validation import validate_payload

# Package data path for known patterns JSON
_PACKAGE_DATA_PATH = Path(__file__).parent / "known-patterns.v1.json"


@lru_cache(maxsize=1)
def _load_known_patterns() -> dict[str, Any]:
    """Load and validate known formula patterns from package data.

    Returns cached validated patterns on subsequent calls.
    Raises FileNotFoundError if package data is missing.
    Raises ValueError if schema validation fails.
    """
    if not _PACKAGE_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Known formula patterns data not found: {_PACKAGE_DATA_PATH}"
        )

    with open(_PACKAGE_DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)

    # Validate against schema
    validate_payload(data, "formula-known-patterns.v1.schema.json")

    return data


def get_noisy_form_recovery() -> dict[str, str]:
    """Get noisy formula form recovery mapping.

    Returns a copy of the mapping so caller cannot mutate cache.
    Maps noisy linearized formula text to clean normalized forms.
    """
    patterns = _load_known_patterns()
    return copy.copy(patterns["noisy_form_recovery"])


def get_known_formula_representation(normalized: str) -> dict[str, Any] | None:
    """Get full representation for a known formula by normalized linear text.

    Args:
        normalized: Normalized linear text form of the formula (lookup key).

    Returns:
        Copy of formula representation dict with display_latex, calc_expr,
        variables, confidence, and warnings, or None if not found.
    """
    patterns = _load_known_patterns()
    for formula in patterns["formula_representations"]:
        if formula["linear_text"] == normalized:
            return copy.deepcopy(formula)
    return None


def get_mathtype_signature_rules() -> list[dict[str, Any]]:
    """Get MathType WMF signature matching rules.

    Returns a deep copy of the rules list so caller cannot mutate cache.
    Each rule has 'condition', 'linear_text', and optional 'comment'.
    """
    patterns = _load_known_patterns()
    return copy.deepcopy(patterns["mathtype_signature_rules"])
