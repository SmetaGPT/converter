# Agent Weekly Eval

Дата среза: 2026-05-31
Окно: 2026-05-25 .. 2026-05-31 (7 дней)
Статус: needs-attention

Этот отчёт generated из `docs/agent-quality-scorecard.v1.json`, `docs/agent-telemetry.v1.jsonl` и `docs/agent-weekly-reviews.v1.json`.

## 1. Snapshot

- telemetry entries in window: `67`;
- state updates in window: `67`;
- feature-traceable entries in window: `67`;
- validated features in spine: `56`;
- referenced features in telemetry: `57`.

## 2. Observed signals

| Signal | Score | Basis |
| --- | ---: | --- |
| Validation discipline | 5/5 | 103/105 telemetry entries have pass-like validation results. |
| State hygiene | 5/5 | 105/105 telemetry entries report state_update=true. |
| Feature traceability | 5/5 | 105/105 telemetry entries reference at least one feature_id. |
| Feature coverage in telemetry | 5/5 | 57/56 validated features are referenced by structured telemetry. |

## 3. Findings

- HIGH: В weekly window есть failed или blocked validation results. Рекомендация: Разобрать blocking entries и не считать weekly loop healthy, пока narrow validation не возвращён в pass-like state.

## 4. Coverage gaps

- Coverage gaps нет: все validated feature_id уже наблюдаются в structured telemetry.

## 5. Qualitative sampling

- completed reviews in window: `0`;
- sampled tasks in window: `0`.

- Machine-readable qualitative sampling для этого окна пока не зафиксирован.

## 6. Refresh command

- `.\.venv\Scripts\python.exe scripts\refresh_agent_eval.py`
- `.\.venv\Scripts\python.exe scripts\refresh_agent_eval.py --check --check-markdown`
