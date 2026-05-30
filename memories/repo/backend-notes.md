# Backend Notes

## 2026-05-31 - Secret redaction must cover compatibility mirrors

- Trigger: `S3.3` artifact-scan test found an env secret in legacy `errors.jsonl` even after schema-backed telemetry was already redacted.
- Confirmed fact: secrets leak through the last serialization boundary, not through the conceptual ownership of an artifact. Compatibility mirrors and alternate formats like XLSX catalogs are the same leak surface as primary JSON/JSONL files.
- Practical guidance: apply `redact_secrets` at every run-artifact boundary (`run.json`, manifest/review JSONL, telemetry/errors mirrors, formula-recognition sidecars, catalog outputs), then scan the produced run directory for env values `*API_KEY*/*TOKEN*/*SECRET*`.
