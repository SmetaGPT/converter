from __future__ import annotations

import sys
from pathlib import Path

FONT_SUFFIXES = frozenset({".otf", ".ttc", ".ttf"})
ROOT = Path(__file__).resolve().parents[2]


def font_bundle_candidates() -> tuple[Path, ...]:
    candidates: list[Path] = []
    if getattr(sys, "frozen", False):
        executable_dir = Path(sys.executable).resolve().parent
        candidates.extend(
            [
                executable_dir / "assets" / "fonts",
                executable_dir / "_internal" / "assets" / "fonts",
            ]
        )
    candidates.append(ROOT / "assets" / "fonts")

    unique: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(resolved)
    return tuple(unique)


def font_bundle_directory() -> Path:
    candidates = font_bundle_candidates()
    return next((candidate for candidate in candidates if candidate.exists()), candidates[0])


def bundled_font_paths() -> tuple[Path, ...]:
    fonts: list[Path] = []
    seen: set[Path] = set()
    for bundle_dir in font_bundle_candidates():
        if not bundle_dir.exists():
            continue
        for path in sorted(bundle_dir.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in FONT_SUFFIXES:
                continue
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            fonts.append(resolved)
    return tuple(fonts)