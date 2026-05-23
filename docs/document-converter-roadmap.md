# Roadmap: Windows Document Converter

Дата: 2026-05-22
Статус: проектная дорожная карта и факт исполнения

## 1. Цель проекта

Создать Windows-приложение, которое пользователь запускает как обычную программу, выбирает входную папку с DOCX и PDF, выбирает выходную папку и получает переносимый пакет машиночитаемых документов.

Выходной пакет должен быть пригоден для последующей загрузки в другой проект, базу данных, полнотекстовый поиск, векторный индекс и семантический поиск без повторного OCR и без повторного парсинга исходных файлов.

## 2. Scope первой версии

В первой версии обрабатываются:

- DOCX;
- PDF с текстовым слоем;
- PDF-сканы;
- изображения, формулы и графика внутри этих документов как сохраняемые structural assets.

Вне первой версии:

- XML/XSD;
- XLSX;
- ZIP-пакеты;
- старые DOC;
- прямая загрузка в БД;
- расчёт embeddings внутри конвертера.

## 3. Главный принцип выхода

Конвертер не должен выпускать только plain text. Главный результат обработки одного документа — стабильный файл `document.v1.json`.

Этот файл должен хранить:

- метаданные источника;
- маршрут обработки;
- структурные единицы документа;
- порядок чтения;
- страницы и координаты, где доступны;
- таблицы;
- формулы;
- рисунки, графики и схемы;
- ссылки на extracted assets;
- quality flags;
- ошибки и предупреждения.

Plain text, Markdown и chunks являются производными слоями. Они не заменяют `document.v1.json`.

## 4. Structural units contract

Каждая структурная единица документа должна иметь стабильную ссылку, чтобы на неё можно было ссылаться после загрузки в БД и при построении чанков.

Минимальная единица хранится так:

```json
{
  "unit_id": "u_000123",
  "parent_id": "u_000087",
  "type": "paragraph",
  "order": 123,
  "text": "...",
  "source_ref": {
    "document_id": "sha256:...",
    "page": 4,
    "bbox": [72.1, 144.2, 512.7, 188.4],
    "docx_path": null
  },
  "quality": {
    "flags": [],
    "warnings": []
  }
}
```

Типы structural units первой версии:

| Тип | Назначение |
| --- | --- |
| `document` | Корневая единица документа |
| `page` | Страница PDF или виртуальная страница DOCX, если доступна |
| `section` | Раздел или заголовочный блок |
| `paragraph` | Абзац |
| `list` | Список |
| `list_item` | Элемент списка |
| `table` | Таблица |
| `table_row` | Строка таблицы |
| `table_cell` | Ячейка таблицы |
| `formula` | Распознанная формула |
| `formula_image` | Формула, вставленная как изображение |
| `figure` | Рисунок, схема, график или диаграмма |
| `caption` | Подпись к таблице или рисунку |
| `footnote` | Сноска |
| `header` | Колонтитул или верхний служебный текст |
| `footer` | Нижний колонтитул или служебный текст |

Правила ссылочности:

- `unit_id` стабилен внутри `document_id`;
- `order` задаёт порядок чтения;
- `parent_id` сохраняет иерархию;
- `source_ref` связывает единицу с исходным документом;
- для PDF по возможности сохраняются `page` и `bbox`;
- для DOCX сохраняется путь или индекс элемента в OOXML-структуре;
- таблицы не разворачиваются только в текст, а сохраняют строки и ячейки;
- картинки и формулы не удаляются, а сохраняются как assets со ссылками из JSON.

## 5. Целевая структура выходной папки

```text
output/
  runs/
    2026-05-22_153000/
      run.json
      manifest.jsonl
      processing-log.jsonl
      summary.json
      errors.jsonl
      documents/
        sha256_abcd.../
          document.v1.json
          extractor_raw.json
          search_text.txt
          assets/
            page_0001.png
            figure_0007.png
            formula_0012.png
          ocr/
            searchable.pdf
            sidecar.txt
```

Назначение файлов:

| Файл | Назначение |
| --- | --- |
| `run.json` | Настройки запуска, версии конвертера и окружения |
| `manifest.jsonl` | Одна строка на исходный файл, включая hash, route и status |
| `processing-log.jsonl` | События обработки по документам и этапам |
| `summary.json` | Сводка по запуску |
| `errors.jsonl` | Машиночитаемый список ошибок |
| `document.v1.json` | Главный переносимый результат документа |
| `extractor_raw.json` | Сырой вывод extractor для аудита и отладки |
| `search_text.txt` | Производный текстовый слой для быстрых проверок |
| `assets/` | Изображения страниц, рисунки, графики, формулы |
| `ocr/` | OCR-производные для PDF-сканов |

## 6. Архитектура приложения

Компоненты:

- GUI layer: выбор входной и выходной папки, настройки, прогресс, отчёт;
- batch orchestrator: очередь файлов, маршрутизация, статусы, resume;
- inventory module: обход папки, hash, dedup, manifest;
- route detector: DOCX, PDF-text, PDF-scan;
- DOCX converter: нативный разбор DOCX;
- PDF text converter: извлечение текста, страниц, блоков и таблиц;
- OCR preprocessor: подготовка сканов и создание searchable PDF;
- asset extractor: выделение рисунков, формул, страниц и таблиц;
- canonical writer: сборка `document.v1.json`;
- quality gate: проверки полноты и качества;
- logger: человекочитаемый и JSONL-лог;
- packager: сборка Windows EXE или installer.

## 7. Спринты

Фактический статус исполнения на 2026-05-22:

| Sprint | Статус | Комментарий |
| --- | --- | --- |
| 0 | Выполнен | Product contract, representative samples и acceptance criteria зафиксированы |
| 1 | Выполнен | CLI skeleton, run directory и базовый запуск реализованы |
| 2 | Выполнен | Canonical schemas и stable IDs добавлены |
| 3 | Выполнен | Inventory, hashing, dedup и queue state реализованы |
| 4 | Выполнен | DOCX route реализован; headings/lists/captions, tables, formulas, headers, footers и footnotes выделяются в текущем semantic scope |
| 5 | Выполнен | PDF-text route реализован; layout-first extraction и heuristic table/formula/figure units добавлены |
| 6 | Выполнен | OCR route и runtime готовы; OCR text получает page boundaries и heuristic table/formula/figure units |
| 7 | Выполнен | Assets и figure/formula-image handling добавлены в текущем heuristic scope |
| 8 | Выполнен в MVP scope | Quality gates, summary и review flags реализованы в первой версии |
| 9 | Выполнен | GUI MVP реализован |
| 10 | Выполнен | Windows EXE build подтверждён |
| 11 | Частично выполнен | Downstream handoff и chunk-source schema добавлены; sample chunks и DB mapping notes ещё не завершены |
| 12 | Выполнен | Full pilot, OCR runtime, build validation и automated GUI launch smoke завершены |
| 13 | Выполнен | OCR page mapping, asset fingerprints и portable source metadata реализованы |
| 14 | Выполнен | DOCX body order и базовая semantic typing для section/list/caption реализованы |
| 15 | Выполнен | Layout-first PDF extraction, page provenance, repeated edge filtering и heuristic table/formula/figure extraction реализованы |
| 16 | Выполнен | Schema hardening, unit-level quality contract и release profile notes синхронизированы |

### Sprint 0. Product contract и эталонные документы

Цель: зафиксировать, что именно считается успешной обработкой документа.

Задачи:

- выбрать 10-20 representative DOCX/PDF из корпуса;
- разметить ожидаемые structural units вручную на 3-5 документах;
- зафиксировать маршруты `docx_native`, `pdf_text`, `pdf_scan`;
- зафиксировать критерии качества для текста, таблиц, рисунков и формул;
- определить минимальный набор настроек GUI.

Артефакты:

- `docs/document-converter-roadmap.md`;
- `docs/document-converter-acceptance.md`;
- `samples/manifest.sample.jsonl`;
- `samples/expected/`.

Definition of Done:

- есть список эталонных документов;
- есть acceptance criteria для каждого маршрута;
- известны обязательные поля `document.v1.json`;
- определены quality flags первой версии.

### Sprint 1. Project scaffold и CLI ядро

Цель: создать основу проекта без GUI, чтобы обработку можно было запускать из командной строки.

Задачи:

- создать Python package;
- добавить CLI-команду `convert-folder`;
- добавить конфигурацию запуска;
- добавить базовое логирование;
- добавить unit tests для конфигурации и путей;
- добавить smoke-test на пустой папке.

Артефакты:

- `src/`;
- `tests/`;
- `pyproject.toml`;
- CLI help;
- базовый `run.json`.

Definition of Done:

- CLI принимает input/output папки;
- создаёт run directory;
- пишет run metadata;
- корректно завершает пустой запуск;
- ошибки путей фиксируются в логах.

### Sprint 2. Canonical schema и structural references

Цель: создать стабильный контракт `document.v1.json`, который можно переносить в другие проекты.

Задачи:

- описать JSON Schema для `document.v1.json`;
- описать JSON Schema для `manifest.jsonl`;
- описать модель `structural_unit`;
- реализовать генератор стабильных `document_id` и `unit_id`;
- реализовать schema validation;
- добавить тесты на валидные и невалидные документы.

Артефакты:

- `schemas/document.v1.schema.json`;
- `schemas/manifest.v1.schema.json`;
- `schemas/chunk-source.v1.schema.json`;
- модуль canonical models.

Definition of Done:

- каждый документ имеет `document_id`;
- каждая structural unit имеет `unit_id`, `type`, `order`, `parent_id`, `source_ref`;
- JSON валидируется схемой;
- downstream-проект может ссылаться на `document_id + unit_id`.

### Sprint 3. Inventory, hashing, dedup и resume

Цель: сделать обработку воспроизводимой и безопасной для больших папок.

Задачи:

- рекурсивно обходить входную папку;
- исключать временные файлы;
- считать SHA-256;
- определять расширение и размер;
- группировать exact duplicates;
- записывать `manifest.jsonl`;
- сохранять состояние очереди;
- поддержать resume после сбоя.

Артефакты:

- inventory module;
- queue state;
- duplicate groups;
- resume tests.

Definition of Done:

- повторный запуск не обрабатывает неизменившийся документ заново;
- дубликаты не теряют provenance;
- manifest содержит все исходные пути;
- сбой на одном файле не останавливает весь batch.

### Sprint 4. DOCX route

Цель: переводить DOCX в `document.v1.json` с сохранением структуры.

Задачи:

- извлекать абзацы, заголовки, списки и таблицы;
- сохранять порядок чтения;
- сохранять сноски, колонтитулы и подписи, если доступны;
- извлекать embedded images;
- формировать structural units;
- формировать `search_text.txt`;
- сохранять `extractor_raw.json`.

Артефакты:

- DOCX converter;
- DOCX fixtures;
- DOCX quality checks.

Definition of Done:

- DOCX создаёт валидный `document.v1.json`;
- таблицы представлены как `table`, `table_row`, `table_cell`;
- embedded images сохраняются как assets;
- каждый текстовый блок имеет `unit_id` и `order`;
- тестовый DOCX проходит acceptance checks.

### Sprint 5. PDF text route

Цель: переводить PDF с текстовым слоем без OCR.

Задачи:

- определять наличие текстового слоя;
- извлекать страницы, блоки и порядок чтения;
- сохранять `page` и `bbox`, где доступны;
- извлекать таблицы;
- выделять изображения и подписи;
- формировать structural units;
- не запускать OCR для качественного PDF-text.

Артефакты:

- PDF text converter;
- PDF route detector;
- page/block fixtures.

Definition of Done:

- PDF-text создаёт валидный `document.v1.json`;
- каждый блок привязан к странице;
- OCR не запускается без необходимости;
- пустой или сломанный text layer переводит документ в fallback queue.

### Sprint 6. PDF scan route и OCR

Цель: обрабатывать сканированные PDF через OCR-производную без потери оригинала.

Задачи:

- определять PDF-сканы;
- запускать OCR с языками `rus` и `eng`;
- создавать searchable PDF;
- создавать sidecar text;
- сохранять OCR metadata;
- передавать searchable PDF в PDF converter;
- выставлять OCR quality flags.

Артефакты:

- OCR preprocessor;
- OCR output directory;
- OCR quality report;
- scan fixtures.

Definition of Done:

- оригинальный PDF не перезаписывается;
- OCR-производная сохраняется отдельно;
- `document.v1.json` содержит `ocr_applied: true`;
- страницы с низким качеством помечаются для review;
- OCR failures фиксируются в `errors.jsonl`.

### Sprint 7. Формулы, графика и image assets

Цель: не терять формулы и графику, вставленные как изображения.

Задачи:

- сохранять все значимые изображения как assets;
- классифицировать изображения как `figure`, `formula_image`, `decorative`, `unknown`;
- извлекать подписи рядом с рисунками;
- сохранять OCR текста внутри изображений, если доступен;
- для формул сохранять crop и поле для LaTeX-распознавания;
- добавлять `review_required` при низкой уверенности.

Артефакты:

- asset extraction module;
- image classification metadata;
- formula placeholder contract;
- review flags.

Definition of Done:

- формула-картинка не исчезает из результата;
- каждый image asset имеет ссылку из `document.v1.json`;
- график или схема доступны как отдельная structural unit;
- downstream chunker может сослаться на рисунок через `document_id + unit_id`.

### Sprint 8. Quality gates и отчёты

Цель: автоматически отличать успешные документы от частично обработанных и проблемных.

Задачи:

- проверять пустой текст;
- проверять подозрительно короткий extraction;
- проверять отсутствие страниц у PDF;
- проверять ошибки таблиц;
- проверять OCR warnings;
- генерировать summary report;
- генерировать список документов для ручной проверки.

Артефакты:

- quality module;
- `summary.json`;
- `review-required.jsonl`;
- отчёт в GUI.

Definition of Done:

- каждый документ получает `status`;
- `partial_success` отличается от `failed`;
- batch summary показывает причины проблем;
- ошибки не скрываются в обычном текстовом логе.

### Sprint 9. GUI для Windows

Цель: дать пользователю простое приложение для выбора папок и запуска batch processing.

Задачи:

- выбрать GUI framework;
- реализовать выбор input/output папок;
- добавить настройки OCR language, parallelism, duplicate policy;
- показать очередь документов;
- показать progress bar;
- показать live log;
- добавить cancel/pause;
- открыть output folder после завершения.

Артефакты:

- Windows GUI;
- integration with CLI core;
- operator-facing errors.

Definition of Done:

- пользователь может обработать папку без командной строки;
- GUI не зависает во время обработки;
- ошибки видны в интерфейсе;
- после завершения можно открыть папку результата.

### Sprint 10. Windows packaging

Цель: собрать приложение в распространяемый Windows package.

Задачи:

- выбрать packaging strategy: PyInstaller, Nuitka или installer;
- включить runtime dependencies;
- проверить OCR dependencies;
- добавить версию приложения;
- добавить smoke-test собранного EXE;
- подготовить инструкцию установки.

Артефакты:

- Windows build artifact;
- installer или portable package;
- build script;
- release notes.

Definition of Done:

- приложение запускается на Windows без IDE;
- пользователь может выбрать папки и выполнить batch;
- output package создаётся корректно;
- версия приложения записывается в `run.json`.

### Sprint 11. Downstream handoff для БД, chunks и search

Статус: частично выполнен.

Факт на 2026-05-22:

- уже выполнено: `docs/downstream-handoff.md`, `schemas/chunk-source.v1.schema.json`, правила переносимости output package и contract `document_id + unit_id`;
- остаётся: sample `chunks.v1.jsonl`, завершённые DB mapping notes и reference loader flow на уровне артефактов.

Цель: сделать выход конвертера удобным для другого проекта, который будет грузить данные в БД и строить поиск.

Задачи:

- описать contract для downstream loader;
- определить правила chunking по structural units;
- добавить пример `chunks.v1.jsonl`;
- добавить reference loader pseudo-flow;
- описать mapping в PostgreSQL и vector store;
- проверить перенос output package в отдельную папку без потери ссылок.

Артефакты:

- `docs/downstream-handoff.md`;
- `schemas/chunks.v1.schema.json`;
- sample chunks;
- DB mapping notes.

Definition of Done:

- downstream-проекту не нужен исходный DOCX/PDF для индексации;
- chunks ссылаются на `document_id + unit_id`;
- asset references остаются относительными и переносимыми;
- один output package можно скопировать в другой проект.

### Sprint 12. Pilot на корпусе ФСНБ и release hardening

Статус: выполнен.

Факт на 2026-05-22:

- выполнено: full 21-sample pilot, OCR runtime activation, build hardening, workspace setup, запуск Context7 MCP, automated GUI startup smoke в тестах и EXE launch smoke для собранного package;
- release closure v0.2.0 дополнительно закрыла runtime schema validation, resume/reuse, duplicate skip, reference chunks, Windows CI и portable release packaging;
- остаточный backlog перенесён в post-release improvements: advanced PDF extraction для tables/figures/formulas, DOCX footnotes/header/footer semantic pass и optional OCR helpers polish.

Цель: проверить приложение на реальном наборе DOCX и PDF.

Задачи:

- прогнать pilot batch на части корпуса;
- измерить скорость и объём output;
- зафиксировать ошибки по типам;
- улучшить маршрутизацию PDF-text/PDF-scan;
- проверить качество DOCX structural units;
- проверить переносимость output package;
- подготовить release checklist.

Артефакты:

- pilot report;
- performance notes;
- error taxonomy;
- release candidate.

Definition of Done:

- pilot corpus обработан;
- известна доля `success`, `partial_success`, `failed`;
- найденные дефекты заведены как backlog;
- release candidate можно дать пользователю для локальной работы.

### Sprint 13. OCR hardening и portable source/assets metadata

Статус: выполнен.

Факт на 2026-05-22:

- `pdf_scan` сохраняет OCR page boundaries через form-feed и больше не теряет paragraph units;
- OCR assets и extracted files получают `sha256`, `size_bytes`, `filename`, `media_type`;
- `source.relative_input_path` добавлен в `document.v1.json` и покрыт tests.

Цель: закрыть локальные defects OCR route и усилить переносимость выходного пакета.

Задачи:

- исправить page mapping в `pdf_scan`, чтобы paragraph units строились по реальным страницам OCR output;
- сохранять page-level OCR text и не терять paragraph children у page units;
- досчитывать `sha256`, `size_bytes` и MIME/file metadata для extracted assets и OCR artifacts;
- добавить `relative_input_path` или `source_locator` рядом с `original_path`, чтобы package оставался переносимым без machine-local path;
- проверить, что OCR asset metadata достаточно для downstream dedup и аудита.

Артефакты:

- обновлённый `pdf_scan` route;
- расширенный asset metadata contract;
- portability notes for source metadata;
- tests for OCR page/unit mapping.

Definition of Done:

- `pdf_scan` не теряет paragraph units после OCR;
- assets получают fingerprints и базовую file metadata;
- output package можно перенести без критической зависимости от absolute Windows path;
- regression tests покрывают OCR page mapping.

### Sprint 14. DOCX reading order и semantic body blocks

Статус: выполнен.

Факт на 2026-05-22:

- DOCX converter переведён на реальный body traversal `paragraph/table`;
- headings, list items и captions маппятся в явные structural unit types;
- formulas, headers, footers и footnotes маппятся в явные semantic units;
- unit-level quality flags появились и покрыты mixed-structure DOCX tests.

Цель: привести DOCX output к реальному порядку чтения и базовой семантике headings, lists и captions.

Задачи:

- обходить DOCX body blocks в реальном порядке `paragraph/table`;
- отличать headings от обычных paragraphs по style mapping;
- выделять списки и `list_item`;
- сохранять captions рядом с `figure` и `table`, где это доступно;
- по возможности сохранять `footnote`, `header`, `footer` semantics вместо flattening в plain paragraph;
- добавлять unit-level review flags для сомнительных DOCX blocks.

Артефакты:

- обновлённый DOCX converter;
- DOCX semantic mapping rules;
- fixtures на mixed paragraph/table order;
- unit-level DOCX quality checks.

Definition of Done:

- DOCX body blocks сохраняют фактический порядок чтения;
- heading/list/caption units представлены явно в `document.v1.json`;
- DOCX quality flags могут назначаться на уровне units, а не только документа;
- acceptance checks покрывают mixed-structure DOCX.

### Sprint 15. Layout-aware PDF text и provenance

Статус: выполнен.

Факт на 2026-05-22:

- `pypdf.extract_text(extraction_mode="layout")` внедрён как layout-first path с fallback на plain mode;
- page units получают `bbox`, `coordinate_system`, `page_width`, `page_height`;
- repeated edge blocks переводятся в `header`/`footer` units и не засоряют `search_text.txt`;
- text-layer и OCR PDF blocks получают heuristic `table`, `formula` и `figure` units там, где это видно из layout/OCR text.

Цель: улучшить порядок чтения PDF-text и сделать provenance пригодным для downstream layout-aware processing.

Задачи:

- проверить и внедрить `pypdf.extract_text(extraction_mode="layout")` там, где это улучшает output;
- добавить visitor-based provenance hooks для координат и page-level layout metadata, где они доступны;
- хранить coordinate system и page size вместе с `bbox`;
- обнаруживать повторяющиеся `header`, `footer` и page numbers, чтобы не смешивать их с body text;
- улучшить reading order для multi-column PDF;
- начать отдельное представление tables, figures и captions в PDF-text route.

Артефакты:

- layout-aware PDF text converter;
- expanded provenance model;
- fixtures для multi-column PDF;
- updated PDF extraction notes.

Definition of Done:

- PDF-text reading order ближе к реальному visual layout;
- provenance содержит `page + bbox + coordinate system`, где это доступно;
- repeated headers/footers/page numbers больше не засоряют body paragraphs;
- ограничения layout extraction зафиксированы явно в docs.

### Sprint 16. Schema hardening и richer quality semantics

Статус: выполнен.

Факт на 2026-05-22:

- core schema ужесточена: top-level/source/source_ref/asset/quality contract больше не опирается на blanket `additionalProperties`;
- unit quality нормализован в `flags + warnings` на document и unit level;
- acceptance, build и OCR runtime docs синхронизированы с текущими emitters и optional OCR helper profile.

Цель: ужесточить `document.v1` как межпроектный контракт и выровнять schema, acceptance и emitters.

Задачи:

- сократить blanket `additionalProperties` в core schema и вынести расширяемые поля в явные секции `extensions` или `debug`;
- выровнять schema, acceptance и emitters для `figure`, `caption`, `formula`, `header`, `footer`;
- расширить unit-level quality payloads и добавить richer provenance/debug metadata;
- считать asset hashes последовательно для всех export artifacts;
- проверить, нужен ли release profile с optional OCR helpers `jbig2`, `pngquant`, `verapdf`.

Артефакты:

- tightened `document.v1` schema;
- updated acceptance criteria;
- richer quality contract;
- release profile notes for optional OCR helpers.

Definition of Done:

- schema contract строже и соответствует фактическим emitters;
- quality signals доступны на document и unit level;
- asset hashes стабильны и заполнены там, где они обязательны;
- release profile для optional OCR helpers описан явно.

## 8. Chunking readiness

Конвертер не обязан строить embeddings, но обязан сохранить структуру так, чтобы future chunker мог работать без повторного парсинга.

Правила для будущего chunker:

- chunk строится из одной или нескольких structural units;
- chunk хранит список `unit_refs`;
- chunk не должен терять страницу, раздел и источник;
- таблицы chunkаются отдельно от обычного текста;
- рисунки и формулы могут попадать в multimodal chunk через ссылку на asset;
- один и тот же `unit_id` может участвовать в нескольких chunk strategies.

Пример будущего chunk:

```json
{
  "chunk_id": "c_000045",
  "document_id": "sha256:...",
  "unit_refs": ["u_000120", "u_000121", "u_000122"],
  "section_path": ["1", "1.2"],
  "pages": [3, 4],
  "text": "...",
  "asset_refs": ["assets/figure_0007.png"]
}
```

## 9. MVP release boundary

MVP считается готовым, когда пользователь может:

1. запустить Windows-приложение;
2. выбрать папку с DOCX/PDF;
3. выбрать выходную папку;
4. обработать документы;
5. получить `document.v1.json` по каждому успешному документу;
6. увидеть ошибки и partial successes;
7. перенести output folder в другой проект;
8. построить chunks по structural units без повторного чтения исходных DOCX/PDF.

## 10. Главные риски

| Риск | Контроль |
| --- | --- |
| OCR/PDF dependencies сложно упаковать в один EXE | Делать installer или self-contained package, не обещать single-file EXE в первой версии |
| PDF с плохим text layer будет ошибочно принят за PDF-text | Добавить quality gate по длине, страницам и покрытию текста |
| Таблицы потеряют структуру | Хранить `table`, `table_row`, `table_cell` отдельно от `search_text` |
| Формулы и графика пропадут | Сохранять image assets и ссылаться на них из structural units |
| Downstream-проект не сможет ссылаться на фрагменты | Делать стабильные `document_id + unit_id` обязательными |
| Повторный запуск создаст несовместимый output | Версионировать schema и converter version в `run.json` |

## 11. Рекомендуемый порядок реализации

Практический порядок:

1. Sprint 0-2: контракт, схемы, CLI skeleton.
2. Sprint 3-6: рабочая batch-обработка DOCX/PDF/PDF-scan.
3. Sprint 7-8: assets и quality gates.
4. Sprint 9-10: GUI и Windows packaging.
5. Sprint 11-12: downstream handoff и pilot release.
6. Sprint 13-16: hardening OCR/DOCX/PDF, provenance и schema contract.

Такой порядок снижает риск: сначала фиксируется переносимый формат и structural references, затем строится обработка, после этого появляется GUI и EXE, и только затем ужесточается accuracy/provenance contract для production-like downstream use.
