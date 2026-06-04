from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = Path(__file__).resolve().parent
DEFAULT_EXCERPT_LINES = 40
WORKING_STATE = "docs/agent-working-state.v1.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Classify startup scope and print a rough startup budget in one step.")
    parser.add_argument("--task", required=True, help="Short natural-language task description.")
    parser.add_argument(
        "--anchor",
        action="append",
        default=[],
        help="Optional file, symbol, test or error anchor. Can be passed multiple times.",
    )
    parser.add_argument(
        "--excerpt-lines",
        type=int,
        default=DEFAULT_EXCERPT_LINES,
        help="Estimate file budget from the first N lines. Use 0 to count the full file.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable markdown.")
    args = parser.parse_args(argv)

    payload = build_preflight_payload(
        ROOT,
        task=args.task,
        anchors=[str(anchor) for anchor in args.anchor],
        excerpt_lines=max(0, int(args.excerpt_lines)),
    )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(format_preflight(payload))
    return 0


def build_preflight_payload(root: Path, *, task: str, anchors: list[str], excerpt_lines: int) -> dict[str, Any]:
    classifier_module = _load_script_module("classify_agent_scope", SCRIPTS_DIR / "classify_agent_scope.py")
    estimator_module = _load_script_module("estimate_context_tokens", SCRIPTS_DIR / "estimate_context_tokens.py")

    classify_scope = cast(Any, classifier_module.classify_scope)
    classification = cast(dict[str, Any], classify_scope(task, anchors))
    scope = cast(str, classification["scope"])

    existing_reads, skipped_reads = _partition_existing_files(root, cast(list[str], classification["first_reads"]))
    budget_payload = cast(
        dict[str, Any],
        estimator_module.build_report(
            root,
            path_specs=existing_reads,
            inline_texts=[task],
            include_startup_bundles=False,
            excerpt_lines=excerpt_lines,
        ),
    )

    reference_bundles = _reference_bundles(root, estimator_module, excerpt_lines, scope=scope)
    handoff_summary = _handoff_summary(root, scope=scope, anchors=anchors)
    startup_budget = {
        "excerpt_lines": excerpt_lines,
        "estimated_tokens": cast(dict[str, Any], budget_payload["summary"])["estimated_tokens"],
        "chars": cast(dict[str, Any], budget_payload["summary"])["chars"],
        "counted_reads": existing_reads,
        "skipped_reads": skipped_reads,
        "items": cast(list[dict[str, Any]], budget_payload["items"]),
    }

    return {
        "task": task,
        "anchors": anchors,
        "scope": scope,
        "reasons": classification["reasons"],
        "feature_id_required": classification["feature_id_required"],
        "first_reads": classification["first_reads"],
        "first_validation": classification["first_validation"],
        "state_strategy": classification["state_strategy"],
        "escalation_rules": classification["escalation_rules"],
        "startup_budget": startup_budget,
        "working_state": _working_state_summary(root),
        "reference_bundles": reference_bundles,
        "handoff_summary": handoff_summary,
    }


def format_preflight(payload: dict[str, Any]) -> str:
    startup_budget = cast(dict[str, Any], payload["startup_budget"])
    lines = [
        "# Agent Preflight",
        "",
        f"Task: {payload['task']}",
        f"Scope: {payload['scope']}",
        f"Feature ID required: {'yes' if payload['feature_id_required'] else 'no'}",
        f"First validation: {payload['first_validation']}",
        "",
        "## Startup Path",
        "",
    ]
    for index, read in enumerate(cast(list[str], payload["first_reads"]), start=1):
        lines.append(f"{index}. {read}")

    lines.extend([
        "",
        "## Why This Scope",
        "",
    ])
    for reason in cast(list[str], payload["reasons"]):
        lines.append(f"- {reason}")

    lines.extend([
        "",
        "## Rough Budget",
        "",
        f"- mode: {'full-file' if startup_budget['excerpt_lines'] == 0 else f'first {startup_budget['excerpt_lines']} lines'};",
        f"- estimated tokens: {startup_budget['estimated_tokens']};",
        f"- chars counted: {startup_budget['chars']};",
    ])
    if cast(list[str], startup_budget["counted_reads"]):
        lines.append(f"- counted reads: {', '.join(cast(list[str], startup_budget['counted_reads']))};")
    if cast(list[str], startup_budget["skipped_reads"]):
        lines.append(f"- skipped non-file reads: {', '.join(cast(list[str], startup_budget['skipped_reads']))};")

    working_state = cast(dict[str, Any] | None, payload.get("working_state"))
    if working_state is not None:
        lines.extend([
            "",
            "## Working State",
            "",
            f"- current goal: {working_state['current_goal']};",
            f"- active feature IDs: {', '.join(cast(list[str], working_state['active_feature_ids']))};",
        ])
        for item in cast(list[str], working_state["next"])[:2]:
            lines.append(f"- next: {item}")

    reference_bundles = cast(list[dict[str, Any]], payload["reference_bundles"])
    if reference_bundles:
        lines.extend([
            "",
            "## Reference Bundles",
            "",
        ])
        for bundle in reference_bundles:
            lines.append(f"- {bundle['label']}: {bundle['estimated_tokens']} tokens ({bundle['mode']}).")

    handoff_summary = cast(dict[str, Any] | None, payload.get("handoff_summary"))
    if handoff_summary is not None:
        lines.extend([
            "",
            "## Handoff",
            "",
            f"- goal: {handoff_summary['goal']};",
            f"- current anchor: {handoff_summary['current_anchor']};",
            f"- next step: {handoff_summary['next_step']};",
        ])

    return "\n".join(lines)


def _partition_existing_files(root: Path, reads: list[str]) -> tuple[list[str], list[str]]:
    existing: list[str] = []
    skipped: list[str] = []
    for read in reads:
        candidate = Path(read)
        if not candidate.is_absolute():
            candidate = root / candidate
        if candidate.exists() and candidate.is_file():
            existing.append(read)
            continue
        skipped.append(read)
    return existing, skipped


def _reference_bundles(root: Path, estimator_module: Any, excerpt_lines: int, *, scope: str) -> list[dict[str, Any]]:
    if scope == "local-fast-path":
        return []
    default_startup_files = cast(list[str], estimator_module.DEFAULT_STARTUP_FILES)
    full_state_extra_files = cast(list[str], estimator_module.FULL_STATE_EXTRA_FILES)
    required_files = [*default_startup_files, *full_state_extra_files]
    if not all((root / relative_path).exists() for relative_path in required_files):
        return []
    payload = cast(
        dict[str, Any],
        estimator_module.build_report(
            root,
            path_specs=[],
            inline_texts=[],
            include_startup_bundles=True,
            excerpt_lines=excerpt_lines,
        ),
    )
    return cast(list[dict[str, Any]], payload["bundles"])


def _working_state_summary(root: Path) -> dict[str, Any] | None:
    path = root / WORKING_STATE
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return None
    return {
        "current_goal": payload.get("current_goal", "unknown"),
        "current_status": payload.get("current_status", "unknown"),
        "active_feature_ids": payload.get("active_feature_ids", []),
        "next": payload.get("next", []),
        "blockers": payload.get("blockers", []),
        "validation_targets": payload.get("validation_targets", []),
    }


def _handoff_summary(root: Path, *, scope: str, anchors: list[str]) -> dict[str, Any] | None:
    if scope == "local-fast-path":
        return None
    state_snapshot = root / "docs" / "state-snapshot.md"
    telemetry = root / "docs" / "agent-telemetry.v1.jsonl"
    if not state_snapshot.exists() or not telemetry.exists():
        return None
    handoff_module = _load_script_module("build_agent_handoff", SCRIPTS_DIR / "build_agent_handoff.py")
    anchored_surface = [anchor for anchor in anchors if anchor != WORKING_STATE]
    return cast(
        dict[str, Any],
        handoff_module.build_handoff_payload(root, validator_summary=None, changed_files=anchored_surface or None),
    )


def _load_script_module(module_name: str, file_path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    raise SystemExit(main())
