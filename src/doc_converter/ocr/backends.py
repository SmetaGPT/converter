from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from doc_converter.ocr_runtime import find_ocrmypdf_executable

OCR_BACKEND_TIMEOUT_SECONDS = 900


@dataclass(frozen=True)
class OcrBackendContext:
    source_path: Path
    searchable_pdf: Path
    sidecar_text: Path
    ocr_languages: tuple[str, ...]


@dataclass(frozen=True)
class OcrBackendResult:
    status: str
    backend_id: str
    status_payload: dict[str, Any]
    searchable_pdf: Path | None = None
    sidecar_text: Path | None = None
    message: str | None = None


class OCRBackend(Protocol):
    @property
    def backend_id(self) -> str: ...

    def run(self, context: OcrBackendContext) -> OcrBackendResult: ...


@dataclass(frozen=True)
class NullOcrBackend:
    backend_id: str = "null"

    def run(self, context: OcrBackendContext) -> OcrBackendResult:
        del context
        return OcrBackendResult(
            status="unavailable",
            backend_id=self.backend_id,
            status_payload={
                "engine": self.backend_id,
                "available": False,
                "status": "disabled",
            },
            message="OCR backend is disabled by configuration.",
        )


@dataclass(frozen=True)
class OcrmypdfBackend:
    backend_id: str = "ocrmypdf"

    def run(self, context: OcrBackendContext) -> OcrBackendResult:
        executable = find_ocrmypdf_executable()
        if executable is None:
            return OcrBackendResult(
                status="unavailable",
                backend_id=self.backend_id,
                status_payload={
                    "engine": self.backend_id,
                    "available": False,
                    "status": "unavailable",
                },
                message="OCRmyPDF is not available in the current runtime.",
            )

        command = [
            executable,
            "--mode",
            "skip",
            "--deskew",
            "--sidecar",
            str(context.sidecar_text),
            "-l",
            "+".join(context.ocr_languages),
            str(context.source_path),
            str(context.searchable_pdf),
        ]
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=OCR_BACKEND_TIMEOUT_SECONDS,
            check=False,
        )
        status_payload = {
            "engine": self.backend_id,
            "command": command,
            "returncode": completed.returncode,
            "stdout": completed.stdout[-4000:],
            "stderr": completed.stderr[-4000:],
        }
        if completed.returncode != 0:
            return OcrBackendResult(
                status="failed",
                backend_id=self.backend_id,
                status_payload=status_payload,
                message=completed.stderr.strip()[:1000] or "OCRmyPDF failed.",
            )
        return OcrBackendResult(
            status="success",
            backend_id=self.backend_id,
            status_payload=status_payload,
            searchable_pdf=context.searchable_pdf,
            sidecar_text=context.sidecar_text,
        )


def build_ocr_backend(backend: str | None) -> OCRBackend:
    normalized = (backend or "ocrmypdf").strip().lower()
    if normalized == "ocrmypdf":
        return OcrmypdfBackend()
    if normalized in {"null", "none", "disabled"}:
        return NullOcrBackend()
    raise RuntimeError(f"Unsupported OCR backend: {backend}")


__all__ = [
    "OCRBackend",
    "NullOcrBackend",
    "OcrBackendContext",
    "OcrBackendResult",
    "OcrmypdfBackend",
    "build_ocr_backend",
]
