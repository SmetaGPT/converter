# pyright: reportMissingTypeStubs=false

from __future__ import annotations

import importlib
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

from build_agent_scorecard import build_scorecard_markdown_section, build_scorecard_payload
from build_agent_weekly_eval import build_weekly_eval_markdown, build_weekly_eval_payload

ROOT = Path(__file__).resolve().parents[1]
FEATURE_SPINE = ROOT / "docs" / "agent-feature-spine.json"
FEATURE_SCHEMA = ROOT / "schemas" / "agent-feature-spine.v1.schema.json"
TELEMETRY_JSONL = ROOT / "docs" / "agent-telemetry.v1.jsonl"
TELEMETRY_SCHEMA = ROOT / "schemas" / "agent-telemetry-entry.v1.schema.json"
WEEKLY_REVIEWS_JSON = ROOT / "docs" / "agent-weekly-reviews.v1.json"
WEEKLY_REVIEWS_SCHEMA = ROOT / "schemas" / "agent-weekly-reviews.v1.schema.json"
SCORECARD_JSON = ROOT / "docs" / "agent-quality-scorecard.v1.json"
SCORECARD_MARKDOWN = ROOT / "docs" / "agent-quality-scorecard.md"
SCORECARD_SCHEMA = ROOT / "schemas" / "agent-quality-scorecard.v1.schema.json"
WEEKLY_EVAL_JSON = ROOT / "docs" / "agent-weekly-eval.v1.json"
WEEKLY_EVAL_MARKDOWN = ROOT / "docs" / "agent-weekly-eval.md"
WEEKLY_EVAL_SCHEMA = ROOT / "schemas" / "agent-weekly-eval.v1.schema.json"
VALIDATE_COMMAND = ".\\.venv\\Scripts\\python.exe scripts\\validate_harness_assets.py"
SCORECARD_SYNC_COMMAND = ".\\.venv\\Scripts\\python.exe scripts\\build_agent_scorecard.py --sync-markdown"
WEEKLY_REFRESH_COMMAND = ".\\.venv\\Scripts\\python.exe scripts\\refresh_agent_eval.py"
RUBRIC_SCORE_KEYS = (
    "scope_control",
    "feature_traceability",
    "hypothesis_quality",
    "validation_quality",
    "evidence_quality",
    "state_hygiene",
    "closeout_quality",
)
JSONSCHEMA = cast(Any, importlib.import_module("jsonschema"))
REQUIRED_DOCS = (
    ROOT / "docs" / "agent-bootstrap-contract.md",
    ROOT / "docs" / "agent-session-exit-checklist.md",
    ROOT / "docs" / "agent-sprint-contract-template.md",
    ROOT / "docs" / "agent-evaluator-rubric.md",
    ROOT / "docs" / "agent-evals.md",
)
REQUIRED_DOC_MARKERS = {
    ROOT / "docs" / "agent-bootstrap-contract.md": (
        "затронутые `feature_id`",
        "docs/agent-feature-spine.json",
    ),
    ROOT / "docs" / "agent-sprint-contract-template.md": (
        "### 3. Feature traceability",
        "Связанные `feature_id`:",
        "Какие evidence paths будут добавлены или обновлены",
    ),
    ROOT / "docs" / "agent-task-checkpoint-template.md": (
        "### 3. Feature traceability",
        "Связанные `feature_id`:",
        "Что изменилось в evidence или status:",
    ),
    ROOT / "docs" / "agent-session-exit-checklist.md": (
        "docs/agent-feature-spine.json",
        "traceability до затронутых `feature_id`",
        "docs/agent-telemetry.v1.jsonl",
    ),
    ROOT / "docs" / "agent-evaluator-rubric.md": (
        "| Feature traceability |",
        "затронутых `feature_id`",
    ),
    ROOT / "docs" / "agent-quality-scorecard.md": (
        "docs/agent-quality-scorecard.v1.json",
        "## 9. Structured companion",
    ),
    ROOT / "docs" / "agent-evals.md": (
        "docs/agent-weekly-eval.v1.json",
        "docs/agent-weekly-reviews.v1.json",
        "scripts/refresh_agent_eval.py",
        "scripts/build_agent_weekly_eval.py",
        "Generated weekly eval companion",
    ),
}
REQUIRED_PRODUCT_FEATURE_IDS = {
    "canonical-document-package",
    "docx-native-route",
    "pdf-text-route",
    "pdf-scan-route",
    "semantic-document-metadata",
    "quality-and-review-reporting",
    "resume-dedup-and-queue-state",
    "chunking-and-downstream-handoff",
    "operator-gui-and-release-packaging",
}


def _fail(what: str, why: str, fix: str) -> None:
    print(f"WHAT: {what}", file=sys.stderr)
    print(f"WHY: {why}", file=sys.stderr)
    print(f"FIX: {fix}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    payload = _load_json(FEATURE_SPINE)
    schema = _load_json(FEATURE_SCHEMA)
    telemetry_schema = _load_json(TELEMETRY_SCHEMA)
    weekly_reviews_schema = _load_json(WEEKLY_REVIEWS_SCHEMA)
    scorecard_schema = _load_json(SCORECARD_SCHEMA)
    weekly_eval_schema = _load_json(WEEKLY_EVAL_SCHEMA)
    features = _feature_list(payload)

    validator = JSONSCHEMA.Draft202012Validator(schema)
    telemetry_validator = JSONSCHEMA.Draft202012Validator(telemetry_schema)
    weekly_reviews_validator = JSONSCHEMA.Draft202012Validator(weekly_reviews_schema)
    scorecard_validator = JSONSCHEMA.Draft202012Validator(scorecard_schema)
    weekly_eval_validator = JSONSCHEMA.Draft202012Validator(weekly_eval_schema)
    errors = sorted(validator.iter_errors(payload), key=lambda error: list(error.absolute_path))
    if errors:
        details = []
        for error in errors:
            path = ".".join(str(part) for part in error.absolute_path) or "<root>"
            details.append(f"{path}: {error.message}")
        _fail(
            "agent feature spine schema validation failed: " + "; ".join(details),
            "docs/agent-feature-spine.json is the machine-readable source of truth for harness and product feature coverage.",
            f"Edit docs/agent-feature-spine.json to satisfy schemas/agent-feature-spine.v1.schema.json, then rerun `{VALIDATE_COMMAND}`.",
        )

    feature_ids: set[str] = set()
    for feature in features:
        feature_id = feature["feature_id"]
        if feature_id in feature_ids:
            _fail(
                f"duplicate feature_id: {feature_id}",
                "Feature IDs are used by telemetry, scorecards and weekly evals as stable join keys.",
                f"Rename one feature_id and update every reference in docs/agent-telemetry.v1.jsonl and docs/agent-weekly-reviews.v1.json, then rerun `{VALIDATE_COMMAND}`.",
            )
        feature_ids.add(feature_id)

        _assert_paths_exist(feature["owner_docs"], f"owner_docs for {feature_id}")
        _assert_paths_exist(feature["evidence"], f"evidence for {feature_id}")

        if feature["status"] == "validated" and not feature["evidence"]:
            _fail(
                f"validated feature has no evidence: {feature_id}",
                "A validated feature without evidence recreates subjective completion claims.",
                f"Add at least one evidence path for `{feature_id}` or downgrade its status, then rerun `{VALIDATE_COMMAND}`.",
            )

    for required_doc in REQUIRED_DOCS:
        if not required_doc.exists():
            _fail(
                f"required harness doc missing: {required_doc.relative_to(ROOT)}",
                "Core process documents are part of the cold-start and clean-exit contract.",
                f"Restore or recreate {required_doc.relative_to(ROOT)} with the required contract content, then rerun `{VALIDATE_COMMAND}`.",
            )

    for required_doc, markers in REQUIRED_DOC_MARKERS.items():
        _assert_markers(required_doc, markers)

    missing_product_features = sorted(REQUIRED_PRODUCT_FEATURE_IDS - feature_ids)
    if missing_product_features:
        _fail(
            "missing required product features: " + ", ".join(missing_product_features),
            "The feature spine must cover core converter capabilities, not only process-layer assets.",
            f"Add the missing feature_id entries to docs/agent-feature-spine.json with verification and evidence, then rerun `{VALIDATE_COMMAND}`.",
        )

    telemetry_entries = _validate_telemetry_jsonl(TELEMETRY_JSONL, telemetry_validator, feature_ids)
    _validate_weekly_reviews_json(WEEKLY_REVIEWS_JSON, weekly_reviews_validator, feature_ids)
    _validate_scorecard_json(SCORECARD_JSON, scorecard_validator)
    _assert_scorecard_synced(SCORECARD_JSON, build_scorecard_payload(ROOT))
    _assert_scorecard_markdown_synced(SCORECARD_MARKDOWN, build_scorecard_markdown_section(build_scorecard_payload(ROOT)))
    _validate_weekly_eval_json(WEEKLY_EVAL_JSON, weekly_eval_validator)
    _assert_weekly_eval_synced(WEEKLY_EVAL_JSON, build_weekly_eval_payload(ROOT, days=7))
    _assert_weekly_eval_markdown_synced(WEEKLY_EVAL_MARKDOWN, build_weekly_eval_markdown(build_weekly_eval_payload(ROOT, days=7)))

    summary = {
        "status": "ok",
        "features": len(features),
        "validated": sum(1 for feature in features if feature["status"] == "validated"),
        "active": sum(1 for feature in features if feature["status"] == "active"),
        "backlog": sum(1 for feature in features if feature["status"] == "backlog"),
        "telemetry_entries": telemetry_entries,
    }
    print(json.dumps(summary, ensure_ascii=False))
    return 0


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected object at {path}")
    return cast(dict[str, Any], payload)


def _feature_list(payload: dict[str, Any]) -> list[dict[str, Any]]:
    raw_features = payload.get("features")
    if not isinstance(raw_features, list):
        raise ValueError("feature spine must contain a list in features")
    return [cast(dict[str, Any], feature) for feature in raw_features]


def _assert_paths_exist(paths: Sequence[str], label: str) -> None:
    for relative_path in paths:
        target = ROOT / relative_path
        if not target.exists():
            _fail(
                f"missing path in {label}: {relative_path}",
                "Feature spine owner_docs and evidence must point to files that a fresh agent can actually inspect.",
                f"Restore {relative_path} or update the corresponding entry in docs/agent-feature-spine.json, then rerun `{VALIDATE_COMMAND}`.",
            )


def _assert_markers(path: Path, markers: Sequence[str]) -> None:
    text = path.read_text(encoding="utf-8")
    for marker in markers:
        if marker not in text:
            _fail(
                f"missing marker in {path.relative_to(ROOT)}: {marker}",
                "Marker-based checks keep task-flow documents tied to feature traceability and generated companions.",
                f"Restore the missing marker or update REQUIRED_DOC_MARKERS in scripts/validate_harness_assets.py if the contract intentionally changed, then rerun `{VALIDATE_COMMAND}`.",
            )


def _validate_telemetry_jsonl(
    path: Path,
    validator: Any,
    known_feature_ids: set[str],
) -> int:
    if not path.exists():
        _fail(
            f"missing telemetry file: {path.relative_to(ROOT)}",
            "Structured telemetry is the machine-readable evidence layer for validation, state hygiene and feature traceability.",
            f"Restore {path.relative_to(ROOT)} or recreate it from recent task records, then rerun `{VALIDATE_COMMAND}`.",
        )

    count = 0
    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        count += 1
        payload = json.loads(line)
        entry = cast(dict[str, Any], payload)

        errors = sorted(validator.iter_errors(entry), key=lambda error: list(error.absolute_path))
        if errors:
            details = []
            for error in errors:
                error_path = ".".join(str(part) for part in error.absolute_path) or "<root>"
                details.append(f"line {index} {error_path}: {error.message}")
            _fail(
                "telemetry schema validation failed: " + "; ".join(details),
                "Telemetry rows must stay schema-valid so scorecard and weekly eval generation can consume them deterministically.",
                f"Edit docs/agent-telemetry.v1.jsonl to satisfy schemas/agent-telemetry-entry.v1.schema.json, then rerun `{VALIDATE_COMMAND}`.",
            )

        for feature_id in cast(list[str], entry["feature_ids"]):
            if feature_id not in known_feature_ids:
                _fail(
                    f"unknown feature_id in telemetry line {index}: {feature_id}",
                    "Telemetry can only reference feature IDs declared in docs/agent-feature-spine.json.",
                    f"Add `{feature_id}` to the feature spine or correct the telemetry row, then rerun `{VALIDATE_COMMAND}`.",
                )

    if count == 0:
        _fail(
            f"telemetry file has no entries: {path.relative_to(ROOT)}",
            "An empty telemetry companion makes the generated scorecard and weekly eval blind to actual task evidence.",
            f"Add at least one schema-valid telemetry row with feature_ids and validation evidence, then rerun `{VALIDATE_COMMAND}`.",
        )

    return count


def _validate_weekly_reviews_json(path: Path, validator: Any, known_feature_ids: set[str]) -> None:
    if not path.exists():
        _fail(
            f"missing weekly reviews file: {path.relative_to(ROOT)}",
            "Machine-readable sampled reviews keep qualitative weekly evidence separate from generated markdown narrative.",
            f"Restore {path.relative_to(ROOT)} with schema-valid sampled review data, then rerun `{VALIDATE_COMMAND}`.",
        )

    payload = _load_json(path)
    errors = sorted(validator.iter_errors(payload), key=lambda error: list(error.absolute_path))
    if errors:
        details = []
        for error in errors:
            error_path = ".".join(str(part) for part in error.absolute_path) or "<root>"
            details.append(f"{error_path}: {error.message}")
        _fail(
            "weekly reviews schema validation failed: " + "; ".join(details),
            "Weekly review scores feed the generated weekly eval and must remain machine-readable.",
            f"Edit docs/agent-weekly-reviews.v1.json to satisfy schemas/agent-weekly-reviews.v1.schema.json, then rerun `{VALIDATE_COMMAND}`.",
        )

    for review in cast(list[dict[str, Any]], payload["reviews"]):
        for task in cast(list[dict[str, Any]], review["sampled_tasks"]):
            scores = cast(dict[str, Any], task["scores"])
            computed_total = sum(cast(int, scores[key]) for key in RUBRIC_SCORE_KEYS)
            total_score = cast(int, task["total_score"])
            if total_score != computed_total:
                _fail(
                    f"weekly reviews total_score mismatch in {path.relative_to(ROOT)} for {review['review_id']}::{task['task']}: {total_score} != {computed_total}",
                    "The total_score must equal the rubric dimension sum or qualitative sampling becomes misleading.",
                    f"Recompute total_score for the task or fix the dimension scores, then rerun `{WEEKLY_REFRESH_COMMAND}` and `{VALIDATE_COMMAND}`.",
                )

            for feature_id in cast(list[str], task["feature_ids"]):
                if feature_id not in known_feature_ids:
                    _fail(
                        f"unknown feature_id in weekly reviews {review['review_id']}::{task['task']}: {feature_id}",
                        "Sampled weekly reviews must reference feature IDs declared in the feature spine.",
                        f"Add `{feature_id}` to docs/agent-feature-spine.json or correct the review entry, then rerun `{WEEKLY_REFRESH_COMMAND}` and `{VALIDATE_COMMAND}`.",
                    )


def _validate_scorecard_json(path: Path, validator: Any) -> None:
    if not path.exists():
        _fail(
            f"missing scorecard file: {path.relative_to(ROOT)}",
            "The generated scorecard companion is the structured bridge from telemetry to weekly eval.",
            f"Regenerate it with `{SCORECARD_SYNC_COMMAND}`, then rerun `{VALIDATE_COMMAND}`.",
        )

    payload = _load_json(path)
    errors = sorted(validator.iter_errors(payload), key=lambda error: list(error.absolute_path))
    if errors:
        details = []
        for error in errors:
            error_path = ".".join(str(part) for part in error.absolute_path) or "<root>"
            details.append(f"{error_path}: {error.message}")
        _fail(
            "scorecard schema validation failed: " + "; ".join(details),
            "The scorecard JSON must match its schema before markdown and weekly eval drift can be checked.",
            f"Regenerate with `{SCORECARD_SYNC_COMMAND}` or edit docs/agent-quality-scorecard.v1.json to satisfy schemas/agent-quality-scorecard.v1.schema.json, then rerun `{VALIDATE_COMMAND}`.",
        )


def _assert_scorecard_synced(path: Path, expected_payload: dict[str, Any]) -> None:
    current_payload = _load_json(path)
    if current_payload != expected_payload:
        _fail(
            f"scorecard drift detected: {path.relative_to(ROOT)}",
            "The generated scorecard no longer matches docs/agent-telemetry.v1.jsonl and docs/agent-feature-spine.json.",
            f"Regenerate the scorecard with `{SCORECARD_SYNC_COMMAND}`, then rerun `{VALIDATE_COMMAND}`.",
        )


def _assert_scorecard_markdown_synced(path: Path, expected_section: str) -> None:
    if not path.exists():
        _fail(
            f"missing scorecard markdown: {path.relative_to(ROOT)}",
            "The human-readable scorecard is the operator-facing view of generated quality signals.",
            f"Restore {path.relative_to(ROOT)} or regenerate its structured section with `{SCORECARD_SYNC_COMMAND}`, then rerun `{VALIDATE_COMMAND}`.",
        )

    text = path.read_text(encoding="utf-8")
    start = text.find("## 9. Structured companion")
    if start == -1:
        _fail(
            f"missing structured companion section: {path.relative_to(ROOT)}",
            "The markdown scorecard must expose the generated structured companion section for human review.",
            f"Restore section `## 9. Structured companion` or run `{SCORECARD_SYNC_COMMAND}`, then rerun `{VALIDATE_COMMAND}`.",
        )
    next_heading = text.find("\n## ", start + len("## 9. Structured companion"))
    if next_heading == -1:
        next_heading = len(text)
    current_section = text[start:next_heading].strip() + "\n"
    if current_section != expected_section:
        _fail(
            f"scorecard markdown drift detected: {path.relative_to(ROOT)}",
            "The human-readable structured companion section no longer matches the generated scorecard payload.",
            f"Run `{SCORECARD_SYNC_COMMAND}` to refresh markdown, then rerun `{VALIDATE_COMMAND}`.",
        )


def _validate_weekly_eval_json(path: Path, validator: Any) -> None:
    if not path.exists():
        _fail(
            f"missing weekly eval file: {path.relative_to(ROOT)}",
            "The generated weekly eval JSON is the machine-readable weekly health snapshot.",
            f"Regenerate it with `{WEEKLY_REFRESH_COMMAND}`, then rerun `{VALIDATE_COMMAND}`.",
        )

    payload = _load_json(path)
    errors = sorted(validator.iter_errors(payload), key=lambda error: list(error.absolute_path))
    if errors:
        details = []
        for error in errors:
            error_path = ".".join(str(part) for part in error.absolute_path) or "<root>"
            details.append(f"{error_path}: {error.message}")
        _fail(
            "weekly eval schema validation failed: " + "; ".join(details),
            "The weekly eval JSON must be schema-valid before it can serve as a reliable operational snapshot.",
            f"Regenerate with `{WEEKLY_REFRESH_COMMAND}` or edit docs/agent-weekly-eval.v1.json to satisfy schemas/agent-weekly-eval.v1.schema.json, then rerun `{VALIDATE_COMMAND}`.",
        )


def _assert_weekly_eval_synced(path: Path, expected_payload: dict[str, Any]) -> None:
    current_payload = _load_json(path)
    if current_payload != expected_payload:
        _fail(
            f"weekly eval drift detected: {path.relative_to(ROOT)}",
            "The generated weekly eval no longer matches the scorecard, telemetry and sampled weekly reviews.",
            f"Run `{WEEKLY_REFRESH_COMMAND}`, then rerun `{VALIDATE_COMMAND}`.",
        )


def _assert_weekly_eval_markdown_synced(path: Path, expected_markdown: str) -> None:
    if not path.exists():
        _fail(
            f"missing weekly eval markdown: {path.relative_to(ROOT)}",
            "The markdown weekly eval is the human-readable companion to the generated JSON snapshot.",
            f"Regenerate it with `{WEEKLY_REFRESH_COMMAND}`, then rerun `{VALIDATE_COMMAND}`.",
        )

    current_markdown = path.read_text(encoding="utf-8")
    if current_markdown != expected_markdown:
        _fail(
            f"weekly eval markdown drift detected: {path.relative_to(ROOT)}",
            "The human-readable weekly eval no longer matches the generated JSON snapshot.",
            f"Run `{WEEKLY_REFRESH_COMMAND}`, then rerun `{VALIDATE_COMMAND}`.",
        )


if __name__ == "__main__":
    raise SystemExit(main())