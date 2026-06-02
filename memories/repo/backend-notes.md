# Backend Notes

## 2026-05-31 - Secret redaction must cover compatibility mirrors

- Trigger: `S3.3` artifact-scan test found an env secret in legacy `errors.jsonl` even after schema-backed telemetry was already redacted.
- Confirmed fact: secrets leak through the last serialization boundary, not through the conceptual ownership of an artifact. Compatibility mirrors and alternate formats like XLSX catalogs are the same leak surface as primary JSON/JSONL files.
- Practical guidance: apply `redact_secrets` at every run-artifact boundary (`run.json`, manifest/review JSONL, telemetry/errors mirrors, formula-recognition sidecars, catalog outputs), then scan the produced run directory for env values `*API_KEY*/*TOKEN*/*SECRET*`.

## 2026-05-31 - Ordering must be enforced on records, not only traversal

- Trigger: `S4.1` determinism test forced two different `_iter_input_files` orders and showed that stable traversal alone is not the same thing as stable manifest semantics.
- Confirmed fact: duplicate-primary selection and manifest order remain vulnerable if the contract lives only in the filesystem iterator. Determinism has to be re-applied on finalized inventory records and duplicate groups with an explicit key such as `relative_path + sha256`.
- Practical guidance: whenever a new iterator source or preprocessing stage appears, sort the produced records again at the boundary that feeds artifacts or skip-logic, then keep a rerun test that injects conflicting iterator order and compares clean-run manifests.

## 2026-05-31 - Benchmark cache keys must include quality-artifact fingerprints

- Trigger: the first `S4.2` cache implementation reused a benchmark case after the gold payload changed at the same path, which would have hidden quality drift behind a cache hit.
- Confirmed fact: for benchmark caching, a manifest path string is not enough. The cache fingerprint has to include the content hash of linked quality artifacts such as `gold_path`, and `required_gate` still needs a fresh aggregate pass on every rerun.
- Practical guidance: build the per-entry cache key from `sha256(asset)` plus a manifest fingerprint that already embeds hashes of any referenced gold/quality files, and keep a regression test that changes the gold payload without moving the file path.

## 2026-05-31 - Font bundle resolution must be shared across runtime, doctor and packaging

- Trigger: the first S4.3 validation proved the new bundled-font code path was correct, but both focused tests still failed because `assets/fonts` was empty; before the repair, doctor/preflight and inline glyph matching were also using separate path contracts.
- Confirmed fact: bundled-font determinism only holds when runtime lookup, preflight reporting and PyInstaller datas all resolve the same `assets/fonts` bundle. Bare font names or implicit `C:/Windows/Fonts` fallbacks are not a stable production contract.
- Practical guidance: keep one helper for repo/frozen bundle directories, prefer bundled font files before system fonts, ship the font license next to the TTF, and validate both `_check_font_bundle` and `_available_inline_glyph_fonts` plus a build smoke whenever packaging paths change.

## 2026-05-31 - Formula review state must bubble above unit-level sidecars

- Trigger: `S11.2b` added provider cache/budget/review semantics, but the existing `review-required.jsonl` path only looked at document-level `quality` and would have missed low-confidence or budget-skipped formula cases if they stayed only inside `formula-recognition.jsonl`.
- Confirmed fact: formula-recognition sidecars are not the operator surface of record. Any provider outcome that changes human review load has to propagate into document-level `quality.flags` / `quality.warnings`, otherwise release telemetry and operator triage undercount real review work.
- Practical guidance: when adding postprocess-originated review semantics, trace the signal through all consumer layers (`document.v1.json`, run summary, `review-required.jsonl`, telemetry), not only through the specialist sidecar that produced it.

## 2026-05-31 - Strict typing only helps when legacy noise is declared explicitly

- Trigger: switching `pyright` to `typeCheckingMode = "strict"` for `S11.1` surfaced hundreds of diagnostics, but the bulk was not fresh correctness debt; it was legacy private-helper access in tests/re-export modules and loose JSON payload typing in scripts/validators.
- Confirmed fact: on this repository, strict mode is useful only if the high-volume historical noise is carved out explicitly. Otherwise real regressions disappear inside `reportPrivateUsage` / `reportUnknown*` floods and the gate stops being actionable.
- Practical guidance: keep strict mode enabled, but document every temporary carve-out in config and treat it as tracked debt. The goal is not zero theoretical diagnostics overnight; the goal is a green gate that still catches new regressions while the carve-out set shrinks intentionally over time.
