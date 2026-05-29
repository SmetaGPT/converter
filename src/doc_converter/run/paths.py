from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path


class ConverterError(RuntimeError):
    """Raised when a conversion run cannot be started."""


def validate_run_directories(input_dir: Path, output_dir: Path) -> tuple[Path, Path]:
    resolved_input_dir = input_dir.expanduser().resolve()
    resolved_output_dir = output_dir.expanduser().resolve()

    _validate_startup_paths(resolved_input_dir, resolved_output_dir)
    return resolved_input_dir, resolved_output_dir


def _validate_startup_paths(input_dir: Path, output_dir: Path) -> None:
    if not input_dir.exists():
        raise ConverterError(f"Input directory does not exist: {input_dir}")
    if not input_dir.is_dir():
        raise ConverterError(f"Input path is not a directory: {input_dir}")
    if output_dir.exists() and not output_dir.is_dir():
        raise ConverterError(f"Output path is not a directory: {output_dir}")
    if _paths_overlap(input_dir, output_dir):
        raise ConverterError(
            "Input and output directories must be different and must not be nested inside each other: "
            f"input={input_dir}, output={output_dir}"
        )
    output_dir.mkdir(parents=True, exist_ok=True)


def _paths_overlap(first_path: Path, second_path: Path) -> bool:
    return _is_relative_to(first_path, second_path) or _is_relative_to(second_path, first_path)


def _is_relative_to(path: Path, other_path: Path) -> bool:
    try:
        path.relative_to(other_path)
    except ValueError:
        return False
    return True


def _new_run_id() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _allocate_run_dir(runs_dir: Path, base_run_id: str) -> Path:
    runs_dir.mkdir(parents=True, exist_ok=True)
    candidate = runs_dir / base_run_id
    if not candidate.exists():
        candidate.mkdir()
        return candidate

    for index in range(1, 1000):
        candidate = runs_dir / f"{base_run_id}-{index:03d}"
        if not candidate.exists():
            candidate.mkdir()
            return candidate

    raise ConverterError(f"Unable to allocate run directory under: {runs_dir}")


def _document_output_dir(documents_dir: Path, sha256: str) -> Path:
    document_dir = _document_output_path(documents_dir, sha256)
    document_dir.mkdir(parents=True, exist_ok=True)
    return document_dir


def _document_output_path(documents_dir: Path, sha256: str) -> Path:
    return documents_dir / f"sha256_{sha256}"