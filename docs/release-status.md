# Release Status

Последнее обновление: 2026-05-24
Релизный контур: Windows Document Converter v0.3.0
Статус: production-ready within declared scope

## 1. Цель релиза

Довести репозиторий до состояния, в котором агентный контур поддерживает полный цикл: baseline, state, memory, lifecycle, routing, evaluation и release discipline.

## 2. Текущая стадия

Сейчас проект находится в release closure state: converter имеет runtime schema validation, resume/reuse для неизменённых файлов, duplicate skip без перезаписи canonical package, operator-grade GUI surface, reference chunk builder, Windows CI, synthetic e2e и portable release packaging. После v0.2.0 реализованы semantic metadata enhancement для `document.v1.json`, heuristic semantic extraction для DOCX/PDF tables/formulas/figures и DOCX footnotes/header/footer, native XLSX route для workbook/sheet/cell/formula packages, env-based formula-recognition provider config с безопасной сериализацией run metadata, formula-recognition postprocess с local WMF hint extraction и OpenRouter fallback, optional Windows schedule helper для eval refresh, root-level `processed-documents-catalog.json` и `processed-documents-catalog.xlsx` для operator navigation, а portable package пересобран как v0.3.0. Дополнительно harness layer теперь имеет machine-readable feature spine, bootstrap contract, clean-exit checklist, sprint contract template, evaluator rubric и CI-backed validator для этих артефактов, а feature spine покрывает и core product-capabilities конвертера, связан с task-flow через `feature_id` traceability, дополнен schema-backed telemetry JSONL companion, generated scorecard companion, generated weekly eval companion, machine-readable weekly review source, one-command refresh wrapper и guarded schedule helper для этого eval contour.

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
- env-based formula-recognition config: `.env.local`/`.env` и process env overrides автоматически подхватываются в runtime; explicit `FORMULA_RECOGNITION_*` keys и shorthand `LLM_PROVIDER`/provider-specific model key/`FORMULA_MODEL` совместимы, а `run.json` получает только безопасный `formula_recognition` block без `api_key`.
- formula-recognition postprocess: runner теперь может дообогащать `formula_image` units через local WMF hint extraction и OpenRouter fallback, сохраняя результаты в `document.v1.json` и `formula-recognition.jsonl` без утечки секрета в артефакты run package.
- heuristic calc layer for DOCX formulas: generic `docx_text_linearized` formulas теперь могут получать `calc_expr` и `variables` без hardcoded formula signature, если выражение удалось безопасно нормализовать в линейную arithmetic form; fresh `812/пр` run подтвердил это для формул `ДЗ_(вП)` и `С_(Свлс) = ПЗ1_(п) + ПЗ2_(п) x S_(влс)`.
- safe calc evaluator and richer DOCX arithmetic syntax: operator can now evaluate `calc_expr` through CLI `evaluate-formula`, while heuristic DOCX parsing additionally supports percentages `%` and powers `^`; on Windows the supported operator path is `--values-file` with BOM-safe JSON reading.
- dependency-aware document formula evaluation: operator can now run `evaluate-document-formulas` against `document.v1.json`, get per-formula machine-readable statuses and reuse already computed targets inside the same document; DOCX parser also collapses line-wrap multiply artifacts like `x x` before tokenization so wrapped formulas keep a usable `calc_expr`.
- root-level processed documents catalog: каждый run сохраняет `processed-documents-catalog.json` и `processed-documents-catalog.xlsx` с исходным именем файла, папкой документа, итоговым статусом/issue и hyperlinks на основные обработанные артефакты.
- frozen schema packaging: Windows EXE теперь получает локальный каталог `schemas` в bundle, а runtime schema resolver ищет схемы и в `dist\...\_internal\schemas`, поэтому operator GUI больше не падает на старте обработки из-за missing `run.v1.schema.json`.

Следующий backlog:

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

Операционных blocker-ов для релиза v0.3.0 не осталось. Последний внешний production audit больше не оставляет runtime- или CI-blocker: self-ingestion guard и unsupported accounting закрыты в runtime, OCR traineddata direct downloads проверяются по pinned SHA-256, а lint/type/pip/package smoke выполняются в штатном workflow. Advanced semantic extraction теперь закрыт в heuristic scope: PDF/DOCX tables/formulas/figures и DOCX footnotes/header/footer попадают в canonical units, но сложные layouts и multimodal figure semantics всё ещё требуют review/tuning на новых корпусах. Optional OCR helpers `jbig2`, `pngquant`, `verapdf` остаются необязательными и не блокируют core OCR path. Для harness layer остаточный риск теперь в основном операционный: telemetry, generated scorecard, generated weekly eval, machine-readable weekly reviews и schedule helper замкнуты, но качественный weekly sampling всё ещё должен обновляться осознанно.

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
- Результат: `status: ok`, `features: 25`, `validated: 25`, `active: 0`, `backlog: 0`, `telemetry_entries: 33`.
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
- Formula evaluation operator path: `src/doc_converter/formula_eval.py` and CLI subcommand `evaluate-formula` now evaluate the normalized `calc_expr` layer with a safe arithmetic subset only; real Windows validation confirmed the path with BOM-safe JSON values file and produced `S_Svls = 1340.0` for a calc_expr shape extracted from `812/пр`.
- Document-level formula evaluation path: `src/doc_converter/formula_eval.py` and CLI subcommand `evaluate-document-formulas` now walk `document.v1.json`, resolve intra-document formula dependencies through already computed targets and report unresolved inputs per formula; real Windows validation on `812/пр` found 41 `calc_expr` units, computed `S_Svls = 1340.0` and honestly surfaced 40 unresolved formulas without external values.
- XLSX native route validation: real workbook `Расчет стоимости этапов.xlsx` produced schema-valid run `runs\xlsx-sample-output-20260524T011906\runs\20260523T221907Z` with `status=success`, `route=xlsx_native`, 13 sheets, 8533 cell units, 1711 formula cells and 0 missing cached formula values. Residual risk: formulas are preserved, not recalculated by `openpyxl`.
- Env-based formula-recognition config: `src/doc_converter/config.py` now auto-loads `.env.local`/`.env` and process env overrides for both explicit `FORMULA_RECOGNITION_*` keys and shorthand OpenRouter-style aliases like `LLM_PROVIDER`, `OPENROUTER_MODEL`, `FORMULA_MODEL` and `OPENROUTER_API_KEY`, while `src/doc_converter/runner.py` writes only `provider`, `model` and `configured` to `run.json` without serializing the secret.
- Formula-recognition postprocess: `src/doc_converter/formula_recognition.py` now enriches `formula_image` units after extraction, first using local WMF/MathType hints and then OpenRouter fallback for unresolved assets; automated validation uses mocked provider responses only, so live provider quality and cost still need an operator-triggered real run.
