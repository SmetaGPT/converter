# Current Sprint

Последнее обновление: 2026-05-22
Активный спринт: Release Closure — Production readiness v0.2.0
Статус: completed

Последний завершённый спринт: Release Closure — Production readiness v0.2.0
Статус wave 1: completed

## 1. Цель спринта

Закрыть production gates поверх Sprint 13-16: runtime schema validation, resume/idempotency, honest CLI/GUI contract, quality reporting, downstream chunks, Windows CI и portable release packaging.

## 2. Артефакты спринта

- docs/document-converter-roadmap.md
- docs/document-converter-acceptance.md
- docs/build-and-run.md
- docs/ocr-runtime-windows.md
- docs/current-status.md
- docs/release-status.md
- .github/prompts/production-readiness-hardening.prompt.md
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

## 4. Validation targets спринта

1. Full test suite проходит.
2. Representative pilot-run создаёт output package без failed documents.
3. Windows package собирается через `scripts/build-windows.ps1`.
4. OCR runtime preflight возвращает `status: ready`.
5. Собранный EXE проходит automated launch smoke без мгновенного падения.
6. Synthetic e2e создаёт schema-valid run package и `chunks.v1.jsonl`.
7. Portable release package создаётся с checksum и release notes.
8. Ограничения advanced semantic extraction и optional OCR helpers зафиксированы явно.

## 5. Риски спринта

- Advanced semantic extraction PDF tables/figures/formulas остаётся post-release enhancement;
- DOCX footnotes/header/footer semantic pass остаётся post-release enhancement;
- Optional OCR helpers `jbig2`, `pngquant`, `verapdf` не установлены; это не блокирует OCR, но ограничивает оптимизацию и PDF/A checks.

## 6. Критерий выхода

Спринт закрыт, потому что delivery loop подтвердил:

- representative pilot-run на расширенном sample set выполнен;
- OCR runtime установлен и проверен;
- Python GUI и собранный EXE проходят automated startup smoke;
- runtime schema validation, resume/idempotency, quality reporting, downstream chunks, CI и portable release packaging подтверждены.

## 7. Следующий operational focus

1. Расширить advanced semantic extraction для PDF tables/figures/formulas.
2. Добавить DOCX footnotes/header/footer semantic pass при наличии product need.
3. Решить, нужны ли optional OCR helpers `jbig2`, `pngquant`, `verapdf` по эксплуатационным метрикам.

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
- Portable release: `powershell -ExecutionPolicy Bypass -File scripts\package-release.ps1 -Name DocumentConverter -Version 0.2.0 -SkipBuild`.
- Synthetic e2e: `.\.venv\Scripts\python.exe scripts\run_synthetic_e2e.py --clean`.
- Python GUI smoke: `.\.venv\Scripts\python.exe -m unittest tests.test_gui_import -v`.
- EXE smoke: `dist\DocumentConverter\DocumentConverter.exe` стартует как процесс и не завершается мгновенно.
