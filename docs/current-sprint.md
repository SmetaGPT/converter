# Current Sprint

Последнее обновление: 2026-05-30
Активный спринт: S6.2 — Structured logs and telemetry
Статус: completed

Предыдущий приоритетный tranche: S6.1 — Structured CLI
Статус: completed
Статус wave W6: in_progress

## 1. Цель спринта

Перевести runtime events на schema-backed telemetry contract: каждый run должен эмитить `telemetry.jsonl` по `log.v1`, а `validate_run_package.py` обязан валидировать этот event stream вместе с остальными run-package артефактами.

## 2. Артефакты спринта

- src/doc_converter/run/logging.py
- src/doc_converter/run/orchestration.py
- scripts/validate_run_package.py
- schemas/log.v1.schema.json
- tests/test_cli_smoke.py
- docs/current-status.md
- docs/current-sprint.md
- docs/production-roadmap.md
- docs/release-status.md
- docs/agent-feature-spine.json
- docs/agent-telemetry-log.md
- docs/agent-telemetry.v1.jsonl
- docs/agent-quality-scorecard.md
- docs/agent-quality-scorecard.v1.json
- docs/agent-weekly-eval.md
- docs/agent-weekly-eval.v1.json

## 3. Задачи спринта

| Задача | Статус |
| --- | --- |
| Добавить schema `log.v1` для runtime event stream | Готово |
| Ввести central logger adapter на orchestration boundary | Готово |
| Эмитить `runs/<id>/telemetry.jsonl` для каждого run и оставить legacy logs как compatibility mirrors | Готово |
| Дополнить `scripts/validate_run_package.py` проверкой telemetry JSONL | Готово |
| Обновить smoke tests так, чтобы они проверяли новый telemetry contract | Готово |

## 4. Validation targets спринта

1. `runTests tests/test_cli_smoke.py` прошёл зелёно: 29 tests, 0 failed.
2. `runTests` прошёл зелёно: 203 tests, 0 failed.
3. `$env:PYTHONPATH = 'src'; .\.venv\Scripts\python.exe scripts\validate_run_package.py <fresh_run_dir>` прошёл зелёно на новом run package с `telemetry.jsonl`.
4. `$env:PYTHONPATH = 'src'; .\.venv\Scripts\python.exe -m ruff check src tests scripts` прошёл зелёно.
5. `$env:PYTHONPATH = 'src'; .\.venv\Scripts\python.exe -m pyright` прошёл зелёно: 0 errors, 0 warnings.
6. `$env:PYTHONPATH = 'src'; .\.venv\Scripts\python.exe scripts\refresh_agent_eval.py` пересобрал generated companions без drift.
7. `$env:PYTHONPATH = 'src'; .\.venv\Scripts\python.exe scripts\validate_harness_assets.py` вернул `status: ok`, `features: 37`, `validated: 37`, `telemetry_entries: 72`.

## 5. Риски спринта

- Structured telemetry закрывает runtime event contract, но security/input hardening для untrusted документов всё ещё остаётся следующим critical path в S7.1.
- Legacy `processing-log.jsonl` и `errors.jsonl` пока сохранены как compatibility mirrors; их явное выключение или deprecation потребует отдельного operator-facing tranche.
- Repo-wide file-size debt вне critical path по-прежнему локализован в `src/doc_converter/formula_benchmark.py`.

## 6. Критерий выхода

Спринт закрыт: каждый run теперь пишет schema-backed `telemetry.jsonl` по `log.v1`, runtime events проходят через central logger adapter, `scripts/validate_run_package.py` валидирует telemetry contract, а focused smoke tests и реальный validator smoke подтверждают новый event stream без разрыва legacy compatibility logs.

## 7. Следующий operational focus

1. Открыть critical-path sprint S7.1 и закрыть threat model, input hardening limits и `docs/security.md`.
2. Затем закрыть S7.2 secret-scan CI и только потом возвращаться к S9.x automation.
3. После security baseline решить отдельным tranche судьбу legacy compatibility logs.
4. Держать `src/doc_converter/formula_benchmark.py` как отдельный non-critical follow-up по oversize debt.
5. После critical path продолжать measured table backlog и richer DOCX semantics.
