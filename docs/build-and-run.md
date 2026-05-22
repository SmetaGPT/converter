# Build and Run

Дата: 2026-05-22

## 1. CLI запуск из исходников

```powershell
.\.venv\Scripts\python.exe -m doc_converter.cli convert-folder "D:\ФСНБ\Документы\Загрузка НПА\metod" "D:\converter-output"
```

Результат создаётся в:

```text
D:\converter-output\runs\<run_id>\
```

## 2. GUI запуск из исходников

```powershell
.\.venv\Scripts\python.exe scripts\gui_entry.py
```

GUI позволяет выбрать входную и выходную папки, OCR languages, число потоков и запустить обработку.

## 3. Проверка OCR runtime

```powershell
.\.venv\Scripts\python.exe -m doc_converter.cli check-ocr
```

Команда возвращает JSON `ocr-runtime.v1` и exit code `0`, если доступны OCRmyPDF, Tesseract, Ghostscript и запрошенные OCR languages. Если runtime неполный, команда возвращает exit code `1` и список missing tools/languages.

Текущий runtime: `status: ready`; локальный `ocrmypdf` находится в `.venv\Scripts`, Tesseract и Ghostscript установлены через `scoop`, языки `rus`, `eng`, `osd` доступны.

Инструкция установки OCR runtime: `docs/ocr-runtime-windows.md`.

## 4. Тесты

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
```

## 5. Сборка Windows package

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build-windows.ps1 -Name DocumentConverter
```

После успешной сборки EXE находится здесь:

```text
dist\DocumentConverter\DocumentConverter.exe
```

## 6. Representative pilot

```powershell
.\.venv\Scripts\python.exe scripts\run_sample_pilot.py --clean
```

Команда читает `samples/manifest.sample.jsonl`, копирует 21 representative sample во временную input-папку `runs\sample-pilot-input`, запускает тот же batch core и сохраняет сводку в `pilot-summary.json` внутри run directory.

Последняя проверка: 21 processed, 21 success, 0 partial_success, 0 failed; route counts `docx_native: 8`, `pdf_text: 10`, `pdf_scan: 3`.

## 7. Текущие ограничения

- Если OCRmyPDF недоступен, `pdf_scan` документы получают `partial_success`, flags `ocr_required`, `ocr_unavailable`, `review_required` и не теряются.
- Опциональные OCRmyPDF helpers `jbig2`, `pngquant` и `verapdf` не установлены; OCR работает, но часть оптимизаций и PDF/A-проверок пропускается.
- Текущий GUI является MVP-оболочкой над тем же batch core, что и CLI.
- Embeddings и загрузка в БД не входят в converter runtime; для них используется output package и `docs/downstream-handoff.md`.
