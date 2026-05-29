# Current Sprint

Последнее обновление: 2026-05-29
Активный спринт: S2.3 — tables shared package
Статус: completed

Предыдущий приоритетный tranche: S2.2 — Split runner.py
Статус wave W2: in_progress

## 1. Цель спринта

Вынести dominant-width inference, continuation merge и `table_structure_warning` из PDF converters в shared `src/doc_converter/tables/` package и сохранить measured table behaviour для `pdf_text`/`pdf_scan`.

## 2. Артефакты спринта

- src/doc_converter/tables/__init__.py
- src/doc_converter/converters/pdf_text.py
- src/doc_converter/converters/pdf_scan.py
- tests/test_pdf_text_converter.py
- tests/test_pdf_scan_converter.py
- tests/test_sample_expectations.py
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
| Вынести shared table parser в `src/doc_converter/tables/` | Готово |
| Перевести `pdf_text` и `pdf_scan` на один parser import path | Готово |
| Подтвердить continuation/ragged-row behavior focused quartet tests | Готово |
| Подтвердить full PDF/sample-expectations slice без regressions | Готово |
| Подтвердить `sample_009/018` на fresh table-anchor run | Готово |
| Зафиксировать remaining follow-up после table package tranche | Готово |

## 4. Validation targets спринта

1. `runTests tests/test_pdf_text_converter.py::test_pdf_text_merges_table_continuation_lines_into_previous_cell tests/test_pdf_text_converter.py::test_pdf_text_marks_ragged_tables_with_warning_and_pads_rows tests/test_pdf_scan_converter.py::test_ocr_success_merges_table_continuation_lines tests/test_pdf_scan_converter.py::test_ocr_success_marks_ragged_table_warning_and_pads_rows` прошёл зелёно: 4 tests, OK.
2. `runTests tests/test_pdf_text_converter.py tests/test_pdf_scan_converter.py tests/test_sample_expectations.py` прошёл зелёно: 13 tests, OK.
3. `$env:PYTHONPATH = 'src'; .\.venv\Scripts\python.exe scripts\run_sample_pilot.py --manifest samples\manifest.table-anchors.jsonl --output runs\s23-table-anchors --input runs\s23-table-anchors-input --clean` прошёл зелёно: fresh run `runs\s23-table-anchors\runs\20260529T162149Z`, `2 success / 1 partial_success / 0 failed`, route mismatches `0`.
4. `$env:PYTHONPATH = 'src'; .\.venv\Scripts\python.exe scripts\validate_sample_expectations.py runs\s23-table-anchors\runs\20260529T162149Z --manifest samples\manifest.table-anchors.jsonl --expected-dir samples\expected --sample-id sample_009 --sample-id sample_018` вернул `status: ok`, `samples_failed: 0`.
5. `$env:PYTHONPATH = 'src'; .\.venv\Scripts\python.exe -m unittest discover -v` прошёл зелёно: 142 tests, OK.
6. `\.venv\Scripts\python.exe -m ruff check src tests scripts` прошёл зелёно.
7. `\.venv\Scripts\python.exe -m pyright` прошёл зелёно: 0 errors, 0 warnings.
8. `\.venv\Scripts\python.exe scripts\validate_harness_assets.py` вернул `status: ok`, `features: 32`, `validated: 32`, `telemetry_entries: 69`.

## 5. Риски спринта

- Shared parser package снимает route drift в table normalization, но table unit assembly пока всё ещё живёт в самих converters, поэтому следующий architecture step лежит уже не в parser heuristics, а в route registry / richer table semantics.
- Repo-wide file-size debt после закрытия S2.3 по-прежнему остаётся только в `src/doc_converter/formula_benchmark.py`.
- Full unittest discover в этом shell-контуре надёжнее запускать с явным `PYTHONPATH=src`, чтобы discovery не терял import context для `src/`.

## 6. Критерий выхода

Спринт закрыт: shared table parser вынесен в `src/doc_converter/tables/`, `pdf_text` и `pdf_scan` используют один и тот же normalizer, focused/full gates остаются зелёными, а measured anchors `sample_009/018` не показывают regression на fresh run.

## 7. Следующий operational focus

1. Начать S2.4 `ConverterProtocol` + route registry.
2. Отдельно вывести `src/doc_converter/formula_benchmark.py` из oversize-состояния как следующий architecture follow-up.
3. Затем продолжить measured table benchmark backlog и richer DOCX table semantics.
4. Продолжать выполнять prompt `.github/prompts/execute-production-roadmap-autonomous.prompt.md`: sprint → focused validation → state update → commit → push.
