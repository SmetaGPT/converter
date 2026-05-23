# pyright: reportMissingTypeStubs=false

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, cast


ROOT = Path(__file__).resolve().parents[1]
FEATURE_SPINE = ROOT / "docs" / "agent-feature-spine.json"
TELEMETRY_JSONL = ROOT / "docs" / "agent-telemetry.v1.jsonl"
DEFAULT_OUTPUT = ROOT / "docs" / "agent-quality-scorecard.v1.json"
DEFAULT_MARKDOWN = ROOT / "docs" / "agent-quality-scorecard.md"
STRUCTURED_COMPANION_HEADING = "## 9. Structured companion"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build or check the machine-readable agent quality scorecard.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Path to the generated scorecard JSON file.")
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MARKDOWN, help="Path to the human-readable markdown scorecard.")
    parser.add_argument("--check", action="store_true", help="Fail if the output file does not match the generated payload.")
    parser.add_argument("--sync-markdown", action="store_true", help="Rewrite the structured companion section in markdown from the generated payload.")
    parser.add_argument("--check-markdown", action="store_true", help="Fail if the structured companion markdown section does not match the generated payload.")
    args = parser.parse_args(argv)

    output_path = args.output.expanduser().resolve()
    markdown_path = args.markdown.expanduser().resolve()
    payload = build_scorecard_payload(ROOT)
    markdown_section = build_scorecard_markdown_section(payload)
    status = "ok"

    if args.check:
        if not output_path.exists():
            print(json.dumps({"status": "missing", "path": str(output_path)}, ensure_ascii=False))
            return 1
        current = json.loads(output_path.read_text(encoding="utf-8"))
        if current != payload:
            print(json.dumps({"status": "drift", "path": str(output_path)}, ensure_ascii=False))
            return 1
    else:
        output_path.write_text(_dump_json(payload), encoding="utf-8", newline="\n")
        status = "written"

    if args.check_markdown:
        if not markdown_path.exists():
            print(json.dumps({"status": "missing-markdown", "path": str(markdown_path)}, ensure_ascii=False))
            return 1
        current_section = _extract_markdown_section(markdown_path.read_text(encoding="utf-8"))
        if current_section != markdown_section:
            print(json.dumps({"status": "markdown-drift", "path": str(markdown_path)}, ensure_ascii=False))
            return 1
    elif args.sync_markdown:
        _write_markdown_section(markdown_path, markdown_section)
        if status == "ok":
            status = "markdown-written"

    print(
        json.dumps(
            {
                "status": status,
                "path": str(output_path),
                "markdown_path": str(markdown_path),
            },
            ensure_ascii=False,
        )
    )
    return 0


def build_scorecard_payload(root: Path) -> dict[str, Any]:
    feature_spine = _load_json(root / "docs" / "agent-feature-spine.json")
    telemetry_entries = _load_jsonl(root / "docs" / "agent-telemetry.v1.jsonl")

    features = cast(list[dict[str, Any]], feature_spine["features"])
    feature_map = {cast(str, feature["feature_id"]): feature for feature in features}
    validated_features = [feature for feature in features if feature["status"] == "validated"]

    validation_results = Counter(cast(str, entry["validation_result"]) for entry in telemetry_entries)
    task_types = Counter(cast(str, entry["task_type"]) for entry in telemetry_entries)
    state_updates = sum(1 for entry in telemetry_entries if entry["state_update"] is True)
    feature_traceable_entries = sum(1 for entry in telemetry_entries if entry["feature_ids"])

    referenced_feature_ids = sorted({
        cast(str, feature_id)
        for entry in telemetry_entries
        for feature_id in cast(list[str], entry["feature_ids"])
    })

    referenced_areas = Counter(
        cast(str, feature_map[feature_id]["area"]) for feature_id in referenced_feature_ids if feature_id in feature_map
    )

    pass_like_entries = validation_results["passed"] + validation_results["passed_after_repair"]
    total_entries = len(telemetry_entries)
    known_feature_ratio = _score(len(referenced_feature_ids), len(validated_features))

    latest_date = max(
        [cast(str, feature_spine["last_updated"])] + [cast(str, entry["date"]) for entry in telemetry_entries]
    )

    payload = {
        "schema_version": "agent-quality-scorecard.v1",
        "as_of_date": latest_date,
        "sources": {
            "feature_spine": "docs/agent-feature-spine.json",
            "telemetry_jsonl": "docs/agent-telemetry.v1.jsonl",
            "scorecard_markdown": "docs/agent-quality-scorecard.md",
        },
        "telemetry_summary": {
            "total_entries": total_entries,
            "validation_results": {
                "passed": validation_results["passed"],
                "passed_after_repair": validation_results["passed_after_repair"],
                "failed": validation_results["failed"],
                "blocked": validation_results["blocked"],
            },
            "state_updates": state_updates,
            "feature_traceable_entries": feature_traceable_entries,
            "task_types": dict(sorted(task_types.items())),
        },
        "feature_summary": {
            "total_features": len(features),
            "validated_features": len(validated_features),
            "referenced_features": len(referenced_feature_ids),
            "referenced_feature_ids": referenced_feature_ids,
            "referenced_areas": dict(sorted(referenced_areas.items())),
        },
        "observed_signals": [
            {
                "signal_id": "validation-discipline",
                "title": "Validation discipline",
                "score": _score(pass_like_entries, total_entries),
                "scale_max": 5,
                "basis": f"{pass_like_entries}/{total_entries} telemetry entries have pass-like validation results.",
            },
            {
                "signal_id": "state-hygiene",
                "title": "State hygiene",
                "score": _score(state_updates, total_entries),
                "scale_max": 5,
                "basis": f"{state_updates}/{total_entries} telemetry entries report state_update=true.",
            },
            {
                "signal_id": "feature-traceability",
                "title": "Feature traceability",
                "score": _score(feature_traceable_entries, total_entries),
                "scale_max": 5,
                "basis": f"{feature_traceable_entries}/{total_entries} telemetry entries reference at least one feature_id.",
            },
            {
                "signal_id": "feature-coverage",
                "title": "Feature coverage in telemetry",
                "score": known_feature_ratio,
                "scale_max": 5,
                "basis": f"{len(referenced_feature_ids)}/{len(validated_features)} validated features are referenced by structured telemetry.",
            },
        ],
    }
    return payload


def build_scorecard_markdown_section(payload: dict[str, Any]) -> str:
    telemetry_summary = cast(dict[str, Any], payload["telemetry_summary"])
    feature_summary = cast(dict[str, Any], payload["feature_summary"])
    observed_signals = cast(list[dict[str, Any]], payload["observed_signals"])

    signal_labels = {
        "validation-discipline": "Validation",
        "state-hygiene": "State hygiene",
        "feature-traceability": "Feature traceability",
        "feature-coverage": "Feature coverage",
    }
    signal_summary = ", ".join(
        f"{signal_labels.get(cast(str, signal['signal_id']), cast(str, signal['title']))} {signal['score']}/{signal['scale_max']}"
        for signal in observed_signals
    )

    lines = [
        STRUCTURED_COMPANION_HEADING,
        "",
        "Machine-readable companion: `docs/agent-quality-scorecard.v1.json`.",
        "",
        "Текущий observed snapshot из structured telemetry:",
        "",
        f"- as_of_date: `{payload['as_of_date']}`;",
        f"- telemetry entries: `{telemetry_summary['total_entries']}`;",
        f"- validated features in spine: `{feature_summary['validated_features']}`;",
        f"- referenced features in telemetry: `{feature_summary['referenced_features']}`;",
        f"- observed signals: `{signal_summary}`.",
        "",
        "Этот companion не заменяет qualitative review и eval loop. Он нужен как быстрый machine-readable слой для weekly checks и CI-backed drift detection.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return cast(dict[str, Any], payload)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        entries.append(cast(dict[str, Any], json.loads(line)))
    return entries


def _score(value: int, total: int) -> int:
    if total <= 0:
        return 0
    return max(0, min(5, int(round(5 * value / total))))


def _dump_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def _extract_markdown_section(text: str) -> str:
    start = text.find(STRUCTURED_COMPANION_HEADING)
    if start == -1:
        raise ValueError(f"missing section heading: {STRUCTURED_COMPANION_HEADING}")
    next_heading = text.find("\n## ", start + len(STRUCTURED_COMPANION_HEADING))
    if next_heading == -1:
        next_heading = len(text)
    return text[start:next_heading].strip() + "\n"


def _write_markdown_section(path: Path, section_text: str) -> None:
    current = path.read_text(encoding="utf-8")
    start = current.find(STRUCTURED_COMPANION_HEADING)
    if start == -1:
        new_text = current.rstrip("\r\n") + "\n\n" + section_text.rstrip("\n") + "\n"
        path.write_text(new_text, encoding="utf-8", newline="\n")
        return

    next_heading = current.find("\n## ", start + len(STRUCTURED_COMPANION_HEADING))
    if next_heading == -1:
        next_heading = len(current)

    prefix = current[:start].rstrip("\r\n")
    suffix = current[next_heading:].lstrip("\r\n")

    parts = [prefix, section_text.rstrip("\n")]
    if suffix:
        parts.append(suffix.rstrip("\n"))
    new_text = "\n\n".join(part for part in parts if part) + "\n"
    path.write_text(new_text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    raise SystemExit(main())