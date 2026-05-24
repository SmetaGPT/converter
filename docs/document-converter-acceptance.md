# Windows Document Converter Acceptance

Дата: 2026-05-22
Статус: v0.2.0 release scope

## 1. Назначение

Этот документ фиксирует стартовый набор эталонных DOCX/PDF и критерии приёмки для Windows Document Converter, а также post-v0.3.0 acceptance для native XLSX route.

Цель Sprint 0 — до начала реализации GUI и EXE определить, какой результат считается корректным машиночитаемым документом.

## 2. Источники образцов

| Каталог | Назначение | Найдено |
| --- | --- | --- |
| `D:\ФСНБ\Документы\Загрузка НПА\metod` | DOCX-образцы методических и нормативных документов | 52 DOCX |
| `D:\ФСНБ\Документы\Загрузка НПА\SP` | PDF-образцы СП | 343 PDF, 1 DOCX, 1 PY |
| `D:\ФСНБ\Документы\Загрузка НПА\sub_law` | PDF-сканы для OCR route | 2 selected scan samples |
| `D:\ФСНБ\Документы\Загрузка НПА\Law` | PDF-скан для OCR route | 1 selected scan sample |

Нецелевые файлы в PDF-каталоге не входят в Sprint 0. Временные файлы Word с префиксом `~$` должны исключаться.

## 3. Стартовый representative sample set

Выбранный набор хранится в `samples/manifest.sample.jsonl`. Для каждого файла зафиксированы `sample_id`, маршрут, исходный каталог, относительный путь, размер и SHA-256.

Проверка text layer через pypdf показала: все 343 PDF из `SP` имеют извлекаемый текстовый слой. Для покрытия OCR-маршрута в representative set добавлены три scan-кандидата из соседних каталогов корпуса. Сводка проверки хранится в `samples/pdf-text-layer-check.sample.json`.

| Sample | Route | Format | File | Size bytes |
| --- | --- | --- | --- | ---: |
| `sample_001` | `docx_native` | DOCX | `Приказ Минстроя России от 04.08.2020 N 421_пр (ред. от 23.01.docx` | 328966 |
| `sample_002` | `docx_native` | DOCX | `Приказ Минздравсоцразвития РФ от 06.04.2007 N 243 (ред. от 3.docx` | 291096 |
| `sample_003` | `docx_native` | DOCX | `Приказ Минтруда России от 07.05.2015 N 277н  Об утверждении.docx` | 229148 |
| `sample_004` | `docx_native` | DOCX | `Приказ Минстроя России от 12.05.2025 N 281_пр  О нормативных.docx` | 202848 |
| `sample_005` | `docx_native` | DOCX | `Приказ Минстроя России от 01.10.2021 N 707_пр (ред. от 08.06.docx` | 190529 |
| `sample_006` | `docx_native` | DOCX | `Приказ Минстроя России от 13.01.2020 N 2_пр (ред. от 19.08.2.docx` | 4457 |
| `sample_007` | `docx_native` | DOCX | `Приказ Минстроя России от 15.12.2025 N 789_пр  О внесении из.docx` | 8738 |
| `sample_008` | `docx_native` | DOCX | `Приказ Минстроя России от 08.02.2017 N 77_пр  Об утверждении.docx` | 18254 |
| `sample_009` | `pdf_text` | PDF | `SP_332.pdf` | 7431686 |
| `sample_010` | `pdf_text` | PDF | `SP_17.pdf` | 6149840 |
| `sample_011` | `pdf_text` | PDF | `SP_14.pdf` | 5726031 |
| `sample_012` | `pdf_text` | PDF | `SP_381.pdf` | 5481759 |
| `sample_013` | `pdf_text` | PDF | `SP_434.pdf` | 5099926 |
| `sample_014` | `pdf_text` | PDF | `SP_387.pdf` | 5085234 |
| `sample_015` | `pdf_text` | PDF | `SP_481.pdf` | 247525 |
| `sample_016` | `pdf_text` | PDF | `SP_480.pdf` | 287805 |
| `sample_017` | `pdf_text` | PDF | `SP_320.pdf` | 289954 |
| `sample_018` | `pdf_text` | PDF | `SP_433.pdf` | 302768 |
| `sample_019` | `pdf_scan` | PDF | `PPRF_680.pdf` | 164545 |
| `sample_020` | `pdf_scan` | PDF | `PPRF1315.pdf` | 957934 |
| `sample_021` | `pdf_scan` | PDF | `ПП РФ 999.pdf` | 971302 |

Примечание: классификация PDF samples является Sprint 0 baseline. В реализации route detector должен повторять эту проверку автоматически и не полагаться на заранее заданный route из manifest.

## 4. Общие критерии приёмки `document.v1.json`

Каждый успешно обработанный документ должен давать валидный `document.v1.json`.

Обязательные свойства:

- `schema_version` равен `document.v1`;
- `document_id` стабилен и строится от SHA-256 исходного файла;
- `source` содержит исходный путь, `relative_input_path`, имя, формат, размер и SHA-256;
- `processing.route` содержит один из маршрутов `docx_native`, `pdf_text`, `pdf_scan`, `xlsx_native`;
- `processing.status` содержит `success`, `partial_success`, `failed` или `skipped_duplicate`;
- `metadata` содержит `title`, `document_type`, `short_summary`, `confidence`, `method`;
- `units` содержит structural units с `unit_id`, `type`, `order`, `parent_id`, `source_ref`;
- `assets` содержит ссылки на выделенные изображения, страницы, формулы и графику, а также `sha256`, `size_bytes`, `filename`, `media_type`, где asset физически сохранён;
- `quality` содержит flags и warnings;
- все ссылки на assets являются относительными к папке документа.

Обязательные root-level run artifacts:

- `processed-documents-catalog.json` лежит в корне `run_dir`;
- `processed-documents-catalog.xlsx` лежит в корне `run_dir` и содержит operator-friendly tabular view поверх того же каталога;
- для каждого поддержанного или явно пропущенного input file catalog содержит `original_filename`, `relative_input_path`, `output_dir`, `output_folder_name`, `status`, `status_label`, `issue`;
- `output_dir`/`output_folder_name` позволяют быстро найти папку документа внутри `documents/`, а при ошибке или unsupported input честно допускают `null`;
- при `failed` в `issue` попадает текст ошибки extractor/runtime, а не только код статуса.
- XLSX report содержит локальные hyperlinks как минимум на папку документа и `document.v1.json`; если `search_text.txt` создан, hyperlink на него тоже присутствует.

Semantic metadata minimum:

- `title` — лучший доступный заголовок из первых structural text units или fallback на имя файла;
- `document_type` — rule-based тип документа по заголовку/имени файла с fallback по тексту;
- `short_summary` — краткое описание предмета документа без обращения к внешней LLM;
- `confidence` — `high`, `medium` или `low`;
- `method` — `rule_based_title_extraction` или `filename_fallback`.

## 5. Structural units acceptance

Для будущего chunking и поиска каждая содержательная единица должна иметь ссылку `document_id + unit_id`.

Минимальные правила:

- `unit_id` уникален внутри документа;
- `order` сохраняет порядок чтения;
- `parent_id` сохраняет иерархию документа;
- заголовки не сливаются с абзацами;
- `section`, `list_item`, `caption`, `header`, `footer` не теряются в plain `paragraph`, если их можно вывести из route semantics;
- таблицы не превращаются только в plain text;
- подписи к таблицам и рисункам сохраняются как отдельные units;
- изображения, графики и формулы получают собственные units;
- для PDF units по возможности имеют `page`, `bbox`, `coordinate_system`, `page_width`, `page_height`;
- для DOCX units по возможности имеют ссылку на OOXML-позицию или порядковый индекс исходного элемента;
- для XLSX `table_cell` units имеют optional `cell` payload с worksheet, address, row, column, value, formula, data_type, number_format и hyperlink.
- `quality` доступен на уровне документа и отдельных units в формате `flags` + `warnings`.

## 6. DOCX route acceptance

Маршрут `docx_native` считается успешным, если:

- извлечены заголовки, абзацы, списки и таблицы;
- порядок чтения соответствует документу;
- `section`, `list_item`, `caption` выделяются как отдельные unit types там, где это доступно по style/structure mapping;
- таблицы имеют units `table`, `table_row`, `table_cell`;
- embedded images сохранены в `assets/`;
- формулы выделяются как `formula` там, где они представлены OMML или устойчивым text pattern;
- если DOCX formula восстановлена из MathType WMF/text records или устойчивой линейной формы, `formula` unit может содержать machine-readable блок `formula.display_latex`, `formula.calc_expr`, `formula.variables`, `formula.confidence` и `formula.warnings`;
- embedded images сохраняются как `figure` или `formula_image` units/assets по доступной metadata;
- если включён formula-recognition provider config, `formula_image` units могут быть post-enriched после базового extraction: успешное распознавание заполняет `unit.text` и `unit.formula`, а рядом создаётся `formula-recognition.jsonl` с per-asset результатами;
- headers, footers и footnotes выделяются как отдельные semantic units;
- создан `search_text.txt`;
- создан `extractor_raw.json`;
- `document.v1.json` проходит schema validation.

Минимальная ручная проверка для Sprint 0:

- `sample_001` как крупный нормативный DOCX;
- `sample_003` как DOCX с потенциально сложной структурой;
- `sample_006` как малый DOCX.

## 6.1. XLSX route acceptance

Маршрут `xlsx_native` считается успешным, если:

- `.xlsx` файл классифицируется как поддержанный input, а `manifest.jsonl` содержит `route: xlsx_native`;
- workbook sheets сохраняются как `section` units, а используемые диапазоны листов как `table` units;
- непустые ячейки сохраняются как `table_cell` units с текстовой проекцией вида `A1: значение` или `B2: =FORMULA -> cached_value`;
- `cell` payload сохраняет worksheet, address, row, column, value, formula, data_type, number_format и hyperlink;
- Excel-формулы сохраняются как исходные Excel formula strings, а значения берутся из cached workbook values, если они есть;
- `extractor_raw.json` содержит per-sheet metadata: title, state, dimension, non_empty_cells, formula_cells, merged_ranges, freeze_panes и print_area;
- `search_text.txt` создаётся для быстрого поиска/проверки;
- `document.v1.json` проходит schema validation.

Ограничение: `openpyxl` не пересчитывает формулы. Если cached values отсутствуют, формулы всё равно сохраняются, но расчёт нужно выполнять downstream Excel-compatible движком или отдельным recalculation step.

## 7. PDF route acceptance

PDF route делится на два подмаршрута после проверки text layer.

Для `pdf_text` требуется:

- OCR не запускается;
- текст извлекается layout-first из существующего text layer с fallback на plain mode;
- units привязаны к страницам;
- где возможно, сохраняется `bbox`, `coordinate_system`, `page_width`, `page_height`;
- повторяющиеся верхние и нижние edge-блоки не попадают в body paragraphs и могут быть выделены как `header`/`footer`;
- повёрнутые PDF pages помечаются `rotated_text` и `review_required`;
- heuristic semantic extraction выделяет PDF tables как `table`/`table_row`/`table_cell`, formulas как `formula`, figure captions как `figure` units;
- создан `search_text.txt`.

Для `pdf_scan` требуется:

- оригинальный PDF не перезаписывается;
- создаётся OCR-производная в `ocr/searchable.pdf`;
- создаётся `ocr/sidecar.txt`;
- `processing.ocr_applied` равен `true`;
- OCR warnings и low confidence pages попадают в `quality.flags`;
- итоговые text units строятся из OCR-производной.
- OCR text также проходит heuristic semantic extraction для `table`, `formula` и `figure` units.

Минимальная ручная проверка для Sprint 0:

- `sample_009` как крупный PDF;
- `sample_010` как крупный PDF;
- `sample_015` как малый PDF;
- `sample_018` как малый PDF;
- `sample_019` как малый PDF-скан;
- `sample_020` как многостраничный PDF-скан;
- `sample_021` как русскоязычный PDF-скан из Law-каталога.

## 8. Таблицы, формулы и рисунки

Критерии приёмки для release scope v0.3.0:

- DOCX tables сохраняются как `table`/`table_row`/`table_cell`;
- DOCX formulas, headers, footers и footnotes сохраняются как отдельные semantic units там, где доступны в package XML;
- DOCX formulas, пригодные для восстановления, сохраняют display LaTeX для human-readable rendering и отдельное расчётное выражение там, где оно может быть построено без доменной подстановки значений;
- embedded DOCX media сохраняется как assets и `figure`/`formula_image` units;
- PDF text и OCR routes создают heuristic `table`, `formula` и `figure` units из layout text blocks;
- XLSX route сохраняет workbook tables/cells/formulas нативно, без OCR и без превращения таблиц только в plain text;
- если семантическое распознавание графики или формулы ненадёжно в конкретном документе, это помечается как review concern, а не как потеря исходного content;
- quality contract обязан помечать сомнительные случаи через `review_required`.

## 9. Quality flags первой версии

Минимальные flags:

| Flag | Когда выставляется |
| --- | --- |
| `empty_text` | Текстовая проекция пустая или почти пустая |
| `short_extraction` | Извлечённый текст подозрительно короткий для размера файла |
| `ocr_required` | PDF не имеет пригодного text layer |
| `ocr_applied` | OCR был выполнен |
| `ocr_failed` | OCR завершился ошибкой |
| `table_structure_warning` | Таблица извлечена неполно или сомнительно |
| `asset_extraction_warning` | Изображение или формула не были корректно сохранены |
| `rotated_text` | Страница PDF имеет rotation и требует ручной проверки результата text extraction |
| `review_required` | Документ или unit требует ручной проверки |
| `semantic_style_inferred` | Unit type для DOCX выведен из style или numbering mapping |
| `semantic_structure_inferred` | Unit type выведен эвристикой из OOXML/PDF/OCR structure или text pattern |
| `repeated_edge_block` | PDF header/footer выделен эвристикой повторяющегося edge-блока |
| `spreadsheet_table_inferred` | XLSX sheet/use-range представлен как table structure |
| `sheet_hidden` | XLSX sheet скрыт в исходной workbook |

Дополнительная warning для XLSX: `formula_cached_values_missing`, если формулы сохранены, но workbook не содержит cached result values.

Дополнительные warning для formula-recognition postprocess: `formula_recognition_applied`, `formula_recognition_provider_failed`, `formula_recognition_asset_missing`, `formula_recognition_postprocess_failed`.

## 10. Representative pilot validation

Команда проверки полного representative set:

```powershell
$env:PYTHONPATH = "src"
python scripts\run_sample_pilot.py --clean
```

Последний результат: 21 processed, 21 success, 0 partial_success, 0 failed. Route counts совпали с baseline manifest: `docx_native: 8`, `pdf_text: 10`, `pdf_scan: 3`. Route mismatches не обнаружены.

OCR runtime установлен и активен, поэтому representative pilot больше не содержит ожидаемых `partial_success` по `pdf_scan`.

## 11. Sprint 0 exit criteria

Sprint 0 можно закрыть, когда:

1. `samples/manifest.sample.jsonl` содержит representative DOCX/PDF для всех трёх маршрутов.
2. Для 3-5 документов заведены expected structural units в `samples/expected/`.
3. Acceptance criteria покрывают DOCX, PDF-text, PDF-scan и XLSX-native.
4. Quality flags первой версии зафиксированы.
5. Roadmap и state layer синхронизированы.
