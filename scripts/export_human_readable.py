from __future__ import annotations

import argparse
import json
from pathlib import Path

from doc_converter.human_readable import export_document_markdown


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export a document.v1.json package into human-readable Markdown.")
    parser.add_argument("document", type=Path, help="Path to document.v1.json or a document package directory.")
    parser.add_argument("output", type=Path, nargs="?", help="Output Markdown path. Defaults to human-readable.md next to document.v1.json.")
    args = parser.parse_args(argv)

    output_path = args.output.expanduser().resolve() if args.output is not None else None
    exported_path = export_document_markdown(args.document, output_path)
    print(json.dumps({"status": "ok", "output": str(exported_path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())