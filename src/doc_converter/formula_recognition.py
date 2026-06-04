from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

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
    cache_hits: int = 0
    estimated_cost_usd: float = 0.0
    review_required_units: int = 0
    warnings: tuple[str, ...] = ()
    artifact_path: str | None = None


@dataclass
class FormulaRecognitionRunState:
    attempted_formulas: int = 0
    provider_calls: int = 0
    cache_hits: int = 0
    estimated_cost_usd: float = 0.0
    provider_cache: dict[str, dict[str, Any]] = field(default_factory=dict)


def run_formula_recognition_postprocess(
    document_dir: Path,
    config: FormulaRecognitionConfig,
    providers: Sequence[FormulaProvider] | None = None,
    run_state: FormulaRecognitionRunState | None = None,
) -> FormulaRecognitionPostprocessResult:
    provider_chain = tuple(providers) if providers is not None else build_formula_provider_chain(config)
    active_run_state = run_state if run_state is not None else FormulaRecognitionRunState()

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
    cache_hits = 0
    estimated_cost_usd = 0.0
    review_required_units = 0
    warning_set: set[str] = set()

    for unit in units:
        candidate = _formula_recognition_candidate(unit, mode=config.mode)
        if candidate is None:
            continue

        attempted += 1
        active_run_state.attempted_formulas += 1
        asset_ref = candidate.get("asset_ref")
        source_text = candidate.get("source_text")
        local_hint_text = None
        if isinstance(asset_ref, str) and asset_ref:
            asset_path = document_dir / asset_ref
            if not asset_path.exists():
                warning_set.add("formula_recognition_asset_missing")
                review_required_units += _mark_formula_review_required(payload, unit, "formula_recognition_asset_missing")
                records.append(
                    {
                        "unit_id": unit.get("unit_id"),
                        "asset_ref": asset_ref,
                        "status": "asset_missing",
                        "review_required": True,
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
        partial_formula: dict[str, Any] | None = None

        for provider in provider_chain:
            if isinstance(provider, NullProvider):
                continue

            had_non_null_provider = True
            if provider.stage == "provider":
                cache_key = _build_provider_cache_key(
                    asset=asset,
                    context=context,
                    provider_id=provider.provider_id,
                    model=config.model,
                    prompt_version=config.prompt_version,
                )
                cached_prediction = active_run_state.provider_cache.get(cache_key)
                if cached_prediction is not None:
                    cache_hits += 1
                    active_run_state.cache_hits += 1
                    prediction = _prediction_from_cache(cached_prediction)
                    formula = prediction.formula
                    if prediction.origin == "mathpix" and not _formula_has_machine_readable_contract(formula):
                        partial_formula = formula
                        records.append(
                            {
                                "unit_id": unit.get("unit_id"),
                                "asset_ref": asset_ref,
                                "status": "recognized_mathpix_partial",
                                "candidate_kind": candidate.get("kind"),
                                "provider": provider.provider_id,
                                "confidence": formula.get("confidence"),
                                "source_format": formula.get("source_format"),
                                "cache_key": cache_key,
                                "cache_status": "hit",
                                "estimated_cost_usd": 0.0,
                                "review_required": True,
                            }
                        )
                        context = _context_with_mathpix_hint(context, formula)
                        continue

                    if _provider_formula_requires_review(formula):
                        review_required_units += _mark_formula_review_required(
                            payload,
                            unit,
                            _formula_review_reason(formula, prediction.origin),
                        )
                    _apply_formula_to_unit(unit, formula, origin=prediction.origin)
                    recognized += 1
                    records.append(
                        _recognized_record(
                            unit_id=unit.get("unit_id"),
                            asset_ref=asset_ref,
                            candidate_kind=candidate.get("kind"),
                            formula=formula,
                            prediction_origin=prediction.origin,
                            provider_id=provider.provider_id,
                            model=config.model,
                            cache_key=cache_key,
                            cache_status="hit",
                            estimated_cost_usd=0.0,
                            review_required=_provider_formula_requires_review(formula),
                        )
                    )
                    resolved = True
                    break

                budget_reason = _provider_budget_reason(
                    config=config,
                    run_state=active_run_state,
                    estimated_call_cost=_estimate_provider_call_cost(
                        provider_id=provider.provider_id,
                        model=config.model,
                        source_text=source_text,
                        local_hint_text=local_hint_text,
                    ),
                )
                if budget_reason is not None:
                    warning_set.add("formula_recognition_budget_exceeded")
                    review_required_units += _mark_formula_review_required(payload, unit, budget_reason)
                    records.append(
                        {
                            "unit_id": unit.get("unit_id"),
                            "asset_ref": asset_ref,
                            "status": "budget_skipped",
                            "candidate_kind": candidate.get("kind"),
                            "provider": provider.provider_id,
                            "model": config.model,
                            "message": budget_reason,
                            "review_required": True,
                        }
                    )
                    break

                provider_calls += 1
                active_run_state.provider_calls += 1

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
                review_required_units += _mark_formula_review_required(payload, unit, "formula_recognition_provider_failed")
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
                        "review_required": True,
                    }
                )
                break

            if prediction is None:
                continue

            formula = prediction.formula
            call_cost = 0.0
            cache_key = None
            if provider.stage == "provider":
                cache_key = _build_provider_cache_key(
                    asset=asset,
                    context=context,
                    provider_id=provider.provider_id,
                    model=config.model,
                    prompt_version=config.prompt_version,
                )
                call_cost = _estimate_provider_call_cost(
                    provider_id=provider.provider_id,
                    model=config.model,
                    source_text=source_text,
                    local_hint_text=local_hint_text,
                )
                active_run_state.provider_cache[cache_key] = _cache_entry_for_prediction(
                    prediction=prediction,
                    estimated_cost_usd=call_cost,
                )
                estimated_cost_usd += call_cost
                active_run_state.estimated_cost_usd += call_cost
            if prediction.origin == "local_backend" and not _local_backend_formula_is_sufficient(formula):
                continue
            if prediction.origin == "mathpix" and not _formula_has_machine_readable_contract(formula):
                partial_formula = formula
                records.append(
                    {
                        "unit_id": unit.get("unit_id"),
                        "asset_ref": asset_ref,
                        "status": "recognized_mathpix_partial",
                        "candidate_kind": candidate.get("kind"),
                        "provider": provider.provider_id,
                        "confidence": formula.get("confidence"),
                        "source_format": formula.get("source_format"),
                        "cache_key": cache_key,
                        "cache_status": "miss",
                        "estimated_cost_usd": call_cost,
                        "review_required": True,
                    }
                )
                context = _context_with_mathpix_hint(context, formula)
                continue

            review_required = _provider_formula_requires_review(formula)
            if review_required:
                review_required_units += _mark_formula_review_required(
                    payload,
                    unit,
                    _formula_review_reason(formula, prediction.origin),
                )
            _apply_formula_to_unit(unit, formula, origin=prediction.origin)
            recognized += 1
            records.append(
                _recognized_record(
                    unit_id=unit.get("unit_id"),
                    asset_ref=asset_ref,
                    candidate_kind=candidate.get("kind"),
                    formula=formula,
                    prediction_origin=prediction.origin,
                    provider_id=provider.provider_id,
                    model=config.model,
                    cache_key=cache_key,
                    cache_status="miss" if provider.stage == "provider" else None,
                    estimated_cost_usd=call_cost,
                    review_required=review_required,
                )
            )
            resolved = True
            break

        if not resolved and not provider_failed:
            if partial_formula is not None:
                review_required_units += _mark_formula_review_required(payload, unit, "formula_recognition_display_only")
                _apply_formula_to_unit(unit, partial_formula, origin="mathpix")
                recognized += 1
                continue
            unresolved_record: dict[str, Any] = {
                "unit_id": unit.get("unit_id"),
                "asset_ref": asset_ref,
                "status": "unresolved_without_provider",
                "candidate_kind": candidate.get("kind"),
                "review_required": True,
            }
            if config.local_backend is not None:
                unresolved_record["local_backend"] = config.local_backend
            if not had_non_null_provider:
                unresolved_record["provider"] = "null"
            review_required_units += _mark_formula_review_required(payload, unit, "formula_recognition_unresolved")
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
        "cache_hits": cache_hits,
        "estimated_cost_usd": round(estimated_cost_usd, 6),
        "review_required_units": review_required_units,
        "prompt_version": config.prompt_version,
        "results_path": artifact_path.name,
    }
    if config.provider is not None:
        processing_payload["provider"] = config.provider
    if config.model is not None:
        processing_payload["model"] = config.model
    if config.local_backend is not None:
        processing_payload["local_backend"] = config.local_backend
    if config.mathpix_is_configured():
        processing_payload["mathpix"] = {"configured": True}
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
        cache_hits=cache_hits,
        estimated_cost_usd=round(estimated_cost_usd, 6),
        review_required_units=review_required_units,
        warnings=tuple(sorted(warning_set)),
        artifact_path=artifact_path.name,
    )


def _formula_recognition_candidate(unit: object, *, mode: str = "fallback") -> dict[str, Any] | None:
    if not isinstance(unit, dict):
        return None

    unit_type = unit.get("type")
    asset_ref = unit.get("asset_ref")
    formula = unit.get("formula") if isinstance(unit.get("formula"), dict) else None
    text = unit.get("text") if isinstance(unit.get("text"), str) else None

    if unit_type == "formula_image" and isinstance(asset_ref, str) and asset_ref and _formula_needs_provider_review(formula, mode=mode):
        return {"kind": "formula_image", "asset_ref": asset_ref, "source_text": text}

    if unit_type == "formula" and isinstance(asset_ref, str) and asset_ref and _formula_needs_provider_review(formula, mode=mode):
        return {"kind": "formula_image", "asset_ref": asset_ref, "source_text": text}

    if unit_type == "formula" and text and _formula_needs_provider_review(formula, mode=mode):
        return {"kind": "formula_text", "asset_ref": None, "source_text": text}

    return None


def _formula_needs_provider_review(formula: dict[str, Any] | None, *, mode: str = "fallback") -> bool:
    if formula is None:
        return True
    if mode in {"llm_first", "mathpix_first"} and str(formula.get("confidence")) == "low":
        return True
    return bool(not _formula_has_machine_readable_contract(formula))


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
        if origin == "mathpix":
            _append_unique(warnings, "formula_recognition_mathpix_generated")
            if not _formula_has_machine_readable_contract(formula):
                _append_unique(warnings, "formula_recognition_display_only")


def _cache_entry_for_prediction(prediction: Any, *, estimated_cost_usd: float) -> dict[str, Any]:
    return {
        "origin": prediction.origin,
        "formula": prediction.formula,
        "estimated_cost_usd": round(estimated_cost_usd, 6),
    }


def _prediction_from_cache(entry: dict[str, Any]) -> Any:
    class _CachedPrediction:
        def __init__(self, *, formula: dict[str, Any], origin: str) -> None:
            self.formula = formula
            self.origin = origin

    formula = entry.get("formula")
    origin = entry.get("origin")
    if not isinstance(formula, dict) or not isinstance(origin, str):
        raise TypeError("Formula recognition cache entry is malformed")
    return _CachedPrediction(formula=formula, origin=origin)


def _recognized_record(
    *,
    unit_id: Any,
    asset_ref: Any,
    candidate_kind: Any,
    formula: dict[str, Any],
    prediction_origin: str,
    provider_id: str,
    model: str | None,
    cache_key: str | None,
    cache_status: str | None,
    estimated_cost_usd: float,
    review_required: bool,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "unit_id": unit_id,
        "asset_ref": asset_ref,
        "candidate_kind": candidate_kind,
        "confidence": formula.get("confidence"),
        "source_format": formula.get("source_format"),
        "review_required": review_required,
    }
    if prediction_origin == "local_backend":
        record["status"] = "recognized_local_backend"
        record["local_backend"] = provider_id
        return record
    record["status"] = "recognized_provider"
    record["provider"] = provider_id
    record["model"] = model
    if cache_key is not None:
        record["cache_key"] = cache_key
    if cache_status is not None:
        record["cache_status"] = cache_status
    record["estimated_cost_usd"] = round(estimated_cost_usd, 6)
    return record


def _provider_formula_requires_review(formula: dict[str, Any]) -> bool:
    if not _formula_has_machine_readable_contract(formula):
        return True
    return str(formula.get("confidence")) == "low"


def _formula_review_reason(formula: dict[str, Any], origin: str) -> str:
    if not _formula_has_machine_readable_contract(formula):
        if origin == "mathpix":
            return "formula_recognition_display_only"
        return "formula_recognition_unresolved"
    return "formula_recognition_low_confidence"


def _mark_formula_review_required(payload: dict[str, Any], unit: dict[str, Any], reason: str) -> int:
    document_quality = payload.setdefault("quality", {"flags": [], "warnings": []})
    document_flags = document_quality.setdefault("flags", [])
    document_warnings = document_quality.setdefault("warnings", [])
    processing = payload.setdefault("processing", {})
    processing_warnings = processing.setdefault("warnings", [])
    unit_quality = unit.setdefault("quality", {"flags": [], "warnings": []})
    unit_flags = unit_quality.setdefault("flags", [])
    unit_warnings = unit_quality.setdefault("warnings", [])

    already_marked = "review_required" in unit_flags
    _append_unique(document_flags, "review_required")
    _append_unique(unit_flags, "review_required")
    _append_unique(document_warnings, reason)
    _append_unique(unit_warnings, reason)
    if isinstance(processing_warnings, list):
        _append_unique(processing_warnings, reason)
    return 0 if already_marked else 1


def _build_provider_cache_key(
    *,
    asset: FormulaRecognitionAsset,
    context: FormulaProviderContext,
    provider_id: str,
    model: str | None,
    prompt_version: str,
) -> str:
    asset_sha256 = None
    if asset.blob is not None:
        asset_sha256 = hashlib.sha256(asset.blob).hexdigest()
    payload = {
        "asset_sha256": asset_sha256,
        "candidate_kind": context.candidate_kind,
        "provider": provider_id,
        "model": model,
        "prompt_version": prompt_version,
        "source_text": context.source_text,
        "local_hint_text": context.local_hint_text,
        "mathpix_text": context.mathpix_text,
        "mathpix_latex": context.mathpix_latex,
        "mathpix_asciimath": context.mathpix_asciimath,
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def _provider_budget_reason(
    *,
    config: FormulaRecognitionConfig,
    run_state: FormulaRecognitionRunState,
    estimated_call_cost: float,
) -> str | None:
    if config.max_formulas_per_run is not None and run_state.attempted_formulas > config.max_formulas_per_run:
        return "formula_recognition_budget_max_formulas_per_run"
    if config.max_provider_calls is not None and run_state.provider_calls >= config.max_provider_calls:
        return "formula_recognition_budget_max_provider_calls"
    if (
        config.max_estimated_cost_usd is not None
        and (run_state.estimated_cost_usd + estimated_call_cost) > config.max_estimated_cost_usd
    ):
        return "formula_recognition_budget_max_estimated_cost_usd"
    return None


def _estimate_provider_call_cost(
    *,
    provider_id: str,
    model: str | None,
    source_text: Any,
    local_hint_text: Any,
) -> float:
    if provider_id == "mathpix":
        return 0.002
    if provider_id != "openrouter" or not isinstance(model, str):
        return 0.0
    rate = _openrouter_rate_per_token(model)
    if rate is None:
        return 0.0
    prompt_text = " ".join(
        part for part in [str(source_text or "").strip(), str(local_hint_text or "").strip()] if part
    )
    estimated_input_tokens = max(1, (len(prompt_text) + 3) // 4)
    estimated_output_tokens = 120
    return round((estimated_input_tokens * rate["input"]) + (estimated_output_tokens * rate["output"]), 6)


def _openrouter_rate_per_token(model: str) -> dict[str, float] | None:
    normalized = model.strip().lower()
    if normalized == "openai/gpt-4o-mini":
        return {"input": 0.15 / 1_000_000, "output": 0.60 / 1_000_000}
    if normalized == "openai/gpt-4o":
        return {"input": 2.50 / 1_000_000, "output": 10.0 / 1_000_000}
    return None


def _context_with_mathpix_hint(context: FormulaProviderContext, formula: dict[str, Any]) -> FormulaProviderContext:
    linear_text = formula.get("linear_text") if isinstance(formula.get("linear_text"), str) else None
    display_latex = formula.get("display_latex") if isinstance(formula.get("display_latex"), str) else None
    return FormulaProviderContext(
        candidate_kind=context.candidate_kind,
        asset_name=context.asset_name,
        local_hint_text=context.local_hint_text,
        source_text=context.source_text,
        mathpix_text=linear_text,
        mathpix_latex=display_latex,
        mathpix_asciimath=None,
    )


def _append_unique(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)


def _redacted_record_list(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    redacted = redact_secrets(records)
    if not isinstance(redacted, list):
        raise TypeError("Redacted formula-recognition records must remain a list")
    return redacted
