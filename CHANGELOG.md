# Changelog

Все заметные изменения, влияющие на релизный контур, фиксируются здесь агентами.

## [Unreleased]

### Added

- Tag-driven GitHub Release automation: `push` of `v*` now rebuilds the portable package, re-runs EXE smoke and publishes zip plus checksum to GitHub Releases.
- Portable package release notes are now rendered from this changelog, so nightly and tagged builds share one repo-tracked source for release messaging.

## [0.3.0] - 2026-05-23

### Added

- Portable Windows package `DocumentConverter-0.3.0` with checksum and release notes.
- DOCX semantic extraction for formulas, headers, footers and footnotes.
- PDF text/OCR heuristic semantic units for tables, formulas and figure captions.
- Native XLSX route for workbook, sheet, cell and formula packages.
- Structured CLI surface with `doctor`, `dry-run`, formula evaluation and machine-readable exit envelopes.
- Synthetic E2E, package validation, EXE smoke and Windows CI package gates.
