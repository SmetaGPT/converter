# Current Sprint

Последнее обновление: 2026-05-24
Активный спринт: Release Closure — Production readiness v0.3.0
Статус: completed

Последний завершённый спринт: Release Closure — Production readiness v0.3.0
Статус wave 1: completed

## 1. Цель спринта

Закрыть production gates поверх Sprint 13-16: runtime schema validation, resume/idempotency, honest CLI/GUI contract, quality reporting, downstream chunks, Windows CI и portable release packaging.

## 2. Артефакты спринта

- docs/document-converter-roadmap.md
- docs/document-converter-acceptance.md
- docs/build-and-run.md
- docs/agent-bootstrap-contract.md
- docs/agent-feature-spine.json
- docs/agent-quality-scorecard.md
- docs/agent-quality-scorecard.v1.json
- docs/agent-weekly-eval.md
- docs/agent-weekly-eval.v1.json
- docs/agent-weekly-reviews.v1.json
- docs/agent-session-exit-checklist.md
- docs/agent-sprint-contract-template.md
- docs/agent-task-checkpoint-template.md
- docs/agent-evaluator-rubric.md
- docs/agent-evals.md
- docs/agent-regressions.md
- docs/agent-telemetry.v1.jsonl
- docs/ocr-runtime-windows.md
- docs/current-status.md
- docs/release-status.md
- .github/prompts/production-readiness-hardening.prompt.md
- schemas/agent-feature-spine.v1.schema.json
- schemas/agent-telemetry-entry.v1.schema.json
- schemas/agent-quality-scorecard.v1.schema.json
- schemas/agent-weekly-eval.v1.schema.json
- schemas/agent-weekly-reviews.v1.schema.json
- scripts/build_agent_scorecard.py
- scripts/build_agent_weekly_eval.py
- scripts/refresh_agent_eval.py
- scripts/validate_harness_assets.py
- src/doc_converter/
- tests/
- schemas/
- scripts/
- dist/

## 3. Задачи спринта

| Задача | Статус |
| --- | --- |
| Исправить OCR page mapping и сохранить OCR page boundaries | Готово |
| Добавить `relative_input_path` и asset fingerprints/file metadata | Готово |
| Перевести DOCX converter на реальный body order | Готово |
| Выделить `section`, `list_item`, `caption` в DOCX | Готово |
| Включить layout-first extraction для PDF-text | Готово |
| Добавить `bbox`, `coordinate_system`, `page_width`, `page_height` в page provenance | Готово |
| Выделить repeated edge blocks как `header`/`footer` | Готово |
| Нормализовать `quality` на document и unit level | Готово |
| Ужесточить `document.v1` schema под фактический payload | Готово |
| Синхронизировать roadmap, acceptance, build и OCR docs | Готово |
| Подтвердить full test suite, representative pilot, OCR preflight и build | Готово |
| Провести automated GUI startup smoke для Python GUI и собранного EXE | Готово |
| Создать и ужесточить автономный prompt для полного production hardening без остановок | Готово |
| Валидировать `run/document/manifest/summary/queue/ocr-runtime/chunks` по JSON Schema | Готово |
| Реализовать resume reuse, duplicate skip и `include_originals` | Готово |
| Удалить ложный `workers` из public contract и добавить progress/cancel/open output в GUI | Готово |
| Добавить `review-required.jsonl`, richer summary reasons и `rotated_text` flags | Готово |
| Добавить reference chunk builder и portability-safe `chunks.v1.jsonl` contract | Готово |
| Добавить synthetic e2e, Windows CI и portable release packaging | Готово |
| Добавить semantic metadata `title/document_type/short_summary` в `document.v1.json` | Готово |
| Добавить machine-readable harness feature spine, bootstrap/exit contracts и CI validator | Готово |
| Расширить feature spine на core product-capabilities конвертера и сделать coverage обязательным через validator | Готово |
| Встроить feature-traceability в bootstrap, sprint contract, checkpoint, exit checklist и rubric | Готово |
| Добавить machine-readable telemetry JSONL companion и schema-backed validation | Готово |
| Добавить machine-readable scorecard companion и drift-check against telemetry | Готово |
| Добавить markdown drift-check для structured companion section в scorecard | Готово |
| Operationalize weekly eval loop через generated companion | Готово |
| Закрыть telemetry coverage gaps и провести первый qualitative weekly review | Готово |
| Добавить one-command refresh wrapper для generated eval companions | Готово |
| Вынести sampled weekly review scores в machine-readable companion и weekly eval schema | Готово |
| Улучшить harness validator diagnostics до формата `WHAT / WHY / FIX` | Готово |
| Проверять integrity OCR traineddata downloads в OCR helper | Готово |
| Закрыть post-release semantic extraction для PDF/DOCX tables/formulas/figures и DOCX footnotes/header/footer | Готово |
| Добавить optional Windows schedule helper для `refresh_agent_eval.py` | Готово |
| Пересобрать и версионировать portable package как v0.3.0 | Готово |
| Добавить root-level catalog обработанных документов с output folder и статусом | Готово |
| Добавить XLSX report с hyperlinks на обработанные артефакты | Готово |
| Добавить native XLSX route для workbook/sheet/cell/formula packages | Готово |
| Добавить env-based provider config loader без утечки API key в run metadata | Готово |
| Расширить env loader alias-совместимостью с OpenRouter и отдельной formula model | Готово |
| Добавить formula-recognition postprocess stage с OpenRouter fallback | Готово |
| Добавить heuristic `calc_expr` fallback для generic `docx_text_linearized` formulas | Готово |
| Добавить safe evaluator для `calc_expr` и расширить DOCX parser на `%` и `^` | Готово |
| Схлопнуть line-wrap `x x` в DOCX formulas и добавить dependency-aware batch evaluation по `document.v1.json` | Готово |

## 4. Validation targets спринта

1. Full test suite проходит.
2. Representative pilot-run создаёт output package без failed documents.
3. Windows package собирается через `scripts/build-windows.ps1`.
4. OCR runtime preflight возвращает `status: ready`.
5. Собранный EXE проходит automated launch smoke без мгновенного падения.
6. Synthetic e2e создаёт schema-valid run package и `chunks.v1.jsonl`.
7. Portable release package создаётся с checksum и release notes.
8. Ограничения advanced semantic extraction и optional OCR helpers зафиксированы явно.
9. Real-folder e2e на `metod` создаёт schema-valid package с заполненным semantic metadata block.
10. Harness assets validator проходит локально и встроен в Windows CI.
11. Feature spine покрывает не только process layer, но и core product-capabilities конвертера.
12. Task-flow теперь требует traceability до `feature_id` и evidence paths через шаблоны process layer.
13. Machine-readable telemetry companion валидируется локально и связывается с known `feature_id` из feature spine.
14. Generated scorecard companion синхронизируется с telemetry JSONL и feature spine через `scripts/build_agent_scorecard.py --check`.
15. Structured companion section в markdown scorecard синхронизируется через `scripts/build_agent_scorecard.py --check-markdown` и валидируется внутри harness validator.
16. Generated weekly eval companion собирается из scorecard и telemetry через `scripts/build_agent_weekly_eval.py` и валидируется внутри harness validator.
17. Weekly snapshot больше не содержит unexplained coverage gaps, а первый qualitative weekly review зафиксирован в eval и regression docs.
18. One-command refresh wrapper пересобирает оба generated companions, а weekly eval JSON несёт machine-readable qualitative sampling из отдельного reviews companion.
19. OCR runtime install helper проверяет SHA-256 для direct traineddata downloads и fail-fast останавливается на mismatch.
20. DOCX/PDF routes создают semantic units для formulas, figure captions, heuristic tables, DOCX headers/footers/footnotes и сохраняют это в schema-valid `document.v1.json`.
21. Optional weekly eval schedule helper проходит `-CheckOnly`, а portable release v0.3.0 собран и проходит EXE smoke.
22. Каждый run сохраняет `processed-documents-catalog.json` с оригинальным именем файла, output folder, статусом обработки и текстом ошибки/причины пропуска.
23. Каждый run сохраняет `processed-documents-catalog.xlsx` с hyperlinks на папку документа, `document.v1.json` и `search_text.txt`, если этот файл создан.
24. Собранный Windows EXE включает локальные JSON schemas и на frozen runtime находит их внутри bundle без ошибки `Schema file not found` при старте обработки.
25. XLSX route создаёт schema-valid `document.v1.json` с worksheet sections, table/row/cell units, structured `cell` payload и сохранёнными Excel formulas/cached values.
26. Formula-recognition provider config автоматически загружается из `.env.local`/`.env` и process env overrides, но `run.json` не сериализует `api_key`.
27. Formula-recognition env loader понимает shorthand OpenRouter-схему `LLM_PROVIDER`, `OPENROUTER_MODEL`, `FORMULA_MODEL` и `OPENROUTER_API_KEY`, чтобы reasoning/model routing и formula model override можно было хранить раздельно.
28. Formula-recognition postprocess обогащает `formula_image` units через local WMF hint extraction и OpenRouter fallback, пишет `formula-recognition.jsonl` и не делает live provider call частью automated validation.

## 5. Риски спринта

- PDF/DOCX semantic extraction теперь heuristic и требует review на сложных layouts, но больше не является открытым backlog item;
- Optional OCR helpers `jbig2`, `pngquant`, `verapdf` не установлены; это не блокирует OCR, но ограничивает оптимизацию и PDF/A checks.

## 6. Критерий выхода

Спринт закрыт, потому что delivery loop подтвердил:

- representative pilot-run на расширенном sample set выполнен;
- OCR runtime установлен и проверен;
- Python GUI и собранный EXE проходят automated startup smoke;
- runtime schema validation, resume/idempotency, quality reporting, downstream chunks, CI и portable release packaging подтверждены.

## 7. Следующий operational focus

1. Поддерживать product-aware feature spine, sprint contract, checkpoint template и evaluator rubric на следующих нетривиальных задачах.
2. Вести structured telemetry companion на следующих нетривиальных задачах без пропусков.
3. Использовать `scripts/refresh_agent_eval.py` как штатную weekly discipline для scorecard и weekly eval companions.
4. При необходимости добавить schedule поверх `scripts/refresh_agent_eval.py`.
5. Точечно тюнить heuristic semantic extraction для PDF tables/figures/formulas по результатам новых production-like пакетов.
6. Уточнять DOCX footnotes/header/footer semantics только при наблюдаемой product need или quality gap.
7. Решить, нужны ли optional OCR helpers `jbig2`, `pngquant`, `verapdf` по эксплуатационным метрикам.

## 8. Последняя representative проверка

- Команда: `python scripts\run_sample_pilot.py --clean`.
- Run dir: `runs\sample-pilot\runs\20260522T180732Z`.
- Результат: 21 processed, 21 success, 0 partial_success, 0 failed.
- Routes: `docx_native: 8`, `pdf_text: 10`, `pdf_scan: 3`.
- Route mismatches: 0.

## 9. OCR runtime diagnostic

- Команда: `.\.venv\Scripts\python.exe -m doc_converter.cli check-ocr`.
- Текущий статус: `ready`.
- Tools: локальный `ocrmypdf` в `.venv\Scripts`, `tesseract` и `gswin64c` через `scoop`.
- Languages: `eng`, `rus`, `osd` доступны.

## 10. Build и GUI smoke

- Build команда: `powershell -ExecutionPolicy Bypass -File scripts\build-windows.ps1 -Name DocumentConverter`.
- Результат: `dist\DocumentConverter\DocumentConverter.exe` собран успешно.
- Portable release: `powershell -ExecutionPolicy Bypass -File scripts\package-release.ps1 -Name DocumentConverter -Version 0.3.0 -SkipBuild`.
- Synthetic e2e: `.\.venv\Scripts\python.exe scripts\run_synthetic_e2e.py --clean`.
- Python GUI smoke: `.\.venv\Scripts\python.exe -m unittest tests.test_gui_import -v`.
- EXE smoke: `dist\DocumentConverter\DocumentConverter.exe` стартует как процесс и не завершается мгновенно.
- Frozen schema smoke: локальный check через `schema_validation._load_validator("run.v1.schema.json")` в frozen-mode на `dist\DocumentConverter\DocumentConverter.exe` находит bundle path `dist\DocumentConverter\_internal\schemas`.

## 11. Последние folder e2e проверки

- Команда: `.\.venv\Scripts\python.exe scripts\run_folder_e2e.py "D:\ФСНБ\Документы\Загрузка НПА\SP" --output runs\sp-e2e --clean`.
- Run dir: `runs\sp-e2e\runs\20260522T205641Z`.
- Результат: 344 discovered, 344 supported, 344 processed, 0 partial, 0 failed, 0 review_required, 0 duplicate groups.
- Package validation: `.\.venv\Scripts\python.exe scripts\validate_run_package.py runs\sp-e2e\runs\20260522T205641Z` вернул `status: ok`.
- Routes: `pdf_text: 343`, `docx_native: 1`.
- Semantic metadata distribution: `свод правил: 344`; пустых `metadata.document_type`/`metadata.short_summary` нет.

- Команда: `.\.venv\Scripts\python.exe scripts\run_folder_e2e.py "D:\ФСНБ\Документы\для парсера\Российские\metod" --output runs\metod-e2e --clean`.
- Run dir: `runs\metod-e2e\runs\20260522T204542Z`.
- Результат: 52 discovered, 52 supported, 52 processed, 0 partial, 0 failed, 0 review_required, 1 duplicate group, 6010 chunks.
- Package validation: `.\.venv\Scripts\python.exe scripts\validate_run_package.py runs\metod-e2e\runs\20260522T204542Z` вернул `status: ok`.
- Semantic metadata distribution: `приказ: 49`, `методические указания: 1`, `методическое пособие: 1` по canonical `document.v1.json`; один исходный файл попал в duplicate group.

## 12. Harness assets validation

- Команда: `.\.venv\Scripts\python.exe scripts\validate_harness_assets.py`.
- Результат: `status: ok`, `features: 25`, `validated: 25`, `active: 0`, `backlog: 0`, `telemetry_entries: 33`.
- Артефакты: `docs/agent-feature-spine.json`, bootstrap contract, clean-exit checklist, sprint contract template, task checkpoint template, evaluator rubric, `docs/agent-telemetry.v1.jsonl`, `docs/agent-quality-scorecard.v1.json`, `docs/agent-weekly-eval.v1.json`, `docs/agent-weekly-reviews.v1.json`, one-command refresh wrapper и schema-backed validator.

## 13. Post-audit remediation

- P0 blockers закрыты: runner и GUI reject overlapping input/output paths до inventory, а mixed-input folders теперь дают truthful `discovered/supported/unsupported` counts и `document_skipped_unsupported` log records.
- P1 gates закрыты: repo-local `dev` extra добавляет `ruff` и `pyright`, Windows CI запускает `pip check`, `ruff`, `pyright`, build, EXE smoke и `package-release`, а portable zip/checksum/release-notes публикуются как workflow artifact.
- P2 cleanup закрыт: `workers` больше не эмитится в `run.json`, schema держит его только как deprecated backward-compatible field, standalone scripts используют shared `scripts/sitecustomize.py`, а OCR traineddata downloads проверяются по pinned SHA-256.
- Post-release v0.3.0 закрыт: DOCX formulas/header/footer/footnote units, PDF text/OCR heuristic table/formula/figure units, schedule helper и versioned portable package `DocumentConverter-0.3.0`.
- Поверх `calc_expr` добавлен safe evaluator и CLI `evaluate-formula`; parser теперь также понимает `%` и `^` для heuristic DOCX formulas, а Windows operator-path подтверждён через BOM-safe `--values-file` и расчёт реального выражения `S_Svls = PZ1_p + PZ2_p * S_vls` из `812/пр`.
- Поверх этого batch operator-path расширен до `evaluate-document-formulas`: DOCX parser схлопывает line-wrap артефакт `x x` в одно умножение, а CLI проходит по `document.v1.json`, переиспользует уже вычисленные targets для зависимых выражений и на реальном `812/пр` честно вернул `41 calc_expr / 1 evaluated / 40 missing`, включая `S_Svls = 1340.0`.
- EXE packaging regression закрыт: `scripts/build-windows.ps1` теперь добавляет `schemas/` в bundle, а `schema_validation.py` умеет находить схемы во frozen layout `dist\...\_internal\schemas`.
- DOCX formula symbol recovery hotfix закрыт: body/table/header/footer extraction теперь сохраняет `subscript` и `superscript`, пытается распознавать маленькие inline WMF/EMF/PNG glyph drawings в Unicode-символы и оставляет `[INLINE_DRAWING:...]` только как fallback; реальный DOCX `421/пр` теперь даёт `j = 1 ÷ J, где:` в canonical package.
- DOCX symbol vocabulary расширен: inline glyph recognizer теперь покрывает дополнительные операторы, кванторы и геометрические/логические знаки (`+`, `-`, `=`, `<`, `>`, `∏`, `∂`, `∇`, `∅`, `∀`, `∃`, `∝`, `∥`, `⊥`, `∠`, `⊕`, `⊗`, `∴`, `∵`), а targeted DOCX regression подтверждает их преобразование в Unicode-текст.
- DOCX MathType WMF extraction добавлен как промежуточный слой до raster/glyph fallback: text records из MathType WMF позволяют восстанавливать простые диапазоны и обозначения с индексами без OCR, но сложные суммовые формулы требуют следующего product layer — хранить display LaTeX/MathML и вычислимый AST, чтобы затем рендерить через KaTeX/Word и отдельно считать по нормализованному выражению.
- DOCX formula representation и readable round-trip добавлены: `document.v1.json` допускает `formula.display_latex`/`formula.calc_expr`, `421/пр` fresh run восстановил формулу 1.1 как LaTeX + Python-like expression, а `scripts/export_human_readable.py` создал `human-readable.md` из canonical package.
- DOCX formula stability pass добавлен после visual review: known MathType WMF signatures для формул 1, 1.2, 2, 3.1, 4 и 5 из `421/пр` теперь дают structured LaTeX/calc output, exporter не дублирует normalized range text, а fresh readable export не содержит старых артефактов `PPV=`, `t1Ttt`, `k1К`, `ЦСТ=` и `\mathrm{sum}`.
- DOCX heuristic calc fallback расширен на generic `docx_text_linearized` formulas: простые присваивания теперь получают `calc_expr` и `variables` даже без hardcoded WMF signature, ASCII `x` нормализуется как умножение, base token-ы с цифрами (`ПЗ1_(п)`, `ПЗ2_(п)`) поддерживаются, а fresh single-doc run на `812/пр` подтвердил формулы `ДЗ_(вП)` и `С_(Свлс)` как machine-computable expressions в `document.v1.json` и `human-readable.md`.
- Formula LLM path включён по умолчанию безопаснее: при наличии `OPENROUTER_API_KEY` formula-recognition auto-configures `openrouter` + `openai/gpt-4o` даже без `FORMULA_MODEL`, а OpenRouter call теперь требует strict `json_schema`, чтобы downstream `calc_expr` slice был стабильнее machine-readable.
- First-class HTML QC export добавлен поверх readable slice: shared renderer `src/doc_converter/human_readable.py` теперь строит и Markdown, и HTML, отдельный `scripts/export_human_readable_html.py` умеет экспортировать как document package, так и целый `run_dir` в `human-readable-index.html`, а GUI открывает этот QC index отдельной кнопкой `HTML QC`.
- Follow-up по operator feedback закрыт локально: formula-recognition postprocess теперь дообогащает и low-confidence `formula` units, HTML renderer рендерит low-confidence heuristic formulas как читабельный plain block вместо MathJax, recognized `formula_image` units показываются как формулы со ссылкой на исходный asset, а `config.py` ищет `.env.local` рядом с `sys.executable`, чтобы packaged EXE не терял formula provider config при запуске не из repo root.
- Operator GUI path input hardening дотянут до меньшего friction: при смене входной папки GUI теперь сам предлагает sibling output вида `<input>_output`, но не перетирает вручную выбранный отдельный output; overlap/self-ingestion guard в runtime остаётся жёстким.
- Native XLSX route добавлен: `.xlsx` теперь поддерживается inventory/runner/schema, `openpyxl` сохраняет worksheet/table/row/cell hierarchy, formulas остаются в Excel formula syntax вместе с cached values, а реальный `Расчет стоимости этапов.xlsx` прошёл run-package validation как `xlsx_native`.
- Последняя локальная validation: targeted `runTests tests/test_config.py tests/test_formula_recognition.py tests/test_human_readable.py`, `get_errors` по затронутым `src/`/`tests/` файлам, `scripts\build-windows.ps1 -Name DocumentConverter-next`, `scripts\smoke-test-windows-exe.ps1 -ExePath dist\DocumentConverter-next\DocumentConverter-next.exe`, затем после остановки живого старого процесса штатные `scripts\build-windows.ps1 -Name DocumentConverter` и `scripts\smoke-test-windows-exe.ps1 -ExePath dist\DocumentConverter\DocumentConverter.exe` — passed.
- Clean-room note: отдельная внешняя Python 3.12 venv с `pip install -e .[build,dev]` тоже проходит `pip check`; локальный сбой `charset-normalizer/fonttools is not supported on this platform` был traced to contaminated wheels внутри старой `.venv` и устраняется recreation env или force-reinstall этих пакетов.
