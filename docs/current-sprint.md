# Current Sprint

Последнее обновление: 2026-05-29
Активный спринт: S1.3 — Agent run metadata + universal validator
Статус: completed

Предыдущий приоритетный tranche: S1.2 — Known formula patterns → data
Статус wave W1: completed

## 1. Цель спринта

Закрыть третий Wave 1 спринт production roadmap: сделать `run.json` трассируемым до автономного агента, добавить universal document-package validator и сохранить backward compatibility validator-ов для legacy run packages.

## 2. Артефакты спринта

- src/doc_converter/config.py
- src/doc_converter/cli.py
- src/doc_converter/runner.py
- schemas/run.v1.schema.json
- scripts/validate_run_package.py
- scripts/validate_document_package.py
- tests/test_cli_smoke.py
- tests/test_docx_converter.py
- pyproject.toml
- docs/current-status.md
- docs/current-sprint.md
- docs/production-roadmap.md
- docs/release-status.md
- docs/agent-feature-spine.json
- docs/agent-telemetry-log.md
- docs/agent-telemetry.v1.jsonl

## 3. Задачи спринта

| Задача | Статус |
| --- | --- |
| Сделать `agent_run_metadata` обязательным в `run.v1` для новых run packages | Готово |
| Прокинуть agent metadata через CLI flags и runner defaults | Готово |
| Сохранить legacy compatibility в `validate_run_package.py` | Готово |
| Добавить `scripts/validate_document_package.py` для `document.v1.json` и `formula-recognition.jsonl` | Готово |
| Добавить focused tests для default/custom agent metadata | Готово |
| Устранить env-dependent DOCX test contamination от formula-recognition defaults | Готово |

## 4. Validation targets спринта

1. `\.venv\Scripts\python.exe -m unittest tests.test_cli_smoke.CliSmokeTests.test_empty_folder_creates_run_package tests.test_cli_smoke.CliSmokeTests.test_run_metadata_records_agent_run_metadata tests.test_cli_smoke.CliSmokeTests.test_convert_folder_cli_accepts_agent_metadata_flags` прошёл зелёно.
2. `\.venv\Scripts\python.exe scripts\validate_run_package.py runs\formula-benchmark\runs\20260525T175329Z\cases\anchor-421-pr\output\runs\20260525T175329Z` прошёл зелёно с `legacy_agent_run_metadata: true`.
3. `\.venv\Scripts\python.exe scripts\validate_document_package.py runs\formula-benchmark\runs\20260525T175329Z\cases\anchor-421-pr\output\runs\20260525T175329Z` прошёл зелёно.
4. Fresh empty run c CLI agent flags прошёл через обе проверки: `scripts\validate_run_package.py` вернул `legacy_agent_run_metadata: false`, `scripts\validate_document_package.py` вернул `documents_validated: 0`.
5. `\.venv\Scripts\python.exe -m unittest discover` прошёл зелёно: 142 tests, OK.
6. `\.venv\Scripts\python.exe -m ruff check src tests scripts` прошёл зелёно.
7. `\.venv\Scripts\python.exe -m pyright` прошёл зелёно: 0 errors, 0 warnings.

## 5. Риски спринта

- Исторические `run.json` без `agent_run_metadata` не становятся schema-valid сами по себе; backward compatibility обеспечивается через `scripts/validate_run_package.py`, который синтезирует legacy metadata только на validation path.
- Converter-level DOCX tests не должны зависеть от environment-provided formula-recognition config; для изолированных unit tests теперь нужен явный пустой `FormulaRecognitionConfig()`.
- `validate_document_package.py` валидирует canonical `document.v1.json` и `formula-recognition.jsonl` sidecar, но не заменяет более широкий run-package validator.

## 6. Критерий выхода

Спринт закрыт: каждый новый run package содержит `agent_run_metadata`, CLI умеет фиксировать `agent_id/agent_version/task_id/parent_run_id`, legacy runs продолжают проходить validator через fallback, universal document validator добавлен, а focused/full gates и harness refresh остаются зелёными.

## 7. Следующий operational focus

1. Начать S2.1 `Split converters/docx.py`.
2. При разрезании `docx.py` сохранить текущий public API и data-driven formula layer из S1.2/S1.3.
3. Продолжать выполнять prompt `.github/prompts/execute-production-roadmap-autonomous.prompt.md`: sprint → focused validation → state update → commit → push.
