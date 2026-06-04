# Release Status

Последнее обновление: 2026-06-02
Релизный контур: Windows Document Converter v0.3.0
Статус: production-ready within declared scope; v1.0 GA blocked на S10.1 external time gate и S11.3 live provider evidence/credentials.

> Дайджест. Полная история релизного контура заархивирована: docs/archive/release-status-2026-06-03.md.

## 1. Цель релиза

Довести репозиторий до состояния, где агентный контур поддерживает полный цикл: baseline, state, memory, lifecycle, routing, evaluation, release discipline.

## 2. Что доказано (hosted proof)

- S9.1: `main` защищён required PR gates; auto-merge для label `agent:autonomous` доказан.
- S9.2: hosted nightly path доказан, включая monitor/preflight/release-smoke контур.
- S9.3: tag-driven portable release доказан; tag `v0.3.0` опубликован.

## 3. Закрытые слайсы post-v0.3.0

- Table hardening и benchmark anchors закрыты.
- Formula provider chain (`LocalTesseract`, `OpenRouter`, `Null`, `Mathpix`) и provider-assisted route operationally готовы.
- Security baseline + secret-scan CI и structured telemetry/CLI envelope закрыты.

## 4. Оставшиеся blockers до GA

- S11.3: live provider evidence для formula corpus — нужны opt-in provider credentials.
- S10.1: time-based GA acceptance — external time window.

## 5. Где искать детали

- Полная хронология: docs/archive/release-status-2026-06-03.md
- Product roadmap: docs/production-roadmap.md
- Feature traceability: docs/agent-feature-spine.json (grep по feature_id)
