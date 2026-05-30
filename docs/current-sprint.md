# Current Sprint

Последнее обновление: 2026-05-30
Активный спринт: S6.1 — Structured CLI
Статус: completed

Предыдущий приоритетный tranche: S2.4 — ConverterProtocol + route registry
Статус: completed
Статус wave W6: in_progress

## 1. Цель спринта

Сделать CLI основным machine-readable operator surface: human output оставить default для человека, а для автономных агентов зафиксировать `cli-result.v1`, exit-code matrix `0/10/20/30/40/50` и отдельные preflight-команды `doctor`/`dry-run`.

## 2. Артефакты спринта

- src/doc_converter/cli.py
- schemas/cli-result.v1.schema.json
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
| Ввести единый `cli-result.v1` envelope для JSON-режима CLI | Готово |
| Зафиксировать exit-code matrix `0/10/20/30/40/50` через CLI handlers | Готово |
| Добавить `document-converter doctor` для OCR/schema/font/provider preflight | Готово |
| Добавить `document-converter dry-run` для inventory/classification без записи | Готово |
| Обновить CLI smoke tests так, чтобы они покрывали каждый subcommand и каждый exit code | Готово |

## 4. Validation targets спринта

1. `runTests tests/test_cli_smoke.py` прошёл зелёно: 29 tests, 0 failed.
2. `runTests` прошёл зелёно: 203 tests, 0 failed.
3. `$env:PYTHONPATH = 'src'; .\.venv\Scripts\python.exe -m ruff check src tests scripts` прошёл зелёно.
4. `$env:PYTHONPATH = 'src'; .\.venv\Scripts\python.exe -m pyright` прошёл зелёно: 0 errors, 0 warnings.
5. `$env:PYTHONPATH = 'src'; .\.venv\Scripts\python.exe scripts\refresh_agent_eval.py` пересобрал generated companions без drift.
6. `$env:PYTHONPATH = 'src'; .\.venv\Scripts\python.exe scripts\validate_harness_assets.py` вернул `status: ok`, `features: 36`, `validated: 36`, `telemetry_entries: 71`.

## 5. Риски спринта

- `doctor` теперь честно показывает отсутствие bundled fonts до закрытия S4.3, поэтому часть preflight-checks на текущем main остаётся `environment_invalid` по делу, а не из-за broken CLI contract.
- Structured CLI закрывает operator decision surface, но до S6.2 runtime events всё ещё живут в legacy JSONL/log files без единой event schema.
- Repo-wide file-size debt вне critical path по-прежнему локализован в `src/doc_converter/formula_benchmark.py`.

## 6. Критерий выхода

Спринт закрыт: CLI по умолчанию human-readable, `--output-format=json` выдаёт schema-backed `cli-result.v1`, exit codes соответствуют матрице `0/10/20/30/40/50`, `doctor` и `dry-run` доступны как отдельные subcommands, а focused smoke tests покрывают каждый subcommand и каждый exit code.

## 7. Следующий operational focus

1. Открыть critical-path sprint S6.2 и перевести runtime events на structured logs/telemetry schema.
2. Затем закрыть S7.1 input hardening и `docs/security.md`.
3. После security baseline вернуться к S7.2 secret-scan CI и далее к S9.x automation.
4. Держать `src/doc_converter/formula_benchmark.py` как отдельный non-critical follow-up по oversize debt.
5. После critical path продолжать measured table backlog и richer DOCX semantics.
