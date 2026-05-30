# Current Sprint

Последнее обновление: 2026-05-30
Активный спринт: S2.4 — ConverterProtocol + route registry
Статус: completed

Предыдущий приоритетный tranche: S2.3 — tables shared package
Статус: completed
Статус wave W2: completed

## 1. Цель спринта

Убрать hard-coded knowledge о concrete converters из inventory/orchestration: route detection и conversion должны идти через shared registry и `ConverterProtocol`, а новый converter должен подключаться без правки runner logic.

## 2. Артефакты спринта

- src/doc_converter/converters/__init__.py
- src/doc_converter/converters/protocol.py
- src/doc_converter/converters/txt.py
- src/doc_converter/inventory.py
- src/doc_converter/run/orchestration.py
- tests/test_cli_smoke.py
- tests/test_converter_registry.py
- docs/current-status.md
- docs/current-sprint.md
- docs/production-roadmap.md
- docs/release-status.md
- docs/agent-feature-spine.json
- docs/agent-quality-scorecard.md
- docs/agent-quality-scorecard.v1.json
- docs/agent-telemetry.v1.jsonl
- docs/agent-weekly-eval.md
- docs/agent-weekly-eval.v1.json

## 3. Задачи спринта

| Задача | Статус |
| --- | --- |
| Ввести `ConverterProtocol` и route registry в `src/doc_converter/converters/` | Готово |
| Перевести `inventory.py` на registry-based detection | Готово |
| Перевести `run/orchestration.py` на registry-based dispatch | Готово |
| Обновить runner tests под новый abstraction layer | Готово |
| Добавить extensibility regression с dummy txt converter | Готово |

## 4. Validation targets спринта

1. `$env:PYTHONPATH = 'src'; .\.venv\Scripts\python.exe -m unittest tests.test_cli_smoke tests.test_converter_registry tests.test_inventory -v` прошёл зелёно: 28 tests, OK.
2. `runTests` прошёл зелёно: 200 tests, 0 failed.
3. `$env:PYTHONPATH = 'src'; .\.venv\Scripts\python.exe -m pip check` прошёл зелёно: `No broken requirements found.`
4. `$env:PYTHONPATH = 'src'; .\.venv\Scripts\python.exe -m ruff check src tests scripts` прошёл зелёно.
5. `$env:PYTHONPATH = 'src'; .\.venv\Scripts\python.exe -m pyright` прошёл зелёно: 0 errors, 0 warnings.
6. `$env:PYTHONPATH = 'src'; .\.venv\Scripts\python.exe scripts\refresh_agent_eval.py` выполнил repair generated companions после drift от новой telemetry/feature entry.
7. `$env:PYTHONPATH = 'src'; .\.venv\Scripts\python.exe scripts\validate_harness_assets.py` вернул `status: ok`, `features: 33`, `validated: 33`, `telemetry_entries: 70`.

## 5. Риски спринта

- Stable manifest/document schemas по-прежнему перечисляют только текущие product formats, поэтому architecture-only demo converter должен оставаться opt-in и изолированным от schema validation, пока product contract сознательно не расширяется.
- Следующий critical-path риск уже не в route coupling, а в отсутствии structured CLI/exit-code surface для автономных агентов.
- Repo-wide file-size debt после закрытия Wave 2 остаётся локализованным в `src/doc_converter/formula_benchmark.py`.

## 6. Критерий выхода

Спринт закрыт: `inventory` и `run/orchestration` используют shared `ConverterProtocol`/registry, orchestration больше не знает про конкретные форматы напрямую, а opt-in dummy `txt` converter доказывает extensibility через isolated regression test без изменения default route contract.

## 7. Следующий operational focus

1. Открыть critical-path sprint S6.1 и сделать structured CLI machine-readable contract основным operator surface.
2. Затем закрыть S6.2 для structured logs/telemetry schema.
3. Держать `src/doc_converter/formula_benchmark.py` как отдельный non-critical follow-up по oversize debt.
4. После operator surface вернуться к security hardening, measured table backlog и richer DOCX semantics.
