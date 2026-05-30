# Security

Дата: 2026-05-30
Статус: S7.1 input-hardening baseline

## 1. Назначение

Этот документ фиксирует минимальный security baseline для Windows Document Converter при работе с untrusted DOCX/PDF/XLSX inputs. Цель не в том, чтобы объявить продукт sandboxed, а в том, чтобы явно ограничить самые дешёвые и наиболее вероятные классы риска: path confusion, archive bombs, oversized WMF payloads и неконтролируемый subprocess surface.

## 2. Trust boundaries

- `input_dir` считается недоверенным целиком: структура каталогов, имена файлов, содержимое архивов и embedded assets могут быть враждебными.
- `output_dir` и `runs_dir` считаются единственными разрешёнными корнями записи для conversion path.
- canonical package и telemetry artifacts считаются локальными продукт-артефактами и не должны записываться вне `output_dir`.
- network access не требуется для базового conversion path; optional formula-recognition provider считается отдельной доверительной границей и включается только при явной конфигурации.

## 3. Threat model

| Угроза | Поверхность | Базовый контроль |
| --- | --- | --- |
| Self-ingestion / path confusion | startup paths | `validate_run_directories` резолвит пути, запрещает overlap/nesting и отклоняет symlink components в `input_dir`, `output_dir`, `runs_dir`. |
| Запись вне разрешённого output tree | startup paths | `runs_dir` обязан оставаться внутри резолвленного `output_dir`; другие корни записи не допускаются. |
| OOXML zip bomb | DOCX archive admission | перед `python-docx` и archive extraction действует лимит на entry count и суммарный uncompressed size. |
| Archive traversal внутри DOCX | DOCX media/footnotes extraction | member paths с absolute, drive-qualified, backslash и `..`-segments отклоняются до extraction. |
| Oversized / record-heavy WMF payload | MathType WMF parser | `_extract_wmf_text_chunks` ограничен по общему размеру blob и по числу records. |
| Hanging / unsafe local subprocess | OCR / local render helpers | subprocess запускаются фиксированными аргументами без shell и с timeout. |
| Secret leakage в run artifacts | formula recognition config | API keys не сериализуются в `run.json`, `document.v1.json` и telemetry artifacts. |

## 4. Path policy

- `input_dir` должен существовать и быть директорией.
- `output_dir` может быть создан, но не может быть файлом.
- `input_dir` и `output_dir` не могут совпадать и не могут быть вложены друг в друга.
- Ни один компонент пути в `input_dir`, `output_dir` и `output_dir/runs` не должен быть symlink.
- Все runtime записи должны оставаться внутри `output_dir`, а run-level writes внутри `output_dir/runs`.

## 5. OOXML / DOCX admission limits

Текущий baseline для DOCX:

- `MAX_DOCX_ARCHIVE_ENTRIES = 4096`
- `MAX_DOCX_UNCOMPRESSED_BYTES = 128 MiB`

Эти лимиты применяются до `Document(...)`, а также повторно перед extraction `word/media/*` и `word/footnotes.xml`.

Rejected conditions:

- archive не является корректным ZIP/DOCX;
- число entries выше лимита;
- суммарный uncompressed size выше лимита;
- внутри архива есть absolute, drive-qualified, backslash-based или traversal-like member path.

Поведение при срабатывании: DOCX route fail-closed через `DocxSecurityError`, а runner отражает это как per-document failure без записи за пределы run package.

## 6. WMF limits

Текущий baseline для MathType WMF parser:

- `MAX_WMF_BYTES = 8 MiB`
- `MAX_WMF_RECORDS = 20000`

Поведение при срабатывании: parser поднимает `WmfParseLimitError`; oversized или record-heavy payload не должен парситься без ограничения.

## 7. Font policy

- Конвертер не должен динамически скачивать шрифты во время runtime.
- Для operator/deployment path разрешены только bundled fonts из локального package/repo или уже установленные системные fonts.
- Отсутствие ожидаемого font bundle считается environment issue и должно подсвечиваться preflight-командой `doctor`, а не компенсироваться скрытым network fetch.
- Font handling не должен расширять write surface за пределы временных директорий subprocess helper-ов и `output_dir`.

## 8. Subprocess inventory

| Surface | Файл | Назначение | Guardrails |
| --- | --- | --- | --- |
| `ocrmypdf` | `src/doc_converter/converters/pdf_scan.py` | OCR для scan PDF route | фиксированный argv, `timeout=900`, output only inside run-local `ocr/` |
| `tesseract --list-langs` | `src/doc_converter/ocr_runtime.py` | runtime preflight | фиксированный argv, `timeout=30`, read-only probe |
| `tesseract` local backend | `src/doc_converter/formula_recognition.py` | optional local formula OCR | фиксированный argv, temp files only, timeout, no shell |
| `powershell -File render-inline-metafile.ps1` | `src/doc_converter/converters/docx/inline_glyph.py` | Windows-only WMF/EMF rasterization helper | `-NoProfile -NonInteractive`, temp dir only, timeout, no shell interpolation |
| `explorer` / `webbrowser.open` | `src/doc_converter/gui.py` | operator convenience после конвертации | не участвует в conversion path и не обрабатывает untrusted input как executable content |

## 9. Residual risk

- Это не sandbox: malformed third-party libraries (`python-docx`, `pypdf`, `openpyxl`, PIL/System.Drawing) всё ещё выполняются в процессе конвертера.
- PDF route пока не имеет отдельного parser-level threat model и content-size limits того же уровня детализации, что DOCX/WMF.
- Legacy compatibility logs (`processing-log.jsonl`, `errors.jsonl`) ещё не удалены; они не расширяют write surface, но усложняют final deprecation story.
- Optional provider-backed formula recognition остаётся отдельной network boundary и требует operator judgment по включению в production-like окружениях.

## 10. Validation hooks

- `tests/test_run_paths.py` подтверждает startup path allowlist и symlink rejection.
- `tests/test_docx_converter.py` содержит malicious-limit checks для DOCX archive entry/uncompressed-size limits и WMF parser limits.
- `scripts/validate_run_package.py` остаётся post-run structural validator и не заменяет input-admission checks.