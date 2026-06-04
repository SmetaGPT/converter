from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "docs" / "agent-working-state.v1.json"
SOURCES = [
    "docs/state-snapshot.md",
    "docs/agent-telemetry.v1.jsonl",
    "docs/agent-feature-spine.json",
]
MAX_TEXT_CHARS = 140
MAX_TARGET_CHARS = 120


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build or check the compact generated agent working-state companion.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Path to the generated JSON working state.")
    parser.add_argument("--check", action="store_true", help="Fail if the working-state file drifts from current sources.")
    args = parser.parse_args(argv)

    output_path = args.output.expanduser().resolve()
    payload = build_working_state_payload(ROOT)
    expected_json = dump_working_state_json(payload)
    status = "ok"

    if args.check:
        if not output_path.exists():
            print(json.dumps({"status": "missing", "path": str(output_path)}, ensure_ascii=False))
            return 1
        if output_path.read_text(encoding="utf-8") != expected_json:
            print(json.dumps({"status": "drift", "path": str(output_path)}, ensure_ascii=False))
            return 1
    else:
        output_path.write_text(expected_json, encoding="utf-8", newline="\n")
        status = "written"

    print(json.dumps({"status": status, "path": str(output_path), "sources": SOURCES}, ensure_ascii=False))
    return 0


def build_working_state_payload(root: Path) -> dict[str, Any]:
    snapshot_text = (root / "docs" / "state-snapshot.md").read_text(encoding="utf-8")
    telemetry_entry = _load_latest_telemetry_entry(root / "docs" / "agent-telemetry.v1.jsonl")
    feature_spine = _load_json(root / "docs" / "agent-feature-spine.json")
    snapshot = _parse_state_snapshot(snapshot_text)

    latest_targets = _cast_list_of_str(telemetry_entry.get("validation_targets"))
    raw_validation_targets = [*latest_targets[:2], *_cast_list_of_str(snapshot.get("validation_anchors"))[:3]]
    validation_targets = _dedupe([_compact(item, MAX_TARGET_CHARS) for item in raw_validation_targets])
    active_feature_ids = _dedupe([*_active_feature_ids(feature_spine), *_cast_list_of_str(telemetry_entry.get("feature_ids"))[:5]])
    blockers = _dedupe(_snapshot_blockers(snapshot))
    next_items = _dedupe([*validation_targets[:2], "Read raw state docs only when the task is release/resume/cross-module or the local route is ambiguous."])

    return {
        "schema_version": "agent-working-state.v1",
        "last_updated": _latest_date(cast(str | None, feature_spine.get("last_updated")), cast(str | None, telemetry_entry.get("date"))),
        "current_goal": _cast_str(telemetry_entry.get("task"), default="Continue the current validated slice."),
        "current_status": _compact(_cast_str(snapshot.get("release_status"), default="unknown"), MAX_TEXT_CHARS),
        "active_feature_ids": active_feature_ids,
        "done_latest": [_compact(_cast_str(telemetry_entry.get("note"), default="No latest telemetry note available."), MAX_TEXT_CHARS)],
        "next": next_items,
        "blockers": blockers,
        "validation_targets": validation_targets,
        "memory_tiers": {
            "hot": "docs/agent-working-state.v1.json",
            "snapshot": "docs/state-snapshot.md when scope widens",
            "state": "grep exact section in current-status/current-sprint/release-status",
            "archive": "query telemetry/spine/memory by feature_id or task anchor",
        },
        "token_budget_policy": {
            "local_fast_path": "anchor-first; no state unless route widens",
            "cross_module": "hot+snapshot; grep feature_id before long docs",
            "release_or_resume": "hot+snapshot+targeted full-state sections",
        },
        "sources": SOURCES,
    }


def dump_working_state_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object in {path}")
    return cast(dict[str, Any], payload)


def _load_latest_telemetry_entry(path: Path) -> dict[str, Any]:
    for raw_line in reversed(path.read_text(encoding="utf-8").splitlines()):
        if not raw_line.strip():
            continue
        payload = json.loads(raw_line)
        if isinstance(payload, dict):
            return cast(dict[str, Any], payload)
    raise ValueError(f"telemetry file has no entries: {path}")


def _parse_state_snapshot(text: str) -> dict[str, Any]:
    release_status = "unknown"
    blocker = "unknown"
    validation_anchors: list[str] = []
    current_section = ""
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            current_section = line
            continue
        if line.startswith("- Текущий blocker:"):
            blocker = line.split(":", 1)[1].strip().rstrip(".")
            continue
        if line.startswith("- Release status:"):
            release_status = line.split(":", 1)[1].strip().rstrip(".")
            continue
        if current_section == "## 6. Ближайшие validation anchors" and line and line[0].isdigit() and ". " in line:
            validation_anchors.append(line)
    return {"release_status": release_status, "blocker": blocker, "validation_anchors": validation_anchors}


def _active_feature_ids(feature_spine: dict[str, Any]) -> list[str]:
    features = feature_spine.get("features")
    if not isinstance(features, list):
        return []
    active: list[str] = []
    for feature in features:
        if not isinstance(feature, dict) or feature.get("status") != "active":
            continue
        feature_id = feature.get("feature_id")
        if isinstance(feature_id, str):
            active.append(feature_id)
    return active


def _snapshot_blockers(snapshot: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    blocker = _cast_str(snapshot.get("blocker"), default="")
    release_status = _cast_str(snapshot.get("release_status"), default="")
    if blocker and blocker != "unknown":
        blockers.append(_compact(blocker, MAX_TEXT_CHARS))
    if "blocked" in release_status.lower():
        blockers.append(_compact(release_status, MAX_TEXT_CHARS))
    return blockers


def _latest_date(*raw_dates: str | None) -> str:
    dates = sorted(value for value in raw_dates if value)
    return dates[-1] if dates else "1970-01-01"


def _dedupe(items: list[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        normalized = item.strip()
        if not normalized or normalized in result:
            continue
        result.append(normalized)
    return result


def _compact(value: str, max_chars: int) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= max_chars:
        return normalized
    return normalized[: max(1, max_chars - 1)].rstrip(" .,;:") + "…"


def _cast_list_of_str(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _cast_str(value: Any, *, default: str) -> str:
    return value if isinstance(value, str) and value else default


if __name__ == "__main__":
    raise SystemExit(main())
