from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from ..config import ConverterConfig


@dataclass(frozen=True)
class DetectionResult:
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class ConversionOutcome:
    status: str
    units_count: int
    manifest_data: dict[str, object] = field(default_factory=dict)


class ConverterProtocol(Protocol):
    route: str

    def detect(self, path: Path) -> DetectionResult | None:
        ...

    def convert(
        self,
        source_path: Path,
        output_dir: Path,
        sha256: str,
        *,
        config: ConverterConfig,
        relative_source_path: str | None = None,
    ) -> ConversionOutcome:
        ...