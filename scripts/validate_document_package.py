from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from doc_converter.schema_validation import validate_json_file, validate_payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate canonical document packages under a converter run directory.")
    parser.add_argument("run_dir", type=Path, help="Path to converter run directory")
    args = parser.parse_args(argv)

    run_dir = args.run_dir.expanduser().resolve()
    document_paths = sorted((run_dir / "documents").glob("*/document.v1.json"))
    for document_path in document_paths:
        validate_json_file(document_path, "document.v1.schema.json")
        formula_recognition_path = document_path.parent / "formula-recognition.jsonl"
        if formula_recognition_path.exists():
            _validate_jsonl(formula_recognition_path, "formula-recognition.v1.schema.json")

    print(
        json.dumps(
            {
                "run_dir": str(run_dir),
                "status": "ok",
                "documents_validated": len(document_paths),
            },
            ensure_ascii=False,
        )
    )
    return 0


def _validate_jsonl(path: Path, schema_filename: str) -> None:
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        validate_payload(json.loads(line), schema_filename)


if __name__ == "__main__":
    raise SystemExit(main())
