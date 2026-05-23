# pyright: reportMissingTypeStubs=false

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import date, timedelta
from pathlib import Path
from typing import Any, cast


ROOT = Path(__file__).resolve().parents[1]
FEATURE_SPINE = ROOT / "docs" / "agent-feature-spine.json"
SCORECARD_JSON = ROOT / "docs" / "agent-quality-scorecard.v1.json"
TELEMETRY_JSONL = ROOT / "docs" / "agent-telemetry.v1.jsonl"
WEEKLY_REVIEWS_JSON = ROOT / "docs" / "agent-weekly-reviews.v1.json"
DEFAULT_OUTPUT = ROOT / "docs" / "agent-weekly-eval.v1.json"
DEFAULT_MARKDOWN = ROOT / "docs" / "agent-weekly-eval.md"
RUBRIC_SCORE_KEYS = (
    "scope_control",
    "feature_traceability",
    "hypothesis_quality",
    "validation_quality",
    "evidence_quality",
    "state_hygiene",
    "closeout_quality",
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build or check the generated weekly agent eval snapshot.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Path to the generated weekly eval JSON file.")
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MARKDOWN, help="Path to the generated weekly eval markdown file.")
    parser.add_argument("--days", type=int, default=7, help="Rolling window size in days.")
    parser.add_argument("--check", action="store_true", help="Fail if the JSON output file does not match the generated payload.")
    parser.add_argument("--check-markdown", action="store_true", help="Fail if the markdown report does not match the generated content.")
    args = parser.parse_args(argv)

    days = max(1, args.days)
    output_path = args.output.expanduser().resolve()
    markdown_path = args.markdown.expanduser().resolve()

    payload = build_weekly_eval_payload(ROOT, days=days)
    markdown_text = build_weekly_eval_markdown(payload)
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
        markdown_path.write_text(markdown_text, encoding="utf-8", newline="\n")
        status = "written"

    if args.check_markdown:
        if not markdown_path.exists():
            print(json.dumps({"status": "missing-markdown", "path": str(markdown_path)}, ensure_ascii=False))
            return 1
        current_markdown = markdown_path.read_text(encoding="utf-8")
        if current_markdown != markdown_text:
            print(json.dumps({"status": "markdown-drift", "path": str(markdown_path)}, ensure_ascii=False))
            return 1

    print(
        json.dumps(
            {
                "status": status,
                "path": str(output_path),
                "markdown_path": str(markdown_path),
                "days": days,
            },
            ensure_ascii=False,
        )
    )
    return 0


def build_weekly_eval_payload(root: Path, *, days: int) -> dict[str, Any]:
    feature_spine = _load_json(root / "docs" / "agent-feature-spine.json")
    scorecard = _load_json(root / "docs" / "agent-quality-scorecard.v1.json")
    telemetry_entries = _load_jsonl(root / "docs" / "agent-telemetry.v1.jsonl")
    weekly_reviews = _load_json(root / "docs" / "agent-weekly-reviews.v1.json")

    validated_features = sorted(
        cast(str, feature["feature_id"])
        for feature in cast(list[dict[str, Any]], feature_spine["features"])
        if feature.get("status") == "validated"
    )
    referenced_feature_ids = cast(list[str], cast(dict[str, Any], scorecard["feature_summary"])["referenced_feature_ids"])

    end_date = _latest_known_date(cast(str, scorecard["as_of_date"]), telemetry_entries)
    start_date = end_date - timedelta(days=days - 1)
    window_entries = [
        entry for entry in telemetry_entries if start_date <= _parse_iso_date(cast(str, entry["date"])) <= end_date
    ]

    validation_results = Counter(cast(str, entry["validation_result"]) for entry in window_entries)
    task_types = Counter(cast(str, entry["task_type"]) for entry in window_entries)
    state_updates = sum(1 for entry in window_entries if entry["state_update"] is True)
    feature_traceable_entries = sum(1 for entry in window_entries if entry["feature_ids"])
    coverage_gap_feature_ids = sorted(set(validated_features) - set(referenced_feature_ids))
    observed_signals = cast(list[dict[str, Any]], scorecard["observed_signals"])
    findings = _build_findings(observed_signals, validation_results, len(window_entries), coverage_gap_feature_ids)
    qualitative_sampling = _build_qualitative_sampling(weekly_reviews, start_date, end_date)

    payload = {
        "schema_version": "agent-weekly-eval.v1",
        "as_of_date": end_date.isoformat(),
        "window": {
            "days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        },
        "overall_status": _overall_status(observed_signals, validation_results, len(window_entries)),
        "sources": {
            "feature_spine": "docs/agent-feature-spine.json",
            "scorecard_json": "docs/agent-quality-scorecard.v1.json",
            "telemetry_jsonl": "docs/agent-telemetry.v1.jsonl",
            "weekly_reviews_json": "docs/agent-weekly-reviews.v1.json",
            "evaluator_rubric": "docs/agent-evaluator-rubric.md",
            "eval_instructions": "docs/agent-evals.md",
        },
        "telemetry_window_summary": {
            "total_entries": len(window_entries),
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
        "scorecard_snapshot": {
            "scorecard_as_of_date": cast(str, scorecard["as_of_date"]),
            "validated_features": cast(int, cast(dict[str, Any], scorecard["feature_summary"])["validated_features"]),
            "referenced_features": cast(int, cast(dict[str, Any], scorecard["feature_summary"])["referenced_features"]),
            "referenced_feature_ids": referenced_feature_ids,
            "coverage_gap_feature_ids": coverage_gap_feature_ids,
            "observed_signals": observed_signals,
        },
        "qualitative_sampling": qualitative_sampling,
        "findings": findings,
    }
    return payload


def build_weekly_eval_markdown(payload: dict[str, Any]) -> str:
    window = cast(dict[str, Any], payload["window"])
    telemetry_summary = cast(dict[str, Any], payload["telemetry_window_summary"])
    scorecard_snapshot = cast(dict[str, Any], payload["scorecard_snapshot"])
    qualitative_sampling = cast(dict[str, Any], payload["qualitative_sampling"])
    signals = cast(list[dict[str, Any]], scorecard_snapshot["observed_signals"])
    findings = cast(list[dict[str, Any]], payload["findings"])
    coverage_gaps = cast(list[str], scorecard_snapshot["coverage_gap_feature_ids"])
    reviews = cast(list[dict[str, Any]], qualitative_sampling["reviews"])

    lines = [
        "# Agent Weekly Eval",
        "",
        f"Дата среза: {payload['as_of_date']}",
        f"Окно: {window['start_date']} .. {window['end_date']} ({window['days']} дней)",
        f"Статус: {payload['overall_status']}",
        "",
        "Этот отчёт generated из `docs/agent-quality-scorecard.v1.json`, `docs/agent-telemetry.v1.jsonl` и `docs/agent-weekly-reviews.v1.json`.",
        "",
        "## 1. Snapshot",
        "",
        f"- telemetry entries in window: `{telemetry_summary['total_entries']}`;",
        f"- state updates in window: `{telemetry_summary['state_updates']}`;",
        f"- feature-traceable entries in window: `{telemetry_summary['feature_traceable_entries']}`;",
        f"- validated features in spine: `{scorecard_snapshot['validated_features']}`;",
        f"- referenced features in telemetry: `{scorecard_snapshot['referenced_features']}`.",
        "",
        "## 2. Observed signals",
        "",
        "| Signal | Score | Basis |",
        "| --- | ---: | --- |",
    ]
    for signal in signals:
        lines.append(
            f"| {signal['title']} | {signal['score']}/{signal['scale_max']} | {signal['basis']} |"
        )

    lines.extend([
        "",
        "## 3. Findings",
        "",
    ])
    if findings:
        for finding in findings:
            lines.append(
                f"- {str(finding['severity']).upper()}: {finding['summary']} Рекомендация: {finding['recommended_action']}"
            )
    else:
        lines.append("- Открытых findings по текущему weekly snapshot нет.")

    lines.extend([
        "",
        "## 4. Coverage gaps",
        "",
    ])
    if coverage_gaps:
        lines.append(f"- Missing validated feature_ids in structured telemetry: `{', '.join(coverage_gaps)}`.")
    else:
        lines.append("- Coverage gaps нет: все validated feature_id уже наблюдаются в structured telemetry.")

    lines.extend([
        "",
        "## 5. Qualitative sampling",
        "",
        f"- completed reviews in window: `{qualitative_sampling['completed_reviews_in_window']}`;",
        f"- sampled tasks in window: `{qualitative_sampling['sampled_tasks_in_window']}`.",
    ])

    if reviews:
        for review in reviews:
            lines.extend([
                "",
                f"### Review `{review['review_id']}`",
                "",
                f"- review date: `{review['review_date']}`; average sampled score: `{_format_average_score(cast(float, review['average_score']))}/{review['max_score']}`.",
                f"- {_escape_markdown_cell(cast(str, review['summary']))}",
                "",
                "| Task | Score | Interpretation | Note |",
                "| --- | ---: | --- | --- |",
            ])
            for task in cast(list[dict[str, Any]], review["sampled_tasks"]):
                lines.append(
                    "| "
                    f"{_escape_markdown_cell(cast(str, task['task']))} | "
                    f"{task['total_score']}/{task['max_score']} | "
                    f"{_escape_markdown_cell(cast(str, task['interpretation']))} | "
                    f"{_escape_markdown_cell(cast(str, task.get('note', '—')))} |"
                )
    else:
        lines.extend([
            "",
            "- Machine-readable qualitative sampling для этого окна пока не зафиксирован.",
        ])

    lines.extend([
        "",
        "## 6. Refresh command",
        "",
        "- `.\\.venv\\Scripts\\python.exe scripts\\refresh_agent_eval.py`",
        "- `.\\.venv\\Scripts\\python.exe scripts\\refresh_agent_eval.py --check --check-markdown`",
    ])
    return "\n".join(lines).rstrip() + "\n"


def _build_findings(
    observed_signals: list[dict[str, Any]],
    validation_results: Counter[str],
    total_entries: int,
    coverage_gap_feature_ids: list[str],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    action_by_signal = {
        "validation-discipline": "Держать первый post-edit check узким и исполнимым, а repair loop закрывать тем же validation target.",
        "state-hygiene": "Обновлять status, sprint, telemetry и release state после каждой нетривиальной задачи без пропусков.",
        "feature-traceability": "Фиксировать затронутые feature_id и evidence paths до первой substantive правки.",
        "feature-coverage": "Backfill structured telemetry для missing feature_ids или доводить новые задачи до traceability по этим capability slices.",
    }
    for signal in observed_signals:
        score = cast(int, signal["score"])
        scale_max = cast(int, signal["scale_max"])
        if score >= scale_max:
            continue
        severity = "medium" if score >= scale_max - 1 else "high"
        findings.append(
            {
                "finding_id": f"weak-{signal['signal_id']}",
                "severity": severity,
                "summary": cast(str, signal["basis"]),
                "recommended_action": action_by_signal.get(cast(str, signal["signal_id"]), "Уточнить corrective action в eval loop."),
            }
        )

    if validation_results["failed"] > 0 or validation_results["blocked"] > 0:
        findings.append(
            {
                "finding_id": "window-validation-failures",
                "severity": "high",
                "summary": "В weekly window есть failed или blocked validation results.",
                "recommended_action": "Разобрать blocking entries и не считать weekly loop healthy, пока narrow validation не возвращён в pass-like state.",
            }
        )

    if total_entries == 0:
        findings.append(
            {
                "finding_id": "window-has-no-telemetry",
                "severity": "high",
                "summary": "В weekly window нет structured telemetry, поэтому snapshot не подтверждён фактическими задачами.",
                "recommended_action": "Записать хотя бы один complete task slice в structured telemetry или расширить window для retrospective режима.",
            }
        )
    elif total_entries < 3:
        findings.append(
            {
                "finding_id": "window-has-limited-evidence",
                "severity": "low",
                "summary": f"Weekly window содержит только {total_entries} telemetry entries.",
                "recommended_action": "Использовать snapshot как early signal, но не как полноту weekly process quality без дополнительного evidence.",
            }
        )

    if coverage_gap_feature_ids and not any(finding["finding_id"] == "weak-feature-coverage" for finding in findings):
        findings.append(
            {
                "finding_id": "coverage-gaps-remain",
                "severity": "medium",
                "summary": f"В structured telemetry ещё не покрыты {len(coverage_gap_feature_ids)} validated feature_ids.",
                "recommended_action": "Заполнить historical JSONL backfill или закрывать будущие task slices так, чтобы missing feature_ids начали появляться в telemetry.",
            }
        )

    return findings


def _overall_status(
    observed_signals: list[dict[str, Any]],
    validation_results: Counter[str],
    total_entries: int,
) -> str:
    if total_entries == 0:
        return "no-data"
    if validation_results["failed"] > 0 or validation_results["blocked"] > 0:
        return "needs-attention"
    if any(cast(int, signal["score"]) <= 3 for signal in observed_signals):
        return "needs-attention"
    if any(cast(int, signal["score"]) < cast(int, signal["scale_max"]) for signal in observed_signals):
        return "strong-with-gaps"
    return "strong"


def _build_qualitative_sampling(
    weekly_reviews: dict[str, Any],
    start_date: date,
    end_date: date,
) -> dict[str, Any]:
    reviews_in_window: list[dict[str, Any]] = []
    sampled_tasks_in_window = 0

    for review in cast(list[dict[str, Any]], weekly_reviews.get("reviews", [])):
        review_date = _parse_iso_date(cast(str, review["review_date"]))
        if not (start_date <= review_date <= end_date):
            continue

        sampled_tasks = cast(list[dict[str, Any]], review["sampled_tasks"])
        if not sampled_tasks:
            raise ValueError(f"weekly review has no sampled_tasks: {review['review_id']}")

        normalized_tasks: list[dict[str, Any]] = []
        for task in sampled_tasks:
            scores = cast(dict[str, Any], task["scores"])
            computed_total = sum(cast(int, scores[key]) for key in RUBRIC_SCORE_KEYS)
            total_score = cast(int, task["total_score"])
            max_score = cast(int, task["max_score"])
            if total_score != computed_total:
                raise ValueError(
                    f"weekly review task score mismatch for {review['review_id']}::{task['task']}: "
                    f"expected {computed_total}, got {total_score}"
                )
            if max_score != 14:
                raise ValueError(
                    f"weekly review task max_score mismatch for {review['review_id']}::{task['task']}: {max_score}"
                )
            normalized_tasks.append(dict(task))

        sampled_tasks_in_window += len(normalized_tasks)
        average_score = round(
            sum(cast(int, task["total_score"]) for task in normalized_tasks) / len(normalized_tasks),
            1,
        )
        reviews_in_window.append(
            {
                "review_id": cast(str, review["review_id"]),
                "review_date": cast(str, review["review_date"]),
                "window": cast(dict[str, Any], review["window"]),
                "summary": cast(str, review["summary"]),
                "average_score": average_score,
                "max_score": 14,
                "sampled_tasks": normalized_tasks,
            }
        )

    reviews_in_window.sort(key=lambda review: (cast(str, review["review_date"]), cast(str, review["review_id"])))
    return {
        "completed_reviews_in_window": len(reviews_in_window),
        "sampled_tasks_in_window": sampled_tasks_in_window,
        "reviews": reviews_in_window,
    }


def _latest_known_date(scorecard_date: str, telemetry_entries: list[dict[str, Any]]) -> date:
    known_dates = [_parse_iso_date(scorecard_date)]
    known_dates.extend(_parse_iso_date(cast(str, entry["date"])) for entry in telemetry_entries)
    return max(known_dates)


def _format_average_score(value: float) -> str:
    return f"{value:.1f}"


def _escape_markdown_cell(value: str) -> str:
    return value.replace("|", "/")


def _parse_iso_date(value: str) -> date:
    return date.fromisoformat(value)


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


def _dump_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())