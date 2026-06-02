from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

DEFAULT_VALIDATION_COMMANDS: tuple[str, ...] = (
    "python -m pip check",
    "python -m ruff check src tests scripts",
    "python -m pyright",
    "python -m unittest discover -v",
    "python scripts\\run_synthetic_e2e.py --clean",
    "powershell -ExecutionPolicy Bypass -File scripts\\build-windows.ps1 -Name DocumentConverter",
    "powershell -ExecutionPolicy Bypass -File scripts\\smoke-test-windows-exe.ps1 -ExePath dist\\DocumentConverter\\DocumentConverter.exe",
)

_SECTION_RE = re.compile(r"^## \[(?P<version>[^\]]+)\](?:\s*-\s*(?P<date>.+))?$", re.MULTILINE)


@dataclass(frozen=True)
class ChangelogSection:
    version: str
    date: str | None
    body: str


def _normalize_version(value: str) -> str:
    normalized = value.strip()
    if normalized.lower().startswith("v"):
        normalized = normalized[1:]
    return normalized.lower()


def parse_changelog_sections(text: str) -> dict[str, ChangelogSection]:
    matches = list(_SECTION_RE.finditer(text))
    if not matches:
        raise ValueError("CHANGELOG.md does not contain any '## [version]' sections.")

    sections: dict[str, ChangelogSection] = {}
    for index, match in enumerate(matches):
        section_start = match.end()
        section_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[section_start:section_end].strip()
        version = match.group("version").strip()
        sections[_normalize_version(version)] = ChangelogSection(
            version=version,
            date=match.group("date").strip() if match.group("date") else None,
            body=body,
        )
    return sections


def resolve_release_section(changelog_text: str, version: str) -> tuple[ChangelogSection, str]:
    sections = parse_changelog_sections(changelog_text)
    normalized_version = _normalize_version(version)

    exact = sections.get(normalized_version)
    if exact is not None:
        return exact, "exact"

    if "-" in normalized_version:
        unreleased = sections.get("unreleased")
        if unreleased is not None:
            return unreleased, "unreleased"

    raise ValueError(
        f"CHANGELOG.md does not contain a section for version '{version}' "
        "and no [Unreleased] fallback is available for prerelease builds."
    )


def render_release_notes(
    *,
    name: str,
    version: str,
    artifact_name: str,
    checksum: str,
    changelog_text: str,
    validation_commands: Sequence[str] = DEFAULT_VALIDATION_COMMANDS,
) -> str:
    section, resolution = resolve_release_section(changelog_text, version)
    checksum_value = checksum.strip().lower()

    lines: list[str] = [
        f"# {name} {version}",
        "",
        "## Artifact",
        f"- Artifact: {artifact_name}",
        f"- SHA256: {checksum_value}",
        "- Packaging: portable Windows zip",
        "",
        "## Highlights",
    ]

    if resolution == "unreleased":
        lines.append("- Source changelog section: [Unreleased] (prerelease/nightly fallback)")
    elif section.date:
        lines.append(f"- Source changelog section: [{section.version}] - {section.date}")
    else:
        lines.append(f"- Source changelog section: [{section.version}]")
    lines.append("")

    if section.body:
        lines.extend(section.body.splitlines())
    else:
        lines.append("- No changelog notes recorded.")

    lines.extend(
        [
            "",
            "## Validation baseline",
            *[f"- `{command}`" for command in validation_commands],
            "",
        ]
    )
    return "\n".join(lines)


def write_release_notes(
    *,
    output_path: Path,
    name: str,
    version: str,
    artifact_name: str,
    checksum: str,
    changelog_path: Path,
    validation_commands: Sequence[str] = DEFAULT_VALIDATION_COMMANDS,
) -> Path:
    changelog_text = changelog_path.read_text(encoding="utf-8")
    notes = render_release_notes(
        name=name,
        version=version,
        artifact_name=artifact_name,
        checksum=checksum,
        changelog_text=changelog_text,
        validation_commands=validation_commands,
    )
    output_path.write_text(notes, encoding="utf-8")
    return output_path
