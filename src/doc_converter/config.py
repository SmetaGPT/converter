from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ConverterOptions:
    ocr_languages: tuple[str, ...] = ("rus", "eng")
    include_originals: bool = False
    duplicate_policy: str = "record_provenance"


@dataclass(frozen=True)
class ConverterConfig:
    input_dir: Path
    output_dir: Path
    options: ConverterOptions = ConverterOptions()