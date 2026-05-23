# pyright: reportMissingTypeStubs=false

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from doc_converter.chunking import build_chunks_from_document
from doc_converter.schema_validation import validate_json_file, validate_payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build reference chunks.v1.jsonl from a converter run package.")
    parser.add_argument("run_dir", type=Path, help="Path to a converter run directory containing documents/*/document.v1.json")
    parser.add_argument("--output", type=Path, help="Optional output file path. Defaults to <run_dir>/chunks.v1.jsonl")
    parser.add_argument("--max-chars", type=int, default=1200, help="Maximum characters per chunk before flushing.")
    args = parser.parse_args(argv)

    run_dir = args.run_dir.expanduser().resolve()
    output_path = (args.output or (run_dir / "chunks.v1.jsonl")).expanduser().resolve()
    document_paths = sorted((run_dir / "documents").glob("*/document.v1.json"))
    chunks: list[dict[str, Any]] = []
    for document_path in document_paths:
        payload = validate_json_file(document_path, "document.v1.schema.json")
        for chunk in build_chunks_from_document(payload, max_chars=max(1, args.max_chars)):
            validate_payload(chunk, "chunks.v1.schema.json")
            chunks.append(chunk)

    with output_path.open("w", encoding="utf-8", newline="\n") as handle:
        for chunk in chunks:
            handle.write(json.dumps(chunk, ensure_ascii=False, separators=(",", ":")) + "\n")

    print(json.dumps({"run_dir": str(run_dir), "output": str(output_path), "chunks": len(chunks)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())