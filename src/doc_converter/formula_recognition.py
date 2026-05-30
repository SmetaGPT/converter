from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from doc_converter.config import FormulaRecognitionConfig
from doc_converter.converters.docx import (
    _extract_formula_text_from_asset,
    _formula_representation_from_text,
)
from doc_converter.formulas.providers import (
    FormulaProvider,
    FormulaProviderContext,
    FormulaRecognitionAsset,
    NullProvider,
    build_formula_provider_chain,
)
from doc_converter.redaction import redact_secrets
from doc_converter.schema_validation import validate_payload

FORMULA_RECOGNITION_RESULTS_FILENAME = "formula-recognition.jsonl"


@dataclass(frozen=True)
class FormulaRecognitionPostprocessResult:
    attempted: int = 0
    recognized: int = 0
    provider_calls: int = 0
    warnings: tuple[str, ...] = ()
    artifact_path: str | None = None


def run_formula_recognition_postprocess(
    document_dir: Path,
    config: FormulaRecognitionConfig,
    providers: Sequence[FormulaProvider] | None = None,
) -> FormulaRecognitionPostprocessResult:
    provider_chain = tuple(providers) if providers is not None else build_formula_provider_chain(config)

    if providers is None and not config.is_configured():
        return FormulaRecognitionPostprocessResult()

    document_path = document_dir / "document.v1.json"
    if not document_path.exists():
        return FormulaRecognitionPostprocessResult(warnings=("formula_recognition_document_missing",))

    payload = json.loads(document_path.read_text(encoding="utf-8"))
    units = payload.get("units")
    if not isinstance(units, list):
        return FormulaRecognitionPostprocessResult(warnings=("formula_recognition_units_missing",))

    records: list[dict[str, Any]] = []
    attempted = 0
    recognized = 0
    provider_calls = 0
    warning_set: set[str] = set()

    for unit in units:
        candidate = _formula_recognition_candidate(unit)
        if candidate is None:
            continue

        attempted += 1
        asset_ref = candidate.get("asset_ref")
        source_text = candidate.get("source_text")
        local_hint_text = None
        if isinstance(asset_ref, str) and asset_ref:
            asset_path = document_dir / asset_ref
            if not asset_path.exists():
                warning_set.add("formula_recognition_asset_missing")
                records.append(
                    {
                        "unit_id": unit.get("unit_id"),
                        "asset_ref": asset_ref,
                        "status": "asset_missing",
                    }
                )
                continue

            blob = asset_path.read_bytes()
            local_hint_text = _extract_formula_text_from_asset(blob, asset_path.name)
            local_formula = _formula_representation_from_text(local_hint_text) if local_hint_text else None
            if _local_formula_is_sufficient(local_formula):
                assert local_formula is not None
                _apply_formula_to_unit(unit, local_formula)
                recognized += 1
                records.append(
                    {
                        "unit_id": unit.get("unit_id"),
                        "asset_ref": asset_ref,
                        "status": "recognized_local",
                        "source_format": local_formula.get("source_format"),
                        "confidence": local_formula.get("confidence"),
                    }
                )
                continue
        else:
            asset_path = None
            blob = None

        asset = FormulaRecognitionAsset(path=asset_path, blob=blob)
        context = FormulaProviderContext(
            candidate_kind=str(candidate.get("kind")),
            asset_name=asset_path.name if asset_path is not None else None,
            local_hint_text=local_hint_text,
            source_text=source_text,
        )
        resolved = False
        provider_failed = False
        had_non_null_provider = False

        for provider in provider_chain:
            if isinstance(provider, NullProvider):
                continue

            had_non_null_provider = True
            if provider.stage == "provider":
                provider_calls += 1

            try:
                prediction = provider.predict(asset, context)
            except Exception as exc:  # noqa: BLE001 - best-effort providers should not fail the document.
                if provider.stage == "local_backend":
                    warning_set.add("formula_recognition_local_backend_failed")
                    records.append(
                        {
                            "unit_id": unit.get("unit_id"),
                            "asset_ref": asset_ref,
                            "status": "local_backend_failed",
                            "candidate_kind": candidate.get("kind"),
                            "local_backend": provider.provider_id,
                            "error": type(exc).__name__,
                            "message": str(exc),
                        }
                    )
                    continue

                provider_failed = True
                warning_set.add("formula_recognition_provider_failed")
                records.append(
                    {
                        "unit_id": unit.get("unit_id"),
                        "asset_ref": asset_ref,
                        "status": "provider_failed",
                        "candidate_kind": candidate.get("kind"),
                        "provider": provider.provider_id,
                        "model": config.model,
                        "error": type(exc).__name__,
                        "message": str(exc),
                    }
                )
                break

            if prediction is None:
                continue

            formula = prediction.formula
            if prediction.origin == "local_backend" and not _local_backend_formula_is_sufficient(formula):
                continue

            _apply_formula_to_unit(unit, formula, origin=prediction.origin)
            recognized += 1
            record: dict[str, Any] = {
                "unit_id": unit.get("unit_id"),
                "asset_ref": asset_ref,
                "candidate_kind": candidate.get("kind"),
                "confidence": formula.get("confidence"),
                "source_format": formula.get("source_format"),
            }
            if prediction.origin == "local_backend":
                record["status"] = "recognized_local_backend"
                record["local_backend"] = provider.provider_id
            else:
                record["status"] = "recognized_provider"
                record["provider"] = provider.provider_id
                record["model"] = config.model
            records.append(record)
            resolved = True
            break

        if not resolved and not provider_failed:
            unresolved_record: dict[str, Any] = {
                "unit_id": unit.get("unit_id"),
                "asset_ref": asset_ref,
                "status": "unresolved_without_provider",
                "candidate_kind": candidate.get("kind"),
            }
            if config.local_backend is not None:
                unresolved_record["local_backend"] = config.local_backend
            if not had_non_null_provider:
                unresolved_record["provider"] = "null"
            records.append(unresolved_record)

    if attempted == 0:
        return FormulaRecognitionPostprocessResult()

    processing = payload.setdefault("processing", {})
    processing_warnings = processing.setdefault("warnings", [])
    if isinstance(processing_warnings, list):
        if recognized > 0:
            _append_unique(processing_warnings, "formula_recognition_applied")
        for warning in sorted(warning_set):
            _append_unique(processing_warnings, warning)

    artifact_path = document_dir / FORMULA_RECOGNITION_RESULTS_FILENAME
    redacted_records = _redacted_record_list(records)
    artifact_path.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in redacted_records), encoding="utf-8")
    processing_payload: dict[str, Any] = {
        "attempted": attempted,
        "recognized": recognized,
        "provider_calls": provider_calls,
        "results_path": artifact_path.name,
    }
    if config.provider is not None:
        processing_payload["provider"] = config.provider
    if config.model is not None:
        processing_payload["model"] = config.model
    if config.local_backend is not None:
        processing_payload["local_backend"] = config.local_backend
    processing["formula_recognition"] = processing_payload

    redacted_payload = redact_secrets(payload)
    if not isinstance(redacted_payload, dict):
        raise TypeError("Redacted document payload must remain a dictionary")
    validate_payload(redacted_payload, "document.v1.schema.json")
    document_path.write_text(json.dumps(redacted_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return FormulaRecognitionPostprocessResult(
        attempted=attempted,
        recognized=recognized,
        provider_calls=provider_calls,
        warnings=tuple(sorted(warning_set)),
        artifact_path=artifact_path.name,
    )


def _formula_recognition_candidate(unit: object) -> dict[str, Any] | None:
    if not isinstance(unit, dict):
        return None

    unit_type = unit.get("type")
    asset_ref = unit.get("asset_ref")
    formula = unit.get("formula") if isinstance(unit.get("formula"), dict) else None
    text = unit.get("text") if isinstance(unit.get("text"), str) else None

    if unit_type == "formula_image" and isinstance(asset_ref, str) and asset_ref:
        if _formula_needs_provider_review(formula):
            return {"kind": "formula_image", "asset_ref": asset_ref, "source_text": text}

    if unit_type == "formula" and text and _formula_needs_provider_review(formula):
        return {"kind": "formula_text", "asset_ref": None, "source_text": text}

    return None


def _formula_needs_provider_review(formula: dict[str, Any] | None) -> bool:
    if formula is None:
        return True
    if not _formula_has_machine_readable_contract(formula):
        return True
    return False


def _formula_has_machine_readable_contract(formula: dict[str, Any]) -> bool:
    calc_expr = formula.get("calc_expr")
    return isinstance(calc_expr, str) and bool(calc_expr.strip())


def _local_formula_is_sufficient(formula: dict[str, Any] | None) -> bool:
    if formula is None:
        return False
    return str(formula.get("confidence")) in {"high", "medium"}


def _local_backend_formula_is_sufficient(formula: dict[str, Any] | None) -> bool:
    if formula is None:
        return False
    if str(formula.get("confidence")) in {"high", "medium"}:
        return True
    calc_expr = formula.get("calc_expr")
    return isinstance(calc_expr, str) and bool(calc_expr.strip())


def _apply_formula_to_unit(unit: dict[str, Any], formula: dict[str, Any], *, origin: str | None = None) -> None:
    unit["formula"] = formula
    unit["text"] = formula.get("linear_text")
    quality = unit.setdefault("quality", {"flags": [], "warnings": []})
    warnings = quality.setdefault("warnings", [])
    if isinstance(warnings, list):
        if origin == "provider":
            _append_unique(warnings, "formula_recognition_model_generated")
        if origin == "local_backend":
            _append_unique(warnings, "formula_recognition_local_backend_generated")


def _append_unique(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)


def _redacted_record_list(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    redacted = redact_secrets(records)
    if not isinstance(redacted, list):
        raise TypeError("Redacted formula-recognition records must remain a list")
    return redacted
