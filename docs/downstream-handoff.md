# Downstream Handoff

Дата: 2026-05-26
Статус: validated reference contract + formula machine-readable contract

## 1. Назначение

Этот документ описывает, как другой проект должен забирать output package Windows Document Converter и загружать его в БД, chunking pipeline, полнотекстовый поиск, векторный индекс и семантический поиск.

Конвертер не является базой данных и не считает embeddings. Его задача — создать переносимый слой `document.v1.json` и связанные assets.

Stable JSON Schema contracts for downstream artifacts are cataloged in [contracts.md](contracts.md).

## 2. Что является source layer

Source layer для downstream-проекта:

- `run.json`;
- `manifest.jsonl`;
- `summary.json`;
- `review-required.jsonl`;
- `chunks.v1.jsonl`, если он был построен downstream builder-ом;
- `documents/*/document.v1.json`;
- `documents/*/search_text.txt`;
- `documents/*/assets/`;
- `documents/*/ocr/`.

Исходные DOCX/PDF/XLSX не нужны для индексации, если `document.v1.json` уже создан. Они нужны только для аудита или повторной обработки новой версией конвертера.

## 3. Стабильные ссылки

Главный внешний ключ для downstream-систем:

```text
document_id + unit_id
```

Правила:

- `document_id` строится от SHA-256 исходного файла;
- `unit_id` стабилен внутри документа;
- chunk должен хранить `unit_refs`, а не только plain text;
- ссылка на источник должна вести к `source_ref.page`, `source_ref.bbox` или `source_ref.docx_path`, если они доступны;
- assets должны ссылаться относительными путями внутри document package.

## 4. Минимальная схема загрузки в БД

Рекомендуемые таблицы:

| Таблица | Назначение |
| --- | --- |
| `documents` | Один ряд на `document.v1.json` |
| `document_units` | Structural units: paragraph, page, table, figure, formula |
| `document_assets` | Изображения, OCR artifacts, formula crops |
| `document_runs` | История запусков converter |
| `chunks` | Производные chunks для поиска |
| `chunk_units` | Связь chunk с исходными `unit_id` |

Минимальные поля `documents`:

- `document_id`;
- `schema_version`;
- `source_sha256`;
- `source_filename`;
- `source_format`;
- `document_title`;
- `document_type`;
- `short_summary`;
- `metadata_confidence`;
- `metadata_method`;
- `processing_route`;
- `processing_status`;
- `quality_flags`;
- `document_json`.

Минимальные поля `document_units`:

- `document_id`;
- `unit_id`;
- `parent_id`;
- `type`;
- `order_index`;
- `text`;
- `page`;
- `bbox`;
- `docx_path`;
- `asset_ref`;
- `unit_json`.

### 4.1 Formula Contract (обязательно для downstream)

Downstream должен трактовать formulas как три отдельных класса, а не как один общий текстовый блок.

- `calculable_formula`:
- `unit.type in {"formula", "formula_image"}`.
- `unit.formula.calc_expr` непустой.
- `unit.formula.variables` объект.
- `unit.formula.confidence` и `unit.formula.warnings` сохранены.
- downstream может запускать вычисление при наличии значений переменных.

- `display_only_formula`:
- формульный unit есть, но `calc_expr` отсутствует.
- `display_latex`/`linear_text` используются только для отображения и поиска.
- downstream не должен пытаться молча вычислять такие формулы.

- `unresolved_formula`:
- формульный unit есть, но recovery явно неполный (обычно `confidence=low` и/или предупреждения).
- unit должен попадать в review-контур, а не в автоматический расчёт.

Минимальные стабильные formula fields для загрузки в БД/индекс:

- `formula_source_format` <- `unit.formula.source_format`
- `formula_linear_text` <- `unit.formula.linear_text`
- `formula_display_latex` <- `unit.formula.display_latex`
- `formula_calc_expr` <- `unit.formula.calc_expr`
- `formula_variables_json` <- `unit.formula.variables`
- `formula_confidence` <- `unit.formula.confidence`
- `formula_warnings_json` <- `unit.formula.warnings`
- `formula_provenance_json` <- `unit.formula.provenance` (если присутствует)

Классификатор для downstream:

```text
if unit.formula.calc_expr != null -> calculable_formula
else if unit.type in {formula, formula_image} and unit.formula != null -> display_only_formula
else -> not_formula
```

Правило для расчётных сервисов:

- запускать вычисление только для `calculable_formula`;
- для `display_only_formula` и `unresolved_formula` возвращать status `not_calculable`/`needs_review` без попытки подстановки.

Reference mapping для текущего релиза:

- `documents.document_id` <- `document.v1.json.document_id`
- `documents.source_sha256` <- `document.v1.json.source.sha256`
- `documents.document_title` <- `document.v1.json.metadata.title`
- `documents.document_type` <- `document.v1.json.metadata.document_type`
- `documents.short_summary` <- `document.v1.json.metadata.short_summary`
- `documents.metadata_confidence` <- `document.v1.json.metadata.confidence`
- `documents.metadata_method` <- `document.v1.json.metadata.method`
- `documents.processing_route` <- `document.v1.json.processing.route`
- `documents.processing_status` <- `document.v1.json.processing.status`
- `document_units.page` <- `unit.source_ref.page`
- `document_units.bbox` <- `unit.source_ref.bbox`
- `document_units.asset_ref` <- `unit.asset_ref`
- `document_assets.path` <- `asset.path`

## 5. Chunking rules

Chunker должен работать от structural units, а не от сырой строки `search_text.txt`.

Базовые правила:

- chunk не разрывает таблицу посередине без сохранения `unit_refs`;
- заголовок включается в metadata chunk или section path;
- несколько коротких абзацев можно объединять в один chunk;
- длинный абзац можно делить, но ссылка на исходный `unit_id` сохраняется;
- таблицы chunkаются отдельно от обычного текста;
- figure/formula units могут попадать в multimodal chunk через `asset_ref`.

Пример chunk record:

```json
{
  "chunk_id": "c_000001",
  "document_id": "sha256:...",
  "unit_refs": ["u_000010", "u_000011"],
  "section_path": ["1", "1.1"],
  "pages": [3],
  "text": "...",
  "asset_refs": []
}
```

Reference builder для текущего релиза: `scripts/build_sample_chunks.py`.
Reference validator для output package: `scripts/validate_run_package.py`.

## 6. Векторный и семантический поиск

Рекомендуемая схема:

1. Загрузить `document.v1.json` в обычную БД.
2. Построить chunks из `document_units`.
3. Посчитать embeddings только для chunks.
4. Сохранить embedding рядом с `chunk_id`.
5. При поиске возвращать `chunk_id`, `document_id`, `unit_refs`, page refs и asset refs.

Не рекомендуется:

- считать embedding для всего документа одной строкой;
- терять `unit_refs` после chunking;
- хранить embeddings внутри `document.v1.json`;
- смешивать converter output и downstream index state.

### 6.1 Formula Search Notes

- Для semantic retrieval индексируйте `formula_linear_text` и `formula_display_latex` отдельно от обычного paragraph text.
- Для фильтрации по готовности расчёта используйте флаг `formula_calc_expr is not null`.
- Не интерпретируйте `display_latex` как исполняемое выражение.

## 7. Проверка переносимости

Output package считается переносимым, если:

- его можно скопировать в другую папку;
- все asset paths остаются относительными;
- downstream loader не требует доступа к исходному `D:\ФСНБ`;
- `manifest.jsonl` и `document.v1.json` читаются как UTF-8 без BOM;
- `document_id + unit_id` достаточно для ссылок на фрагменты.
