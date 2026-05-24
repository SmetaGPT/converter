# Build and Run

.\.venv\Scripts\python.exe -m doc_converter.cli convert-folder "D:\ФСНБ\Документы\Загрузка НПА\metod" "D:\converter-output"

Поддержанные входные форматы: DOCX, PDF с текстовым слоем, PDF-сканы и XLSX. Для XLSX route конвертер сохраняет листы, строки, ячейки, значения и Excel-формулы в `document.v1.json`; cached values формул читаются из workbook, но сами формулы не пересчитываются внутри конвертера.

## 0. Подготовка окружения из чистого checkout

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .[build,dev]
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m ruff check src tests scripts
.\.venv\Scripts\python.exe -m pyright
```

Если `pip check` сообщает `is not supported on this platform`, текущая `.venv` загрязнена wheel-артефактами от другого Python minor version. Для этого репозитория правильный фикс — пересоздать `.venv`, а не менять project dependencies наугад.

## 1. CLI запуск из исходников

```powershell
.\.venv\Scripts\python.exe -m doc_converter.cli convert-folder "D:\ФСНБ\Документы\Загрузка НПА\metod" "D:\converter-output"
```

Для formula-recognition provider config в репозитории заведены env-файлы:

- `.env.example` - отслеживаемый шаблон;
- `.env.local` - локальный файл, который можно заполнить либо explicit-переменными `FORMULA_RECOGNITION_*`, либо shorthand-схемой `LLM_PROVIDER`, provider-specific model key и `FORMULA_MODEL`; он исключён из git.

CLI, GUI и прямое создание `ConverterOptions()` автоматически читают `.env.local` и `.env` из текущей рабочей папки или её родительских каталогов; переменные окружения процесса имеют приоритет над файлами.

Для вашего текущего сценария shorthand-конфиг выглядит так:

- `LLM_PROVIDER=openrouter`
- `OPENROUTER_MODEL=deepseek/deepseek-v4-pro`
- `FORMULA_MODEL=openai/gpt-4o`
- `OPENROUTER_API_KEY=...`

Заполнять нужно именно `.env.local`. В `run.json` попадает только безопасный срез `formula_recognition` с `provider`, `model` и `configured`; `api_key` в run metadata не сериализуется.

Если formula-recognition config заполнен, runner после базового extraction открывает `document.v1.json`, ищет `formula_image` units и запускает отдельный post-processing stage:

- сначала используется локальная WMF/MathType hint extraction, если она даёт достаточную уверенность;
- затем для оставшихся кандидатов вызывается OpenRouter vision model;
- результаты пишутся в `formula-recognition.jsonl`, а успешные распознавания попадают в `unit.text`, `unit.formula` и `processing.formula_recognition` внутри `document.v1.json`.

Live provider call не входит в automated validation этого репозитория, чтобы не расходовать внешние кредиты во время тестов и CI.

Поддержанные входные форматы: DOCX, PDF с текстовым слоем, PDF-сканы и XLSX. Для XLSX route конвертер сохраняет листы, строки, ячейки, значения и Excel-формулы в `document.v1.json`; cached values формул читаются из workbook, но сами формулы не пересчитываются внутри конвертера.

Результат создаётся в:

```text
D:\converter-output\runs\<run_id>\
```

В корне каждого `run_dir` теперь создаются `processed-documents-catalog.json` и `processed-documents-catalog.xlsx`. XLSX-версия содержит тот же каталог в табличном виде и локальные hyperlinks на папку документа, `document.v1.json` и `search_text.txt`, чтобы оператор мог быстро открыть обработанный артефакт и проверить его наличие.

Для обратного человекочитаемого Markdown-экспорта из canonical package:

```powershell
.\.venv\Scripts\python.exe scripts\export_human_readable.py "D:\converter-output\runs\<run_id>\documents\<document_folder>\document.v1.json"
```

Скрипт создаёт `human-readable.md` рядом с `document.v1.json`. Если у `formula` unit есть `formula.display_latex`, он выводится как KaTeX-compatible block `$$...$$`; если есть `formula.calc_expr`, рядом добавляется code block для расчётного слоя.

Для first-class HTML QC-экспорта из canonical package или целого `run_dir`:

```powershell
.\.venv\Scripts\python.exe scripts\export_human_readable_html.py "D:\converter-output\runs\<run_id>\documents\<document_folder>\document.v1.json"
.\.venv\Scripts\python.exe scripts\export_human_readable_html.py "D:\converter-output\runs\<run_id>"
```

Если передан `document.v1.json`, скрипт создаёт `human-readable.html` рядом с canonical package. Если передан весь `run_dir`, скрипт пересобирает `human-readable.html` для каждого документа и создаёт run-level `human-readable-index.html` со ссылками на HTML, `document.v1.json` и `search_text.txt`, чтобы оператор мог быстро открыть QC-срез в браузере.

Для прямой проверки расчётного слоя по уже нормализованному `calc_expr`:

```powershell
@{
    PZ1_p = 1200
    PZ2_p = 3.5
    S_vls = 40
} | ConvertTo-Json | Set-Content -Path .\values.json -Encoding utf8

.\.venv\Scripts\python.exe -m doc_converter.cli evaluate-formula --calc-expr "S_Svls = PZ1_p + PZ2_p * S_vls" --values-file .\values.json
```

На Windows PowerShell практичнее использовать `--values-file`, а не inline `--values`, чтобы не упираться в shell quoting. CLI читает такой JSON BOM-safe через `utf-8-sig`, поэтому файл, записанный PowerShell `Set-Content -Encoding utf8`, тоже принимается корректно.

Для расчёта всех нормализованных `calc_expr` внутри уже готового `document.v1.json`:

```powershell
.\.venv\Scripts\python.exe -m doc_converter.cli evaluate-document-formulas "D:\converter-output\runs\<run_id>\documents\<document_folder>\document.v1.json" --values-file .\values.json
```

Команда проходит по `units[*].formula.calc_expr`, возвращает machine-readable summary и пытается переиспользовать уже вычисленные targets как входы для следующих формул того же документа. Если части значений всё ещё не хватает, CLI честно возвращает `status: partial`, exit code `1` и per-formula `missing_variables`.

## 2. GUI запуск из исходников

```powershell
.\.venv\Scripts\python.exe scripts\gui_entry.py
```

GUI позволяет выбрать входную и выходную папки, OCR languages и запустить обработку.
После завершения run кнопка `HTML QC` пересобирает `human-readable-index.html` для последнего `run_dir` и открывает этот индекс в браузере, чтобы можно было сразу проверить качество конвертации на человекочитаемом HTML-представлении.

Входная и выходная папки не должны совпадать и не могут быть вложены друг в друга.

Текущий GUI v0.2.0 показывает текущий файл, progress, summary counts, позволяет отменить обработку после текущего файла и открыть папку результата. Отдельная кнопка pause/resume не заявляется; вместо этого поддерживается безопасный повторный запуск с reuse предыдущего output для неизменённых файлов.

Базовый automated smoke для GUI:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_gui_import -v
```

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

## 5. Synthetic E2E и schema validation

```powershell
.\.venv\Scripts\python.exe scripts\run_synthetic_e2e.py --clean
.\.venv\Scripts\python.exe scripts\validate_run_package.py runs\synthetic-e2e-output\runs\<run_id>
```

Synthetic e2e создаёт локальный DOCX, прогоняет converter end-to-end, строит `chunks.v1.jsonl` и валидирует `run.json`, `summary.json`, `queue-state.json`, `processed-documents-catalog.json`, `processed-documents-catalog.xlsx`, `manifest.jsonl`, `review-required.jsonl`, `document.v1.json` и `chunks.v1.jsonl`.

## 6. Сборка Windows package

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build-windows.ps1 -Name DocumentConverter
```

После успешной сборки EXE находится здесь:

```text
dist\DocumentConverter\DocumentConverter.exe
```

Последняя автоматическая проверка запуска EXE: process стартует и не завершается мгновенно, после чего корректно останавливается как launch-smoke без ручного UI walkthrough.

Команда smoke-проверки собранного EXE:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\smoke-test-windows-exe.ps1 -ExePath dist\DocumentConverter\DocumentConverter.exe
```

## 7. Portable release package

```powershell
powershell -ExecutionPolicy Bypass -File scripts\package-release.ps1 -Name DocumentConverter -Version 0.3.0
```

Portable release формируется в `dist\release\DocumentConverter-0.3.0\` и содержит zip, SHA-256 checksum и release notes.

## 8. Representative pilot

```powershell
.\.venv\Scripts\python.exe scripts\run_sample_pilot.py --clean
```

Команда читает `samples/manifest.sample.jsonl`, копирует 21 representative sample во временную input-папку `runs\sample-pilot-input`, запускает тот же batch core и сохраняет сводку в `pilot-summary.json` внутри run directory.

Последняя проверка: 21 processed, 21 success, 0 partial_success, 0 failed; route counts `docx_native: 8`, `pdf_text: 10`, `pdf_scan: 3`; run dir `runs\sample-pilot\runs\20260522T180732Z`.

## 9. Reference chunks

```powershell
.\.venv\Scripts\python.exe scripts\build_sample_chunks.py runs\sample-pilot\runs\<run_id>
```

Скрипт строит reference `chunks.v1.jsonl` из `document.v1.json` и валидирует каждую запись по `schemas/chunks.v1.schema.json`.

## 10. Optional weekly eval schedule

Generated scorecard и weekly eval можно оставить ручной командой:

```powershell
.\.venv\Scripts\python.exe scripts\refresh_agent_eval.py
.\.venv\Scripts\python.exe scripts\refresh_agent_eval.py --check --check-markdown
```

Если ручной weekly refresh начинает создавать overhead, guarded helper регистрирует Windows Scheduled Task поверх того же script:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\register-agent-eval-schedule.ps1 -CheckOnly
powershell -ExecutionPolicy Bypass -File scripts\register-agent-eval-schedule.ps1 -DayOfWeek Monday -At 09:00
```

`-CheckOnly` печатает JSON plan и ничего не регистрирует. Если task уже существует, helper требует `-Force`, чтобы замена была явной.

## 11. Текущие ограничения

- Если OCRmyPDF недоступен, `pdf_scan` документы получают `partial_success`, flags `ocr_required`, `ocr_unavailable`, `review_required` и не теряются.
- Release profile сейчас делится на core и optional: core = `ocrmypdf`, `tesseract`, `ghostscript`; optional = `jbig2`, `pngquant`, `verapdf`.
- Опциональные OCRmyPDF helpers `jbig2`, `pngquant` и `verapdf` не установлены; OCR работает, но часть оптимизаций и PDF/A-проверок пропускается.
- PDF route в release scope v0.3.0 добавляет heuristic semantic units для tables/formulas/figure captions поверх text-layer и OCR text; сложные multi-column/table layouts всё ещё требуют downstream review по quality flags.
- DOCX route в release scope v0.3.0 добавляет semantic pass для formulas, headers, footers и footnotes; embedded formula images классифицируются эвристически по media metadata, а MathType WMF formula text records могут заполнять `formula.display_latex` и `formula.calc_expr` для последующего KaTeX/Word rendering и расчётов.
- Embeddings и загрузка в БД не входят в converter runtime; для них используется output package и `docs/downstream-handoff.md`.
