from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_COMMAND = ".\\.venv\\Scripts\\python.exe scripts\\validate_harness_assets.py"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a compact handoff summary for the next chat/session.")
    parser.add_argument("--task", help="Optional task label override. Defaults to the latest telemetry task.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable markdown.")
    parser.add_argument("--skip-validator", action="store_true", help="Do not run validate_harness_assets.py while building the handoff.")
    args = parser.parse_args(argv)

    validator_summary = None if args.skip_validator else run_validator(ROOT)
    payload = build_handoff_payload(ROOT, task_override=args.task, validator_summary=validator_summary)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(format_handoff(payload))
    return 0


def build_handoff_payload(
    root: Path,
    *,
    task_override: str | None = None,
    validator_summary: dict[str, Any] | None = None,
    changed_files: list[str] | None = None,
    latest_telemetry_entry: dict[str, Any] | None = None,
    state_snapshot_text: str | None = None,
) -> dict[str, Any]:
    snapshot_text = state_snapshot_text if state_snapshot_text is not None else (root / "docs" / "state-snapshot.md").read_text(encoding="utf-8")
    telemetry_entry = latest_telemetry_entry if latest_telemetry_entry is not None else load_latest_telemetry_entry(root / "docs" / "agent-telemetry.v1.jsonl")
    touched_surface = changed_files if changed_files is not None else get_changed_files(root)
    snapshot_info = parse_state_snapshot(snapshot_text)

    goal = task_override or cast_str(telemetry_entry.get("task"), default="Continue current working slice")
    current_anchor = choose_current_anchor(touched_surface, telemetry_entry)
    files_to_read = choose_files_to_read(current_anchor, touched_surface, telemetry_entry)
    checked = build_checked_items(telemetry_entry, validator_summary)
    remaining = build_remaining_items(snapshot_info, touched_surface, telemetry_entry, validator_summary)
    next_step = build_next_step(current_anchor, telemetry_entry, validator_summary, touched_surface)

    return {
        "goal": goal,
        "current_anchor": current_anchor,
        "current_outcome": cast_str(telemetry_entry.get("note"), default="No structured telemetry note available."),
        "checked": checked,
        "touched_surface": touched_surface or cast_list_of_str(telemetry_entry.get("touched_areas")),
        "validation_result": {
            "latest_task_result": cast_str(telemetry_entry.get("validation_result"), default="unknown"),
            "latest_validation_targets": cast_list_of_str(telemetry_entry.get("validation_targets"))[:3],
            "validator": validator_summary or {"status": "not-run", "command": VALIDATOR_COMMAND},
        },
        "blocker_or_residual_risk": remaining,
        "next_step": next_step,
        "approval_state": infer_approval_state(snapshot_info, validator_summary),
        "files_to_read_in_new_chat": files_to_read,
        "state_snapshot": snapshot_info,
        "sources": {
            "state_snapshot": "docs/state-snapshot.md",
            "telemetry_jsonl": "docs/agent-telemetry.v1.jsonl",
            "changed_files": touched_surface,
        },
    }


def format_handoff(payload: dict[str, Any]) -> str:
    validation_result = cast(dict[str, Any], payload["validation_result"])
    validator = cast(dict[str, Any], validation_result["validator"])
    lines = [
        "# Agent Handoff",
        "",
        f"Goal: {payload['goal']}",
        f"Current anchor: {payload['current_anchor']}",
        f"Approval state: {payload['approval_state']}",
        "",
        "## Current Outcome",
        "",
        str(payload["current_outcome"]),
        "",
        "## Checked",
        "",
    ]
    for item in cast(list[str], payload["checked"]):
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## Touched Surface",
        "",
    ])
    for item in cast(list[str], payload["touched_surface"]):
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## Validation",
        "",
        f"- latest task result: {validation_result['latest_task_result']};",
        f"- validator status: {validator['status']};",
    ])
    for target in cast(list[str], validation_result["latest_validation_targets"]):
        lines.append(f"- target: {target}")

    lines.extend([
        "",
        "## Remaining",
        "",
    ])
    for item in cast(list[str], payload["blocker_or_residual_risk"]):
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## Next Step",
        "",
        str(payload["next_step"]),
        "",
        "## Read Next",
        "",
    ])
    for item in cast(list[str], payload["files_to_read_in_new_chat"]):
        lines.append(f"- {item}")
    return "\n".join(lines)


def load_latest_telemetry_entry(path: Path) -> dict[str, Any]:
    for raw_line in reversed(path.read_text(encoding="utf-8").splitlines()):
        if not raw_line.strip():
            continue
        payload = json.loads(raw_line)
        if isinstance(payload, dict):
            return payload
    raise ValueError(f"telemetry file has no entries: {path}")


def get_changed_files(root: Path) -> list[str]:
    try:
        completed = subprocess.run(
            ["git", "status", "--short"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except OSError:
        return []
    if completed.returncode != 0:
        return []
    changed: list[str] = []
    for raw_line in completed.stdout.splitlines():
        if not raw_line.strip():
            continue
        changed.append(parse_git_status_path(raw_line))
    return changed


def parse_git_status_path(line: str) -> str:
    body = line[3:] if len(line) > 3 else line.strip()
    if " -> " in body:
        return body.split(" -> ", 1)[1].strip().replace("\\", "/")
    return body.strip().replace("\\", "/")


def parse_state_snapshot(text: str) -> dict[str, Any]:
    product = "unknown"
    blocker = "unknown"
    release_status = "unknown"
    validation_anchors: list[str] = []
    current_section = ""
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            current_section = line
            continue
        if line.startswith("- Продукт:"):
            product = line.split(":", 1)[1].strip().rstrip(".")
            continue
        if line.startswith("- Текущий blocker:"):
            blocker = line.split(":", 1)[1].strip().rstrip(".")
            continue
        if line.startswith("- Release status:"):
            release_status = line.split(":", 1)[1].strip().rstrip(".")
            continue
        if current_section == "## 6. Ближайшие validation anchors" and line and line[0].isdigit() and ". " in line:
            validation_anchors.append(line)
    return {
        "product": product,
        "blocker": blocker,
        "release_status": release_status,
        "validation_anchors": validation_anchors,
    }


def run_validator(root: Path) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            VALIDATOR_COMMAND.split(),
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except OSError as error:
        return {"status": "unavailable", "command": VALIDATOR_COMMAND, "detail": str(error)}

    detail = (completed.stdout or completed.stderr).strip()
    return {
        "status": "ok" if completed.returncode == 0 else "failed",
        "command": VALIDATOR_COMMAND,
        "detail": detail.splitlines()[-1] if detail else "",
    }


def choose_current_anchor(touched_surface: list[str], telemetry_entry: dict[str, Any]) -> str:
    if touched_surface:
        return touched_surface[0]
    touched_areas = cast_list_of_str(telemetry_entry.get("touched_areas"))
    if touched_areas:
        return touched_areas[0]
    return "docs/state-snapshot.md"


def choose_files_to_read(current_anchor: str, touched_surface: list[str], telemetry_entry: dict[str, Any]) -> list[str]:
    candidates = ["docs/state-snapshot.md", current_anchor, *touched_surface, *cast_list_of_str(telemetry_entry.get("touched_areas"))]
    files: list[str] = []
    for candidate in candidates:
        normalized = candidate.replace("\\", "/")
        if normalized in files:
            continue
        files.append(normalized)
        if len(files) >= 4:
            break
    return files


def build_checked_items(telemetry_entry: dict[str, Any], validator_summary: dict[str, Any] | None) -> list[str]:
    checked = []
    task = cast_str(telemetry_entry.get("task"), default="unknown task")
    validation_result = cast_str(telemetry_entry.get("validation_result"), default="unknown")
    checked.append(f"latest structured telemetry task: {task} ({validation_result})")
    note = cast_str(telemetry_entry.get("note"), default="")
    if note:
        checked.append(note)
    if validator_summary is not None:
        detail = cast_str(validator_summary.get("detail"), default="")
        checked.append(f"validator: {validator_summary['status']} {detail}".strip())
    return checked


def build_remaining_items(
    snapshot_info: dict[str, Any],
    touched_surface: list[str],
    telemetry_entry: dict[str, Any],
    validator_summary: dict[str, Any] | None,
) -> list[str]:
    remaining: list[str] = []
    blocker = cast_str(snapshot_info.get("blocker"), default="")
    release_status = cast_str(snapshot_info.get("release_status"), default="")
    if blocker and blocker != "unknown":
        remaining.append(blocker)
    if release_status and release_status != "unknown":
        remaining.append(release_status)
    if touched_surface:
        remaining.append(f"working tree still has {len(touched_surface)} changed paths")
    validation_result = cast_str(telemetry_entry.get("validation_result"), default="unknown")
    if validation_result not in {"passed", "passed_after_repair"}:
        remaining.append(f"latest validation result is {validation_result}")
    if validator_summary is not None and cast_str(validator_summary.get("status"), default="unknown") != "ok":
        remaining.append(f"validator status is {validator_summary['status']}")
    if not remaining:
        remaining.append("No explicit residual risk was inferred beyond the latest validated slice.")
    return remaining


def build_next_step(
    current_anchor: str,
    telemetry_entry: dict[str, Any],
    validator_summary: dict[str, Any] | None,
    touched_surface: list[str],
) -> str:
    validator_status = cast_str((validator_summary or {}).get("status"), default="not-run")
    if validator_status not in {"ok", "not-run"}:
        return f"Open {current_anchor}, repair validator drift and rerun {VALIDATOR_COMMAND}."
    latest_targets = cast_list_of_str(telemetry_entry.get("validation_targets"))
    if touched_surface and latest_targets:
        return f"Open {current_anchor}, continue the current slice and rerun the latest focused check: {latest_targets[0]}."
    if touched_surface:
        return f"Open {current_anchor} and continue the current local slice before widening scope."
    return f"Start from {current_anchor} and confirm the next focused validation target before any new edits."


def infer_approval_state(snapshot_info: dict[str, Any], validator_summary: dict[str, Any] | None) -> str:
    blocker = cast_str(snapshot_info.get("blocker"), default="").lower()
    release_status = cast_str(snapshot_info.get("release_status"), default="").lower()
    if "credential" in blocker or "approval" in blocker or "provider" in blocker:
        return "external approval or credentials still required"
    if validator_summary is not None and cast_str(validator_summary.get("status"), default="unknown") != "ok":
        return "blocked by local validation failure"
    if "blocked" in release_status:
        return "external gate or explicit approval may still apply"
    return "no explicit additional approval inferred"


def cast_list_of_str(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def cast_str(value: Any, *, default: str) -> str:
    return value if isinstance(value, str) else default


if __name__ == "__main__":
    raise SystemExit(main())