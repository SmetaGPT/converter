from __future__ import annotations

import unittest

from doc_converter.release_notes import render_release_notes, resolve_release_section


CHANGELOG_TEXT = """# Changelog

## [Unreleased]

### Added

- Nightly artifact publication.

## [0.3.1] - 2026-05-30

### Added

- Tagged release publication.

## [0.3.0] - 2026-05-23

### Added

- Baseline package.
"""


class ReleaseNotesTests(unittest.TestCase):
    def test_resolve_release_section_prefers_exact_version(self) -> None:
        section, resolution = resolve_release_section(CHANGELOG_TEXT, "0.3.1")

        self.assertEqual(resolution, "exact")
        self.assertEqual(section.version, "0.3.1")
        self.assertIn("Tagged release publication.", section.body)

    def test_resolve_release_section_uses_unreleased_for_prerelease(self) -> None:
        section, resolution = resolve_release_section(CHANGELOG_TEXT, "0.3.1-nightly")

        self.assertEqual(resolution, "unreleased")
        self.assertEqual(section.version, "Unreleased")
        self.assertIn("Nightly artifact publication.", section.body)

    def test_render_release_notes_includes_exact_section_and_validation_commands(self) -> None:
        notes = render_release_notes(
            name="DocumentConverter",
            version="0.3.1",
            artifact_name="DocumentConverter-0.3.1-windows-portable.zip",
            checksum="ABCDEF",
            changelog_text=CHANGELOG_TEXT,
            validation_commands=("python -m unittest discover -v",),
        )

        self.assertIn("# DocumentConverter 0.3.1", notes)
        self.assertIn("SHA256: abcdef", notes)
        self.assertIn("Tagged release publication.", notes)
        self.assertNotIn("Nightly artifact publication.", notes)
        self.assertIn("`python -m unittest discover -v`", notes)

    def test_resolve_release_section_rejects_missing_stable_version(self) -> None:
        with self.assertRaisesRegex(ValueError, "does not contain a section for version '0.3.9'"):
            resolve_release_section(CHANGELOG_TEXT, "0.3.9")
