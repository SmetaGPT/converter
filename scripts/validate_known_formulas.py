"""Validate known formula patterns data and schema consistency.

This script validates:
1. Canonical samples/formulas/known-patterns.v1.json against schema
2. Package data src/doc_converter/formulas/known-patterns.v1.json against schema
3. Both files are in sync (same content)
4. Basic consistency checks on pattern data
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_repo_root / "src"))

from doc_converter.schema_validation import validate_payload

CANONICAL_SOURCE = _repo_root / "samples" / "formulas" / "known-patterns.v1.json"
PACKAGE_DATA = _repo_root / "src" / "doc_converter" / "formulas" / "known-patterns.v1.json"
SCHEMA_NAME = "formula-known-patterns.v1.schema.json"


def validate_file(file_path: Path, label: str) -> dict[str, Any] | None:
    """Validate a single known patterns file."""
    print(f"Validating {label}: {file_path}")

    if not file_path.exists():
        print("  ERROR: File not found", file=sys.stderr)
        return None

    try:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"  ERROR: Invalid JSON: {e}", file=sys.stderr)
        return None

    try:
        validate_payload(data, SCHEMA_NAME)
    except Exception as e:
        print(f"  ERROR: Schema validation failed: {e}", file=sys.stderr)
        return None

    print("  OK: schema validation passed")
    return data


def check_consistency(data: dict[str, Any]) -> bool:
    """Check basic consistency of pattern data."""
    print("Checking pattern consistency...")

    errors = []

    # Check noisy form recovery keys are unique
    noisy_forms = data.get("noisy_form_recovery", {})
    if not noisy_forms:
        errors.append("No noisy form recovery mappings found")

    # Check formula representations have unique linear_text keys
    representations = data.get("formula_representations", [])
    if not representations:
        errors.append("No formula representations found")
    else:
        linear_texts = [f["linear_text"] for f in representations]
        if len(linear_texts) != len(set(linear_texts)):
            errors.append("Duplicate linear_text keys in formula_representations")

    # Check mathtype signature rules exist
    rules = data.get("mathtype_signature_rules", [])
    if not rules:
        errors.append("No MathType signature rules found")

    if errors:
        for error in errors:
            print(f"  ERROR: {error}", file=sys.stderr)
        return False

    print("  OK: consistency checks passed")
    print(f"    - {len(noisy_forms)} noisy form recovery mappings")
    print(f"    - {len(representations)} formula representations")
    print(f"    - {len(rules)} MathType signature rules")
    return True


def check_sync(canonical_data: dict[str, Any], package_data: dict[str, Any]) -> bool:
    """Check that canonical and package data are in sync."""
    print("Checking canonical and package data sync...")

    # Compare as JSON strings to detect any differences
    canonical_json = json.dumps(canonical_data, sort_keys=True, indent=2)
    package_json = json.dumps(package_data, sort_keys=True, indent=2)

    if canonical_json != package_json:
        print("  ERROR: Canonical and package data are out of sync", file=sys.stderr)
        print("         Run scripts/export_known_formulas.py to sync", file=sys.stderr)
        return False

    print("  OK: canonical and package data are in sync")
    return True


def main() -> int:
    """Validate known formula patterns."""
    print("=" * 60)
    print("Validating known formula patterns")
    print("=" * 60)

    canonical_data = validate_file(CANONICAL_SOURCE, "Canonical source")
    if canonical_data is None:
        return 1

    package_data = validate_file(PACKAGE_DATA, "Package data")
    if package_data is None:
        return 1

    if not check_consistency(canonical_data):
        return 1

    if not check_sync(canonical_data, package_data):
        return 1

    print()
    print("=" * 60)
    print("All validations passed")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
