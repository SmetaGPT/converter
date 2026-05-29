# Current Sprint

Последнее обновление: 2026-05-29
Активный спринт: S2.2 — Split runner.py
Статус: completed

Предыдущий приоритетный tranche: S2.1 — Split converters/docx.py
Статус wave W2: in_progress

## 1. Цель спринта

Убрать orchestration monolith `src/doc_converter/runner.py`, вынести path/resume/catalog/postprocess/run logic в `src/doc_converter/run/` и сохранить текущий public API/import surface для `cli`, `gui` и regression tests.

## 2. Артефакты спринта

- src/doc_converter/runner.py
- src/doc_converter/run/__init__.py
- src/doc_converter/run/paths.py
- src/doc_converter/run/resume.py
- src/doc_converter/run/catalog.py
- src/doc_converter/run/postprocess.py
- src/doc_converter/run/orchestration.py
- tests/test_cli_smoke.py
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
| Вынести startup/path validation в `src/doc_converter/run/paths.py` | Готово |
| Разнести resume/catalog/postprocess/orchestration по smaller modules | Готово |
| Сохранить public imports через thin `src/doc_converter/runner.py` | Готово |
| Обновить monkeypatch targets в runner tests на concrete run submodules | Готово |
| Подтвердить focused и full validation без behavioral drift | Готово |
| Зафиксировать remaining file-size debt как follow-up вне runner slice | Готово |

## 4. Validation targets спринта

1. `runTests tests/test_cli_smoke.py::test_missing_input_directory_fails test_equal_input_and_output_directory_fails_before_run_starts test_output_directory_inside_input_fails_before_run_starts test_input_directory_inside_output_fails_before_run_starts` прошёл зелёно: 4 tests, OK.
2. `runTests tests/test_cli_smoke.py::test_empty_folder_creates_run_package test_run_metadata_records_agent_run_metadata test_runner_invokes_formula_recognition_postprocess_when_configured test_processed_documents_catalog_describes_output_folder_and_status test_failed_document_writes_review_required_file_and_failed_reason test_repeated_run_reuses_previous_output_for_unchanged_input` прошёл зелёно: 6 tests, OK.
3. `$env:PYTHONPATH = 'src'; .\.venv\Scripts\python.exe -m unittest discover -v` прошёл зелёно: 142 tests, OK.
4. `\.venv\Scripts\python.exe -m ruff check src tests scripts` прошёл зелёно.
5. `\.venv\Scripts\python.exe -m pyright` прошёл зелёно: 0 errors, 0 warnings.
6. `(Get-Content src\doc_converter\runner.py).Count` вернул `5`.
7. `\.venv\Scripts\python.exe scripts\validate_harness_assets.py` вернул `status: ok`, `features: 31`, `validated: 31`, `telemetry_entries: 68`.

## 5. Риски спринта

- Package-level re-export сохраняет compatibility, но internal monkeypatching теперь должно указывать на реальные `run/` submodule symbols, если implementation импортирует helper напрямую.
- Repo-wide file-size debt после закрытия S2.2 остаётся уже не в orchestration layer, а только в `src/doc_converter/formula_benchmark.py`.
- Full unittest discover в этом shell-контуре надёжнее запускать с явным `PYTHONPATH=src`, чтобы discovery не терял import context для `src/`.

## 6. Критерий выхода

Спринт закрыт: orchestration вынесен в `src/doc_converter/run/`, `src/doc_converter/runner.py` сокращён до thin wrapper, public API для `cli`/`gui` сохранён, focused/full gates остаются зелёными, а runner больше не содержит monolith-sized implementation.

## 7. Следующий operational focus

1. Начать S2.3 `tables/` shared package.
2. Отдельно вывести `src/doc_converter/formula_benchmark.py` из oversize-состояния как следующий architecture follow-up.
3. Затем продолжить measured table benchmark backlog и richer DOCX table semantics.
4. Продолжать выполнять prompt `.github/prompts/execute-production-roadmap-autonomous.prompt.md`: sprint → focused validation → state update → commit → push.
