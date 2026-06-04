from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WORD_RE = re.compile(r"[0-9A-Za-zА-Яа-яЁё_]+")
TOKEN_RE = re.compile(r"[0-9A-Za-zА-Яа-яЁё_]+|[^\s]")
DEFAULT_STARTUP_FILES = [
    "docs/agent-working-state.v1.json",
    "docs/state-snapshot.md",
    "docs/current-status.md",
    "docs/current-sprint.md",
    "docs/release-status.md",
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Estimate rough prompt-token cost for local context files and text.")
    parser.add_argument("--path", action="append", default=[], help="Relative or absolute file path to estimate. Can be passed multiple times.")
    parser.add_argument("--text", action="append", default=[], help="Inline text snippet to estimate. Can be passed multiple times.")
    parser.add_argument(
        "--excerpt-lines",
        type=int,
        default=0,
        help="If > 0, estimate file cost only from the first N lines instead of the whole file.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable markdown.")
    parser.add_argument(
        "--include-startup-bundles",
        action="store_true",
        help="Include the default startup state-doc bundle alongside explicit paths/text.",
    )
    args = parser.parse_args(argv)

    payload = build_report(
        ROOT,
        path_specs=[str(value) for value in args.path],
        inline_texts=[str(value) for value in args.text],
        include_startup_bundles=args.include_startup_bundles or (not args.path and not args.text),
        excerpt_lines=max(0, int(args.excerpt_lines)),
    )

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(format_report(payload))
    return 0


def build_report(
    root: Path,
    *,
    path_specs: list[str],
    inline_texts: list[str],
    include_startup_bundles: bool,
    excerpt_lines: int,
) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    bundles: list[dict[str, Any]] = []

    if include_startup_bundles:
        startup_items = [_estimate_file(root, relative_path, excerpt_lines=excerpt_lines) for relative_path in DEFAULT_STARTUP_FILES]
        items.extend(startup_items)
        bundles.extend(_startup_bundles(startup_items, excerpt_lines=excerpt_lines))

    for path_spec in path_specs:
        items.append(_estimate_file(root, path_spec, excerpt_lines=excerpt_lines))

    for index, text in enumerate(inline_texts, start=1):
        items.append(_estimate_inline_text(f"text[{index}]", text))

    total_tokens = sum(int(item["estimated_tokens"]) for item in items)
    total_chars = sum(int(item["chars"]) for item in items)
    return {
        "status": "ok",
        "heuristic": "alnum chunks ~= ceil(len/4) tokens, symbols count as 1 token, blank lines add no extra token",
        "excerpt_lines": excerpt_lines,
        "items": items,
        "bundles": bundles,
        "summary": {
            "items": len(items),
            "bundles": len(bundles),
            "chars": total_chars,
            "estimated_tokens": total_tokens,
        },
    }


def estimate_text_tokens(text: str) -> int:
    tokens = 0
    for chunk in TOKEN_RE.findall(text):
        if WORD_RE.fullmatch(chunk):
            tokens += max(1, math.ceil(len(chunk) / 4))
            continue
        tokens += 1
    return tokens


def format_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Context Token Estimate",
        "",
        f"Heuristic: {payload['heuristic']}",
        "",
        "## Items",
        "",
        "| Label | Source | Lines | Chars | Tokens | Mode |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for item in payload["items"]:
        mode = item.get("mode", "full")
        lines.append(
            f"| {item['label']} | {item['source']} | {item['lines']} | {item['chars']} | {item['estimated_tokens']} | {mode} |"
        )

    bundles = payload["bundles"]
    if bundles:
        lines.extend([
            "",
            "## Bundles",
            "",
            "| Bundle | Sources | Tokens | Mode |",
            "| --- | --- | ---: | --- |",
        ])
        for bundle in bundles:
            sources = ", ".join(bundle["sources"])
            lines.append(f"| {bundle['label']} | {sources} | {bundle['estimated_tokens']} | {bundle['mode']} |")

    summary = payload["summary"]
    lines.extend([
        "",
        "## Summary",
        "",
        f"- items: {summary['items']};",
        f"- bundles: {summary['bundles']};",
        f"- chars across items: {summary['chars']};",
        f"- estimated tokens across items: {summary['estimated_tokens']}.",
    ])
    return "\n".join(lines)


def _estimate_file(root: Path, path_spec: str, *, excerpt_lines: int) -> dict[str, Any]:
    path = Path(path_spec)
    if not path.is_absolute():
        path = root / path
    resolved = path.resolve()
    full_text = resolved.read_text(encoding="utf-8")
    full_line_list = full_text.splitlines()
    excerpted = excerpt_lines > 0
    if excerpted:
        line_list = full_line_list[:excerpt_lines]
        text = "\n".join(line_list)
        if full_text.endswith("\n") and line_list:
            text += "\n"
    else:
        line_list = full_line_list
        text = full_text

    lines = len(line_list)
    estimated_tokens = estimate_text_tokens(text)
    try:
        source = str(resolved.relative_to(root)).replace("\\", "/")
    except ValueError:
        source = str(resolved)

    mode = f"excerpt:first_{excerpt_lines}_lines" if excerpted else "full"
    return {
        "kind": "file",
        "label": Path(source).name,
        "source": source,
        "lines": lines,
        "chars": len(text),
        "estimated_tokens": estimated_tokens,
        "mode": mode,
        "total_lines": len(full_line_list),
        "total_chars": len(full_text),
    }


def _estimate_inline_text(label: str, text: str) -> dict[str, Any]:
    return {
        "kind": "text",
        "label": label,
        "source": "inline-text",
        "lines": len(text.splitlines()) or 1,
        "chars": len(text),
        "estimated_tokens": estimate_text_tokens(text),
        "mode": "full",
    }


def _startup_bundles(startup_items: list[dict[str, Any]], *, excerpt_lines: int) -> list[dict[str, Any]]:
    hot_state = [item for item in startup_items if item["source"] == "docs/agent-working-state.v1.json"]
    snapshot_only = [item for item in startup_items if item["source"] == "docs/state-snapshot.md"]
    full_state = [
        item
        for item in startup_items
        if item["source"]
        in {
            "docs/agent-working-state.v1.json",
            "docs/state-snapshot.md",
            "docs/current-status.md",
            "docs/current-sprint.md",
            "docs/release-status.md",
        }
    ]
    mode = f"excerpt:first_{excerpt_lines}_lines" if excerpt_lines > 0 else "full"
    return [
        {
            "label": "hot-state startup",
            "sources": [item["source"] for item in hot_state],
            "estimated_tokens": sum(int(item["estimated_tokens"]) for item in hot_state),
            "mode": mode,
        },
        {
            "label": "snapshot-only startup",
            "sources": [item["source"] for item in snapshot_only],
            "estimated_tokens": sum(int(item["estimated_tokens"]) for item in snapshot_only),
            "mode": mode,
        },
        {
            "label": "full-state startup",
            "sources": [item["source"] for item in full_state],
            "estimated_tokens": sum(int(item["estimated_tokens"]) for item in full_state),
            "mode": mode,
        },
    ]


if __name__ == "__main__":
    raise SystemExit(main())
