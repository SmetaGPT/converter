from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from doc_converter.formula_benchmark import build_formula_gold_payload
from doc_converter.schema_validation import validate_json_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export a formula gold snapshot from a document.v1.json package.")
    parser.add_argument("document", type=Path, help="Path to document.v1.json")
    parser.add_argument("output", type=Path, help="Path to output formula gold JSON file")
    parser.add_argument("--document-label", required=True, help="Stable label for the gold document")
    parser.add_argument(
        "--banned-substring",
        action="append",
        default=[],
        help="Substring that must stay absent from formula text or LaTeX.",
    )
    args = parser.parse_args(argv)

    payload = validate_json_file(args.document.expanduser().resolve(), "document.v1.schema.json")
    gold_payload = build_formula_gold_payload(
        payload,
        document_label=args.document_label,
        banned_substrings_absent=list(args.banned_substring),
    )

    output_path = args.output.expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(gold_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "output": str(output_path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())