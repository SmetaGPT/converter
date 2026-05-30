from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main(argv: list[str] | None = None) -> int:
    from doc_converter.schema_validation import validate_payload

    parser = argparse.ArgumentParser(
        description="Validate the JSON envelope emitted by doc_converter.cli check-ocr."
    )
    parser.add_argument(
        "--ocr-languages",
        default="eng",
        help="Comma-separated OCR languages passed through to doc_converter.cli check-ocr.",
    )
    args = parser.parse_args(argv)

    command = [
        sys.executable,
        "-m",
        "doc_converter.cli",
        "check-ocr",
        "--output-format=json",
        "--ocr-languages",
        args.ocr_languages,
    ]
    completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")

    if completed.stderr:
        sys.stderr.write(completed.stderr)

    if completed.returncode not in (0, 1):
        if completed.stdout:
            sys.stdout.write(completed.stdout)
        return completed.returncode

    stdout = completed.stdout.strip()
    if not stdout:
        raise SystemExit("check-ocr produced empty stdout")

    payload = json.loads(stdout)
    validate_payload(payload, "cli-result.v1.schema.json")
    if payload.get("command") != "check-ocr":
        raise SystemExit(f"Unexpected command payload: {payload.get('command')!r}")
    if payload.get("exit_code") != completed.returncode:
        raise SystemExit(
            f"CLI exit code mismatch: payload={payload.get('exit_code')!r}, process={completed.returncode!r}"
        )

    sys.stdout.write(completed.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())