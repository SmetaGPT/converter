from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[1]
CURRENT_STATUS = ROOT / "docs" / "current-status.md"
CURRENT_SPRINT = ROOT / "docs" / "current-sprint.md"
RELEASE_STATUS = ROOT / "docs" / "release-status.md"
FEATURE_SPINE = ROOT / "docs" / "agent-feature-spine.json"
DEFAULT_OUTPUT = ROOT / "docs" / "state-snapshot.md"
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build or check the generated state snapshot entry point.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Path to the generated markdown snapshot.")
    parser.add_argument("--check", action="store_true", help="Fail if the snapshot file drifts from current sources.")
    args = parser.parse_args(argv)

    output_path = args.output.expanduser().resolve()
    payload = build_state_snapshot_payload(ROOT)
    markdown = build_state_snapshot_markdown(payload)
    status = "ok"

    if args.check:
        if not output_path.exists():
            print(json.dumps({"status": "missing", "path": str(output_path)}, ensure_ascii=False))
            return 1
        current = output_path.read_text(encoding="utf-8")
        if current != markdown:
            print(json.dumps({"status": "drift", "path": str(output_path)}, ensure_ascii=False))
            return 1
    else:
        output_path.write_text(markdown, encoding="utf-8", newline="\n")
        status = "written"

    print(
        json.dumps(
            {
                "status": status,
                "path": str(output_path),
                "sources": [
                    str(CURRENT_STATUS.relative_to(ROOT)),
                    str(CURRENT_SPRINT.relative_to(ROOT)),
                    str(RELEASE_STATUS.relative_to(ROOT)),
                    str(FEATURE_SPINE.relative_to(ROOT)),
                ],
            },
            ensure_ascii=False,
        )
    )
    return 0


def build_state_snapshot_payload(root: Path) -> dict[str, Any]:
    current_status_text = (root / "docs" / "current-status.md").read_text(encoding="utf-8")
    current_sprint_text = (root / "docs" / "current-sprint.md").read_text(encoding="utf-8")
    release_status_text = (root / "docs" / "release-status.md").read_text(encoding="utf-8")
    feature_spine = _load_json(root / "docs" / "agent-feature-spine.json")

    current_status_meta = _parse_front_matter(current_status_text)
    current_sprint_meta = _parse_front_matter(current_sprint_text)
    release_status_meta = _parse_front_matter(release_status_text)
    feature_map = _feature_map(feature_spine)

    validation_anchors = _ordered_items_in_section(current_sprint_text, "## 4. Validation targets текущего состояния")
    active_gate = cast(str, current_sprint_meta.get("Активный спринт") or current_status_meta.get("Статус контура") or "не определён")
    blocker = _first_bullet_in_section(current_sprint_text, "## 5. Риски и blocker")
    release_status = cast(str, release_status_meta.get("Статус") or "не определён")
    product_line = cast(str, release_status_meta.get("Релизный контур") or "не определён")
    latest_update = _latest_date(
        cast(str | None, current_status_meta.get("Последнее обновление")),
        cast(str | None, current_sprint_meta.get("Последнее обновление")),
        cast(str | None, release_status_meta.get("Последнее обновление")),
    )

    important_context = [
        _strip_trailing_punctuation(cast(str, feature_map["state-layer"]["behavior"])),
        _strip_trailing_punctuation(cast(str, feature_map["bootstrap-contract"]["behavior"])),
    ]

    return {
        "last_updated": latest_update,
        "status": "generated lightweight startup entry point for agent cold-start",
        "product_line": product_line,
        "active_gate": active_gate,
        "current_blocker": blocker,
        "release_status": release_status,
        "important_context": [item for item in important_context if item],
        "entry_rules": [
            "Всегда первым для release-, resume- и действительно кросс-модульных задач.",
            "Вместо полного state layer для локальных однофайловых и short explanation задач.",
            "Если после чтения всё ещё неясен scope, только тогда эскалировать в docs/current-status.md, docs/current-sprint.md и docs/release-status.md.",
        ],
        "fast_path_rules": [
            "Локальная задача в одном файле, одном тесте или вокруг одной ошибки: не читать полный state layer.",
            "Resume, release, process/state docs, CI/release gates или неочевидный owning surface: дочитать полный state layer.",
            "Если задача меняет capability/process contract, определить feature_id из docs/agent-feature-spine.json до substantive edit.",
        ],
        "full_state_docs": FULL_STATE_DOCS,
        "escalation_rules": FAST_PATH_ESCALATION_RULES,
        "validation_anchors": validation_anchors[:3],
    }


def build_state_snapshot_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# State Snapshot",
        "",
        f"Последнее обновление: {payload['last_updated']}",
        f"Статус: {payload['status']}",
        "",
        "## 1. Когда читать этот файл",
        "",
    ]
    for index, rule in enumerate(cast(list[str], payload["entry_rules"]), start=1):
        lines.append(f"{index}. {rule}")

    lines.extend(
        [
            "",
            "## 2. Текущий контур",
            "",
            f"- Продукт: {payload['product_line']}.",
            f"- Текущий active gate: {payload['active_gate']}.",
            f"- Текущий blocker: {payload['current_blocker']}",
            f"- Release status: {payload['release_status']}",
            "",
            "## 3. Что важно помнить без чтения длинных state docs",
            "",
        ]
    )
    for context_line in cast(list[str], payload["important_context"]):
        lines.append(f"- {context_line}.")

    lines.extend(
        [
            "",
            "## 4. Fast-path routing",
            "",
        ]
    )
    for rule in cast(list[str], payload["fast_path_rules"]):
        lines.append(f"- {rule}")

    lines.extend(
        [
            "",
            "## 5. Полный state layer читать, если",
            "",
        ]
    )
    for index, rule in enumerate(cast(list[str], payload["escalation_rules"]), start=1):
        lines.append(f"{index}. {rule}")

    lines.extend(
        [
            "",
            "## 6. Ближайшие validation anchors",
            "",
        ]
    )
    for anchor in cast(list[str], payload["validation_anchors"]):
        lines.append(anchor)

    return "\n".join(lines).rstrip() + "\n"


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object in {path}")
    return cast(dict[str, Any], payload)


def _feature_map(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw_features = payload.get("features")
    if not isinstance(raw_features, list):
        raise ValueError("feature spine must contain a list in features")
    feature_map: dict[str, dict[str, Any]] = {}
    for feature in raw_features:
        if not isinstance(feature, dict):
            continue
        feature_id = feature.get("feature_id")
        if isinstance(feature_id, str):
            feature_map[feature_id] = cast(dict[str, Any], feature)
    for required_id in ("state-layer", "bootstrap-contract"):
        if required_id not in feature_map:
            raise ValueError(f"missing required feature_id in feature spine: {required_id}")
    return feature_map


def _parse_front_matter(text: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("## "):
            break
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip()
    return metadata


def _ordered_items_in_section(text: str, heading: str) -> list[str]:
    section = _section_lines(text, heading)
    items: list[str] = []
    for line in section:
        match = re.match(r"^(\d+)\.\s+(.*)$", line)
        if match is None:
            continue
        items.append(f"{match.group(1)}. {match.group(2).strip()}")
    return items


def _first_bullet_in_section(text: str, heading: str) -> str:
    section = _section_lines(text, heading)
    for line in section:
        if not line.startswith("- "):
            continue
        return _strip_trailing_punctuation(line[2:].strip()) + "."
    return "не определён."


def _section_lines(text: str, heading: str) -> list[str]:
    lines = text.splitlines()
    inside = False
    collected: list[str] = []
    for line in lines:
        if line.strip() == heading:
            inside = True
            continue
        if inside and line.startswith("## "):
            break
        if inside:
            collected.append(line.rstrip())
    return collected


def _latest_date(*raw_dates: str | None) -> str:
    known_dates = [date.fromisoformat(value) for value in raw_dates if value]
    if not known_dates:
        return date.today().isoformat()
    return max(known_dates).isoformat()


def _strip_trailing_punctuation(value: str) -> str:
    return value.rstrip(" .;")


if __name__ == "__main__":
    raise SystemExit(main())