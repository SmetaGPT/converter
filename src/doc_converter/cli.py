from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .config import AgentRunMetadata, ConverterConfig, ConverterOptions
from .formula_eval import (
    DocumentFormulaEvaluationItem,
    FormulaEvaluationError,
    MissingFormulaVariablesError,
    evaluate_document_formulas,
    evaluate_formula_expression,
)
from .ocr_runtime import detect_ocr_runtime
from .runner import ConverterError, run_convert_folder
from .schema_validation import validate_json_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="document-converter",
        description="Convert DOCX/PDF/XLSX folders into portable machine-readable run packages.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    convert = subparsers.add_parser("convert-folder", help="Convert an input folder into an output run package.")
    convert.add_argument("input_dir", type=Path, help="Folder with source DOCX/PDF/XLSX files.")
    convert.add_argument("output_dir", type=Path, help="Folder where run output will be created.")
    convert.add_argument("--ocr-languages", default="rus,eng", help="Comma-separated OCR language codes.")
    convert.add_argument("--include-originals", action="store_true", help="Copy source files into each canonical document package.")
    convert.add_argument("--agent-id", help="Autonomous agent identifier to store in run metadata.")
    convert.add_argument("--agent-version", help="Autonomous agent version to store in run metadata.")
    convert.add_argument("--task-id", help="Agent task identifier to store in run metadata.")
    convert.add_argument("--parent-run-id", help="Parent agent/converter run identifier, when this run is a child task.")
    convert.set_defaults(func=_handle_convert_folder)

    check_ocr = subparsers.add_parser("check-ocr", help="Check OCRmyPDF/Tesseract/Ghostscript runtime availability.")
    check_ocr.add_argument("--ocr-languages", default="rus,eng", help="Comma-separated OCR language codes.")
    check_ocr.set_defaults(func=_handle_check_ocr)

    evaluate_formula = subparsers.add_parser(
        "evaluate-formula",
        help="Evaluate a safe calc_expr formula against a JSON object of variable values.",
    )
    evaluate_formula.add_argument("--calc-expr", required=True, help="Formula calculation expression, e.g. 'R = A + B * C'.")
    values_group = evaluate_formula.add_mutually_exclusive_group(required=True)
    values_group.add_argument("--values", help="JSON object with variable values.")
    values_group.add_argument("--values-file", type=Path, help="Path to a JSON file with variable values.")
    evaluate_formula.set_defaults(func=_handle_evaluate_formula)

    evaluate_document = subparsers.add_parser(
        "evaluate-document-formulas",
        help="Evaluate all calc_expr formulas from a document.v1.json package against a JSON object of variable values.",
    )
    evaluate_document.add_argument(
        "document",
        type=Path,
        help="Path to document.v1.json or a document package directory.",
    )
    document_values_group = evaluate_document.add_mutually_exclusive_group(required=True)
    document_values_group.add_argument("--values", help="JSON object with variable values.")
    document_values_group.add_argument("--values-file", type=Path, help="Path to a JSON file with variable values.")
    evaluate_document.set_defaults(func=_handle_evaluate_document_formulas)

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
        include_originals=args.include_originals,
    )
    result = run_convert_folder(
        ConverterConfig(
            input_dir=args.input_dir,
            output_dir=args.output_dir,
            options=options,
            agent_run_metadata=_agent_run_metadata_from_args(args),
        )
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


def _agent_run_metadata_from_args(args: argparse.Namespace) -> AgentRunMetadata | None:
    if not any((args.agent_id, args.agent_version, args.task_id, args.parent_run_id)):
        return None
    return AgentRunMetadata(
        agent_id=args.agent_id,
        agent_version=args.agent_version,
        task_id=args.task_id,
        parent_run_id=args.parent_run_id,
    )


def _handle_check_ocr(args: argparse.Namespace) -> int:
    payload = detect_ocr_runtime(_parse_ocr_languages(args.ocr_languages))
    print(json.dumps(payload, ensure_ascii=False))
    return 0 if payload["status"] == "ready" else 1


def _handle_evaluate_formula(args: argparse.Namespace) -> int:
    values = _load_formula_values(args)
    try:
        result = evaluate_formula_expression(args.calc_expr, values)
    except MissingFormulaVariablesError as exc:
        print(
            json.dumps(
                {
                    "status": "missing_variables",
                    "calc_expr": exc.calc_expr,
                    "target": exc.target,
                    "expression": exc.expression,
                    "missing_variables": list(exc.missing_variables),
                },
                ensure_ascii=False,
            )
        )
        return 1
    except FormulaEvaluationError as exc:
        raise ConverterError(str(exc)) from exc

    print(
        json.dumps(
            {
                "status": "ok",
                "calc_expr": result.calc_expr,
                "target": result.target,
                "expression": result.expression,
                "value": result.value,
                "used_variables": result.used_variables,
            },
            ensure_ascii=False,
        )
    )
    return 0


def _handle_evaluate_document_formulas(args: argparse.Namespace) -> int:
    values = _load_formula_values(args)
    document_path = _resolve_document_path(args.document)
    try:
        payload = validate_json_file(document_path, "document.v1.schema.json")
        result = evaluate_document_formulas(payload, values)
    except FormulaEvaluationError as exc:
        raise ConverterError(str(exc)) from exc

    status = "ok" if result.missing_count == 0 and result.error_count == 0 else "partial"
    print(
        json.dumps(
            {
                "status": status,
                "document": str(document_path),
                "formula_units": result.formula_units,
                "calc_expr_units": result.calc_expr_units,
                "evaluated": result.evaluated_count,
                "missing_variables": result.missing_count,
                "errors": result.error_count,
                "results": [_document_formula_result_payload(item) for item in result.results],
            },
            ensure_ascii=False,
        )
    )
    return 0 if status == "ok" else 1


def _parse_ocr_languages(value: str) -> tuple[str, ...]:
    languages = tuple(item.strip() for item in value.split(",") if item.strip())
    if not languages:
        raise ConverterError("At least one OCR language must be provided.")
    return languages


def _load_formula_values(args: argparse.Namespace) -> dict[str, object]:
    if args.values_file is not None:
        try:
            payload = json.loads(args.values_file.read_text(encoding="utf-8-sig"))
        except OSError as exc:
            raise ConverterError(f"Unable to read values file: {args.values_file}") from exc
        except json.JSONDecodeError as exc:
            raise ConverterError(f"Values file is not valid JSON: {args.values_file}") from exc
    else:
        try:
            payload = json.loads(args.values)
        except json.JSONDecodeError as exc:
            raise ConverterError("--values must be a valid JSON object.") from exc

    if not isinstance(payload, dict):
        raise ConverterError("Formula values must be provided as a JSON object.")
    return payload


def _resolve_document_path(path: Path) -> Path:
    candidate = path.expanduser().resolve()
    if candidate.is_file():
        return candidate
    document_path = candidate / "document.v1.json"
    if document_path.is_file():
        return document_path
    raise ConverterError(f"document.v1.json not found: {path}")


def _document_formula_result_payload(item: DocumentFormulaEvaluationItem) -> dict[str, Any]:
    return {
        "unit_id": item.unit_id,
        "unit_type": item.unit_type,
        "order": item.order,
        "text": item.text,
        "calc_expr": item.calc_expr,
        "target": item.target,
        "expression": item.expression,
        "status": item.status,
        "value": item.value,
        "used_variables": item.used_variables,
        "missing_variables": list(item.missing_variables),
        "error": item.error,
    }


if __name__ == "__main__":
    raise SystemExit(main())