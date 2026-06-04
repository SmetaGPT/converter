# Release Status

Последнее обновление: 2026-06-02
Релизный контур: Windows Document Converter v0.3.0
Статус: production-ready within declared scope. W9 hosted nightly + tag-driven release proof завершены. v1.0 GA остаётся blocked на S10.1 (time-based) и provider-assisted formula acceptance gates. Локальные strict-config, provider-hardening и S11.4 coverage-expansion слайсы закрыты. Оставшиеся blockers: S11.3 live provider evidence для малого formula corpus, отсутствие opt-in provider credentials в текущей сессии, external time window.

> Дайджест. Полная история релизного контура заархивирована: docs/archive/release-status-2026-06-03.md.

## 1. Цель релиза

Довести репозиторий до состояния, где агентный контур поддерживает полный цикл: baseline, state, memory, lifecycle, routing, evaluation, release discipline.

## 2. Что доказано (hosted proof)

- S9.1 PR-gates: `main` защищён strict required contexts (secret-scan, lint, typecheck, unit-tests, harness-validator, formula-benchmark-gate, document-package-validator, release-smoke); auto-merge для label `agent:autonomous`.
- S9.2 nightly: `nightly-full-e2e.yml` (synthetic e2e, formula monitor, CI-safe gate, table-anchor preflight, EXE smoke, portable package); auto-issue path доказан (issue #4).
- S9.3 release-automation: `release.yml` публикует portable release по `v*` tag; release-notes рендерятся из CHANGELOG.md. Tag `v0.3.0` опубликован: https://github.com/SmetaGPT/converter/releases/tag/v0.3.0

## 3. Закрытые слайсы post-v0.3.0

- Table hardening: shared table parser (`pdf_text`/`pdf_scan`), row width normalization, continuation merge, `table_structure_warning`; DOCX multiline + formula-like cell metadata.
- Table benchmark anchors: `sample_009`, `sample_018` executable specs; `sample_020` OCR-blocked baseline; validator `scripts/validate_sample_expectations.py`.
- Formula providers: `FormulaProvider` protocol (`LocalTesseractProvider`, `OpenRouterProvider`, `NullProvider`, `MathpixProvider`).
- Security baseline (S7.1) + secret-scan CI (S7.2, Gitleaks).
- Structured telemetry (S6.2, `telemetry.jsonl` по `log.v1`); CLI envelope `cli-result.v1` (S6.1).

## 4. Оставшиеся blockers до GA

- S11.3: live provider evidence для formula corpus — нужны opt-in provider credentials.
- S10.1: time-based GA acceptance — external time window.

## 5. Где искать детали

- Полная хронология: docs/archive/release-status-2026-06-03.md
- Product roadmap: docs/production-roadmap.md
- Feature traceability: docs/agent-feature-spine.json (grep по feature_id)
