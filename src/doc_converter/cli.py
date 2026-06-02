from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from .config import AgentRunMetadata, ConverterConfig, ConverterOptions, FormulaRecognitionConfig
from .font_bundle import bundled_font_paths, font_bundle_directory
from .formula_eval import (
    DocumentFormulaEvaluationItem,
    FormulaEvaluationError,
    MissingFormulaVariablesError,
    evaluate_document_formulas,
    evaluate_formula_expression,
)
from .inventory import InventoryScanResult, build_inventory
from .ocr_runtime import detect_ocr_runtime
from .runner import ConverterError, run_convert_folder
from .schema_validation import SchemaValidationError, _schemas_dir, validate_json_file, validate_payload

_CLI_RESULT_SCHEMA = "cli-result.v1.schema.json"
_CLI_EXIT_CODES = {
    "ok": 0,
    "partial": 10,
    "review_required": 20,
    "input_invalid": 30,
    "environment_invalid": 40,
    "internal_error": 50,
}
_REQUIRED_SCHEMA_FILENAMES = (
    _CLI_RESULT_SCHEMA,
    "document.v1.schema.json",
    "manifest.v1.schema.json",
    "ocr-runtime.v1.schema.json",
    "processed-documents-catalog.v1.schema.json",
    "queue-state.v1.schema.json",
    "review-required.v1.schema.json",
    "run.v1.schema.json",
    "summary.v1.schema.json",
)
_OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"


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
    _add_output_format_argument(convert)
    convert.set_defaults(func=_handle_convert_folder)

    check_ocr = subparsers.add_parser("check-ocr", help="Check OCRmyPDF/Tesseract/Ghostscript runtime availability.")
    check_ocr.add_argument("--ocr-languages", default="rus,eng", help="Comma-separated OCR language codes.")
    _add_output_format_argument(check_ocr)
    check_ocr.set_defaults(func=_handle_check_ocr)

    doctor = subparsers.add_parser(
        "doctor",
        help="Check OCR runtime, bundled fonts, OpenRouter reachability and schema availability.",
    )
    doctor.add_argument("--ocr-languages", default="rus,eng", help="Comma-separated OCR language codes.")
    _add_output_format_argument(doctor)
    doctor.set_defaults(func=_handle_doctor)

    dry_run = subparsers.add_parser(
        "dry-run",
        help="Scan and classify an input folder without writing a run package.",
    )
    dry_run.add_argument("input_dir", type=Path, help="Folder with source DOCX/PDF/XLSX files.")
    _add_output_format_argument(dry_run)
    dry_run.set_defaults(func=_handle_dry_run)

    evaluate_formula = subparsers.add_parser(
        "evaluate-formula",
        help="Evaluate a safe calc_expr formula against a JSON object of variable values.",
    )
    evaluate_formula.add_argument("--calc-expr", required=True, help="Formula calculation expression, e.g. 'R = A + B * C'.")
    values_group = evaluate_formula.add_mutually_exclusive_group(required=True)
    values_group.add_argument("--values", help="JSON object with variable values.")
    values_group.add_argument("--values-file", type=Path, help="Path to a JSON file with variable values.")
    _add_output_format_argument(evaluate_formula)
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
    _add_output_format_argument(evaluate_document)
    evaluate_document.set_defaults(func=_handle_evaluate_document_formulas)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except ConverterError as exc:
        return _emit_cli_result(
            args,
            command=getattr(args, "command", "document-converter"),
            status="input_invalid",
            message=str(exc),
            data={"error_type": type(exc).__name__},
        )
    except Exception as exc:  # noqa: BLE001 - CLI must return structured internal errors.
        return _emit_cli_result(
            args,
            command=getattr(args, "command", "document-converter"),
            status="internal_error",
            message=str(exc) or f"Unhandled {type(exc).__name__}",
            data={"error_type": type(exc).__name__},
        )


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
    summary = validate_json_file(result.run_dir / "summary.json", "summary.v1.schema.json")
    return _emit_cli_result(
        args,
        command="convert-folder",
        status=_convert_folder_cli_status(summary),
        message=(
            f"Conversion finished with {summary['status']}: "
            f"{summary['supported_files']} supported, {summary['unsupported_files']} unsupported."
        ),
        data=summary,
    )


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
    status = "ok" if payload["status"] == "ready" else "environment_invalid"
    message = "OCR runtime is ready." if status == "ok" else "OCR runtime is missing required tools or languages."
    return _emit_cli_result(args, command="check-ocr", status=status, message=message, data=payload)


def _handle_doctor(args: argparse.Namespace) -> int:
    formula_config = ConverterOptions().formula_recognition
    payload = {
        "ocr_runtime": detect_ocr_runtime(_parse_ocr_languages(args.ocr_languages)),
        "font_bundle": _check_font_bundle(),
        "schemas": _check_schema_contracts(),
        "formula_recognition": formula_config.public_payload(),
        "openrouter": _check_openrouter_reachability(formula_config),
    }
    failing_checks = []
    if payload["ocr_runtime"]["status"] != "ready":
        failing_checks.append("ocr_runtime")
    if payload["font_bundle"]["status"] != "ready":
        failing_checks.append("font_bundle")
    if payload["schemas"]["status"] != "ready":
        failing_checks.append("schemas")
    if payload["openrouter"]["status"] == "error":
        failing_checks.append("openrouter")

    status = "ok" if not failing_checks else "environment_invalid"
    message = "Environment checks passed." if not failing_checks else f"Environment checks failed: {', '.join(failing_checks)}."
    return _emit_cli_result(args, command="doctor", status=status, message=message, data=payload)


def _handle_dry_run(args: argparse.Namespace) -> int:
    input_dir = _resolve_input_dir(args.input_dir)
    inventory = build_inventory(input_dir)
    payload = _build_dry_run_payload(input_dir, inventory)
    has_warnings = bool(payload["warning_counts"]) or payload["unsupported_files"] > 0
    status = "review_required" if has_warnings else "ok"
    message = (
        f"Dry run classified {payload['scanned_files']} files: "
        f"{payload['supported_files']} supported, {payload['unsupported_files']} unsupported."
    )
    return _emit_cli_result(args, command="dry-run", status=status, message=message, data=payload)


def _handle_evaluate_formula(args: argparse.Namespace) -> int:
    values = _load_formula_values(args)
    try:
        result = evaluate_formula_expression(args.calc_expr, values)
    except MissingFormulaVariablesError as exc:
        return _emit_cli_result(
            args,
            command="evaluate-formula",
            status="review_required",
            message=f"Formula is missing variables: {', '.join(exc.missing_variables)}.",
            data={
                "status": "missing_variables",
                "calc_expr": exc.calc_expr,
                "target": exc.target,
                "expression": exc.expression,
                "missing_variables": list(exc.missing_variables),
            },
        )
    except FormulaEvaluationError as exc:
        raise ConverterError(str(exc)) from exc

    return _emit_cli_result(
        args,
        command="evaluate-formula",
        status="ok",
        message=f"Formula {result.target} evaluated successfully.",
        data={
            "status": "ok",
            "calc_expr": result.calc_expr,
            "target": result.target,
            "expression": result.expression,
            "value": result.value,
            "used_variables": result.used_variables,
        },
    )


def _handle_evaluate_document_formulas(args: argparse.Namespace) -> int:
    values = _load_formula_values(args)
    document_path = _resolve_document_path(args.document)
    try:
        payload = validate_json_file(document_path, "document.v1.schema.json")
        result = evaluate_document_formulas(payload, values)
    except FormulaEvaluationError as exc:
        raise ConverterError(str(exc)) from exc

    formula_payload = {
        "status": "ok" if result.missing_count == 0 and result.error_count == 0 else "partial",
        "document": str(document_path),
        "formula_units": result.formula_units,
        "calc_expr_units": result.calc_expr_units,
        "evaluated": result.evaluated_count,
        "missing_variables": result.missing_count,
        "errors": result.error_count,
        "results": [_document_formula_result_payload(item) for item in result.results],
    }
    cli_status = "ok" if formula_payload["status"] == "ok" else "partial"
    message = (
        f"Evaluated {formula_payload['evaluated']} of {formula_payload['calc_expr_units']} document formulas."
    )
    return _emit_cli_result(
        args,
        command="evaluate-document-formulas",
        status=cli_status,
        message=message,
        data=formula_payload,
    )


def _parse_ocr_languages(value: str) -> tuple[str, ...]:
    languages = tuple(item.strip() for item in value.split(",") if item.strip())
    if not languages:
        raise ConverterError("At least one OCR language must be provided.")
    return languages


def _add_output_format_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--output-format",
        choices=("human", "json"),
        default="human",
        help="CLI output format: human-readable text or machine-readable JSON envelope.",
    )


def _emit_cli_result(
    args: argparse.Namespace,
    *,
    command: str,
    status: str,
    message: str,
    data: dict[str, Any],
) -> int:
    exit_code = _CLI_EXIT_CODES[status]
    payload = {
        "schema_version": "cli-result.v1",
        "command": command,
        "status": status,
        "exit_code": exit_code,
        "message": message,
        "data": data,
    }
    validate_payload(payload, _CLI_RESULT_SCHEMA)
    if getattr(args, "output_format", "human") == "json":
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(_format_human_result(payload))
    return exit_code


def _format_human_result(payload: dict[str, Any]) -> str:
    command = str(payload["command"])
    data = payload["data"]
    lines = [str(payload["message"])]
    if command == "convert-folder":
        lines.append(f"run_dir: {data['run_dir']}")
    elif command == "check-ocr":
        lines.append(f"ocr_status: {data['status']}")
    elif command == "doctor":
        lines.append(
            "checks: "
            + ", ".join(
                f"{name}={details['status']}"
                for name, details in (
                    ("ocr_runtime", data["ocr_runtime"]),
                    ("font_bundle", data["font_bundle"]),
                    ("schemas", data["schemas"]),
                    ("openrouter", data["openrouter"]),
                )
            )
        )
    elif command == "dry-run":
        lines.append(
            f"scanned_files: {data['scanned_files']}, supported_files: {data['supported_files']}, unsupported_files: {data['unsupported_files']}"
        )
    elif command == "evaluate-formula" and data.get("status") == "ok":
        lines.append(f"{data['target']} = {data['value']}")
    elif command == "evaluate-document-formulas":
        lines.append(f"evaluated: {data['evaluated']}/{data['calc_expr_units']}")
    if payload["status"] != "ok":
        lines.append(f"exit_code: {payload['exit_code']}")
    return "\n".join(lines)


def _resolve_input_dir(input_dir: Path) -> Path:
    candidate = input_dir.expanduser().resolve()
    if not candidate.exists():
        raise ConverterError(f"Input directory does not exist: {input_dir}")
    if not candidate.is_dir():
        raise ConverterError(f"Input path is not a directory: {input_dir}")
    return candidate


def _build_dry_run_payload(input_dir: Path, inventory: InventoryScanResult) -> dict[str, Any]:
    route_counts = _count_values(record.route for record in inventory.supported_records)
    warning_counts = _count_values(
        warning
        for record in inventory.supported_records
        for warning in record.warnings
    )
    unsupported_warning_counts = _count_values(
        warning
        for record in inventory.unsupported_records
        for warning in record.warnings
    )
    for key, value in unsupported_warning_counts.items():
        warning_counts[key] = warning_counts.get(key, 0) + value
    return {
        "input_dir": str(input_dir),
        "scanned_files": inventory.scanned_files,
        "supported_files": len(inventory.supported_records),
        "unsupported_files": len(inventory.unsupported_records),
        "route_counts": route_counts,
        "warning_counts": dict(sorted(warning_counts.items())),
        "supported_records": [
            {
                "relative_path": record.relative_path,
                "format": record.format,
                "route": record.route,
                "duplicate_of": record.duplicate_of,
                "warnings": list(record.warnings),
            }
            for record in inventory.supported_records
        ],
        "unsupported_records": [
            {
                "relative_path": record.relative_path,
                "format": record.format,
                "warnings": list(record.warnings),
            }
            for record in inventory.unsupported_records
        ],
    }


def _convert_folder_cli_status(summary: dict[str, Any]) -> str:
    summary_status = str(summary["status"])
    if summary_status == "success":
        if int(summary.get("review_required_files", 0)) > 0 or int(summary.get("unsupported_files", 0)) > 0:
            return "review_required"
        return "ok"
    return "partial"


def _check_schema_contracts() -> dict[str, Any]:
    try:
        schema_dir = _schemas_dir()
    except SchemaValidationError as exc:
        return {
            "status": "missing",
            "directory": None,
            "schemas": [],
            "warnings": [str(exc)],
        }

    schema_payloads = []
    missing = []
    for filename in _REQUIRED_SCHEMA_FILENAMES:
        available = (schema_dir / filename).exists()
        schema_payloads.append({"name": filename, "available": available})
        if not available:
            missing.append(filename)
    return {
        "status": "ready" if not missing else "missing",
        "directory": str(schema_dir),
        "schemas": schema_payloads,
        "warnings": [f"Missing schema: {filename}" for filename in missing],
    }


def _check_font_bundle() -> dict[str, Any]:
    bundle_dir = font_bundle_directory()
    fonts = sorted(path.name for path in bundled_font_paths())
    return {
        "status": "ready" if fonts else "missing",
        "directory": str(bundle_dir),
        "fonts": fonts,
        "warnings": [] if fonts else ["Bundled fonts directory is missing or empty."],
    }


def _check_openrouter_reachability(config: FormulaRecognitionConfig) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "provider": config.provider,
        "model": config.model,
        "status": "not_configured",
        "warnings": [],
    }
    if not config.provider_is_configured():
        return payload
    if (config.provider or "").lower() != "openrouter":
        payload["status"] = "not_applicable"
        return payload
    request = urllib.request.Request(
        _OPENROUTER_MODELS_URL,
        headers={
            "Authorization": f"Bearer {config.api_key}",
            "X-OpenRouter-Title": "DocumentConverter",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            payload["status"] = "ready" if 200 <= response.status < 300 else "error"
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        payload["status"] = "error"
        payload["warnings"] = [f"OpenRouter request failed: {exc.code} {details}"[:1000]]
    except urllib.error.URLError as exc:
        payload["status"] = "error"
        payload["warnings"] = [f"OpenRouter request failed: {exc.reason}"[:1000]]
    return payload


def _count_values(values: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        normalized = str(value).strip()
        if not normalized:
            continue
        counts[normalized] = counts.get(normalized, 0) + 1
    return dict(sorted(counts.items()))


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