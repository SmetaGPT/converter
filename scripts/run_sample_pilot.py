from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from doc_converter.config import ConverterConfig, ConverterOptions
from doc_converter.runner import run_convert_folder


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run converter on representative samples from a JSONL manifest.")
    parser.add_argument("--manifest", type=Path, default=ROOT / "samples" / "manifest.sample.jsonl")
    parser.add_argument("--output", type=Path, default=ROOT / "runs" / "sample-pilot")
    parser.add_argument("--input", type=Path, default=ROOT / "runs" / "sample-pilot-input")
    parser.add_argument("--ocr-languages", default="rus+eng")
    parser.add_argument("--clean", action="store_true", help="Remove previous pilot input/output folders before running.")
    args = parser.parse_args(argv)

    records = _read_jsonl(args.manifest)
    if args.clean:
        _remove_if_exists(args.input)
        _remove_if_exists(args.output)

    args.input.mkdir(parents=True, exist_ok=True)
    args.output.mkdir(parents=True, exist_ok=True)
    staged_records = _stage_records(records, args.input)
    _write_jsonl(args.input / "pilot-input-manifest.jsonl", staged_records)

    options = ConverterOptions(ocr_languages=tuple(part for part in args.ocr_languages.split("+") if part))
    result = run_convert_folder(ConverterConfig(input_dir=args.input, output_dir=args.output, options=options))
    run_manifest = _read_jsonl(result.run_dir / "manifest.jsonl")
    pilot_summary = _build_summary(staged_records, run_manifest, result.run_dir)
    pilot_summary_path = result.run_dir / "pilot-summary.json"
    pilot_summary_path.write_text(json.dumps(pilot_summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({"run_dir": str(result.run_dir), **pilot_summary}, ensure_ascii=False, indent=2))
    return 0 if _pilot_passed(pilot_summary) else 1


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")


def _stage_records(records: list[dict[str, Any]], input_dir: Path) -> list[dict[str, Any]]:
    staged_records: list[dict[str, Any]] = []
    for record in records:
        source_path = Path(record["source_root"]) / record["relative_path"]
        if not source_path.exists():
            raise FileNotFoundError(f"Sample source not found: {source_path}")

        staged_name = f"{record['sample_id']}__{source_path.name}"
        staged_path = input_dir / staged_name
        shutil.copy2(source_path, staged_path)
        staged_record = dict(record)
        staged_record["source_path"] = str(source_path)
        staged_record["staged_relative_path"] = staged_name
        staged_records.append(staged_record)
    return staged_records


def _build_summary(
    staged_records: list[dict[str, Any]],
    run_manifest: list[dict[str, Any]],
    run_dir: Path,
) -> dict[str, Any]:
    expected_by_sha = {record["sha256"]: record for record in staged_records}
    route_mismatches: list[dict[str, str]] = []
    for run_record in run_manifest:
        expected = expected_by_sha.get(run_record.get("sha256"))
        if expected and expected["route"] != run_record.get("route"):
            route_mismatches.append(
                {
                    "sample_id": expected["sample_id"],
                    "expected_route": expected["route"],
                    "actual_route": str(run_record.get("route")),
                }
            )

    status_counts = Counter(str(record.get("status")) for record in run_manifest)
    route_counts = Counter(str(record.get("route")) for record in run_manifest)
    return {
        "samples": len(staged_records),
        "processed": len(run_manifest),
        "success": status_counts.get("success", 0),
        "partial_success": status_counts.get("partial_success", 0),
        "failed": status_counts.get("failed", 0),
        "routes": dict(sorted(route_counts.items())),
        "statuses": dict(sorted(status_counts.items())),
        "route_mismatches": route_mismatches,
        "run_dir": str(run_dir),
    }


def _pilot_passed(summary: dict[str, Any]) -> bool:
    return (
        summary["processed"] == summary["samples"]
        and summary["failed"] == 0
        and not summary["route_mismatches"]
    )


def _remove_if_exists(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


if __name__ == "__main__":
    raise SystemExit(main())