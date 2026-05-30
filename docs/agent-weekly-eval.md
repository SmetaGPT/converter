# Agent Weekly Eval

Дата среза: 2026-05-30
Окно: 2026-05-24 .. 2026-05-30 (7 дней)
Статус: strong

Этот отчёт generated из `docs/agent-quality-scorecard.v1.json`, `docs/agent-telemetry.v1.jsonl` и `docs/agent-weekly-reviews.v1.json`.

## 1. Snapshot

- telemetry entries in window: `48`;
- state updates in window: `48`;
- feature-traceable entries in window: `48`;
- validated features in spine: `36`;
- referenced features in telemetry: `36`.

## 2. Observed signals

| Signal | Score | Basis |
| --- | ---: | --- |
| Validation discipline | 5/5 | 71/71 telemetry entries have pass-like validation results. |
| State hygiene | 5/5 | 71/71 telemetry entries report state_update=true. |
| Feature traceability | 5/5 | 71/71 telemetry entries reference at least one feature_id. |
| Feature coverage in telemetry | 5/5 | 36/36 validated features are referenced by structured telemetry. |

## 3. Findings

- Открытых findings по текущему weekly snapshot нет.

## 4. Coverage gaps

- Coverage gaps нет: все validated feature_id уже наблюдаются в structured telemetry.

## 5. Qualitative sampling

- completed reviews in window: `0`;
- sampled tasks in window: `0`.

- Machine-readable qualitative sampling для этого окна пока не зафиксирован.

## 6. Refresh command

- `.\.venv\Scripts\python.exe scripts\refresh_agent_eval.py`
- `.\.venv\Scripts\python.exe scripts\refresh_agent_eval.py --check --check-markdown`
