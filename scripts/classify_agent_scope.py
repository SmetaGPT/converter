from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
WORKING_STATE = "docs/agent-working-state.v1.json"
STATE_SNAPSHOT = "docs/state-snapshot.md"
FULL_STATE_DOCS = [
    "docs/current-status.md",
    "docs/current-sprint.md",
    "docs/release-status.md",
]
FAST_PATH_ESCALATION_RULES = [
    "задача продолжает незавершённую работу или явно просит resume/handoff",
    "задача меняет state/release/process docs или harness assets",
    "локальный маршрут показал, что изменение реально cross-module",
    "validation target зависит от текущего sprint/release blocker",
]
RESUME_KEYWORDS = (
    "resume",
    "resuming",
    "handoff",
    "checkpoint",
    "continue",
    "continuation",
    "продолж",
    "возобнов",
    "вчера",
    "незаверш",
)
STRONG_RELEASE_KEYWORDS = (
    "nightly",
    "workflow",
    "github actions",
    "ci",
    "tag",
    "merge",
    "pull request",
    "pr ",
    "релиз",
    "тег",
    "публикац",
    "выкладк",
)
WEAK_RELEASE_KEYWORDS = (
    "release",
)
CROSS_MODULE_KEYWORDS = (
    "cross-module",
    "cross module",
    "multi-file",
    "multi file",
    "архитектур",
    "refactor",
    "рефактор",
    "process layer",
    "state layer",
    "feature spine",
    "несколько модул",
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Classify agent task scope for fast-path vs full state startup.")
    parser.add_argument("--task", required=True, help="Short natural-language task description.")
    parser.add_argument(
        "--anchor",
        action="append",
        default=[],
        help="Optional file, symbol, test or error anchor. Can be passed multiple times.",
    )
    args = parser.parse_args(argv)

    normalized_anchors = _normalize_anchors(args.anchor)
    payload = classify_scope(args.task, normalized_anchors)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def classify_scope(task: str, anchors: list[str]) -> dict[str, object]:
    lowered_task = task.lower()
    anchor_roles = [_anchor_role(anchor) for anchor in anchors]
    unique_roles = sorted(set(anchor_roles))
    reasons: list[str] = []

    if _contains_any(lowered_task, RESUME_KEYWORDS):
        scope = "resume"
        reasons.append("task text contains resume/continuation markers")
    elif _is_release_task(lowered_task, anchors, anchor_roles):
        scope = "release"
        reasons.append("task looks related to CI/release/workflow surface")
    elif _is_cross_module_task(lowered_task, anchors, anchor_roles):
        scope = "cross-module"
        reasons.append("task touches multiple areas or explicit architecture/process signals")
    else:
        scope = "local-fast-path"
        if anchors:
            reasons.append("single local anchor is sufficient for a narrow start")
        else:
            reasons.append("no broad state or release signals detected")

    if anchors:
        reasons.append("anchor roles: " + ", ".join(unique_roles))

    feature_id_required = scope in {"resume", "release", "cross-module"} or any(role == "process" for role in anchor_roles)
    first_validation = _first_validation_target(anchors, anchor_roles, scope)
    first_reads = _first_reads(scope, anchors)
    state_strategy = _state_strategy(scope)

    return {
        "scope": scope,
        "task": task,
        "anchors": anchors,
        "reasons": reasons,
        "state_strategy": state_strategy,
        "first_reads": first_reads,
        "feature_id_required": feature_id_required,
        "first_validation": first_validation,
        "escalation_rules": FAST_PATH_ESCALATION_RULES,
    }


def _normalize_anchors(raw_anchors: list[str]) -> list[str]:
    normalized: list[str] = []
    for raw_anchor in raw_anchors:
        candidate = raw_anchor.strip()
        if not candidate:
            continue
        normalized.append(candidate.replace("\\", "/"))
    return normalized


def _anchor_role(anchor: str) -> str:
    path = PurePosixPath(anchor)
    anchor_lower = anchor.lower()
    if anchor_lower.startswith("docs/") or anchor_lower == "agents.md":
        return "process"
    if anchor_lower.startswith(".github/"):
        if "/workflows/" in anchor_lower:
            return "release"
        return "process"
    if anchor_lower.startswith("tests/"):
        return "test"
    if anchor_lower.startswith("src/"):
        return "code"
    if anchor_lower.startswith("scripts/"):
        return "script"
    if path.suffix in {".md", ".json", ".jsonl", ".yml", ".yaml"}:
        return "process"
    return "unknown"


def _contains_any(haystack: str, needles: tuple[str, ...]) -> bool:
    return any(needle in haystack for needle in needles)


def _is_release_task(lowered_task: str, anchors: list[str], anchor_roles: list[str]) -> bool:
    if _contains_any(lowered_task, STRONG_RELEASE_KEYWORDS):
        return True
    if _contains_any(lowered_task, WEAK_RELEASE_KEYWORDS) and not any(role in {"test", "code"} for role in anchor_roles):
        return True
    return any(role == "release" for role in anchor_roles) or any(anchor.lower().startswith("docs/release-status.md") for anchor in anchors)


def _is_cross_module_task(lowered_task: str, anchors: list[str], anchor_roles: list[str]) -> bool:
    if _contains_any(lowered_task, CROSS_MODULE_KEYWORDS):
        return True
    if any(role == "process" for role in anchor_roles):
        return True
    return len(set(anchor_roles)) >= 2 and len(anchors) >= 2


def _state_strategy(scope: str) -> dict[str, object]:
    if scope == "local-fast-path":
        return {
            "mode": "fast-path",
            "read_working_state_first": False,
            "read_snapshot_first": False,
            "read_full_state": False,
            "entry_docs": [],
        }
    if scope == "cross-module":
        return {
            "mode": "hot-state-then-snapshot",
            "read_working_state_first": True,
            "read_snapshot_first": True,
            "read_full_state": False,
            "entry_docs": [WORKING_STATE, STATE_SNAPSHOT],
        }
    return {
        "mode": "hot-state-then-full-state",
        "read_working_state_first": True,
        "read_snapshot_first": True,
        "read_full_state": True,
        "entry_docs": [WORKING_STATE, STATE_SNAPSHOT, *FULL_STATE_DOCS],
    }


def _first_reads(scope: str, anchors: list[str]) -> list[str]:
    reads: list[str] = []
    if scope == "local-fast-path":
        return anchors[:2]
    reads.append(WORKING_STATE)
    reads.append(STATE_SNAPSHOT)
    if scope in {"resume", "release"}:
        reads.extend(FULL_STATE_DOCS)
    reads.extend(anchor for anchor in anchors[:2] if anchor not in reads)
    return reads


def _first_validation_target(anchors: list[str], anchor_roles: list[str], scope: str) -> str:
    test_target = _first_test_target(anchors)
    if test_target is not None:
        return test_target

    if scope in {"resume", "release", "cross-module"} or any(role == "process" for role in anchor_roles):
        return ".\\.venv\\Scripts\\python.exe scripts\\validate_harness_assets.py"

    code_anchor = _first_anchor_with_role(anchors, anchor_roles, "code")
    if code_anchor is not None:
        return f".\\.venv\\Scripts\\python.exe -m pyright {code_anchor.replace('/', '\\')}"

    script_anchor = _first_anchor_with_role(anchors, anchor_roles, "script")
    if script_anchor is not None:
        return f".\\.venv\\Scripts\\python.exe -m pyright {script_anchor.replace('/', '\\')}"

    return ".\\.venv\\Scripts\\python.exe scripts\\validate_harness_assets.py"


def _first_test_target(anchors: list[str]) -> str | None:
    for anchor in anchors:
        anchor_lower = anchor.lower()
        if not anchor_lower.startswith("tests/") or not anchor_lower.endswith(".py"):
            continue
        module = anchor[:-3].replace("/", ".")
        return f".\\.venv\\Scripts\\python.exe -m unittest {module} -v"
    return None


def _first_anchor_with_role(anchors: list[str], anchor_roles: list[str], role: str) -> str | None:
    for anchor, current_role in zip(anchors, anchor_roles, strict=True):
        if current_role == role:
            return anchor
    return None


if __name__ == "__main__":
    raise SystemExit(main())
