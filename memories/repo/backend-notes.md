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
