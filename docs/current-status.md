# Current Status

Последнее обновление: 2026-05-23
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
- repo-memory, lifecycle hooks, routing, eval loop и release loop завершены;
- machine-readable harness and product feature spine, bootstrap contract, clean-exit contract, telemetry companion, generated scorecard companion и generated weekly eval companion добавлены.

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
32. Дорожная карта `docs/document-converter-roadmap.md` синхронизирована с фактическим исполнением Sprint 0-12 и расширена hardening backlog Sprint 13-16 по OCR, DOCX, PDF provenance и schema contract.
33. Sprint 13 выполнен: `pdf_scan` сохраняет OCR page boundaries, assets получают fingerprints и file metadata, в `source` добавлен `relative_input_path`.
34. Sprint 14 выполнен: DOCX converter переведён на реальный body order, headings/lists/captions выделяются как semantic units.
35. Sprint 15 выполнен в текущем scope: `pypdf` переведён на layout-first extraction, page provenance расширен до `bbox + coordinate_system + page size`, repeated edge blocks выделяются как `header`/`footer`.
36. Sprint 16 выполнен: schema contract ужесточён, `quality` нормализован на document и unit level, acceptance/build/OCR docs синхронизированы с emitters.
37. Добавлен GUI startup smoke test через инициализацию `ConverterApp`, а собранный `dist\DocumentConverter\DocumentConverter.exe` проходит automated launch smoke без мгновенного падения.
38. Повторная широкая validation после hardening прошла: full unittest suite даёт 23 passed.
39. Representative pilot после hardening остаётся зелёным: `runs\sample-pilot\runs\20260522T180732Z`, 21 success, 0 partial_success, 0 failed.
40. OCR runtime и build контур подтверждены после hardening: `check-ocr` возвращает `ready`, а `scripts\build-windows.ps1` успешно пересобирает Windows package.
41. Добавлен и ужесточён автономный workspace prompt `.github/prompts/production-readiness-hardening.prompt.md` для uninterrupted доведения проекта до production readiness по gates G1-G12 без остановок на approval/планировании.
42. Добавлена runtime schema validation для `run.v1`, `summary.v1`, `queue-state.v1`, `manifest.v1`, `document.v1`, `ocr-runtime.v1` и `chunks.v1`.
43. Runner теперь делает reuse предыдущего output для неизменённых файлов, не допускает перезаписи duplicate canonical package и реализует `include_originals`.
44. GUI доведён до operator-grade v0.2 surface: progress, current file, cancel, open output и summary counts.
45. Добавлены `review-required.jsonl`, richer summary reasons и `rotated_text` quality flag для PDF pages с rotation.
46. Добавлены `src/doc_converter/chunking.py`, `scripts/build_sample_chunks.py` и portability-safe `chunks.v1.jsonl` contract.
47. Добавлены `scripts/validate_run_package.py`, `scripts/run_synthetic_e2e.py`, `.github/workflows/windows-ci.yml` и `scripts/package-release.ps1`.
48. Сформирован portable release package v0.2.0 с checksum/release notes; production scope сужен и зафиксирован в release docs честно.
49. Добавлен `scripts/run_folder_e2e.py` и выполнен e2e на `D:\ФСНБ\Документы\для парсера\Российские\metod`: 52 discovered/supported/processed, 0 partial, 0 failed, 6010 chunks, run package validation ok.
50. Добавлен schema-backed semantic metadata block в `document.v1.json`: `title`, `document_type`, `short_summary`, `confidence`, `method`; финальный metod e2e подтвердил 52 processed, 0 failed, 6010 chunks, типы `приказ: 49`, `методические указания: 1`, `методическое пособие: 1`.
51. Выполнен real-folder e2e на `D:\ФСНБ\Документы\Загрузка НПА\SP`: 344 processed, 0 partial, 0 failed, 0 review_required, run package validation ok; routes `pdf_text: 343`, `docx_native: 1`, `metadata.document_type` заполнен во всех 344 canonical packages и классифицирован как `свод правил`.
52. Добавлены harness-артефакты article-grade уровня: `docs/agent-feature-spine.json`, `docs/agent-bootstrap-contract.md`, `docs/agent-session-exit-checklist.md`, `docs/agent-sprint-contract-template.md`, `docs/agent-evaluator-rubric.md`, schema `schemas/agent-feature-spine.v1.schema.json` и validator `scripts/validate_harness_assets.py`; validator встроен в Windows CI.
53. `docs/agent-feature-spine.json` расширен с process-only слоя до product-aware spine: добавлены core capabilities конвертера (`document.v1` package, DOCX/PDF routes, semantic metadata, quality/reporting, resume/dedup, chunking/handoff, GUI/release packaging), а validator теперь требует этот coverage как обязательный минимум.
54. Feature spine встроен в task-flow: bootstrap contract, sprint contract template, task checkpoint template, exit checklist и evaluator rubric теперь требуют traceability до `feature_id` и evidence paths, а `scripts/validate_harness_assets.py` проверяет эти связки через marker-based rules.
55. Добавлен machine-readable telemetry companion `docs/agent-telemetry.v1.jsonl` со schema `schemas/agent-telemetry-entry.v1.schema.json`; `scripts/validate_harness_assets.py` теперь валидирует telemetry JSONL, проверяет known `feature_id` и наличие хотя бы одной записи.
56. Добавлен generated scorecard companion `docs/agent-quality-scorecard.v1.json` со schema `schemas/agent-quality-scorecard.v1.schema.json` и генератором `scripts/build_agent_scorecard.py`; `scripts/validate_harness_assets.py` теперь валидирует schema и проверяет drift между feature spine, telemetry JSONL и scorecard.
57. Для generated scorecard добавлен markdown drift-check: `scripts/build_agent_scorecard.py` теперь умеет `--check-markdown` и `--sync-markdown`, а `scripts/validate_harness_assets.py` проверяет синхронность structured companion section в `docs/agent-quality-scorecard.md` с generated JSON.
58. Добавлен generated weekly eval companion: `scripts/build_agent_weekly_eval.py` собирает `docs/agent-weekly-eval.v1.json` и `docs/agent-weekly-eval.md` из scorecard и structured telemetry, а `scripts/validate_harness_assets.py` проверяет schema и drift для weekly snapshot.
59. В `docs/agent-telemetry.v1.jsonl` выполнен historical backfill для `state-layer`, `lifecycle-validation`, `routing-matrix` и `real-e2e-and-run-validation`; generated scorecard и weekly eval теперь показывают coverage `22/22` без unexplained gaps.
60. Проведён первый complete weekly review по `docs/agent-evaluator-rubric.md` на реальных задачах из разных категорий; recurring issues зафиксированы в `docs/agent-regressions.md`, assumptions обновлены в `docs/agent-quality-scorecard.md`, а `AGENTS.md` оставлен без изменений как достаточный operational contract.
61. Добавлен one-command refresh wrapper `scripts/refresh_agent_eval.py`; generated scorecard и weekly eval companions теперь пересобираются и проверяются одним вызовом вместо ручного двухкомандного шага.
62. Sampled task scores для weekly review вынесены в `docs/agent-weekly-reviews.v1.json` со schema `schemas/agent-weekly-reviews.v1.schema.json`, а generated weekly eval теперь несёт machine-readable qualitative sampling вместе с proxy signals.
63. `scripts/validate_harness_assets.py` переведён на agent-oriented failure diagnostics в формате `WHAT / WHY / FIX`; зелёный путь validator-а и failure-helper smoke подтверждены локально.
64. Закрыт follow-up по production audit от 2026-05-23: runner и GUI теперь reject overlapping input/output paths до inventory, mixed-input folders честно считают unsupported inputs, `workers` больше не эмитится в `run.json`, standalone scripts используют shared `scripts/sitecustomize.py`, а Windows CI валидирует `pip check`, `ruff`, `pyright`, EXE smoke и portable release artifact.
65. Закрыт последний P2 follow-up production audit: OCR runtime helper фиксирует SHA-256 для `eng`, `rus`, `osd` traineddata, проверяет direct downloads после `curl.exe`, удаляет mismatch artifact и документирует integrity verification в OCR runtime notes.
66. Закрыт post-release semantic/package bundle v0.3.0: DOCX route выделяет formulas, headers, footers и footnotes; PDF text/OCR routes выделяют heuristic `table`/`formula`/`figure` units; weekly eval получил guarded Windows schedule helper; portable package `DocumentConverter-0.3.0` пересобран с checksum `2ce1f979b0eecc7644ca52b903034c72d642a7cdef7c54b760e4b4d510ed72f8`.

### Готовые артефакты

- docs/agent-baseline.md
- docs/agent-assets-inventory.md
- docs/agent-eval-tasks.md
- docs/agent-quality-scorecard.md
- docs/agent-quality-scorecard.v1.json
- docs/agent-weekly-eval.md
- docs/agent-weekly-eval.v1.json
- docs/agent-weekly-reviews.v1.json
- docs/current-status.md
- docs/current-sprint.md
- docs/release-status.md
- docs/agent-task-checkpoint-template.md
- docs/agent-telemetry-log.md
- docs/agent-telemetry.v1.jsonl
- docs/agent-memory-model.md
- docs/agent-memory-hygiene.md
- docs/agent-lessons-template.md
- docs/agent-lifecycle.md
- docs/agent-bootstrap-contract.md
- docs/agent-feature-spine.json
- docs/agent-guardrails.md
- docs/agent-tool-interface-audit.md
- docs/agent-stop-budgets.md
- docs/agent-routing-matrix.md
- docs/agent-session-exit-checklist.md
- docs/agent-sprint-contract-template.md
- docs/agent-evaluator-rubric.md
- docs/agent-task-checkpoint-template.md
- docs/agent-bootstrap-contract.md
- docs/agent-evals.md
- docs/agent-regressions.md
- docs/agent-instruction-change-log.md
- docs/agent-self-review-template.md
- docs/document-converter-roadmap.md
- docs/document-converter-acceptance.md
- docs/build-and-run.md
- docs/ocr-runtime-windows.md
- docs/downstream-handoff.md
- .github/prompts/production-readiness-hardening.prompt.md
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
- schemas/agent-feature-spine.v1.schema.json
- schemas/agent-telemetry-entry.v1.schema.json
- schemas/agent-quality-scorecard.v1.schema.json
- schemas/agent-weekly-eval.v1.schema.json
- schemas/agent-weekly-reviews.v1.schema.json
- scripts/build_agent_scorecard.py
- scripts/build_agent_weekly_eval.py
- scripts/refresh_agent_eval.py
- scripts/register-agent-eval-schedule.ps1
- scripts/build-windows.ps1
- scripts/install-ocr-runtime.ps1
- scripts/run_folder_e2e.py
- scripts/validate_harness_assets.py
- AGENTS.md

## 3. Что делается сейчас

Текущий фокус: поддержание уже закрытого harness/eval contour для production-ready v0.3.0 scope и точечные улучшения только там, где они реально снижают operational overhead.

Последний production-audit follow-up закрыт локально и в repo contract: self-ingestion guard, truthful unsupported accounting, repo-local lint/type tooling, clean source-setup path и CI-backed release artifact validation теперь входят в штатный контур.

В работе:

- поддержание product-aware feature spine и feature-traceability workflow на следующих нетривиальных задачах;
- поддержание machine-readable telemetry companion без пропусков на следующих нетривиальных задачах;
- поддержание generated scorecard companion, weekly eval companion и markdown drift-check как штатной части weekly checks;
- optional historical telemetry backfill beyond the minimum coverage set, если понадобится более широкий retrospective analysis;
- дальнейшая оценка качества rule-based `document_type`/`short_summary` и heuristic semantic extraction на новых пакетах;
- optional OCR helper profile `jbig2`, `pngquant`, `verapdf` по мере необходимости.

## 4. Что идёт дальше

Следующая последовательность после закрытия Sprint 1:

1. Поддерживать weekly eval loop на реальных пакетах v0.3.0 как регулярный ritual, а не как bootstrap work.
2. Держать product-aware feature spine, sprint contract, checkpoint template и evaluator rubric обязательными на новых cross-module задачах.
3. Не допускать пропусков в machine-readable telemetry companion на новых нетривиальных задачах.
4. Использовать `scripts/register-agent-eval-schedule.ps1` только если weekly refresh действительно нужно перевести в Windows Scheduled Task.
5. Поддерживать `docs/agent-weekly-reviews.v1.json` синхронно с будущими completed weekly reviews.
6. Проверить heuristic semantic extraction на новых production-like пакетах и уточнять эвристики только по наблюдаемым ошибкам.
7. Optional OCR helpers и installer polish только если это потребуется по эксплуатации.

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
| Baseline и метрики качества | docs/agent-quality-scorecard.md, docs/agent-quality-scorecard.v1.json, docs/agent-weekly-eval.md, docs/agent-weekly-eval.v1.json, docs/agent-weekly-reviews.v1.json |
| Inventory agent assets | docs/agent-assets-inventory.md |
| Eval set | docs/agent-eval-tasks.md |
| Task checkpoint schema | docs/agent-task-checkpoint-template.md |
| Telemetry | docs/agent-telemetry-log.md, docs/agent-telemetry.v1.jsonl |
| Memory policy | docs/agent-memory-model.md, docs/agent-memory-hygiene.md |
| Routing | docs/agent-routing-matrix.md, .github/agents/ |
| Release discipline | docs/ops/, docs/agent-handoffs.md |

## 7. Обязательный минимум обновления после задачи

После завершения нетривиальной задачи должны обновляться:

1. docs/current-status.md — краткое изменение статуса и следующий шаг;
2. docs/current-sprint.md — прогресс внутри активного спринта;
3. docs/agent-telemetry-log.md и docs/agent-telemetry.v1.jsonl — validation target, результат и факт state update;
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
- `document.v1.json` содержит обязательный semantic metadata block: `title`, `document_type`, `short_summary`, `confidence`, `method`;
- DOCX route создаёт paragraphs, tables, table cells, extracted DOCX media assets и `search_text.txt`;
- PDF-text route создаёт page/paragraph units без OCR;
- PDF-scan route сохраняет page units и OCR status; без OCRmyPDF возвращает `partial_success` с review flags;
- OCR runtime preflight доступен через `python -m doc_converter.cli check-ocr`;
- primary project environment: `.venv\Scripts\python.exe`;
- downstream handoff описан в `docs/downstream-handoff.md`.

Последняя проверка: `.\.venv\Scripts\python.exe -m unittest discover -v` прошёл, 36 tests OK; `.\.venv\Scripts\python.exe scripts\run_folder_e2e.py "D:\ФСНБ\Документы\Загрузка НПА\SP" --output runs\sp-e2e --clean` создал `runs\sp-e2e\runs\20260522T205641Z` с 344 processed, 0 partial, 0 failed, 0 review_required и schema-valid package; routes `pdf_text: 343`, `docx_native: 1`; metadata заполнены во всех 344 canonical packages. Предыдущий metod run `runs\metod-e2e\runs\20260522T204542Z` остаётся зелёным: 52 processed, 0 partial, 0 failed, 6010 chunks; `.\.venv\Scripts\python.exe scripts\run_sample_pilot.py --clean` ранее обработал 21 sample и дал 21 success без partial/failed; `.\.venv\Scripts\python.exe -m doc_converter.cli check-ocr` вернул `status: ready`; реальный OCR smoke на `PPRF_680.pdf` дал `processing.status: success` и `ocr_applied: true`; `scripts\build-windows.ps1` успешно собрал EXE из `.venv`.
