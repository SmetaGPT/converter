# Downstream Handoff

Дата: 2026-05-22
Статус: initial contract

## 1. Назначение

Этот документ описывает, как другой проект должен забирать output package Windows Document Converter и загружать его в БД, chunking pipeline, полнотекстовый поиск, векторный индекс и семантический поиск.

Конвертер не является базой данных и не считает embeddings. Его задача — создать переносимый слой `document.v1.json` и связанные assets.

## 2. Что является source layer

Source layer для downstream-проекта:

- `run.json`;
- `manifest.jsonl`;
- `summary.json`;
- `documents/*/document.v1.json`;
- `documents/*/search_text.txt`;
- `documents/*/assets/`;
- `documents/*/ocr/`.

Исходные DOCX/PDF не нужны для индексации, если `document.v1.json` уже создан. Они нужны только для аудита или повторной обработки новой версией конвертера.

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

## 7. Проверка переносимости

Output package считается переносимым, если:

- его можно скопировать в другую папку;
- все asset paths остаются относительными;
- downstream loader не требует доступа к исходному `D:\ФСНБ`;
- `manifest.jsonl` и `document.v1.json` читаются как UTF-8 без BOM;
- `document_id + unit_id` достаточно для ссылок на фрагменты.
