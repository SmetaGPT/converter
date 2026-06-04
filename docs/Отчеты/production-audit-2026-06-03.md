# Аудит готовности к продакшену — 2026-06-03

Продукт: Windows Document Converter v0.3.0
Сверка с целями: `Agent_made.md` (агентный контур) + `docs/production-roadmap.md` (путь к v1.0).
Предыдущий независимый аудит: `docs/production-readiness-audit-2026-05-31.md`.

## 1. Вердикт

- Релизный статус: **production-ready в рамках declared scope v0.3.0**. Tag `v0.3.0` опубликован, hosted nightly + tag-driven release proof закрыты.
- **v1.0 GA не достигнут.** Заблокирован двумя классами gate: (a) provider-assisted formula evidence (S11.3), (b) time-based acceptance (S10.1). Дополнительно остаётся незакрытый инженерный долг S11.5 (S8.2) и S11.6.
- Локальные качественные сигналы зелёные: `unittest discover` (206 тестов, 4 skipped), `ruff` (strict E,F,W,I,UP,B,SIM), `pyright` (strict), `pip check`.

## 2. Что сделано

| Волна | Тема | Статус |
| --- | --- | --- |
| W0 | Stabilize baseline | ✅ (расхождение strict-config закрыто в S11.1) |
| W1 | Machine-readable contracts (v1 schemas) | ✅ |
| W2 | Demonolize (converter registry) | ✅ |
| W3 | Plug-in providers (`FormulaProvider`, `OcrBackend`, `CatalogWriter`) | ✅ |
| W4 | Determinism | 🟡 (timing-smoke и clean-VM proof открыты — S11.6) |
| W5 | Coverage expansion | 🟡 (S5.2/S5.3 закрыты в S11.4; S5.1 пороги не достигнуты) |
| W6 | Operator surface (JSON CLI, telemetry) | ✅ |
| W7 | Security baseline (hardening + Gitleaks) | ✅ |
| W8 | Harness consolidation | 🟡 (S8.1 частично; S8.2 не выполнен) |
| W9 | CI/CD automation (PR-gates, nightly, release) | ✅ hosted proof |
| W10 | v1.0 acceptance (S10.1) | 🔴 заблокирована |
| W11 | Production hardening | 🟡 S11.1/S11.2a/S11.2b/S11.4 закрыты; S11.3/S11.5/S11.6 открыты |

Ключевые закрытые слайсы post-v0.3.0:
- Provider cascade `local → Mathpix → OpenRouter/LLM normalizer → deterministic validator` с run-level cache, budget/cost guardrails и `review_required` propagation (S11.2a/S11.2b).
- Strict lint/type alignment (S11.1).
- Negative samples + Hypothesis property tests + coverage-сигнал в CI (S11.4).
- Table hardening (shared parser, row normalization, continuation merge, `table_structure_warning`).
- Hosted CI/CD: required PR-gates, `nightly-full-e2e`, tag-driven `release.yml`.

## 3. Что нужно для продакшена (v1.0 GA)

### Блокеры external (нельзя закрыть в текущей сессии)
1. **S11.3 — provider-assisted formula GA evidence.** Требует opt-in credentials (`MATHPIX_APP_ID`, `MATHPIX_APP_KEY`, `OPENROUTER_API_KEY` / `FORMULA_RECOGNITION_API_KEY`), live pilot на 10–20 реальных документах. Цели gate: `calc_expr_coverage ≥ 0.80`, `display_latex_coverage ≥ 0.90`, `review_required_rate ≤ 0.10`. Текущий baseline: `calc_expr=0.6776`, `native=0.1858`.
2. **S10.1 — time-based acceptance.** 4 недели telemetry без unresolved regressions (текущее окно ~10 дней) + 30 подряд зелёных portable EXE/package/smoke runs.

### Инженерный долг (закрывается локально, без external)
3. **S11.5 (W8 closeout).** S8.1 частично (archive создан, но bootstrap-contract не финализирован); S8.2 не выполнен — отсутствуют `schemas/agent-guardrails.v1.json`, `schemas/agent-stop-budgets.v1.json`, `scripts/validate_session_exit.py`.
4. **S11.6 (determinism/perf + oversize).** `src/doc_converter/formula_benchmark.py` = 1215 строк (порог 800, вырос с 1059) — требует split без слома CLI/report contract. Также: timing-smoke benchmark rerun `<30s` не зафиксирован; clean-VM real-renderer proof для bundled fonts открыт.
5. **Контракты v1 — финальный review.** Snapshots есть, но explicit GA-финализация (partial) перед bump-policy не выполнена.

## 4. Рекомендованный порядок доводки

1. Закрыть локальный долг, не требующий external: **S11.5** (guardrails schemas + `validate_session_exit.py`, финализация bootstrap-contract) и **S11.6** (split `formula_benchmark.py`, timing-smoke, font proof).
2. Провести финальный review контрактов v1.
3. По получении opt-in provider credentials — выполнить **S11.3** live pilot и зафиксировать provider-assisted benchmark report.
4. Накопить **S10.1** time-based evidence (4 недели telemetry + 30-run streak), затем публиковать tag `v1.0.0` с release notes и verdict «v1.0 GA» в `release-status.md`.

## 5. Сверка с метриками успеха Agent_made.md

Агентный operating model (state layer, multi-tier memory, lifecycle, specialist agents, eval loop, release loop, guardrails) — **внедрён**. Sprints 0–7 завершены. Единственный системный gap по целям Agent_made.md — **machine-readable guardrails/exit-checklist** (S8.2), который остаётся текстовым, а не enforced программно.

## 6. Источники

- `docs/state-snapshot.md`, `docs/current-status.md`, `docs/release-status.md`, `docs/current-sprint.md`
- `docs/production-roadmap.md` (Wave 0–11), `docs/production-readiness-audit-2026-05-31.md`
- Локальная проверка oversize: `formula_benchmark.py` = 1215 строк.
