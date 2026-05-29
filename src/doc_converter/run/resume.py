from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..schema_validation import SchemaValidationError, validate_json_file, validate_payload


@dataclass(frozen=True)
class ResumeHit:
    run_id: str
    output_dir: str
    status: str
    manifest_record: dict[str, Any]


def _reuse_document_dir(source_dir: Path, target_dir: Path) -> None:
    if target_dir.exists():
        shutil.rmtree(target_dir)
    shutil.copytree(source_dir, target_dir)


def _copy_result_metadata(source_record: dict[str, object], target_record: dict[str, object]) -> None:
    for key in ("assets_count", "pages", "search_text_chars", "units_count", "warnings", "original_copy_path"):
        if key in source_record:
            target_record[key] = source_record[key]


def _load_resume_index(runs_dir: Path, current_run_dir: Path) -> dict[tuple[str, str], ResumeHit]:
    if not runs_dir.exists():
        return {}

    index: dict[tuple[str, str], ResumeHit] = {}
    for candidate in sorted((path for path in runs_dir.iterdir() if path.is_dir()), reverse=True):
        if candidate.resolve() == current_run_dir.resolve():
            continue
        manifest_path = candidate / "manifest.jsonl"
        if not manifest_path.exists():
            continue
        for line in manifest_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                manifest_record = json.loads(line)
                validate_payload(manifest_record, "manifest.v1.schema.json")
            except (json.JSONDecodeError, SchemaValidationError):
                continue

            status = str(manifest_record.get("status", ""))
            output_dir = manifest_record.get("output_dir")
            sha256 = manifest_record.get("sha256")
            relative_path = manifest_record.get("relative_path")
            if status not in {"success", "partial_success"}:
                continue
            if not isinstance(output_dir, str) or not isinstance(sha256, str) or not isinstance(relative_path, str):
                continue

            document_path = candidate / output_dir / "document.v1.json"
            if not document_path.exists():
                continue
            try:
                validate_json_file(document_path, "document.v1.schema.json")
            except (json.JSONDecodeError, OSError, SchemaValidationError):
                continue

            key = (sha256, relative_path)
            if key in index:
                continue
            index[key] = ResumeHit(
                run_id=candidate.name,
                output_dir=output_dir,
                status=status,
                manifest_record=manifest_record,
            )
    return index