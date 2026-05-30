from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from ..schema_validation import validate_payload


@dataclass(frozen=True)
class RuntimeLogger:
    run_id: str
    telemetry_path: Path
    progress_callback: Callable[[dict[str, object]], None] | None = None
    legacy_log_path: Path | None = None
    legacy_error_path: Path | None = None

    def emit(
        self,
        event: str,
        *,
        progress: bool = False,
        legacy: bool = False,
        **payload: object,
    ) -> dict[str, Any]:
        event_payload = _build_event_payload(self.run_id, event, payload)
        _append_validated_jsonl(self.telemetry_path, event_payload, "log.v1.schema.json")

        if legacy:
            legacy_path = self.legacy_error_path if event == "document_failed" else self.legacy_log_path
            if legacy_path is not None:
                _append_jsonl(legacy_path, _legacy_event_payload(event_payload))

        if progress and self.progress_callback is not None:
            self.progress_callback(dict(event_payload))
        return event_payload


def _build_event_payload(run_id: str, event: str, payload: dict[str, object]) -> dict[str, Any]:
    warnings = payload.get("warnings")
    normalized_warnings = []
    if isinstance(warnings, list):
        normalized_warnings = [str(item) for item in warnings]

    event_payload = {
        "schema_version": "log.v1",
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "run_id": run_id,
        "event": event,
        "level": _event_level(event),
        "status": _optional_string(payload.get("status")),
        "relative_path": _optional_string(payload.get("relative_path")),
        "filename": _optional_string(payload.get("filename")),
        "format": _optional_string(payload.get("format")),
        "size_bytes": _optional_int(payload.get("size_bytes")),
        "warnings": normalized_warnings,
        "route": _optional_string(payload.get("route")),
        "duplicate_of": _optional_string(payload.get("duplicate_of")),
        "resumed_from_run_id": _optional_string(payload.get("resumed_from_run_id")),
        "error_type": _optional_string(payload.get("error_type")),
        "error": _optional_string(payload.get("error")),
        "total_files": _optional_int(payload.get("total_files")),
        "processed_files": _optional_int(payload.get("processed_files")),
    }
    validate_payload(event_payload, "log.v1.schema.json")
    return event_payload


def _event_level(event: str) -> str:
    if event == "document_failed":
        return "error"
    if event in {"document_skipped_unsupported", "run_cancelled"}:
        return "warning"
    return "info"


def _legacy_event_payload(event_payload: dict[str, Any]) -> dict[str, Any]:
    legacy_payload: dict[str, Any] = {
        "event": event_payload["event"],
        "run_id": event_payload["run_id"],
    }
    for field in (
        "status",
        "relative_path",
        "filename",
        "format",
        "size_bytes",
        "warnings",
        "route",
        "duplicate_of",
        "resumed_from_run_id",
        "error_type",
        "error",
        "total_files",
        "processed_files",
    ):
        value = event_payload[field]
        if value is None:
            continue
        if field == "warnings" and not value:
            continue
        legacy_payload[field] = value
    return legacy_payload


def _append_validated_jsonl(path: Path, payload: dict[str, Any], schema_filename: str) -> None:
    validate_payload(payload, schema_filename)
    _append_jsonl(path, payload)


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    return int(str(value))


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None