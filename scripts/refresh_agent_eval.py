# pyright: reportMissingTypeStubs=false

from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_agent_scorecard import (
    DEFAULT_MARKDOWN as SCORECARD_MARKDOWN,
    DEFAULT_OUTPUT as SCORECARD_JSON,
    _dump_json as dump_scorecard_json,
    _extract_markdown_section as extract_scorecard_markdown_section,
    _write_markdown_section as write_scorecard_markdown_section,
    build_scorecard_markdown_section,
    build_scorecard_payload,
)
from build_agent_weekly_eval import (
    DEFAULT_MARKDOWN as WEEKLY_EVAL_MARKDOWN,
    DEFAULT_OUTPUT as WEEKLY_EVAL_JSON,
    _dump_json as dump_weekly_eval_json,
    build_weekly_eval_markdown,
    build_weekly_eval_payload,
)


ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Refresh or check generated agent eval companions in one command.")
    parser.add_argument("--days", type=int, default=7, help="Rolling window size in days for weekly eval.")
    parser.add_argument("--check", action="store_true", help="Fail if generated files drift from current sources.")
    parser.add_argument(
        "--check-markdown",
        action="store_true",
        help="Fail if generated markdown views drift from current sources.",
    )
    args = parser.parse_args(argv)

    days = max(1, args.days)
    status = "ok"

    scorecard_payload = build_scorecard_payload(ROOT)
    scorecard_markdown = build_scorecard_markdown_section(scorecard_payload)

    if args.check:
        if _assert_json_matches(SCORECARD_JSON, scorecard_payload, "scorecard") != 0:
            return 1
    else:
        SCORECARD_JSON.write_text(dump_scorecard_json(scorecard_payload), encoding="utf-8", newline="\n")
        write_scorecard_markdown_section(SCORECARD_MARKDOWN, scorecard_markdown)
        status = "written"

    if args.check_markdown:
        if _assert_scorecard_markdown_matches(SCORECARD_MARKDOWN, scorecard_markdown) != 0:
            return 1

    weekly_eval_payload = build_weekly_eval_payload(ROOT, days=days)
    weekly_eval_markdown = build_weekly_eval_markdown(weekly_eval_payload)

    if args.check:
        if _assert_json_matches(WEEKLY_EVAL_JSON, weekly_eval_payload, "weekly-eval") != 0:
            return 1
    else:
        WEEKLY_EVAL_JSON.write_text(dump_weekly_eval_json(weekly_eval_payload), encoding="utf-8", newline="\n")
        WEEKLY_EVAL_MARKDOWN.write_text(weekly_eval_markdown, encoding="utf-8", newline="\n")

    if args.check_markdown:
        if _assert_text_matches(WEEKLY_EVAL_MARKDOWN, weekly_eval_markdown, "weekly-eval-markdown") != 0:
            return 1

    print(
        json.dumps(
            {
                "status": status,
                "days": days,
                "scorecard_json": str(SCORECARD_JSON),
                "scorecard_markdown": str(SCORECARD_MARKDOWN),
                "weekly_eval_json": str(WEEKLY_EVAL_JSON),
                "weekly_eval_markdown": str(WEEKLY_EVAL_MARKDOWN),
            },
            ensure_ascii=False,
        )
    )
    return 0


def _assert_json_matches(path: Path, expected_payload: dict[str, object], label: str) -> int:
    if not path.exists():
        print(json.dumps({"status": "missing", "label": label, "path": str(path)}, ensure_ascii=False))
        return 1

    current = json.loads(path.read_text(encoding="utf-8"))
    if current != expected_payload:
        print(json.dumps({"status": "drift", "label": label, "path": str(path)}, ensure_ascii=False))
        return 1
    return 0


def _assert_scorecard_markdown_matches(path: Path, expected_section: str) -> int:
    if not path.exists():
        print(json.dumps({"status": "missing-markdown", "label": "scorecard-markdown", "path": str(path)}, ensure_ascii=False))
        return 1

    current_section = extract_scorecard_markdown_section(path.read_text(encoding="utf-8"))
    if current_section != expected_section:
        print(json.dumps({"status": "markdown-drift", "label": "scorecard-markdown", "path": str(path)}, ensure_ascii=False))
        return 1
    return 0


def _assert_text_matches(path: Path, expected_text: str, label: str) -> int:
    if not path.exists():
        print(json.dumps({"status": "missing-markdown", "label": label, "path": str(path)}, ensure_ascii=False))
        return 1

    current_text = path.read_text(encoding="utf-8")
    if current_text != expected_text:
        print(json.dumps({"status": "markdown-drift", "label": label, "path": str(path)}, ensure_ascii=False))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())