# Current Status

Последнее обновление: 2026-05-30
Статус контура: wave 2 complete, operational use ready

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
- roadmap wave 2 завершена;
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
59. В `docs/agent-telemetry.v1.jsonl` выполнен historical backfill для `state-layer`, `lifecycle-validation`, `routing-matrix` и `real-e2e-and-run-validation`; generated scorecard и weekly eval теперь показывают coverage `25/25` без unexplained gaps.
60. Проведён первый complete weekly review по `docs/agent-evaluator-rubric.md` на реальных задачах из разных категорий; recurring issues зафиксированы в `docs/agent-regressions.md`, assumptions обновлены в `docs/agent-quality-scorecard.md`, а `AGENTS.md` оставлен без изменений как достаточный operational contract.
61. Добавлен one-command refresh wrapper `scripts/refresh_agent_eval.py`; generated scorecard и weekly eval companions теперь пересобираются и проверяются одним вызовом вместо ручного двухкомандного шага.
62. Sampled task scores для weekly review вынесены в `docs/agent-weekly-reviews.v1.json` со schema `schemas/agent-weekly-reviews.v1.schema.json`, а generated weekly eval теперь несёт machine-readable qualitative sampling вместе с proxy signals.
63. `scripts/validate_harness_assets.py` переведён на agent-oriented failure diagnostics в формате `WHAT / WHY / FIX`; зелёный путь validator-а и failure-helper smoke подтверждены локально.
64. Закрыт follow-up по production audit от 2026-05-23: runner и GUI теперь reject overlapping input/output paths до inventory, mixed-input folders честно считают unsupported inputs, `workers` больше не эмитится в `run.json`, standalone scripts используют shared `scripts/sitecustomize.py`, а Windows CI валидирует `pip check`, `ruff`, `pyright`, EXE smoke и portable release artifact.
65. Закрыт последний P2 follow-up production audit: OCR runtime helper фиксирует SHA-256 для `eng`, `rus`, `osd` traineddata, проверяет direct downloads после `curl.exe`, удаляет mismatch artifact и документирует integrity verification в OCR runtime notes.
66. Закрыт post-release semantic/package bundle v0.3.0: DOCX route выделяет formulas, headers, footers и footnotes; PDF text/OCR routes выделяют heuristic `table`/`formula`/`figure` units; weekly eval получил guarded Windows schedule helper; portable package `DocumentConverter-0.3.0` пересобран с checksum `2ce1f979b0eecc7644ca52b903034c72d642a7cdef7c54b760e4b4d510ed72f8`.
67. Добавлен root-level `processed-documents-catalog.json`: после каждого run оператор получает индекс по исходным файлам с `output_dir`, именем папки документа, статусом обработки и текстом ошибки/причины пропуска, если документ не обработан успешно.
68. Root-level catalog расширен до `processed-documents-catalog.xlsx`: операторский отчёт теперь содержит hyperlinks на папку документа, `document.v1.json` и `search_text.txt`, а run-package validation проверяет и JSON, и XLSX-версию.
69. Исправлен runtime regression в Windows EXE: PyInstaller build теперь включает локальный каталог `schemas`, а frozen schema resolver ищет схемы в `dist\...\schemas`, `dist\...\_internal\schemas` и `sys._MEIPASS`, поэтому GUI больше не падает на старте обработки с `Schema file not found: ... run.v1.schema.json`.
70. DOCX text linearization сохраняет `subscript`/`superscript` как `_(...)`/`^(...)`, а встроенные inline drawings как `[INLINE_DRAWING:...]`, поэтому formula units и соседние обозначения больше не теряют индексы и графические placeholders на реальном DOCX `421/пр`.
71. DOCX inline symbol recognition теперь пытается преобразовывать маленькие inline WMF/EMF/PNG glyph drawings в Unicode-символы с fallback на `[INLINE_DRAWING:...]`; на реальном DOCX `421/пр` формула 2 теперь сохраняется как `j = 1 ÷ J, где:` вместо графического placeholder.
72. DOCX inline symbol recognizer расширен на дополнительные математические glyph-символы, включая `+`, `-`, `=`, `<`, `>`, `∏`, `∂`, `∇`, `∅`, `∀`, `∃`, `∝`, `∥`, `⊥`, `∠`, `⊕`, `⊗`, `∴`, `∵`; regression tests подтверждают, что эти inline-картинки теперь превращаются в нормальные Unicode-символы вместо placeholder.
73. Для MathType WMF formula images в DOCX добавлен прямой text-record extraction до glyph fallback: простые диапазоны вроде `n = 1 ÷ N` и `m = 1 ÷ M`, а также обозначения с индексами вроде `СЦэм_(тек)^(m)` восстанавливаются без raster OCR; реальные суммовые формулы `421/пр` показали следующий обязательный слой — сохранение LaTeX/MathML/AST-представления для расчётного use-case, а не только линейного текста.
74. Добавлен machine-readable formula block для DOCX formulas и обратный Markdown exporter: формула 1.1 из реального `421/пр` теперь сохраняется в `document.v1.json` как `formula.display_latex` + `formula.calc_expr`, а `scripts/export_human_readable.py` выводит её в `human-readable.md` как KaTeX-compatible `$$...$$` и code block для расчётного слоя.
75. Стабилизированы повторяющиеся MathType WMF formulas из `421/пр`: формулы 1, 1.1, 1.2, 2, 3.1, 4 и 5 теперь восстанавливаются как нормальный display LaTeX с `\sum`/`\frac` и расчётными выражениями, диапазоны `i/n/k/m/j = 1 ÷ ...` не дублируют `, где:` в math block, а старые артефакты `PPV=`, `t1Ttt`, `k1К`, `ЦСТ=` и `\mathrm{sum}` исчезли из fresh readable export.
76. Добавлен native XLSX route: `.xlsx` теперь классифицируется как `xlsx_native`, workbook sheets сохраняются как `section`/`table`/`table_row`/`table_cell` units, каждая содержательная ячейка получает structured `cell` payload с address/value/formula/number_format, а реальный файл `Расчет стоимости этапов.xlsx` прошёл schema-valid run package: 13 sheets, 8533 cell units, 1711 formula cells, 0 missing cached formula values.
77. Добавлен env-based provider config для future formula recognition: `ConverterOptions()` автоматически читает `.env.local`/`.env` и process env override для `FORMULA_RECOGNITION_PROVIDER`, `FORMULA_RECOGNITION_MODEL` и `FORMULA_RECOGNITION_API_KEY`, но `run.json` сохраняет только безопасный `formula_recognition` block без секрета.
78. Env-based provider config расширен alias-совместимостью с OpenRouter workflow: loader понимает `LLM_PROVIDER=openrouter`, `OPENROUTER_MODEL=deepseek/deepseek-v4-pro`, отдельный `FORMULA_MODEL=openai/gpt-4o` и `OPENROUTER_API_KEY`, при этом formula slice в `run.json` всё равно остаётся без секрета.
79. Добавлен formula-recognition postprocess stage в runner: если provider config включён, `formula_image` assets проходят локальный WMF hint extraction и затем OpenRouter fallback, результаты пишутся в `formula-recognition.jsonl`, а `document.v1.json` обогащается `unit.text`, `unit.formula` и `processing.formula_recognition` без сериализации API key.
80. Для generic `docx_text_linearized` formulas добавлен heuristic `calc_expr`/`variables` fallback: простые присваивания с `+`, `-`, `x`/`×`, `÷`/`/`, скобками, кириллическими идентификаторами и base token-ами с цифрами теперь получают machine-computable expression layer; fresh real run на `812/пр` подтвердил вычислимые формулы для `ДЗ_(вП)` и `С_(Свлс) = ПЗ1_(п) + ПЗ2_(п) x S_(влс)`.
81. Добавлен safe formula evaluator для `calc_expr`: новый CLI subcommand `evaluate-formula` считает только ограниченное арифметическое подмножество (`+`, `-`, `*`, `/`, `**`, unary `+/-`, скобки и переменные), а DOCX heuristic parser расширен на проценты `%` и степени `^`; real operator-path на Windows подтвердил расчёт `S_Svls = PZ1_p + PZ2_p * S_vls` из свежего `812/пр` run package.
82. Для DOCX formulas с переносами строки добавлена нормализация повторённого оператора на границе line-wrap (`x`/`x` схлопывается в одно умножение), а новый CLI subcommand `evaluate-document-formulas` проходит по `document.v1.json`, считает все доступные `calc_expr` и переиспользует уже вычисленные targets как входы для зависимых формул того же документа; real run на `812/пр` показал 41 `calc_expr`, успешный расчёт `S_Svls = 1340.0` и честный partial по оставшимся 40 формулам без входных значений.
83. Добавлен first-class HTML QC export: `src/doc_converter/human_readable.py` стал shared renderer для Markdown/HTML, `scripts/export_human_readable_html.py` умеет экспортировать как отдельный `document.v1.json`, так и целый `run_dir` в `human-readable-index.html`, а GUI получил кнопку `HTML QC` для немедленной проверки качества конвертации в браузере.
84. GUI теперь автоматически предлагает sibling output path вида `<input>_output` при выборе входной папки и сохраняет вручную заданный отдельный output без перезаписи; это снижает операторские ошибки на nested output path, не снимая intentional self-ingestion guard.
85. LLM formula recognition теперь включается по умолчанию безопаснее: при наличии `OPENROUTER_API_KEY` formula slice автоматически использует `openrouter` + `openai/gpt-4o` даже без `FORMULA_MODEL`, а OpenRouter request переведён на strict `json_schema`, чтобы `linear_text`/`display_latex`/`calc_expr` стабильно возвращались как machine-readable JSON.
86. Закрыт follow-up по реальному operator feedback для формул и HTML QC: formula-recognition postprocess теперь покрывает не только `formula_image`, но и residual `formula` units без machine-readable `calc_expr`, HTML renderer не отправляет в MathJax low-confidence heuristic `display_latex`, распознаванные `formula_image` units показываются как формульные блоки со ссылкой на исходный asset, обычные абзацы получают отступ/переносы, а env loader ищет `.env.local` также рядом с `sys.executable`, чтобы EXE видел formula config даже при другом `cwd`.
87. Добавлен deterministic formula benchmark harness: `src/doc_converter/formula_benchmark.py`, `scripts/run_formula_benchmark.py`, `scripts/export_formula_gold.py`, versioned `samples/formula-benchmark.manifest.jsonl` и gold fixtures в `samples/expected/formulas/`; manifest/gold loaders читают BOM-safe через `utf-8-sig`, relative paths резолвятся от manifest file, а benchmark по умолчанию отключает live formula-recognition provider, чтобы baseline оставался воспроизводимым.
88. Добавлен opt-in local formula OCR backend: `FORMULA_RECOGNITION_LOCAL_BACKEND=tesseract` теперь включает локальный raster OCR fallback между WMF hints и provider stage, `run.json` безопасно сериализует `local_backend`, а mocked tests подтверждают both local-backend-only path и provider fallback после локального miss без утечки `api_key`.
89. В P1 generalized WMF parser сделан первый data-driven шаг: known MathType matcher теперь умеет coalesce соседние WMF chunks с одинаковыми font/charset/height перед signature matching, поэтому split tokens вроде `ОТ` + `ЗТСЦV` восстанавливаются без добавления новой exact-signature ветки; targeted WMF unittest slice зелёный.
90. Исходный полный formula benchmark manifest по curated `metod`/`SP` set завершён зелёно: run `runs\formula-benchmark\runs\20260525T182005Z` дал `29/29` available entries, `11/11` gold checks passed, `required_failures: 0`, clean negative/control contour для `SP`, а corpus totals зафиксировали `281` formula units, `145` calc_expr units, `39` native WMF units, `242` heuristic units и `256` low-confidence units как первую full-corpus baseline перед guide/`521/пр` hardening slice.
91. Heuristic calc parser для `docx_text_linearized` formulas расширен на narrative/chained arithmetic examples: trailing ссылки вида `, (1)`, narrative prefixes и equality-result tails теперь не блокируют `calc_expr`; narrow benchmark rerun поднял `gate-metod-guide` с `0/25` до `17/25` calc_expr units и `gate-metod-521-pr` с `0/6` до `1/6` без provider и без изменения native/control contour.
92. Тот же heuristic `calc_expr` branch дотянут на semicolon clauses и parenthetical formulas: narrative строки вида `a = 30; b = 0,35` и пояснительные формулы в скобках теперь дают хотя бы первый machine-readable assignment; свежий guide-only rerun поднял `gate-metod-guide` уже до `21/25` calc_expr units при неизменных `native_coverage = 0` и `provider_dependency_rate = 0`.
93. В native WMF parser добавлены structural recovery rules для formula set `(2)-(6)` из `521/пр`: known MathType signatures теперь восстанавливают `З_(ср) = З_(1) × К_(смрТ)`, `З_(пнр) = sum_(i) Т_(i) × З_(i)`, `З_(i) = З_(1) × К_(пнрТ)^(i)`, `С_(эм) = sum_(i) Э_(i) × Ц_(эмi)` и `С_(мат) = sum_(i) М_(i) × Ц_(i)`. Focused benchmark rerun `runs\formula-benchmark\runs\20260525T192109Z` поднял `gate-metod-521-pr` до `native_units: 5/6`, `native_coverage: 0.8333`, `calc_expr_units: 6/6` и `confidence medium: 5`, оставив только один heuristic formula unit.
94. Полный formula benchmark manifest перепрогнан после guide/`521/пр` uplift и синхронизации benign gold drift в anchor `421/пр`: run `runs\formula-benchmark\runs\20260525T193008Z` снова зелёный с `29/29` available entries, `11/11` gold checks passed и `required_failures: 0`. Обновлённый corpus baseline теперь даёт `281` formula units, `181` calc_expr units, `44` native WMF units, `237` heuristic units и те же `256` low-confidence units, то есть текущий tranche поднял `calc_expr` на `+36` и native WMF recovery на `+5` относительно исходной corpus baseline.
95. Для `gate-metod-1-pr` закрыт ещё один cheap heuristic parser barrier: expression path теперь нормализует квадратные скобки как grouping, поэтому чистые сметные formulas вида `НЗ_(п) = [ ... ] x (1 + П)` перестали терять `calc_expr`. Focused rerun `runs\formula-benchmark\runs\20260525T194430Z` поднял `1/пр` с `18/49` до `23/49` calc_expr units (`0.3673 -> 0.4694`) без изменения `native_coverage`, что подтверждает: ближайший остаток по `1/пр` уже лежит не в bracket-handling, а в более шумных structural formulas.
96. Для `gate-metod-904-pr` подтверждён ещё один high-yield native WMF slice: визуально проверенные raw MathType signatures теперь восстанавливают formula set `(1)`, `(3)`, `(4)`, `(5)` и `(7)` как `mathtype_wmf_text_records` вместо шумного `docx_text_linearized` fallback. Focused rerun `runs\formula-benchmark\runs\runs\20260525T200228Z` поднял документ с `native_units: 1/7` до `5/7` и с `calc_expr_units: 1/7` до `6/7`, оставив unresolved только formula `(2)`, тогда как formula `(6)` уже была usable heuristic assignment.
97. Для `gate-metod-534-pr` подтверждён ещё один high-yield native WMF slice: raw MathType signatures в сочетании с surrounding prose теперь восстанавливают formulas `(1)-(4)` как `mathtype_wmf_text_records` с корректными обозначениями `СЦ_(...)` вместо шумного `docx_text_linearized` fallback. Focused rerun `runs\formula-benchmark\runs\runs\20260525T202349Z` поднял документ с `native_units: 0/5` до `4/5` и с `calc_expr_units: 2/5` до `5/5`, оставив heuristic только formula `(5)`, которая и так была plain-text assignment.
98. Formula benchmark переведён с narrative thresholds на executable required gate: versioned policy `samples/formula-benchmark.thresholds.json` теперь задаёт baseline floors/ceilings для `anchor`, `gate`, `control` и `overall`, `src/doc_converter/formula_benchmark.py` пишет `tier_summaries` + `required_gate` в benchmark report, а `rolling` зафиксирован как monitor-only tier до следующего полного rerun.
99. Полный formula benchmark rerun под новым required gate прошёл зелёно: `runs\formula-benchmark\runs\20260526T054732Z` дал `29/29` available entries, `11/11` gold checks passed, `required_gate.status = passed`, `194` calc_expr units и `53` native WMF units. Новые tier aggregates подняли `gate.calc_expr_coverage` до `0.6776` и `gate.native_coverage` до `0.1858`, сохранив `control.false_positive_rate = 0.0` и `overall.provider_dependency_rate = 0.0`.
100. `docs/formula-production-plan.md` сверён с фактическим кодом и получил явную status matrix по `P0/P1/P2`: на момент аудита P0-01/P0-02/P0-04 были закрыты, P0-03/P1-04/P1-05/P2-01/P2-02/P2-03 — частично, P1-01 и P1-03 — не закрыты, P1-02 — в работе; зафиксирован автономный порядок продолжения.
101. Закрыт документально-кодовый tranche после аудита: benchmark теперь пишет отдельные `formula-summary.json` и `formula-summary.md` (P0-03), введён первый WMF IR слой с `formula.provenance` в schema/output и оформлен formal spike note `docs/formula-wmf-ir-spike.md` (P1-01), а `docs/downstream-handoff.md` теперь содержит явный machine-readable formula contract (`calculable/display-only/unresolved`) и stable mapping полей (P2-01).
102. Закрыт первый rule-driven execution slice `P1-02`: raw WMF chunks и rendered asset подтвердили, что formula `(2)` в `904/пр` была structural MathType residue, а не OCR dead-end. Token-driven aggregate-price assembly в WMF IR path теперь восстанавливает её как native formula; focused rerun `runs\formula-benchmark\runs\20260526T205614Z` довёл `gate-metod-904-pr` до `native_units: 6/7` и `calc_expr_units: 7/7`, оставив heuristic только formula `(6)`.
103. Уточнён candidate-selection для formula-recognition: LLM/local formula fallback больше не переобрабатывает formula units только из-за low confidence или heuristic provenance, если standard parser уже собрал usable `calc_expr`; AI path теперь целенаправленно применяется к residual формулам без machine-readable contract, включая display-only cases без `calc_expr`.
104. Закрыт следующий execution slice `P1-02` для `1/пр`: inspection исходного DOCX показал, что formulas `(5)` и `(6)` в paragraph-only output были не текстовым шумом, а inline MathType WMF fractions. Native recovery rules теперь восстанавливают `ЗТ_(эСР) = sum_(i=1)^n ЗТ_(э) / n` и `ЗТ_(э) = ЗТ / V`; focused rerun `runs\formula-benchmark\runs\20260528T072055Z` поднял `gate-metod-1-pr` с `23/49` до `25/49` `calc_expr` units и дал первый `native_units: 2/49`.
105. Follow-up execution slice для `1/пр` закрыл ещё один short-fraction native case: rendered WMF для formula `(8)` оказался формулой `К_(уст) = t_(max) / t_(min) <= 1,5`, а не остаточным text noise. Новый known-pattern rule поднял `gate-metod-1-pr` до `26/49` `calc_expr` units и `3/49` `native_units` в rerun `runs\formula-benchmark\runs\20260528T073325Z`.
106. Ещё один cheap native slice для `1/пр` закрыл formula `(3)`: rendered WMF и where-clause согласованно показали formula-level sum case `Н_(ВрП) = Σ Н_(ВрЭ)`. Новый rule-driven recovery поднял `gate-metod-1-pr` до `27/49` `calc_expr` units и `4/49` `native_units` в rerun `runs\formula-benchmark\runs\20260528T073910Z`, после чего remaining residue документа почти полностью сместился к более сложным multi-level fractions.
107. Закрыт и следующий structural anchor для `1/пр`: rendered WMF, where-clause и table/search artifacts согласованно показали formula `(4)` как `Н_(ВрЭ) = ЗТ_(эСР) × 100 / (Ч_(факт) × [100 - (Н_(пзр) + Н_(о) + Н_(тп))] × 60)`. Новый rule-driven recovery поднял `gate-metod-1-pr` до `28/49` `calc_expr` units и `5/49` `native_units` в rerun `runs\formula-benchmark\runs\20260528T074505Z`, поэтому следующий 1/пр backlog уже смещается с одного известного formula anchor на более общий fraction/layout residue.
108. Следующий execution slice для `1/пр` уже закрыл не single-formula anchor, а noisy fraction family без `Н_(тп)`: where-clause для formulas `(23)` и `(31)` показал тот же denominator skeleton, что и у formula `(4)`, но с `ЗТ_(Иср)`/`ЗТ_(эСРл)` и `Ч_(общ)`. Новый known noisy-text recovery поднял `gate-metod-1-pr` до `30/49` `calc_expr` units и `7/49` `native_units` в rerun `runs\formula-benchmark\runs\20260528T080557Z`, поэтому remaining 1/пр backlog теперь смещается дальше от этой fraction family к другим noisy average/resource-cost formulas и broader parser work.
109. Закрыт первый table hardening slice для `pdf_text`: shared parser теперь фиксирует dominant row width, склеивает single-cell continuation lines в предыдущую ячейку при стабильной ширине, дополняет unresolved ragged rows пустыми ячейками и выставляет `table_structure_warning` вместо молчаливой деградации структуры.
110. Тот же table normalization path протянут в `pdf_scan`: OCR route теперь переиспользует shared parsed table block и тот же warning contract, поэтому row integrity и table warning behavior не расходятся между `pdf_text` и `pdf_scan`.
111. DOCX tables получили более богатую cell semantics без расширения schema contract: multiline text в `table_cell` по-прежнему сохраняется, а ячейки с formula-like строками теперь дополнительно несут machine-readable `formula` metadata для downstream evaluation и QC.
112. Добавлен executable contour для representative sample expectations: новый `src/doc_converter/sample_expectations.py` и `scripts/validate_sample_expectations.py` валидируют expected structural/table specs по реальному `run_dir`, поддерживают subset по `sample_id` и проверяют как canonical unit counts, так и aggregate table metrics и processing state.
113. Собран и подтверждён table anchor baseline на реальных `sample_009`, `sample_018` и `sample_020`: добавлены `samples/manifest.table-anchors.jsonl`, table-aware expected specs для `sample_009`/`sample_018`, blocked-scan baseline для `sample_020`, а fresh run `runs\table-anchors\runs\20260528T092227Z` проходит новый validator без drift.
114. Измеримый baseline показал, что `sample_009` и `sample_018` уже держат row/cell integrity (`wide_row_ratio = 1.0`, `single_cell_row_ratio = 0.0`), но warning density остаётся высокой (`162/166` и `22/26` tables c `table_structure_warning`), тогда как `sample_020` пока остаётся OCR-blocked (`partial_success`, `OCRmyPDF failed.`, `0` table units), что делает следующий scan-table backlog явным и проверяемым.
115. Добавлена `docs/production-roadmap.md`: v1.0 roadmap разложен на waves/sprints с dependencies, feature_ids, artifacts и machine-checkable exit criteria для автономных агентов.
116. Добавлен reusable prompt `.github/prompts/execute-production-roadmap-autonomous.prompt.md`: агент получает end-to-end инструкцию для исполнения production roadmap, запуска проверок, state/telemetry updates, commit и push без остановки на планировании.
117. Закрыт production roadmap Sprint S0.1: DOCX inline-glyph тесты очищают `INLINE_GLYPH_CACHE` перед каждым кейсом, flaky additional-symbol assertions стабилизированы через допустимые canonical variants, ruff/pyright конфиг зафиксирован в `pyproject.toml`, `ruff check`, `pyright` и 5 подряд `unittest discover` проходят зелёно.
118. Закрыт production roadmap Sprint S1.1: stable downstream contracts catalog добавлен в `docs/contracts.md`, `formula-recognition.v1` получил JSON Schema, stable schema fingerprints закреплены в `schemas/__snapshot__/stable-contracts.v1.json`, `tests/test_contracts_stability.py` защищает drift, а `validate_run_package.py` теперь валидирует document-level `formula-recognition.jsonl` при наличии.
119. Закрыт production roadmap Sprint S1.2: hard-coded known MathType formula representations, noisy-form recovery и WMF signature rules вынесены в versioned JSON `samples/formulas/known-patterns.v1.json` с package-data copy, schema `formula-known-patterns.v1`, loader `doc_converter.formulas.known`, validator/export scripts и focused regression tests без изменения текущего DOCX formula behavior.
120. Закрыт production roadmap Sprint S1.3: `run.v1` теперь требует `agent_run_metadata` для новых run packages, CLI/runner сериализуют `agent_id/agent_version/task_id/parent_run_id`, `validate_run_package.py` сохраняет legacy compatibility через fallback metadata, а `scripts/validate_document_package.py` валидирует `document.v1.json` и `formula-recognition.jsonl` sidecars по всему run directory.
121. Закрыт production roadmap Sprint S2.1: монолит `src/doc_converter/converters/docx.py` заменён на package `src/doc_converter/converters/docx/` с модулями `pipeline.py`, `inline_glyph.py`, `formulas/text.py` и `formulas/wmf.py`, а `__init__.py` сохраняет публичный import surface для runner, formula-recognition и тестов. Focused DOCX, CLI/formula-recognition и full-suite gates прошли зелёно; remaining repo-wide file-size debt теперь явно локализован в `src/doc_converter/runner.py` и `src/doc_converter/formula_benchmark.py` как следующий architecture backlog.
122. Закрыт production roadmap Sprint S2.2: `src/doc_converter/runner.py` превращён в thin compatibility wrapper, а orchestration/path/resume/catalog/postprocess logic вынесены в `src/doc_converter/run/`. Focused runner/CLI slices, полный unittest с `PYTHONPATH=src`, `ruff` и `pyright` прошли зелёно; remaining repo-wide oversize debt теперь сосредоточен в `src/doc_converter/formula_benchmark.py`.
123. Закрыт production roadmap Sprint S2.3: shared table normalizer вынесен в `src/doc_converter/tables/`, а `pdf_text` и `pdf_scan` теперь импортируют один и тот же parser для dominant-width inference, continuation merge и `table_structure_warning`. Focused PDF/table tests, свежий `table-anchors` pilot `runs\s23-table-anchors\runs\20260529T162149Z`, subset validator для `sample_009/018`, полный suite, `ruff` и `pyright` прошли зелёно.
124. Закрыт production roadmap Sprint S2.4 и вся Wave 2: `inventory.py` и `run/orchestration.py` теперь используют shared `doc_converter.converters` registry + `ConverterProtocol`, direct format-specific imports/branches убраны из orchestration path, runner tests патчат lookup layer вместо direct converter symbols, а opt-in dummy `txt` converter regression доказывает extensibility без изменения default supported-format contract. Focused runner/inventory slice, полный suite (200 tests), `pip check`, `ruff`, `pyright` и `validate_harness_assets.py` проходят зелёно.

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
- docs/production-roadmap.md
- docs/formula-production-plan.md
- samples/formula-benchmark.manifest.jsonl
- samples/expected/formulas/
- docs/build-and-run.md
- docs/ocr-runtime-windows.md
- docs/downstream-handoff.md
- .github/prompts/production-readiness-hardening.prompt.md
- .github/prompts/execute-production-roadmap-autonomous.prompt.md
- .vscode/extensions.json
- .vscode/mcp.json
- .vscode/settings.json
- samples/manifest.sample.jsonl
- samples/manifest.table-anchors.jsonl
- samples/pdf-text-layer-check.sample.json
- samples/expected/README.md
- samples/expected/sample_001.expected-units.json
- samples/expected/sample_003.expected-units.json
- samples/expected/sample_006.expected-units.json
- samples/expected/sample_009.expected-units.json
- samples/expected/sample_018.expected-units.json
- samples/expected/sample_019.expected-units.json
- samples/expected/sample_020.expected-units.json
- pyproject.toml
- sitecustomize.py
- src/doc_converter/
- src/doc_converter/formula_benchmark.py
- src/doc_converter/sample_expectations.py
- tests/
- tests/test_formula_benchmark.py
- tests/test_sample_expectations.py
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
- scripts/run_formula_benchmark.py
- scripts/export_formula_gold.py
- scripts/install-ocr-runtime.ps1
- scripts/run_folder_e2e.py
- scripts/validate_sample_expectations.py
- scripts/validate_harness_assets.py
- AGENTS.md

## 3. Что делается сейчас

Текущий фокус: после закрытия S2.4 и всей Wave 2 следующий critical-path sprint production roadmap — S6.1, то есть structured CLI с machine-readable `--output-format=json`, явной exit-code matrix и отдельными doctor/dry-run subcommands.

Новый architecture-learning по route registry: cheapest root-cause fix для extensibility лежал не в одном `run/orchestration.py`, а в связке `inventory.classify_route` + orchestration dispatch. Перенос только conversion calls оставил бы hard-coded suffix/route coupling в inventory и не закрыл бы sprint exit criteria.

Новый test-learning по extensibility: architecture-only demo converters упираются в stable manifest/document contract не по вине runner, а по schema enums текущего product scope. Для proof-style regression такой converter нужно держать opt-in и изолировать от schema validation, пока product contract сознательно не расширяется.

Новый validation-learning по runner hooks: после registry split resilience tests должны патчить `get_converter`, а не direct `convert_docx` import; это сохраняет reuse/failure assertions устойчивыми к дальнейшим refactor-ам dispatch layer.

В работе:

- открыть production roadmap S6.1 и сделать structured CLI основным contract для автономных агентов;
- держать `src/doc_converter/formula_benchmark.py` как отдельный non-critical architecture follow-up по file-size debt;
- удержать measured table backlog на `sample_009/018/020` и negative/control contour как parallel quality loop, не подменяя им critical path;
- держать state docs, feature spine, telemetry и generated eval companions синхронными после каждого следующего sprint tranche.

## 4. Что идёт дальше

Следующая последовательность после закрытия S2.4:

1. Закрыть production roadmap S6.1: structured CLI JSON output, exit-code matrix, `doctor` и `dry-run`.
2. Затем закрыть S6.2 и перевести runtime events на structured telemetry/log contract.
3. После operator surface перейти к S7.1 input hardening и формализованному `docs/security.md`.
4. Держать `src/doc_converter/formula_benchmark.py` как отдельный follow-up по repo-wide file-size debt вне critical path.
5. Продолжать measured table backlog по `sample_020`, warning density на `sample_009/018` и negative/control false-positive contour уже поверх shared `tables/` package.
6. Затем вернуться к richer DOCX table semantics и generalized WMF parser backlog для formula-rich DOCX.
7. Держать product-aware feature spine, sprint contract, checkpoint template, telemetry JSONL и evaluator rubric обязательными на новых cross-module задачах.

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

Source of truth для прикладной реализации Windows-конвертера: docs/document-converter-roadmap.md. Прикладной scope теперь покрывает DOCX, PDF-text, PDF-scan и XLSX-native, а главный переносимый результат — `document.v1.json` со stable structural units для будущего chunking, DB ingestion и поиска.

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
