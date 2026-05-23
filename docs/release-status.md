# Release Status

Последнее обновление: 2026-05-23
Релизный контур: Windows Document Converter v0.2.0
Статус: production-ready within declared scope

## 1. Цель релиза

Довести репозиторий до состояния, в котором агентный контур поддерживает полный цикл: baseline, state, memory, lifecycle, routing, evaluation и release discipline.

## 2. Текущая стадия

Сейчас проект находится в release closure state: converter имеет runtime schema validation, resume/reuse для неизменённых файлов, duplicate skip без перезаписи canonical package, operator-grade GUI surface, reference chunk builder, Windows CI, synthetic e2e и portable release packaging. После v0.2.0 также реализован и validated post-release semantic metadata enhancement для `document.v1.json` (`title`, `document_type`, `short_summary`). Дополнительно harness layer теперь имеет machine-readable feature spine, bootstrap contract, clean-exit checklist, sprint contract template, evaluator rubric и CI-backed validator для этих артефактов, а feature spine покрывает и core product-capabilities конвертера, связан с task-flow через `feature_id` traceability, дополнен schema-backed telemetry JSONL companion, generated scorecard companion, generated weekly eval companion, machine-readable weekly review source и one-command refresh wrapper для этого eval contour.

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
- one-command refresh wrapper `scripts/refresh_agent_eval.py`, который пересобирает и проверяет generated eval companions одним вызовом.

Следующий backlog:

- advanced semantic extraction для PDF tables, formulas и figures как post-release enhancement;
- DOCX footnotes/header/footer semantic pass как post-release enhancement;
- optional OCR helper profile (`jbig2`, `pngquant`, `verapdf`) по мере необходимости.
- optional schedule поверх `scripts/refresh_agent_eval.py`, если weekly cadence начнёт создавать ручной overhead.
- следующий portable package должен быть пересобран/версирован отдельно, если semantic metadata нужно отдать как installable artifact.

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

Операционных blocker-ов для релиза v0.2.0 не осталось. Остаточный риск теперь ограничен только явно задокументированным scope: advanced semantic extraction PDF tables/figures/formulas и DOCX footnotes/header/footer вынесены в post-release enhancements и не являются частью обещанного release contract. Optional OCR helpers `jbig2`, `pngquant`, `verapdf` остаются необязательными и не блокируют core OCR path. Для harness layer остаточный риск теперь в основном операционный, а не структурный: traceability, structured telemetry, generated scorecard, generated weekly eval и machine-readable weekly reviews уже замкнуты end-to-end, но будущие недели всё ещё требуют дисциплины обновления telemetry и `docs/agent-weekly-reviews.v1.json`.

## 8. Последняя сборка

- Команда: `powershell -ExecutionPolicy Bypass -File scripts\build-windows.ps1 -Name DocumentConverter`.
- Результат: `dist\DocumentConverter\DocumentConverter.exe`.
- Размер EXE: около 7.37 MB.
- Статус: build succeeded; automated launch smoke passed.

## 9. Portable release package

- Команда: `powershell -ExecutionPolicy Bypass -File scripts\package-release.ps1 -Name DocumentConverter -Version 0.2.0 -SkipBuild`.
- Результат: `dist\release\DocumentConverter-0.2.0\DocumentConverter-0.2.0-windows-portable.zip`.
- Дополнительно: `.sha256.txt` checksum и `release-notes.md`.
- Стратегия релиза: portable zip, installer не требуется для v0.2.0.

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
- Документация: `docs/ocr-runtime-windows.md`.

## 13. Synthetic E2E и GUI smoke

- Synthetic e2e: `.\.venv\Scripts\python.exe scripts\run_synthetic_e2e.py --clean` даёт schema-valid run package и `chunks.v1.jsonl`.

- Python startup smoke: `.\.venv\Scripts\python.exe -m unittest tests.test_gui_import -v`.
- EXE startup smoke: `dist\DocumentConverter\DocumentConverter.exe` стартует как процесс и не завершается мгновенно.

## 14. Harness assets validation

- Команда: `.\.venv\Scripts\python.exe scripts\validate_harness_assets.py`.
- Результат: `status: ok`, `features: 22`, `validated: 22`, `active: 0`, `backlog: 0`, `telemetry_entries: 13`.
- Назначение: ранний провал CI при потере feature spine, feature-traceability markers в шаблонах, machine-readable telemetry companion, generated scorecard companion, generated weekly eval companion, machine-readable weekly reviews source, markdown structured companion sync, qualitative weekly review evidence или core product-capabilities ссылок.
