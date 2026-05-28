# Expected Outputs

Эта папка предназначена для ручных expected structural units по representative samples.

В Sprint 0 сюда нужно добавить 3-5 эталонных файлов, например:

- `sample_001.expected-units.json`;
- `sample_003.expected-units.json`;
- `sample_006.expected-units.json`;
- `sample_009.expected-units.json`;
- `sample_015.expected-units.json`;
- `sample_019.expected-units.json`.

Каждый expected file должен проверять не полный текст документа, а наличие ключевых structural units: заголовков, абзацев, таблиц, рисунков, формул, страниц и ссылок `document_id + unit_id`.

Executable validation для этих fixtures: `scripts/validate_sample_expectations.py <run_dir>`.

Для table-heavy anchors можно добавлять:

- `processing_expectations` для route status, OCR state и expected warnings;
- `table_expectations` для aggregate metrics по canonical units, например `table_units`, `table_rows`, `table_cells`, `rows_with_two_plus_cells`, `average_cells_per_row`, `wide_row_ratio`, `single_cell_row_ratio`, `warning_tables`.

Для узкого subset-run validator можно вызывать с несколькими `--sample-id`, чтобы не требовать полный representative pilot на всех samples.
