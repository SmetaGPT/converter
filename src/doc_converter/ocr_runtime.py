from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def detect_ocr_runtime(ocr_languages: tuple[str, ...] = ("rus", "eng")) -> dict[str, Any]:
    ocrmypdf_path = find_ocrmypdf_executable()
    tesseract_path = find_executable("tesseract")
    ghostscript_path = _find_ghostscript()
    installed_languages, language_warning = _tesseract_languages(tesseract_path)
    requested_languages = list(ocr_languages)
    missing_languages = [language for language in requested_languages if language not in installed_languages]

    warnings: list[str] = []
    if ocrmypdf_path is None:
        warnings.append("OCRmyPDF CLI is not available in the active runtime.")
    if tesseract_path is None:
        warnings.append("Tesseract CLI is not available in PATH.")
    if ghostscript_path is None:
        warnings.append("Ghostscript CLI is not available in PATH.")
    if language_warning:
        warnings.append(language_warning)
    if tesseract_path is not None and missing_languages:
        warnings.append(f"Missing Tesseract languages: {', '.join(missing_languages)}.")

    ready = ocrmypdf_path is not None and tesseract_path is not None and ghostscript_path is not None and not missing_languages
    return {
        "schema_version": "ocr-runtime.v1",
        "status": "ready" if ready else "missing",
        "tools": {
            "ocrmypdf": _tool_payload(ocrmypdf_path),
            "tesseract": _tool_payload(tesseract_path),
            "ghostscript": _tool_payload(ghostscript_path),
        },
        "languages": {
            "requested": requested_languages,
            "installed": installed_languages,
            "missing": missing_languages,
        },
        "warnings": warnings,
    }


def find_ocrmypdf_executable() -> str | None:
    return find_executable("ocrmypdf", prefer_python_runtime=True)


def find_executable(executable: str, *, prefer_python_runtime: bool = False) -> str | None:
    if prefer_python_runtime:
        python_dir = Path(sys.executable).resolve().parent
        for candidate in _candidate_names(executable):
            candidate_path = python_dir / candidate
            if candidate_path.exists():
                return str(candidate_path)

    for candidate in _candidate_names(executable):
        path = shutil.which(candidate)
        if path is not None:
            return path
    return None


def _find_ghostscript() -> str | None:
    for executable in ("gswin64c", "gswin32c", "gs"):
        path = find_executable(executable)
        if path is not None:
            return path
    return None


def _candidate_names(executable: str) -> tuple[str, ...]:
    if os.name == "nt" and not executable.lower().endswith(".exe"):
        return (executable, f"{executable}.exe", f"{executable}.EXE")
    return (executable,)


def _tesseract_languages(tesseract_path: str | None) -> tuple[list[str], str | None]:
    if tesseract_path is None:
        return [], None
    try:
        completed = subprocess.run(
            [tesseract_path, "--list-langs"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return [], f"Unable to list Tesseract languages: {exc}."

    if completed.returncode != 0:
        warning = completed.stderr.strip() or completed.stdout.strip() or "Tesseract language listing failed."
        return [], warning[:1000]

    languages: list[str] = []
    for line in completed.stdout.splitlines():
        language = line.strip()
        if not language or language.lower().startswith("list of available languages"):
            continue
        languages.append(language)
    return languages, None


def _tool_payload(path: str | None) -> dict[str, Any]:
    return {
        "available": path is not None,
        "path": str(Path(path)) if path is not None else None,
    }