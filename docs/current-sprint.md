# Current Sprint

Последнее обновление: 2026-05-30
Активный спринт: S7.1 — Threat model и input hardening
Статус: completed

Предыдущий приоритетный tranche: S6.2 — Structured logs and telemetry
Статус: completed
Статус wave W7: in_progress

## 1. Цель спринта

Сделать обработку untrusted inputs fail-closed на самых дешёвых admission boundaries: запретить symlink/path confusion на старте, ограничить OOXML archive size и entry count, ограничить WMF blob/record parsing и зафиксировать эти правила в `docs/security.md`.

## 2. Артефакты спринта

- src/doc_converter/run/paths.py
- src/doc_converter/converters/docx/pipeline.py
- src/doc_converter/converters/docx/formulas/wmf.py
- tests/test_run_paths.py
- tests/test_docx_converter.py
- docs/security.md
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
| Ужесточить startup path validation для `input_dir`/`output_dir`/`runs_dir` | Готово |
| Ввести DOCX archive admission limits до `python-docx` и manual extraction | Готово |
| Ограничить WMF parser по размеру blob и количеству records | Готово |
| Добавить malicious-limit tests для DOCX и WMF | Готово |
| Зафиксировать threat model, subprocess inventory и font/path policy в `docs/security.md` | Готово |

## 4. Validation targets спринта

1. `runTests tests/test_docx_converter.py tests/test_run_paths.py` прошёл зелёно: 88 tests, 0 failed.
2. `$env:PYTHONPATH = 'src'; .\.venv\Scripts\python.exe -m unittest discover -v` прошёл зелёно: 156 tests, 0 failed, `skipped=4`.
3. `$env:PYTHONPATH = 'src'; .\.venv\Scripts\python.exe -m ruff check src tests scripts` прошёл зелёно.
4. `$env:PYTHONPATH = 'src'; .\.venv\Scripts\python.exe -m pyright` прошёл зелёно: 0 errors, 0 warnings.
5. `$env:PYTHONPATH = 'src'; .\.venv\Scripts\python.exe scripts\refresh_agent_eval.py` пересобрал generated companions без drift.
6. `$env:PYTHONPATH = 'src'; .\.venv\Scripts\python.exe scripts\validate_harness_assets.py` вернул `status: ok`, `features: 39`, `validated: 39`, `telemetry_entries: 73`.

## 5. Риски спринта

- Threat model и input hardening закрывают admission baseline для DOCX/WMF и startup paths, но required secret-scan gate по-прежнему остаётся следующим security tranche в S7.2.
- PDF/XLSX routes пока не имеют столь же явных parser-level size limits, как DOCX archive и WMF parser.
- Repo-wide file-size debt вне critical path по-прежнему локализован в `src/doc_converter/formula_benchmark.py`.

## 6. Критерий выхода

Спринт закрыт: startup admission отклоняет symlink-based path confusion, DOCX route проверяет archive limits до parse/extraction, WMF parser ограничен по размеру и record count, malicious-limit tests дают graceful reject path, а `docs/security.md` фиксирует threat model, subprocess inventory и font/path policy.

## 7. Следующий operational focus

1. Открыть critical-path sprint S7.2 и закрыть secret-scan CI как required leak gate.
2. Затем вернуться к S9.x automation и не смешивать его с remaining measured hardening backlog.
3. После security baseline решить отдельным tranche parser-level limits для PDF/XLSX, если они станут release-critical.
4. Держать `src/doc_converter/formula_benchmark.py` как отдельный non-critical follow-up по oversize debt.
5. После critical path продолжать measured table backlog и richer DOCX semantics.
