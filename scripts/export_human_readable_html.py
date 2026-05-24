from __future__ import annotations

import argparse
import json
from pathlib import Path

from doc_converter.human_readable import export_document_html, export_run_human_readable_html


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Export a document.v1.json package or an entire run directory into human-readable HTML."
    )
    parser.add_argument("input", type=Path, help="Path to document.v1.json, a document package directory or a run directory.")
    parser.add_argument(
        "output",
        type=Path,
        nargs="?",
        help="Output HTML path. Defaults to human-readable.html next to document.v1.json or human-readable-index.html in run_dir.",
    )
    args = parser.parse_args(argv)

    input_path = args.input.expanduser().resolve()
    output_path = args.output.expanduser().resolve() if args.output is not None else None

    if (input_path / "run.json").is_file() or (input_path / "documents").is_dir():
        exported_path = export_run_human_readable_html(input_path, output_path)
    else:
        exported_path = export_document_html(input_path, output_path)

    print(json.dumps({"status": "ok", "output": str(exported_path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())