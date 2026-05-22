# Current Status

Последнее обновление: 2026-05-22
Статус контура: wave 1 complete, operational use ready

## 1. Краткий снимок состояния

- roadmap source: Agent_made.md;
- Sprint 0 завершён;
- Sprint 1 завершён;
- Sprint 2 завершён;
- Sprint 3 завершён;
- Sprint 4 завершён;
- Sprint 5 завершён;
- Sprint 6 завершён;
- roadmap wave 1 завершена;
- state layer уже создан;
- repo-memory, lifecycle hooks, routing, eval loop и release loop ещё не завершены.

## 2. Что уже сделано

### Завершённые результаты

1. Зафиксирован baseline процесса до внедрения agent operating model.
2. Сделан inventory текущих assets и gaps.
3. Собран первый eval set.
4. Инициализирован quality scorecard.
5. Создан state layer: status, sprint, release, checkpoint и telemetry.
6. Добавлен root-level startup contract в AGENTS.md.
7. Описана memory model и hygiene policy.
8. Инициализирован repo-memory по категориям.
9. Созданы lifecycle docs, guardrails, stop budgets и hook contracts.
10. Добавлены reusable prompts для kickoff, closeout и blocker handling.
11. Созданы specialist agents первой волны.
12. Зафиксирована routing matrix и pilot-статус implementation mode.
13. Созданы eval rules, regression log, self-review template и instruction change log.
14. Quality scorecard расширен рабочей дельтой после Sprint 4.
15. Созданы release checklist, runbook, handoff rules и retrospective materials.
16. Выполнен первый corpus-level pilot на реальном наборе документов ФСНБ.
17. Создана дорожная карта Windows Document Converter со спринтами и structural units contract.
18. Для Sprint 0 зафиксированы sample-каталоги DOCX/PDF и representative manifest на 18 файлов.
19. Sprint 0 закрыт: PDF samples классифицированы, manifest расширен до 21 файла, созданы 5 expected structural-unit specs.
20. Реализован MVP batch core: CLI, run package, schemas, inventory, hashing, route detection, duplicate provenance и queue state.
21. Реализованы DOCX, PDF-text и PDF-scan routes; scan route имеет degraded mode без OCRmyPDF.
22. Добавлены quality gates, tkinter GUI, PyInstaller build script, downstream handoff и build/run documentation.
23. Выполнен representative pilot-run на DOCX, PDF-text и PDF-scan; собран Windows package `dist\DocumentConverter\DocumentConverter.exe`.
24. Выполнен полный 21-sample representative pilot-run: 21 processed, 18 success, 3 partial_success, 0 failed, route mismatches нет.
25. Добавлен CLI preflight `check-ocr`, который возвращает машинно-читаемый статус OCRmyPDF/Tesseract/Ghostscript runtime.
26. Добавлены Windows OCR runtime install notes и guarded helper `scripts/install-ocr-runtime.ps1`.
27. Создан project-local `.venv`, OCR runtime установлен и проверен: `ocrmypdf` в `.venv`, Tesseract/Ghostscript через `scoop`, `rus/eng/osd` traineddata доступны.
28. OCR executable discovery исправлен: converter и `check-ocr` находят локальный `ocrmypdf` рядом с активным `python.exe` без ручного PATH prepend.
29. Full representative pilot в новой среде дал 21 success, 0 partial_success, 0 failed.
30. Добавлены workspace-рекомендации VS Code и project-local настройки для `.venv`, unittest discovery, `src` extra path и исключения build artifacts из поиска.
31. Context7 подключён и запущен в workspace через `.vscode/mcp.json` как локальный stdio MCP сервер `npx -y @upstash/context7-mcp@latest`.

### Готовые артефакты

- docs/agent-baseline.md
- docs/agent-assets-inventory.md
- docs/agent-eval-tasks.md
- docs/agent-quality-scorecard.md
- docs/current-status.md
- docs/current-sprint.md
- docs/release-status.md
- docs/agent-task-checkpoint-template.md
- docs/agent-telemetry-log.md
- docs/agent-memory-model.md
- docs/agent-memory-hygiene.md
- docs/agent-lessons-template.md
- docs/agent-lifecycle.md
- docs/agent-guardrails.md
- docs/agent-tool-interface-audit.md
- docs/agent-stop-budgets.md
- docs/agent-routing-matrix.md
- docs/agent-evals.md
- docs/agent-regressions.md
- docs/agent-instruction-change-log.md
- docs/agent-self-review-template.md
- docs/document-converter-roadmap.md
- docs/document-converter-acceptance.md
- docs/build-and-run.md
- docs/ocr-runtime-windows.md
- docs/downstream-handoff.md
- .vscode/extensions.json
- .vscode/mcp.json
- .vscode/settings.json
- samples/manifest.sample.jsonl
- samples/pdf-text-layer-check.sample.json
- samples/expected/README.md
- samples/expected/sample_001.expected-units.json
- samples/expected/sample_003.expected-units.json
- samples/expected/sample_006.expected-units.json
- samples/expected/sample_009.expected-units.json
- samples/expected/sample_019.expected-units.json
- pyproject.toml
- src/doc_converter/
- tests/
- schemas/
- scripts/build-windows.ps1
- scripts/install-ocr-runtime.ps1
- AGENTS.md

## 3. Что делается сейчас

Текущий фокус: эксплуатация контура на реальных задачах и weekly eval cycle.

В работе:

- перевод scorecard с экспертной оценки на фактические weekly scores;
- hardening Windows Document Converter MVP;
- расширение PDF/table/figure extraction beyond baseline text route;
- GUI EXE manual smoke и installer polish.

## 4. Что идёт дальше

Следующая последовательность после закрытия Sprint 1:

1. Регулярный weekly eval loop.
2. Реальные full-cycle пилоты на прикладных задачах.
3. Hardening MVP на расширенном наборе ФСНБ.
4. Уточнение repo-memory по мере появления кода и окружения.

## 5. Открытые gaps

| Gap | Статус |
| --- | --- |
| Repo-memory по категориям | Готово |
| Lifecycle hooks | Готово |
| Guardrails и stop budgets | Готово |
| Specialist routing | Готово |
| Eval loop | Готово |
| Release-ready loop | Готово |

## 6. Source of truth matrix

| Область | Главный документ |
| --- | --- |
| Roadmap программы | Agent_made.md |
| Текущий статус проекта | docs/current-status.md |
| Активный спринт | docs/current-sprint.md |
| Ближайший релиз | docs/release-status.md |
| Baseline и метрики качества | docs/agent-quality-scorecard.md |
| Inventory agent assets | docs/agent-assets-inventory.md |
| Eval set | docs/agent-eval-tasks.md |
| Task checkpoint schema | docs/agent-task-checkpoint-template.md |
| Telemetry | docs/agent-telemetry-log.md |
| Memory policy | docs/agent-memory-model.md, docs/agent-memory-hygiene.md |
| Routing | docs/agent-routing-matrix.md, .github/agents/ |
| Release discipline | docs/ops/, docs/agent-handoffs.md |

## 7. Обязательный минимум обновления после задачи

После завершения нетривиальной задачи должны обновляться:

1. docs/current-status.md — краткое изменение статуса и следующий шаг;
2. docs/current-sprint.md — прогресс внутри активного спринта;
3. docs/agent-telemetry-log.md — validation target, результат и факт state update;
4. docs/release-status.md — если задача влияет на ближайший релиз;
5. repo-memory — если появился новый validated learning.

## 8. Resume hint

Если работа прерывается, возобновление должно начинаться в таком порядке:

1. docs/current-status.md;
2. docs/current-sprint.md;
3. docs/release-status.md;
4. последний актуальный task checkpoint;
5. relevant repo-memory notes.

## 9. Итог wave 1

Первая волна roadmap закрыта полностью. Репозиторий теперь содержит baseline, state layer, memory discipline, lifecycle hooks, routing, eval loop и release discipline в git-tracked виде.

## 10. Последний pilot-use

На реальном корпусе ФСНБ подтверждено, что набор документов смешанный: PDF, DOCX, XML/XSD, XLSX и ZIP-пакеты. Для этого корпуса нужен не единый OCR-конвейер, а multi-route ingest с schema-driven парсингом XML, native parsing для DOCX/XLSX и digital-first parsing для PDF с OCR fallback.

## 11. Текущий product roadmap

Source of truth для прикладной реализации Windows-конвертера: docs/document-converter-roadmap.md. Первая прикладная версия ограничена DOCX, PDF-text и PDF-scan, а главный переносимый результат — `document.v1.json` со stable structural units для будущего chunking, DB ingestion и поиска.

## 12. Sprint 0 samples

Для Sprint 0 выбраны источники:

- DOCX: `D:\ФСНБ\Документы\Загрузка НПА\metod`;
- PDF: `D:\ФСНБ\Документы\Загрузка НПА\SP`.

Стартовый representative set зафиксирован в `samples/manifest.sample.jsonl`: 8 DOCX, 10 PDF-text и 3 PDF-scan. Проверка `SP` показала, что все 343 PDF в этом каталоге имеют извлекаемый text layer; scan-кандидаты добавлены из `sub_law` и `Law`.

## 13. MVP implementation status

Windows Document Converter теперь имеет рабочий MVP-контур:

- CLI: `python -m doc_converter.cli convert-folder <input> <output>`;
- GUI: `python scripts\gui_entry.py` или собранный `dist\DocumentConverter\DocumentConverter.exe`;
- output package: `run.json`, `manifest.jsonl`, `queue-state.json`, `processing-log.jsonl`, `summary.json`, `errors.jsonl`, `documents/*/document.v1.json`;
- DOCX route создаёт paragraphs, tables, table cells, extracted DOCX media assets и `search_text.txt`;
- PDF-text route создаёт page/paragraph units без OCR;
- PDF-scan route сохраняет page units и OCR status; без OCRmyPDF возвращает `partial_success` с review flags;
- OCR runtime preflight доступен через `python -m doc_converter.cli check-ocr`;
- primary project environment: `.venv\Scripts\python.exe`;
- downstream handoff описан в `docs/downstream-handoff.md`.

Последняя проверка: `.\.venv\Scripts\python.exe -m unittest discover -v` прошёл; `.\.venv\Scripts\python.exe scripts\run_sample_pilot.py --clean` обработал 21 sample и дал 21 success без partial/failed; `.\.venv\Scripts\python.exe -m doc_converter.cli check-ocr` вернул `status: ready`; реальный OCR smoke на `PPRF_680.pdf` дал `processing.status: success` и `ocr_applied: true`; `scripts\build-windows.ps1` успешно собрал EXE из `.venv`.
