# Release Status

Последнее обновление: 2026-05-23
Релизный контур: Windows Document Converter v0.3.0
Статус: production-ready within declared scope

## 1. Цель релиза

Довести репозиторий до состояния, в котором агентный контур поддерживает полный цикл: baseline, state, memory, lifecycle, routing, evaluation и release discipline.

## 2. Текущая стадия

Сейчас проект находится в release closure state: converter имеет runtime schema validation, resume/reuse для неизменённых файлов, duplicate skip без перезаписи canonical package, operator-grade GUI surface, reference chunk builder, Windows CI, synthetic e2e и portable release packaging. После v0.2.0 реализованы semantic metadata enhancement для `document.v1.json`, heuristic semantic extraction для DOCX/PDF tables/formulas/figures и DOCX footnotes/header/footer, optional Windows schedule helper для eval refresh, а portable package пересобран как v0.3.0. Дополнительно harness layer теперь имеет machine-readable feature spine, bootstrap contract, clean-exit checklist, sprint contract template, evaluator rubric и CI-backed validator для этих артефактов, а feature spine покрывает и core product-capabilities конвертера, связан с task-flow через `feature_id` traceability, дополнен schema-backed telemetry JSONL companion, generated scorecard companion, generated weekly eval companion, machine-readable weekly review source, one-command refresh wrapper и guarded schedule helper для этого eval contour.

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
- Размер EXE: около 7.37 MB.
- Статус: build succeeded; automated launch smoke passed.

## 9. Portable release package

- Команда: `powershell -ExecutionPolicy Bypass -File scripts\package-release.ps1 -Name DocumentConverter -Version 0.3.0 -SkipBuild`.
- Результат: `dist\release\DocumentConverter-0.3.0\DocumentConverter-0.3.0-windows-portable.zip`.
- Дополнительно: `.sha256.txt` checksum и `release-notes.md`.
- SHA-256: `2ce1f979b0eecc7644ca52b903034c72d642a7cdef7c54b760e4b4d510ed72f8`.
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

- Synthetic e2e: `.\.venv\Scripts\python.exe scripts\run_synthetic_e2e.py --clean` даёт schema-valid run package и `chunks.v1.jsonl`.

- Python startup smoke: `.\.venv\Scripts\python.exe -m unittest tests.test_gui_import -v`.
- EXE startup smoke: `dist\DocumentConverter\DocumentConverter.exe` стартует как процесс и не завершается мгновенно.

## 14. Harness assets validation

- Команда: `.\.venv\Scripts\python.exe scripts\validate_harness_assets.py`.
- Результат: `status: ok`, `features: 22`, `validated: 22`, `active: 0`, `backlog: 0`, `telemetry_entries: 17`.
- Назначение: ранний провал CI при потере feature spine, feature-traceability markers в шаблонах, machine-readable telemetry companion, generated scorecard companion, generated weekly eval companion, machine-readable weekly reviews source, markdown structured companion sync, qualitative weekly review evidence или core product-capabilities ссылок.

## 15. Latest Audit Remediation

- Команды: `.\.venv\Scripts\python.exe -m pip check`, `.\.venv\Scripts\python.exe -m ruff check src tests scripts`, `.\.venv\Scripts\python.exe -m pyright`, `.\.venv\Scripts\python.exe -m unittest discover -v`, `.\.venv\Scripts\python.exe scripts\run_synthetic_e2e.py --clean`, `powershell -ExecutionPolicy Bypass -File scripts\build-windows.ps1 -Name DocumentConverter`, `powershell -ExecutionPolicy Bypass -File scripts\smoke-test-windows-exe.ps1 -ExePath dist\DocumentConverter\DocumentConverter.exe`, `powershell -ExecutionPolicy Bypass -File scripts\package-release.ps1 -Name DocumentConverter -Version 0.3.0 -SkipBuild`, `powershell -ExecutionPolicy Bypass -File scripts\register-agent-eval-schedule.ps1 -CheckOnly`, `powershell -ExecutionPolicy Bypass -File scripts\install-ocr-runtime.ps1 -CheckOnly`, OCR traineddata mismatch smoke.
- Результат: все проверки passed; synthetic run `runs\synthetic-e2e-output\runs\20260523T101722Z`, build/smoke/package прошли на локальной `.venv`, schedule helper check-only прошёл, OCR helper check-only и mismatch smoke прошли, portable release сформирован в `dist\release\DocumentConverter-0.3.0`.
- Clean-room setup: отдельная внешняя Python 3.12 venv с `pip install -e .[build,dev]` и `pip check` тоже прошла успешно.
- Local env note: предыдущий `pip check` fail был вызван contaminated `cp313` wheels для `charset-normalizer` и `fonttools` внутри старой `.venv`; force-reinstall этих двух пакетов восстановил корректный `cp312` state без изменений project dependencies.
