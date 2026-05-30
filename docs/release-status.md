# Release Status

Последнее обновление: 2026-05-30
Релизный контур: Windows Document Converter v0.3.0
Статус: production-ready within declared scope

## 1. Цель релиза

Довести репозиторий до состояния, в котором агентный контур поддерживает полный цикл: baseline, state, memory, lifecycle, routing, evaluation и release discipline.

## 2. Текущая стадия

Сейчас проект находится в post-release table and formula hardening state поверх production-ready v0.3.0: converter уже имеет runtime schema validation, resume/reuse для неизменённых файлов, duplicate skip без перезаписи canonical package, operator-grade GUI surface, reference chunk builder, Windows CI, synthetic e2e и portable release packaging. После v0.2.0 реализованы semantic metadata enhancement для `document.v1.json`, heuristic semantic extraction для DOCX/PDF tables/formulas/figures и DOCX footnotes/header/footer, native XLSX route для workbook/sheet/cell/formula packages, env-based formula-recognition provider config с безопасной сериализацией run metadata, formula-recognition postprocess с local WMF hint extraction и OpenRouter fallback, optional Windows schedule helper для eval refresh, root-level `processed-documents-catalog.json` и `processed-documents-catalog.xlsx` для operator navigation, first-class human-readable Markdown/HTML export из canonical package и GUI HTML QC path, а portable package пересобран как v0.3.0. Поверх formula tranche уже закрыт первый table-hardening sprint: `pdf_text` и `pdf_scan` теперь используют shared table parser с dominant row width normalization, continuation-line merge и explicit `table_structure_warning` для unresolved ragged tables, а DOCX `table_cell` units сохраняют multiline text и formula-like cell metadata. Следом закрыт и первый table benchmark anchor baseline: `sample_009` и `sample_018` получили executable expected specs с row/cell metrics, `sample_020` зафиксирован как reproducible OCR-blocked scan baseline, а новый validator `scripts/validate_sample_expectations.py` превращает representative sample expectations из статичных JSON fixtures в воспроизводимый quality loop. Formula benchmark harness, versioned gates и opt-in local formula OCR backend `FORMULA_RECOGNITION_LOCAL_BACKEND=tesseract` остаются отдельным воспроизводимым quality loop для следующего formula backlog. Дополнительно harness layer теперь имеет machine-readable feature spine, bootstrap contract, clean-exit checklist, sprint contract template, evaluator rubric и CI-backed validator для этих артефактов, а feature spine покрывает и core product-capabilities конвертера, связан с task-flow через `feature_id` traceability, дополнен schema-backed telemetry JSONL companion, generated scorecard companion, generated weekly eval companion, machine-readable weekly review source, one-command refresh wrapper и guarded schedule helper для этого eval contour.

Critical-path operator surface S6.1 закрыт: CLI по умолчанию остаётся human-readable для ручного использования, а `--output-format=json` выдаёт fixed `cli-result.v1` envelope с exit-code matrix `0/10/20/30/40/50`. Дополнительно появились `doctor` и `dry-run`, поэтому агент может различать `input_invalid`, `environment_invalid`, `review_required` и `partial` без парсинга prose и без пробного запуска полного conversion path.

Следом закрыт и S6.2 structured telemetry tranche: каждый run теперь эмитит schema-backed `telemetry.jsonl` по `log.v1` через central logger adapter, а `scripts/validate_run_package.py` валидирует этот event stream вместе с остальными run-package артефактами. Legacy `processing-log.jsonl` и `errors.jsonl` пока сохранены как compatibility mirrors, поэтому operator/debug привычки не ломаются одномоментно.

Следом закрыт и S7.1 security baseline: `validate_run_directories` теперь fail-closed отклоняет symlink-based path confusion на `input_dir`/`output_dir`/`runs_dir`, DOCX archive admission ограничен по entry count и суммарному uncompressed size до `python-docx`, WMF parser ограничен по размеру blob и количеству records, а `docs/security.md` фиксирует threat model, subprocess inventory и font/path policy для untrusted документов.

Следом закрыт и S7.2 secret-scan CI tranche: `windows-ci` теперь устанавливает Gitleaks и выполняет required git-backed scan `gitleaks git --config .gitleaks.toml --exit-code 1 .`. Конфиг расширяет default rules узким product-specific rule для `OPENROUTER_API_KEY` / `FORMULA_RECOGNITION_API_KEY`, а global allowlist intentionally покрывает только known fake fixtures и `.env.example`, поэтому clean repo проходит без ручного baseline файла, а synthetic git canary валится детерминированно.

Готово:

- baseline;
- inventory;
- eval task seed;
- initial quality scorecard;
- state foundation;
- memory discipline;
- deterministic workflow и hooks;
- specialist agents и routing;
- evaluation и self-review;
- Windows Document Converter hardening Sprint 13-16;
- runtime schema validation для `run/document/manifest/summary/queue-state/ocr-runtime/chunks`;
- `review-required.jsonl`, richer summary reasons и portable run-package validation;
- structured CLI operator surface: `cli-result.v1`, exit-code matrix, `doctor` и `dry-run`.
- security hardening baseline: `docs/security.md`, symlink-safe startup path admission, DOCX archive limits и WMF parser limits.
- required secret-scan gate: `windows-ci` ставит Gitleaks, использует `.gitleaks.toml`, сохраняет узкий allowlist для fixtures/examples и валит synthetic API-key canary.
- Windows CI workflow, synthetic e2e и portable release package с checksum/release notes.
- schema-backed semantic metadata block в `document.v1.json`, подтверждённый real-folder e2e на 52 DOCX из `metod`.
- machine-readable `docs/agent-feature-spine.json` и validator `scripts/validate_harness_assets.py`, встроенный в CI.
- machine-readable feature coverage для core product-capabilities converter runtime и operator surface.
- machine-readable telemetry companion `docs/agent-telemetry.v1.jsonl` с schema validation и проверкой known `feature_id`.
- generated scorecard companion `docs/agent-quality-scorecard.v1.json`, синхронизированный с telemetry JSONL, feature spine и human-readable markdown section.
- generated weekly eval companion `docs/agent-weekly-eval.v1.json` и `docs/agent-weekly-eval.md`, собираемый из scorecard и structured telemetry вместо ручного weekly proxy review.
- first completed qualitative weekly review, который подтвердил strong closeout по реальным sampled tasks и закрыл bootstrap-phase gaps в eval loop.
- machine-readable sampled weekly reviews в `docs/agent-weekly-reviews.v1.json`, которые делают qualitative sampling частью schema-backed evidence, а не только markdown narrative.
- one-command refresh wrapper `scripts/refresh_agent_eval.py` и optional schedule helper `scripts/register-agent-eval-schedule.ps1`, который можно подключить к Windows Scheduled Task.
- production-audit remediation bundle: overlap/self-ingestion guard, truthful unsupported-input reporting, repo-local `ruff`/`pyright` install surface, shared script bootstrap, deprecated-only `workers` compatibility, OCR traineddata SHA-256 verification и Windows CI gates для `pip check`, `ruff`, `pyright`, EXE smoke и portable release artifact.
- post-release semantic/package bundle v0.3.0: DOCX formulas/header/footer/footnote units, PDF text/OCR heuristic table/formula/figure units и portable release `DocumentConverter-0.3.0`.
- native XLSX route: `.xlsx` поддерживается как `xlsx_native`, листы/строки/ячейки сохраняются в structural units, а Excel formula strings и cached values попадают в structured `cell` payload.
- env-based formula-recognition config: `.env.local`/`.env` и process env overrides автоматически подхватываются в runtime; explicit `FORMULA_RECOGNITION_*` keys и shorthand `LLM_PROVIDER`/provider-specific model key/`FORMULA_MODEL` совместимы, а `run.json` получает только безопасный `formula_recognition` block без `api_key`. Если есть `OPENROUTER_API_KEY`, но нет отдельного `FORMULA_MODEL`, formula slice по умолчанию использует `openai/gpt-4o`.
- formula-recognition postprocess: runner теперь может дообогащать `formula_image` units через local WMF hint extraction и OpenRouter fallback, сохраняя результаты в `document.v1.json` и `formula-recognition.jsonl` без утечки секрета в артефакты run package; multimodal response закреплён через strict `json_schema`.
- deterministic formula benchmark harness: versioned `samples/formula-benchmark.manifest.jsonl`, gold fixtures и scripts `run_formula_benchmark.py` / `export_formula_gold.py` now anchor formula quality on reproducible artifacts instead of ad hoc visual comparison; benchmark runs are BOM-safe and disable live provider inheritance by default.
- executable formula threshold gate: versioned policy `samples/formula-benchmark.thresholds.json` теперь загружается benchmark harness по умолчанию, report пишет `tier_summaries` + `required_gate`, а baseline `20260525T193008Z` закреплён как текущий numeric floor/ceiling для `anchor`, `gate`, `control` и `overall`; `rolling` остаётся monitor-only до следующего полного rerun.
- refreshed full rerun under required gate: `runs\formula-benchmark\runs\20260526T054732Z` подтвердил новый contract end-to-end без provider leakage и поднял corpus totals до `194/281` calc_expr units и `53/281` native WMF units, сохранив `11/11` gold passed, `control.false_positive_rate = 0.0` и `required_gate.status = passed`.
- opt-in local formula OCR backend: `FORMULA_RECOGNITION_LOCAL_BACKEND=tesseract` inserts a local raster OCR fallback between native WMF hints and live provider calls, and `run.json` safely serializes `local_backend` without exposing secrets.
- initial generalized WMF parser hardening step: known MathType matcher now coalesces adjacent WMF chunks with matching style metadata before signature matching, and the first rule-driven aggregate-price IR slice now closes `904/пр` formula `(2)` without adding a new exact-formula branch; broader token/layout parser work remains open.
- heuristic calc normalization for narrative/chained DOCX formulas: linearized examples with trailing references, textual prefixes, equality-result tails, semicolon clauses and parenthetical formulas can now emit expression-only or cleaned assignment `calc_expr`; narrow benchmark reruns improved `gate-metod-guide` from `0/25` to `21/25` and `gate-metod-521-pr` from `0/6` to `1/6` without touching provider/native coverage.
- native WMF recovery for `521/пр`: focused MathType signature rules now restore formulas `(2)-(6)` as native `mathtype_wmf_text_records` with structured `linear_text`/`display_latex`/`calc_expr`; focused rerun lifted `gate-metod-521-pr` to `5/6` native formulas and `6/6` calc_expr units, proving that a substantial part of the remaining DOCX gap is still recoverable from raw WMF signal.
- heuristic bracket normalization for `1/пр`: square brackets in linearized estimate formulas are now treated as ordinary grouping in the calc-expression path; focused rerun lifted `gate-metod-1-pr` from `18/49` to `23/49` calc_expr units without touching native WMF coverage, which means the remaining misses in that document are no longer simple grouping-syntax fallout.
- native WMF recovery for `1/пр`: inline drawings for formulas `(5)` and `(6)` turned out to be recoverable MathType fractions rather than plain text noise; focused rerun `20260528T072055Z` lifted `gate-metod-1-pr` to `25/49` calc_expr units and gave the document its first `2/49` native formulas, which shifts the next parser work from generic heuristic cleanup to the remaining short-fraction and sum families in the same document.
- follow-up short-fraction recovery for `1/пр`: formula `(8)` also proved recoverable through the same native WMF path; focused rerun `20260528T073325Z` lifted the document to `26/49` calc_expr units and `3/49` native formulas by restoring `К_(уст) = t_(max) / t_(min) <= 1,5`, so the remaining residue is now concentrated in heavier structural families like formula `(4)` rather than in small fractions.
- native sum-case recovery for `1/пр`: formula `(3)` also turned out to be a recoverable WMF pattern rather than noise; focused rerun `20260528T073910Z` restored `Н_(ВрП) = sum Н_(ВрЭ)`, lifted the document to `27/49` calc_expr units and `4/49` native formulas, and left the next parser work concentrated almost entirely in the multi-level fraction family around formula `(4)`.
- native multi-level fraction recovery for `1/пр`: formula `(4)` also proved recoverable through the WMF path once the surrounding where-clause and table/search artifacts were lined up; focused rerun `20260528T074505Z` restored `Н_(ВрЭ) = ЗТ_(эСР) × 100 / (Ч_(факт) × [100 - (Н_(пзр) + Н_(о) + Н_(тп))] × 60)`, lifted the document to `28/49` calc_expr units and `5/49` native formulas, and moved the next parser work from a single known anchor to broader fraction/layout residue.
- noisy fraction-family recovery for `1/пр`: formulas `(23)` and `(31)` also proved recoverable once the noisy linearized signature was tied back to the same denominator skeleton as formula `(4)` but without `Н_(тп)`; focused rerun `20260528T080557Z` restored `Н_(ВрИ) = ЗТ_(Иср) × 100 / (Ч_(общ) × [100 - (Н_(пзр) + Н_(о))] × 60)` and `Н_(ВрЭл) = ЗТ_(эСРл) × 100 / (Ч_(общ) × [100 - (Н_(пзр) + Н_(о))] × 60)`, lifted the document to `30/49` calc_expr units and `7/49` native formulas, and pushed the remaining residue away from this fraction family toward other noisy average/resource-cost patterns.
- first table-hardening sprint: `pdf_text` and `pdf_scan` now share one table normalization contract with dominant-width inference, continuation-line merge and explicit `table_structure_warning` for unresolved ragged tables; DOCX `table_cell` units preserve multiline text and can carry machine-readable `formula` metadata when a formula-like line is present inside the cell.
- table benchmark anchor baseline: `src/doc_converter/sample_expectations.py` и `scripts/validate_sample_expectations.py` делают representative sample expectations executable; `samples/manifest.table-anchors.jsonl` и expected specs для `sample_009`/`sample_018`/`sample_020` закрепляют measured table contour, а fresh run `runs\table-anchors\runs\20260528T092227Z` подтверждает `sample_009`/`sample_018` как stable text-layer anchors и `sample_020` как OCR-blocked scan baseline.
- native WMF recovery for `904/пр`: visual inspection plus raw WMF chunk signatures first turned another noisy DOCX outlier into a narrow native slice, and follow-up rule-driven IR assembly closed formula `(2)` as well; focused rerun `20260526T205614Z` now leaves the document at `6/7` native formulas and `7/7` calc_expr units, with only formula `(6)` remaining on the heuristic plain-text path.
- native WMF recovery for `534/пр`: rendered WMF plus nearby prose disambiguated another formula-rich DOCX outlier; focused rerun lifted `gate-metod-534-pr` from `0/5` to `4/5` native formulas and from `2/5` to `5/5` calc_expr units, leaving only formula `(5)` on the heuristic plain-text path.
- formula-recognition/operator HTML follow-up: postprocess теперь покрывает `formula_image` и residual `formula` units без machine-readable `calc_expr`, packaged EXE ищет `.env.local` рядом с `sys.executable`, а human-readable HTML больше не отправляет в MathJax low-confidence heuristic formulas и показывает распознанные `formula_image` units как readable formula block со ссылкой на исходный asset.
- heuristic calc layer for DOCX formulas: generic `docx_text_linearized` formulas теперь могут получать `calc_expr` и `variables` без hardcoded formula signature, если выражение удалось безопасно нормализовать в линейную arithmetic form; fresh `812/пр` run подтвердил это для формул `ДЗ_(вП)` и `С_(Свлс) = ПЗ1_(п) + ПЗ2_(п) x S_(влс)`.
- safe calc evaluator and richer DOCX arithmetic syntax: operator can now evaluate `calc_expr` through CLI `evaluate-formula`, while heuristic DOCX parsing additionally supports percentages `%` and powers `^`; on Windows the supported operator path is `--values-file` with BOM-safe JSON reading.
- dependency-aware document formula evaluation: operator can now run `evaluate-document-formulas` against `document.v1.json`, get per-formula machine-readable statuses and reuse already computed targets inside the same document; DOCX parser also collapses line-wrap multiply artifacts like `x x` before tokenization so wrapped formulas keep a usable `calc_expr`.
- first-class human-readable QC export: shared renderer `src/doc_converter/human_readable.py` now emits both `human-readable.md` and `human-readable.html`; dedicated `scripts/export_human_readable_html.py` can export a single canonical package or an entire `run_dir` into `human-readable-index.html`, and the GUI exposes this path via an `HTML QC` button for immediate browser-based quality review.
- root-level processed documents catalog: каждый run сохраняет `processed-documents-catalog.json` и `processed-documents-catalog.xlsx` с исходным именем файла, папкой документа, итоговым статусом/issue и hyperlinks на основные обработанные артефакты.
- frozen schema packaging: Windows EXE теперь получает локальный каталог `schemas` в bundle, а runtime schema resolver ищет схемы и в `dist\...\_internal\schemas`, поэтому operator GUI больше не падает на старте обработки из-за missing `run.v1.schema.json`.
- production roadmap S0.1 baseline stabilization: DOCX inline-glyph unittest flake закрыт на уровне тестового cache discipline и canonical variant assertions; `ruff check src tests scripts`, `pyright` и 5 подряд `unittest discover` проходят зелёно.
- production roadmap S1.1 contracts catalog: downstream-facing `processed-documents-catalog.v1`, `chunks.v1`, `chunk-source.v1` и `formula-recognition.v1` зафиксированы в `docs/contracts.md`, drift защищён snapshot-тестом, а run-package validator проверяет `formula-recognition.jsonl` sidecars.
- production roadmap S1.2 known formula patterns data: MathType known-pattern recovery больше не зашит в `docx.py`; canonical JSON + package data, schema validation, export/sync script и regression tests позволяют добавлять новые known formulas через data artifact.
- production roadmap S1.3 agent run metadata + universal validator: новые run packages теперь schema-valid только с `agent_run_metadata`, CLI/runner фиксируют `agent_id/agent_version/task_id/parent_run_id`, `validate_run_package.py` сохраняет legacy validation path через fallback metadata, а `scripts/validate_document_package.py` валидирует все `document.v1.json` и optional `formula-recognition.jsonl` sidecars в run directory.
- production roadmap S2.1 DOCX package split: монолит `src/doc_converter/converters/docx.py` заменён на `src/doc_converter/converters/docx/` с smaller modules `pipeline.py`, `inline_glyph.py`, `formulas/text.py` и `formulas/wmf.py`; package `__init__.py` сохраняет прежний import surface, а focused DOCX, CLI/formula-recognition и full-suite gates подтверждают отсутствие behavioral drift.
- production roadmap S2.2 runner package split: orchestration, startup path validation, resume reuse, processed catalog и formula postprocess вынесены в `src/doc_converter/run/`, а `src/doc_converter/runner.py` остался thin import-compatible wrapper для CLI/GUI и тестов.
- production roadmap S2.3 shared tables package: dominant-width inference, continuation merge и `table_structure_warning` вынесены в `src/doc_converter/tables/`; `pdf_text` и `pdf_scan` теперь используют один parser, а fresh table-anchor run `20260529T162149Z` сохраняет `sample_009/018` expectations без regressions.
- production roadmap S2.4 converter protocol and route registry: `inventory` и `run.orchestration` теперь dispatch-ят через shared `doc_converter.converters` registry + `ConverterProtocol`, runner tests патчат lookup layer, а opt-in dummy `txt` converter regression доказывает extensibility без изменения default supported-format contract.

Следующий backlog:

- production roadmap S9.1: PR-gates и branch protection после закрытия security baseline.
- отдельный security follow-up: parser-level hardening для PDF/XLSX только если эти surfaces станут release-critical.
- отдельный architecture follow-up: вывести `src/doc_converter/formula_benchmark.py` из oversize-состояния без ломки benchmark CLI/report contracts.
- table benchmark follow-up на `sample_009`, `sample_018` и `sample_020`: next sprint должен не создавать baseline с нуля, а снижать `table_structure_warning` density на text-layer anchors, вывести explicit negative/control false-positive contour и устранить OCR blocker на `sample_020`, чтобы scan route тоже вошёл в measured table loop.
- richer DOCX table semantics: после formula-in-cell closure следующий backlog лежит в header-like rows, merged-cell hints и richer review signals для operator QC.
- formula production hardening formalized в `docs/formula-production-plan.md`: broader generalized WMF parser (P1-02), remaining structural residue в `1/пр`, local OCR production decision/guardrails и rolling verdict loop остаются отдельным следующим contour после table benchmark loop.
- optional OCR helper profile (`jbig2`, `pngquant`, `verapdf`) по мере необходимости.
- installer polish или следующий versioned portable package только при новом installable feature bundle.
- tuning heuristic semantic extraction по результатам новых production-like пакетов.

## 3. Релизные блоки

| Блок | Статус |
| --- | --- |
| Baseline and inventory | Готово |
| State foundation | Готово |
| Memory discipline | Готово |
| Deterministic workflow и hooks | Готово |
| Specialist agents и routing | Готово |
| Evaluation и self-review | Готово |
| Release discipline | Готово |

## 4. Release gates

| Gate | Условие |
| --- | --- |
| Gate 1 | Все state docs заведены и согласованы — выполнено |
| Gate 2 | Repo-memory описана и инициализирована — выполнено |
| Gate 3 | Lifecycle hooks и stop budgets описаны — выполнено |
| Gate 4 | Routing matrix и specialist agents заведены — выполнено |
| Gate 5 | Eval loop и regression log заведены — выполнено |
| Gate 6 | Release checklist и runbook готовы — выполнено |

## 5. Approval points

До Sprint 6 все risky production-like действия считаются вне рамки автоматического исполнения. Их approval points должны быть описаны в release documentation и guardrails.

## 7. Текущий release risk

Предыдущие critical-path risks по structured CLI/operator contract, structured runtime telemetry contract, input hardening baseline и missing leak gate закрыты в S6.1-S7.2; ближайший critical path теперь смещён на PR-gates и branch protection в S9.1.

Leak-gate risk закрыт предметно: CI теперь проверяет git-tracked репозиторный контур через Gitleaks без broad filesystem scan по локальным `.venv`/`dist` артефактам, а custom rule доказан synthetic canary-run без ослабления default secret rules.

Операционных blocker-ов для релиза v0.3.0 не осталось. Последний внешний production audit больше не оставляет runtime- или CI-blocker: self-ingestion guard и unsupported accounting закрыты в runtime, OCR traineddata direct downloads проверяются по pinned SHA-256, а lint/type/pip/package smoke выполняются в штатном workflow. Runner monolith risk тоже закрыт: orchestration теперь живёт в smaller `run/` modules, а compatibility surface сохраняется через thin wrapper. Route-coupling risk закрыт следующим архитектурным шагом: `inventory` и `run.orchestration` теперь используют shared converter registry вместо hard-coded format-specific imports и route branches. Table parser ownership тоже приведён к архитектурному baseline: dominant-width inference, continuation merge и `table_structure_warning` больше не размазаны по converters, а живут в shared `tables/` package с подтверждённым fresh anchor run `20260529T162149Z`. Новый table benchmark contour остаётся measured: `sample_009` и `sample_018` держат executable row/cell baseline, warning density всё ещё высокая, а `sample_020` по-прежнему OCR-blocked scan baseline с `partial_success` и `OCRmyPDF failed`. Значит ближайший release-risk по tables теперь ещё уже локализован: не parser drift между routes, а warning-heavy parse, missing negative/control false-positive contour и OCR blocker на одном scan anchor. Следующий critical-path release-risk смещается с route architecture на отсутствие structured CLI/operator contract и последующий security hardening в S6.x/S7.x. Formula benchmark manifest по-прежнему зелёный на curated `metod`/`SP` set и подтверждён run `20260526T054732Z` под executable policy `samples/formula-benchmark.thresholds.json`, поэтому formula backlog можно возвращать после operator-surface tranche. Optional OCR helpers `jbig2`, `pngquant`, `verapdf` остаются необязательными и не блокируют core OCR path. Для harness layer остаточный риск теперь в основном операционный: thresholds уже executable и перепроверены, но telemetry, generated scorecard, generated weekly eval, machine-readable weekly reviews и schedule helper всё ещё требуют дисциплины обновления, а из repo-wide file-size debt остался только `src/doc_converter/formula_benchmark.py`.

## 8. Последняя сборка

- Команда: `powershell -ExecutionPolicy Bypass -File scripts\build-windows.ps1 -Name DocumentConverter`.
- Результат: `dist\DocumentConverter\DocumentConverter.exe`.
- Размер EXE: около 7.04 MB.
- Статус: build succeeded; automated launch smoke passed.

## 9. Portable release package

- Команда: `powershell -ExecutionPolicy Bypass -File scripts\package-release.ps1 -Name DocumentConverter -Version 0.3.0 -SkipBuild`.
- Результат: `dist\release\DocumentConverter-0.3.0\DocumentConverter-0.3.0-windows-portable.zip`.
- Дополнительно: `.sha256.txt` checksum и `release-notes.md`.
- SHA-256: `846177da652775571b97575ecd5006a7d9b01d3eaff985b5dfd8116ccce0fea4`.
- Стратегия релиза: portable zip, installer не требуется для v0.3.0.

## 10. Последний representative pilot

- Команда: `.\.venv\Scripts\python.exe scripts\run_sample_pilot.py --clean`.
- Результат: 21 processed, 21 success, 0 partial_success, 0 failed.
- Routes: `docx_native: 8`, `pdf_text: 10`, `pdf_scan: 3`.
- Route mismatches: 0.

## 11. OCR runtime preflight

- Команда: `.\.venv\Scripts\python.exe -m doc_converter.cli check-ocr`.
- Текущий статус: `ready`.
- Tools: `ocrmypdf` в `.venv\Scripts`, `tesseract` и `gswin64c` через `scoop`.
- Languages: `eng`, `rus`, `osd` доступны.

## 12. OCR runtime install path

- Check-only команда: `powershell -ExecutionPolicy Bypass -File scripts\install-ocr-runtime.ps1 -CheckOnly`.
- Предпочтительный path: `.venv + scoop`, без elevated PowerShell, если `scoop` доступен.
- Fallback path: `winget + choco`, если `scoop` отсутствует.
- Integrity check: direct `eng`, `rus`, `osd` traineddata downloads проверяются по pinned SHA-256; mismatch artifact удаляется и установка останавливается fail-fast.
- Документация: `docs/ocr-runtime-windows.md`.

## 12.1 Weekly eval schedule helper

- Check-only команда: `powershell -ExecutionPolicy Bypass -File scripts\register-agent-eval-schedule.ps1 -CheckOnly`.
- Назначение: optional Windows Scheduled Task поверх `scripts\refresh_agent_eval.py --check --check-markdown`.
- Safety: без `-CheckOnly` helper не заменяет существующую task без явного `-Force`.

## 13. Synthetic E2E и GUI smoke

- Synthetic e2e: `.\.venv\Scripts\python.exe scripts\run_synthetic_e2e.py --clean` даёт schema-valid run package, `processed-documents-catalog.json`, `processed-documents-catalog.xlsx` и `chunks.v1.jsonl`.

- Python startup smoke: `.\.venv\Scripts\python.exe -m unittest tests.test_gui_import -v`.
- EXE startup smoke: `dist\DocumentConverter\DocumentConverter.exe` стартует как процесс и не завершается мгновенно.

## 14. Harness assets validation

- Команда: `.\.venv\Scripts\python.exe scripts\validate_harness_assets.py`.
- Результат: `status: ok`, `features: 40`, `validated: 40`, `active: 0`, `backlog: 0`, `telemetry_entries: 74`.
- Назначение: ранний провал CI при потере feature spine, feature-traceability markers в шаблонах, machine-readable telemetry companion, generated scorecard companion, generated weekly eval companion, machine-readable weekly reviews source, markdown structured companion sync, qualitative weekly review evidence или core product-capabilities ссылок.

## 15. Latest Audit Remediation

- Команды: `.\.venv\Scripts\python.exe -m pip check`, `.\.venv\Scripts\python.exe -m ruff check src tests scripts`, `.\.venv\Scripts\python.exe -m pyright`, `.\.venv\Scripts\python.exe -m unittest discover -v`, `.\.venv\Scripts\python.exe scripts\run_synthetic_e2e.py --clean`, `powershell -ExecutionPolicy Bypass -File scripts\build-windows.ps1 -Name DocumentConverter`, `powershell -ExecutionPolicy Bypass -File scripts\smoke-test-windows-exe.ps1 -ExePath dist\DocumentConverter\DocumentConverter.exe`, `powershell -ExecutionPolicy Bypass -File scripts\package-release.ps1 -Name DocumentConverter -Version 0.3.0 -SkipBuild`, `powershell -ExecutionPolicy Bypass -File scripts\register-agent-eval-schedule.ps1 -CheckOnly`, `powershell -ExecutionPolicy Bypass -File scripts\install-ocr-runtime.ps1 -CheckOnly`, OCR traineddata mismatch smoke.
- Результат: все проверки passed; synthetic run `runs\synthetic-e2e-output\runs\20260523T101722Z`, build/smoke/package прошли на локальной `.venv`, frozen schema lookup подтвердил `dist\DocumentConverter\_internal\schemas`, schedule helper check-only прошёл, OCR helper check-only и mismatch smoke прошли, portable release сформирован в `dist\release\DocumentConverter-0.3.0`.
- Clean-room setup: отдельная внешняя Python 3.12 venv с `pip install -e .[build,dev]` и `pip check` тоже прошла успешно.
- Local env note: предыдущий `pip check` fail был вызван contaminated `cp313` wheels для `charset-normalizer` и `fonttools` внутри старой `.venv`; force-reinstall этих двух пакетов восстановил корректный `cp312` state без изменений project dependencies.
- DOCX inline symbol recognition hotfix: `src/doc_converter/converters/docx.py` теперь линейризует run-level `subscript`/`superscript`, пытается распознавать маленькие inline WMF/EMF/PNG drawings как Unicode-символы и оставляет `[INLINE_DRAWING:filename]` только как fallback; targeted `tests.test_docx_converter` и fresh smoke на реальном `421/пр` подтверждают, что canonical package теперь сохраняет `j = 1 ÷ J, где:` без silent gap внутри формулы.
- DOCX inline symbol vocabulary expansion: recognizer теперь покрывает дополнительные операторы, кванторы и геометрические/логические glyphs (`+`, `-`, `=`, `<`, `>`, `∏`, `∂`, `∇`, `∅`, `∀`, `∃`, `∝`, `∥`, `⊥`, `∠`, `⊕`, `⊗`, `∴`, `∵`); новый regression test прогоняет их через весь DOCX route и подтверждает нормальную Unicode-линеаризацию.
- DOCX MathType WMF formula extraction: для формульных WMF-картинок `421/пр` converter теперь сначала читает MathType WMF text records и только затем падает в glyph/raster fallback; targeted regression и single-doc smoke подтвердили восстановление простых диапазонов и обозначений с индексами, а сложные суммовые формулы зафиксированы как следующий scope для `LaTeX/MathML + calculation AST` вместо plain text-only extraction.
- DOCX formula representation round-trip: canonical `formula` unit теперь может хранить `display_latex`, `calc_expr`, `variables`, `confidence` и `warnings`; fresh `421/пр` run создал machine-readable formula block для формулы 1.1 и `scripts/export_human_readable.py` восстановил её в `human-readable.md` как KaTeX-compatible block с расчётным code expression.
- DOCX formula stability remediation: after visual comparison, repeated MathType WMF signatures in `421/пр` now restore formulas 1, 1.2, 2, 3.1, 4 and 5 as structured LaTeX/calc expressions; normalized range formulas no longer duplicate linear text in readable export, and final Markdown/HTML checks show no `PPV=`, `t1Ttt`, `k1К`, `ЦСТ=` or `\mathrm{sum}` artifacts.
- DOCX heuristic calc-expression remediation: generic `docx_text_linearized` formulas now emit `calc_expr`/`variables` for safe linear arithmetic expressions, including identifiers with digits in the base token (`ПЗ1_(п)`, `ПЗ2_(п)`); fresh single-doc run on `812/пр` confirmed real formulas `ДЗ_(вП)` and `С_(Свлс)` as machine-computable output and regenerated `human-readable.md` from the updated canonical package.
- First-class HTML QC export: `src/doc_converter/human_readable.py` now acts as a shared readable renderer, `scripts/export_human_readable_html.py` builds per-document `human-readable.html` plus a run-level `human-readable-index.html`, and GUI operators can open this QC view directly через кнопку `HTML QC`; real run validation updated both `human-readable.html` and the new index for `812/пр`.
- GUI output-path autofill: when the operator changes the input folder, GUI now suggests a sibling output directory `<input>_output` automatically, while preserving a manually chosen separate output folder; runtime overlap/self-ingestion guard remains unchanged.
- Formula evaluation operator path: `src/doc_converter/formula_eval.py` and CLI subcommand `evaluate-formula` now evaluate the normalized `calc_expr` layer with a safe arithmetic subset only; real Windows validation confirmed the path with BOM-safe JSON values file and produced `S_Svls = 1340.0` for a calc_expr shape extracted from `812/пр`.
- Document-level formula evaluation path: `src/doc_converter/formula_eval.py` and CLI subcommand `evaluate-document-formulas` now walk `document.v1.json`, resolve intra-document formula dependencies through already computed targets and report unresolved inputs per formula; real Windows validation on `812/пр` found 41 `calc_expr` units, computed `S_Svls = 1340.0` and honestly surfaced 40 unresolved formulas without external values.
- XLSX native route validation: real workbook `Расчет стоимости этапов.xlsx` produced schema-valid run `runs\xlsx-sample-output-20260524T011906\runs\20260523T221907Z` with `status=success`, `route=xlsx_native`, 13 sheets, 8533 cell units, 1711 formula cells and 0 missing cached formula values. Residual risk: formulas are preserved, not recalculated by `openpyxl`.
- Env-based formula-recognition config: `src/doc_converter/config.py` now auto-loads `.env.local`/`.env` and process env overrides for both explicit `FORMULA_RECOGNITION_*` keys and shorthand OpenRouter-style aliases like `LLM_PROVIDER`, `OPENROUTER_MODEL`, `FORMULA_MODEL` and `OPENROUTER_API_KEY`; if OpenRouter credentials are present and no dedicated formula override is set, formula recognition defaults to `openai/gpt-4o`, while `src/doc_converter/runner.py` still writes only `provider`, `model` and `configured` to `run.json` without serializing the secret.
- Formula-recognition postprocess: `src/doc_converter/formula_recognition.py` now enriches `formula_image` units after extraction, first using local WMF/MathType hints and then OpenRouter fallback for unresolved assets; the OpenRouter call now asks for strict `json_schema` output so the returned formula block is more reliable for machine-readable downstream calculations. Automated validation still uses mocked provider responses only, so live provider quality and cost need an operator-triggered real run.
