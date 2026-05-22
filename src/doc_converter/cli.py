from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import ConverterConfig, ConverterOptions
from .ocr_runtime import detect_ocr_runtime
from .runner import ConverterError, run_convert_folder


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="document-converter",
        description="Convert DOCX/PDF folders into portable machine-readable run packages.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    convert = subparsers.add_parser("convert-folder", help="Convert an input folder into an output run package.")
    convert.add_argument("input_dir", type=Path, help="Folder with source DOCX/PDF files.")
    convert.add_argument("output_dir", type=Path, help="Folder where run output will be created.")
    convert.add_argument("--ocr-languages", default="rus,eng", help="Comma-separated OCR language codes.")
    convert.add_argument("--include-originals", action="store_true", help="Copy source files into each canonical document package.")
    convert.set_defaults(func=_handle_convert_folder)

    check_ocr = subparsers.add_parser("check-ocr", help="Check OCRmyPDF/Tesseract/Ghostscript runtime availability.")
    check_ocr.add_argument("--ocr-languages", default="rus,eng", help="Comma-separated OCR language codes.")
    check_ocr.set_defaults(func=_handle_check_ocr)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except ConverterError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def _handle_convert_folder(args: argparse.Namespace) -> int:
    options = ConverterOptions(
        ocr_languages=_parse_ocr_languages(args.ocr_languages),
        workers=1,
        include_originals=args.include_originals,
    )
    result = run_convert_folder(
        ConverterConfig(input_dir=args.input_dir, output_dir=args.output_dir, options=options)
    )
    print(
        json.dumps(
            {
                "run_id": result.run_id,
                "run_dir": str(result.run_dir),
                "status": result.status,
                "discovered_files": result.discovered_files,
                "supported_files": result.supported_files,
            },
            ensure_ascii=False,
        )
    )
    return 0


def _handle_check_ocr(args: argparse.Namespace) -> int:
    payload = detect_ocr_runtime(_parse_ocr_languages(args.ocr_languages))
    print(json.dumps(payload, ensure_ascii=False))
    return 0 if payload["status"] == "ready" else 1


def _parse_ocr_languages(value: str) -> tuple[str, ...]:
    languages = tuple(item.strip() for item in value.split(",") if item.strip())
    if not languages:
        raise ConverterError("At least one OCR language must be provided.")
    return languages


if __name__ == "__main__":
    raise SystemExit(main())