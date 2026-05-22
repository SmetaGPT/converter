# Current Sprint

Последнее обновление: 2026-05-22
Активный спринт: Sprint 12 — Pilot and Release Hardening
Статус: in-progress

Последний завершённый спринт: Sprint 10 — Windows Packaging MVP
Статус wave 1: completed

## 1. Цель спринта

Проверить Windows Document Converter MVP на representative ФСНБ samples, зафиксировать ограничения и подготовить следующий hardening backlog.

## 2. Артефакты спринта

- docs/document-converter-roadmap.md
- docs/document-converter-acceptance.md
- docs/build-and-run.md
- docs/ocr-runtime-windows.md
- docs/downstream-handoff.md
- samples/manifest.sample.jsonl
- samples/expected/
- pyproject.toml
- src/doc_converter/
- tests/
- schemas/
- scripts/

## 3. Задачи спринта

| Задача | Статус |
| --- | --- |
| Создать roadmap Windows Document Converter | Готово |
| Выбрать representative DOCX/PDF | Готово |
| Описать acceptance criteria для DOCX/PDF/PDF-scan | Готово |
| Зафиксировать обязательные поля `document.v1.json` | Готово |
| Зафиксировать quality flags первой версии | Готово |
| Классифицировать PDF samples на `pdf_text` и `pdf_scan` | Готово |
| Подготовить expected structural units для 3-5 документов | Готово |
| Реализовать CLI core и run directory layout | Готово |
| Реализовать canonical schemas и stable IDs | Готово |
| Реализовать inventory, hashing, dedup и route detection | Готово |
| Реализовать DOCX route | Готово |
| Реализовать PDF-text route | Готово |
| Реализовать PDF-scan degraded route | Готово |
| Добавить quality gates | Готово |
| Добавить GUI MVP | Готово |
| Собрать Windows package | Готово |
| Провести representative pilot-run | Готово |
| Провести full 21-sample pilot-run | Готово |
| Добавить OCR runtime preflight | Готово |
| Добавить OCR runtime install helper | Готово |
| Установить и проверить OCR runtime | Готово |

## 4. Validation targets спринта

1. Full test suite проходит: `python -m unittest discover -v`.
2. Representative pilot-run создаёт output package без failed documents.
3. Windows package собирается через `scripts/build-windows.ps1`.
4. Ограничения OCR и advanced PDF extraction зафиксированы явно.
5. Full representative pilot проходит через `scripts/run_sample_pilot.py` без failed documents и route mismatches.
6. OCR runtime preflight возвращает машинно-читаемый статус готовности OCR dependencies.
7. `pdf_scan` representative samples проходят с `ocr_applied: true` в project venv.

## 5. Риски спринта

- PDF tables, formulas и figures пока не имеют advanced extraction;
- GUI MVP не проходил ручной визуальный smoke после сборки EXE;
- PyInstaller build package собран, но installer ещё не оформлен.
- Optional OCR helpers `jbig2`, `pngquant`, `verapdf` не установлены; это не блокирует OCR, но ограничивает оптимизацию и PDF/A checks.

## 6. Критерий выхода

Спринт считается завершённым, когда delivery loop гарантирует:

- representative pilot-run на расширенном sample set выполнен;
- OCR runtime либо установлен и проверен, либо ограничение сохранено как release blocker;
- GUI EXE вручную открыт и проходит basic operator flow;
- hardening backlog оформлен.

## 7. Следующий operational focus

1. Расширить PDF extraction для tables/figures/formulas.
2. Провести ручной GUI EXE smoke на small batch.
3. Решить, нужны ли optional OCR helpers `jbig2`, `pngquant`, `verapdf` в release package.

## 8. Последняя representative проверка

- Команда: `python scripts\run_sample_pilot.py --clean`.
- Run dir: `runs\sample-pilot\runs\20260522T162409Z` и повторная проверка `runs\sample-pilot\runs\20260522T162602Z`.
- Результат: 21 processed, 21 success, 0 partial_success, 0 failed.
- Routes: `docx_native: 8`, `pdf_text: 10`, `pdf_scan: 3`.
- Route mismatches: 0.

## 9. OCR runtime diagnostic

- Команда: `.\.venv\Scripts\python.exe -m doc_converter.cli check-ocr`.
- Текущий статус: `ready`.
- Tools: локальный `ocrmypdf` в `.venv\Scripts`, `tesseract` и `gswin64c` через `scoop`.
- Languages: `eng`, `rus`, `osd` доступны.

## 10. OCR runtime install helper

- Check-only команда: `powershell -ExecutionPolicy Bypass -File scripts\install-ocr-runtime.ps1 -CheckOnly`.
- Предпочтительный path: `.venv + scoop`, без elevated PowerShell, если `scoop` доступен.
- Fallback path: `winget + choco`, если `scoop` отсутствует.
