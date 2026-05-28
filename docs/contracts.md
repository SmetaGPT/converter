# Stable Output Contracts

This file is the human-readable catalog for contracts that autonomous agents and downstream consumers may depend on. A change to any stable schema below must update `schemas/__snapshot__/stable-contracts.v1.json`, add migration notes, and run the contract stability tests.

## Contract Matrix

| Contract | Artifact | Producer | Schema | Consumer expectation |
| --- | --- | --- | --- | --- |
| `processed-documents-catalog.v1` | `<run_dir>/processed-documents-catalog.json` | `doc_converter.runner._write_processed_documents_catalog` | `schemas/processed-documents-catalog.v1.schema.json` | One run-level document inventory with original filenames, output folders, status labels, and issue text. |
| `chunks.v1` | `<run_dir>/chunks.v1.jsonl` | `doc_converter.chunking.build_chunks` and sample/e2e scripts | `schemas/chunks.v1.schema.json` | JSONL records keyed by stable `chunk_id`, `document_id`, and non-empty `unit_refs`; no extra fields. |
| `chunk-source.v1` | downstream source mapping payloads | downstream handoff tooling | `schemas/chunk-source.v1.schema.json` | Chunk provenance shape that preserves document identity, unit refs, text, section path, pages, and asset refs. Extra fields remain allowed for downstream annotations. |
| `formula-recognition.v1` | `<document_dir>/formula-recognition.jsonl` | `doc_converter.formula_recognition.run_formula_recognition_postprocess` | `schemas/formula-recognition.v1.schema.json` | JSONL audit trail for attempted formula recognition, with explicit status and no serialized credentials. |

## Stability Rules

1. Stable schemas are versioned by filename and `schema_version` or artifact title where applicable.
2. Compatible additions require tests and documentation updates. Breaking changes require a new `*.v2.schema.json` file instead of mutating the stable v1 contract.
3. `schemas/__snapshot__/stable-contracts.v1.json` stores SHA-256 fingerprints for the current stable schema set. It is intentionally small so drift is visible in code review.
4. `tests/test_contracts_stability.py` is the focused guard for schema drift and representative formula-recognition record shapes.
5. `scripts/validate_run_package.py` validates run-level package artifacts and document-level `formula-recognition.jsonl` files when present.

## Validation Commands

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_contracts_stability
.\.venv\Scripts\python.exe scripts\validate_harness_assets.py
```
