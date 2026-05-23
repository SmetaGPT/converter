# Agent Weekly Eval

Дата среза: 2026-05-23
Окно: 2026-05-17 .. 2026-05-23 (7 дней)
Статус: strong

Этот отчёт generated из `docs/agent-quality-scorecard.v1.json`, `docs/agent-telemetry.v1.jsonl` и `docs/agent-weekly-reviews.v1.json`.

## 1. Snapshot

- telemetry entries in window: `14`;
- state updates in window: `14`;
- feature-traceable entries in window: `14`;
- validated features in spine: `22`;
- referenced features in telemetry: `22`.

## 2. Observed signals

| Signal | Score | Basis |
| --- | ---: | --- |
| Validation discipline | 5/5 | 14/14 telemetry entries have pass-like validation results. |
| State hygiene | 5/5 | 14/14 telemetry entries report state_update=true. |
| Feature traceability | 5/5 | 14/14 telemetry entries reference at least one feature_id. |
| Feature coverage in telemetry | 5/5 | 22/22 validated features are referenced by structured telemetry. |

## 3. Findings

- Открытых findings по текущему weekly snapshot нет.

## 4. Coverage gaps

- Coverage gaps нет: все validated feature_id уже наблюдаются в structured telemetry.

## 5. Qualitative sampling

- completed reviews in window: `1`;
- sampled tasks in window: `5`.

### Review `2026-05-23-first-completed-weekly-review`

- review date: `2026-05-23`; average sampled score: `12.6/14`.
- Первый completed weekly review после telemetry backfill; проверяет generated snapshot на реальных задачах из разных категорий.

| Task | Score | Interpretation | Note |
| --- | ---: | --- | --- |
| Sprint 1 state foundation | 12/14 | strong closeout | Исторический task slice до feature spine и формализованной local-hypothesis discipline. |
| Sprint 3 workflow hooks | 12/14 | strong closeout | Историческая задача до явной traceability discipline; quality подтверждена evidence и state sync. |
| Sprint 4 specialist routing | 12/14 | strong closeout | Ранний routing slice с retroactive traceability, но без quality defect в закрытии задачи. |
| SP folder e2e | 13/14 | strong closeout | Сильный product-facing slice; единственный потерянный балл связан с ранней формализацией traceability. |
| Generated weekly eval companion | 14/14 | strong closeout | Полный closeout после structured telemetry backfill и generated companion sync. |

## 6. Refresh command

- `.\.venv\Scripts\python.exe scripts\refresh_agent_eval.py`
- `.\.venv\Scripts\python.exe scripts\refresh_agent_eval.py --check --check-markdown`
