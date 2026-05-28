"""Export known formula patterns from canonical source to package data.

This script syncs samples/formulas/known-patterns.v1.json to the package
data location src/doc_converter/formulas/known-patterns.v1.json.
Run this after updating the canonical patterns data.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

_repo_root = Path(__file__).resolve().parent.parent

CANONICAL_SOURCE = _repo_root / "samples" / "formulas" / "known-patterns.v1.json"
PACKAGE_DATA_TARGET = _repo_root / "src" / "doc_converter" / "formulas" / "known-patterns.v1.json"


def main() -> int:
    """Export canonical known patterns to package data."""
    if not CANONICAL_SOURCE.exists():
        print(f"ERROR: Canonical source not found: {CANONICAL_SOURCE}", file=sys.stderr)
        return 1

    print(f"Exporting {CANONICAL_SOURCE}")
    print(f"       to {PACKAGE_DATA_TARGET}")

    PACKAGE_DATA_TARGET.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(CANONICAL_SOURCE, PACKAGE_DATA_TARGET)

    print("Export complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
