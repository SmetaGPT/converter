# Production Audit Report

Дата: 2026-05-23
Репозиторий: converter
Ветка: main
Формат: read-only production audit

## 1. Общая оценка

- Тип проекта: MVP
- Стек: Python 3.11+/3.12, setuptools, python-docx, pypdf, ocrmypdf, jsonschema, Tkinter GUI, PyInstaller, GitHub Actions Windows CI
- Основные entry points: CLI в `src/doc_converter/cli.py`, GUI в `src/doc_converter/gui.py`, Windows build в `scripts/build-windows.ps1`, portable packaging в `scripts/package-release.ps1`
- Архитектура кратко: локальный single-process batch-конвертер для DOCX/PDF, который строит run package с schema-validated JSON артефактами, отдельным OCR preflight и downstream handoff без встроенной БД и без LLM runtime; это подтверждается `pyproject.toml`, `src/doc_converter/runner.py` и `docs/downstream-handoff.md`
- PRS, Production Readiness Score: 70/100
- Уверенность оценки: Medium

### Вердикт

- Not ready
- Есть два подтверждённых runtime-blocker: self-ingestion при вложенном output path и silent skip unsupported inputs.
- Базовый runtime и build-контур сильные: 41 тест passed, synthetic e2e passed, OCR preflight ready, Windows build и packaging passed.
- CI не закрывает lint, typecheck, dependency hygiene и финальный portable artefact.
- Setup воспроизводим не до конца: lock/constraints не найдены, локальный pip check падает.

## 2. Audit Coverage

### Просмотрено

- Ключевые директории: `src/doc_converter`, `src/doc_converter/converters`, `scripts`, `tests`, `docs`, `.github/workflows`
- Ключевые config files: `pyproject.toml`, `pyrightconfig.json`, `.gitignore`, `docs/build-and-run.md`, `docs/document-converter-acceptance.md`, `docs/downstream-handoff.md`, `docs/ocr-runtime-windows.md`, `scripts/install-ocr-runtime.ps1`
- CI/CD: `.github/workflows/windows-ci.yml`
- Tests: `tests/`
- Deploy/runtime: `scripts/build-windows.ps1`, `scripts/package-release.ps1`, `DocumentConverter.spec`

### Запущенные команды

```text
git status --short -> passed (clean output)
python -m pip check -> failed
python -m unittest discover -v -> passed (41 passed через test runner)
ruff check src tests scripts -> failed (14 findings)
python scripts/validate_harness_assets.py -> passed
python -m doc_converter.cli check-ocr -> passed
python scripts/run_synthetic_e2e.py --clean -> passed
powershell -ExecutionPolicy Bypass -File scripts/build-windows.ps1 -Name DocumentConverter -> passed
powershell -ExecutionPolicy Bypass -File scripts/package-release.ps1 -Name DocumentConverter -Version 0.2.0 -SkipBuild -> passed
temporary smoke: nested output under input -> failed
temporary smoke: mixed supported+unsupported input -> failed
git status --short --ignored -- build dist runs DocumentConverter.spec -> passed
git status --short --ignored -- src/windows_document_converter.egg-info -> passed
```

### Не удалось проверить

- Dependency vulnerability audit.
Причина: `pip-audit` локально не установлен и не запускается в CI.
Остающийся риск: неизвестные CVE в транзитивных зависимостях.

- Полноценный CLI typecheck через pyright.
Причина: `pyrightconfig.json` есть, но `pyright` локально отсутствует и workflow его не исполняет.
Остающийся риск: typed regressions проходят мимо CI; editor diagnostics уже показывают проблему в `tests/test_gui_import.py`.

- Clean-room setup с нуля.
Причина: аудит использовал существующую `.venv`, а lock/constraints files в репозитории не найдены.
Остающийся риск: новый Windows environment может собрать другой dependency graph.

- Coverage percentage.
Причина: coverage gate/config в репозитории не найден, а coverage run не дал полезного summary.
Остающийся риск: покрытие по веткам и edge-cases неизвестно.

- Docker build и migration check.
Причина: Not found in repository: Dockerfile, docker-compose, alembic, DB migrations, DB runtime.
Остающийся риск: для текущего scoped desktop-конвертера не применимо.

## 3. Критические Blockers

### BLOCKER: Overlapping input/output paths allow self-ingestion

- Evidence:
  - file/path: `src/doc_converter/runner.py`, `src/doc_converter/gui.py`
  - observed: preflight проверяет только существование и тип путей; output path создаётся до inventory; GUI передаёт выбранные пути без overlap-check. Во временном smoke input с вложенным output дал `discovered_files=2` и `manifest_relative_paths = out/old.docx; source.docx`.
- Почему критично: оператор может выбрать output внутри input и получить рекурсивное повторное включение прошлых результатов, copied originals и OCR-derived PDF в новый run.
- Что сломается: детерминизм обработки, resume/dedup semantics, размер output, доверие к run summary.
- Confidence: High
- Minimal fix: запретить любой overlap между input и output в runner и GUI, включая equal, output-inside-input и input-inside-output; добавить regression tests.
- Validation: unit tests на CLI/GUI/runner и повторный временный smoke, который должен завершаться ошибкой до старта run.

### BLOCKER: Unsupported files are silently dropped from run accounting

- Evidence:
  - file/path: `src/doc_converter/inventory.py`, `src/doc_converter/runner.py`, `docs/current-status.md`
  - observed: inventory вообще не включает unsupported suffixes, а summary жёстко пишет `discovered_files = len(inventory_records)`, `supported_files = len(inventory_records)`, `unsupported_files = 0`. Во временном mixed-folder smoke с `source.docx` и `ignored.txt` summary вернул `discovered_files=1`, `supported_files=1`, `unsupported_files=0`.
- Почему критично: на реальном mixed corpus проект сам документирует PDF, DOCX, XML/XSD, XLSX и ZIP; при таком вводе оператор не увидит, что часть входа проигнорирована.
- Что сломается: полнота ingest-а, auditability, downstream completeness checks.
- Confidence: High
- Minimal fix: разделить scanned files и supported files, считать unsupported_files честно и логировать unsupported inputs с причиной skip.
- Validation: mixed-folder test должен давать `discovered_files=2`, `supported_files=1`, `unsupported_files=1` и явный log record по unsupported input.

## 4. Security Risks

Явных committed secrets не обнаружено. Not found in repository: `.env` files, secret-like filenames, certificate/key files. Поиск по secret-like filenames и `.env` surface ничего не вернул; grep по secret-словам нашёл только документацию.

- Risk: Unsafe file/path handling around overlapping input/output paths.
- Evidence: `src/doc_converter/runner.py`, `src/doc_converter/gui.py`, подтверждённый nested-output smoke.
- Impact: непреднамеренная повторная обработка собственных outputs, рост диска, искажение результатов run.
- Fix: жёсткий preflight overlap guard и regression tests.
- Validation: nested-output scenario должен падать с понятной ошибкой до inventory.

- Risk: Dependency hygiene and vulnerability visibility gap.
- Evidence: `pyproject.toml`, `.github/workflows/windows-ci.yml`, отсутствие lock/constraints files, локальный `python -m pip check failed`, `pip-audit not available`.
- Impact: свежие окружения могут собирать нестабильный dependency graph; CVE surface не проверяется автоматически.
- Fix: добавить reproducible constraints или lock, затем включить `pip check` и dependency audit в CI.
- Validation: clean venv install + `python -m pip check` passes; CI содержит dependency sanity step.

- Risk: OCR install helper downloads traineddata without explicit integrity verification.
- Evidence: `scripts/install-ocr-runtime.ps1`
- Impact: риск supply-chain tampering при operator setup.
- Fix: зафиксировать ожидаемые SHA-256 для `eng/rus/osd traineddata` и валидировать download before use.
- Validation: checksum mismatch должен приводить к fail-fast.

- AI/RAG prompt injection and data leakage:
Not applicable for current runtime. Конвертер не вызывает LLM и не считает embeddings; downstream/vector concerns вынесены отдельно в `docs/downstream-handoff.md`.

## 5. Чистка репозитория

### 5.1 Удалить

- `DocumentConverter.spec` -> generated PyInstaller spec, build прямо пишет его в root, а `.gitignore` игнорирует pattern `.spec` -> риск удаления низкий -> validation: rerun `scripts/build-windows.ps1`, spec regenerated
- `build/` -> generated PyInstaller intermediates, игнорируется в `.gitignore` -> риск удаления низкий -> validation: rerun build, folder recreated
- `src/windows_document_converter.egg-info/` -> generated packaging metadata, игнорируется в `.gitignore` -> риск удаления низкий -> validation: editable install recreates it if needed

### 5.2 Проверить вручную

- `dist/` -> generated artefact, но сейчас содержит рабочий EXE и portable zip; подтвердить у владельца, нужно ли хранить локально как release evidence
- `runs/` -> generated outputs, но могут быть нужны как acceptance evidence и regression baseline; подтверждение должен дать владелец продукта или тестового контура

### 5.3 Не трогать

- `samples/` -> это acceptance corpus и expected fixtures, а не мусор
- `docs/` -> state layer и runbooks выглядят объёмно, но это рабочий operational evidence, а не лишние файлы

## 6. Архитектурные проблемы

### Проблема: invalid path-state не моделируется как ошибка

- проблема: система принимает конфигурацию, которая приводит к self-ingestion
- evidence: `src/doc_converter/runner.py`, `src/doc_converter/gui.py`
- влияние: система принимает конфигурацию, которая приводит к self-ingestion
- root cause: preflight ограничен existence/type checks
- minimal fix: запретить overlapping paths в одном месте runner и дублировать UX-validation в GUI
- long-term fix: единый path-validation helper с тестами для CLI и GUI
- validation: новый negative test на equal path и nested path

### Проблема: run accounting conflates discovered and supported inputs

- проблема: summary вводит в заблуждение на mixed folders
- evidence: `src/doc_converter/inventory.py`, `src/doc_converter/runner.py`
- влияние: summary вводит в заблуждение на mixed folders
- root cause: inventory сразу фильтрует unsupported inputs, а summary считает только filtered list
- minimal fix: считать full scan отдельно от supported set и логировать unsupported files
- long-term fix: ввести явный inventory result object с totals, supported list и skipped list
- validation: mixed-input regression test

### Проблема: CI валидирует source build, но не финальный release artefact

- проблема: workflow останавливается на build-windows
- evidence: `.github/workflows/windows-ci.yml`, `scripts/package-release.ps1`, `docs/release-status.md`
- влияние: сломанный packaging path или binary-only regression могут пройти незамеченными до ручного релиза
- root cause: workflow останавливается на unittest, synthetic e2e и build-windows
- minimal fix: запускать `package-release` в CI и проверять zip/checksum/release-notes; добавить EXE startup smoke
- long-term fix: отдельный release workflow с uploaded artefacts и smoke stage
- validation: workflow green только после packaging + smoke

### Проблема: public contract drift around workers

- проблема: код, schema и docs расходятся по реальному supported surface
- evidence: `src/doc_converter/config.py`, `src/doc_converter/cli.py`, `schemas/run.v1.schema.json`, `docs/current-sprint.md`
- влияние: код, schema и docs расходятся по реальному supported surface
- root cause: feature partially removed from public API, но не дочищен из internal contract
- minimal fix: либо убрать `workers` из config/schema/run metadata, либо реализовать end-to-end
- long-term fix: contract tests между CLI help, config model и schema
- validation: schema and CLI tests agree on final public API

## 7. Технические проблемы по слоям

### Backend

- Нет guard against overlapping input/output paths: `src/doc_converter/runner.py`
- Unsupported files silent-skip-ятся и не видны в summary: `src/doc_converter/inventory.py`, `src/doc_converter/runner.py`
- Internal contract drift around workers: `src/doc_converter/config.py`, `schemas/run.v1.schema.json`

### DevOps / CI/CD

- Workflow есть, но он не запускает `ruff`, `pyright`, `pip check`, `package-release` и EXE smoke: `.github/workflows/windows-ci.yml`
- Release packaging существует только как manual script path: `scripts/package-release.ps1`

### Security

- Unsafe path handling даёт self-ingestion risk: `src/doc_converter/runner.py`
- Dependency vulnerability visibility отсутствует: нет audit step и lock surface
- OCR helper downloads external traineddata without checksum verification: `scripts/install-ocr-runtime.ps1`

### Observability

- Плюс: per-run JSONL и summary surface есть в `src/doc_converter/runner.py`
- Минус: unsupported inputs вообще не попадают в эти артефакты
- Минус: packaged EXE smoke не автоматизирован в CI

### Testing

- Плюс: 41 unit tests passed
- Минус: нет regression tests на nested output path и truthful unsupported counts
- Минус: coverage gate не найден

### Documentation

- Плюс: build/run/OCR docs хорошие: `docs/build-and-run.md`, `docs/ocr-runtime-windows.md`
- Минус: Not found in repository: root README или clean-room quickstart
- Минус: release docs заявляют EXE smoke, но это не подтверждено workflow automation: `docs/release-status.md`

### Local developer experience

- `pyrightconfig.json` есть, но `pyright` tool отсутствует локально
- Локальный `python -m pip check` падает
- Ruff доступен и сразу ловит 14 проблем, значит static debt уже накоплен

### AI / RAG / LLM

- Не применимо к runtime этого репозитория; downstream embeddings and vector search задокументированы отдельно в `docs/downstream-handoff.md`

## 8. Production Readiness Checklist

- [~] reproducible setup
- [x] documented run command
- [x] tests
- [x] build
- [ ] lint/typecheck
- [~] env config
- [x] secrets handling
- [~] healthcheck
- [~] logging
- [~] error handling
- [n/a] migrations
- [~] CI
- [~] deployment artefacts
- [ ] rollback/backup notes
- [n/a] monitoring/metrics
- [n/a] AI eval/safety checks

Краткая расшифровка:

- reproducible setup частично: `pyproject.toml` есть, но lock/constraints нет и `pip check failed`
- env config частично: runtime options есть через CLI/GUI, OCR runtime documented, но setup зависит от внешних tools и mutable local environment
- healthcheck частично: `check-ocr` и synthetic e2e есть, но packaged EXE smoke не в CI
- logging частично: run-level JSONL есть, но unsupported omissions не видны
- error handling частично: per-document failures логируются, но invalid overlap config и unsupported completeness сейчас не покрыты
- CI частично: workflow работает, но без static/dependency/release-package gates
- deployment artefacts частично: build и `package-release` проходят, но packaging не автоматизирован в CI
- rollback/backup notes отсутствуют для portable release distribution

## 9. Roadmap

### P0 — Blockers до деплоя

- P0-01. Reject overlapping input/output paths.
  - risk reduced: self-ingestion, corrupted run accounting, uncontrolled disk growth
  - affected area: runner, GUI, CLI error surface, tests
  - dependencies: none
  - validation: nested-path negative tests and temp smoke must fail before inventory

- P0-02. Make unsupported-input reporting truthful.
  - risk reduced: silent data loss on mixed folders
  - affected area: inventory, runner summary, processing log, tests, docs
  - dependencies: none
  - validation: mixed-folder test must report discovered 2 / supported 1 / unsupported 1

### P1 — Critical production hardening

- P1-01. Make `ruff` green and add lint gate to CI.
  - risk reduced: silent static regressions in scripts and core modules
  - affected area: scripts, one converter import, workflow
  - dependencies: none
  - validation: `ruff check src tests scripts` passes locally and in CI

- P1-02. Add `pyright` gate and fix current typing issue.
  - risk reduced: typed regressions and misleading green local state
  - affected area: pyright config, workflow, tests
  - dependencies: none
  - validation: `pyright` passes locally and in CI

- P1-03. Make Windows source install reproducible and dependency-clean.
  - risk reduced: environment drift and setup-only failures
  - affected area: dependency metadata, CI, setup docs
  - dependencies: none
  - validation: clean venv install followed by `python -m pip check` passes

- P1-04. Validate final portable artefact in CI.
  - risk reduced: release package or binary-only regressions escaping to operators
  - affected area: workflow, build/package scripts, optional smoke helper
  - dependencies: P1-03 preferred, but not strictly required
  - validation: CI produces zip/checksum/release-notes and runs EXE startup smoke

### P2 — Cleanup / maintainability / optimization

- P2-01. Resolve `workers` contract drift.
  - risk reduced: future schema/API confusion and false expectations
  - affected area: config, schema, docs, CLI tests
  - dependencies: P0 tasks recommended first
  - validation: CLI help, run metadata and schema agree on final contract

- P2-02. Replace ad-hoc script path bootstrap with a shared launcher strategy.
  - risk reduced: repeated `sys.path` hacks, lint exceptions, fragile module resolution
  - affected area: standalone scripts and developer UX
  - dependencies: P1-01
  - validation: scripts still run, `ruff` stays green, no duplicated bootstrap blocks remain

## 10. AI-Execution Tasks

<!-- markdownlint-disable MD024 -->

---

### TASK ID: P0-01

### Название

Запретить пересечение input и output paths

### Priority

P0

### Estimated scope

30-60 min

### Статус

- Выполнено.

### Context

Сейчас overlap между input и output не считается ошибкой. `src/doc_converter/runner.py` проверяет только существование и тип путей, а `src/doc_converter/gui.py` передаёт выбранные папки без preflight. Временный smoke подтвердил self-ingestion.

### Evidence

- `src/doc_converter/runner.py`: нет overlap-check
- `src/doc_converter/gui.py`: GUI не блокирует invalid path state
- Observed: nested output under input дал `manifest_relative_paths = out/old.docx; source.docx`

### Goal

Сделать overlap input/output невозможным для runner, CLI и GUI. Equal path и любая вложенность должны приводить к понятной ошибке до inventory.

### Non-goals

Не менять dedup, OCR, packaging и summary semantics вне overlap validation.

### Files to inspect

- `src/doc_converter/runner.py`
- `src/doc_converter/gui.py`
- `tests/test_cli_smoke.py`
- `tests/test_gui_import.py`

### Files to change

- `src/doc_converter/runner.py`
- `src/doc_converter/gui.py`
- `tests/test_cli_smoke.py`
- `tests/test_gui_import.py`
- `docs/build-and-run.md`

### Step-by-step instructions for agent

1. Найди текущий startup path validation в `src/doc_converter/runner.py`.
2. Добавь единый helper, который запрещает equal path и любую вложенность между `input_dir` и `output_dir`.
3. Вызывай этот helper из runner до создания `output_dir`.
4. В GUI добавь раннюю пользовательскую ошибку до старта worker thread.
5. Добавь regression tests для CLI/runner и GUI negative path cases.
6. Обнови краткую run doc строкой про недопустимое пересечение путей.
7. Проверь, что existing happy-path tests не сломались.

### Definition of Done

- [x] `input == output` отвергается до старта run
- [x] `output inside input` отвергается до старта run
- [x] `input inside output` отвергается до старта run
- [x] GUI показывает понятную ошибку и не стартует worker
- [x] regression tests на invalid path state проходят

### Validation command

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_cli_smoke tests.test_gui_import -v
```

```bash
python -m unittest tests.test_cli_smoke tests.test_gui_import -v
```

### Expected result

Оператор не сможет случайно скормить конвертеру собственный output или пересекающиеся каталоги.

### Rollback note

Если change сломает valid scenarios, откатить только overlap guard и связанные tests, не трогая остальной runner flow.

---

### TASK ID: P0-02

### Название

Сделать summary честным для unsupported inputs

### Priority

P0

### Estimated scope

30-60 min

### Статус

- Выполнено.

### Context

Сейчас unsupported files не входят в inventory, а summary всегда пишет `unsupported_files = 0`. Это делает mixed-folder runs misleading, хотя реальный corpus смешанный.

### Evidence

- `src/doc_converter/inventory.py`: inventory фильтрует только `.docx` и `.pdf`
- `src/doc_converter/runner.py`: `discovered_files` и `supported_files` равны filtered inventory, `unsupported_files` захардкожен в 0
- `docs/current-status.md`: реальный corpus смешанный
- Observed: smoke с `source.docx` и `ignored.txt` вернул `discovered_files=1`, `supported_files=1`, `unsupported_files=0`

### Goal

Считать total scanned files отдельно от supported files и отражать unsupported inputs в summary и processing log.

### Non-goals

Не добавлять новые supported formats и не менять output schema `document.v1`.

### Files to inspect

- `src/doc_converter/inventory.py`
- `src/doc_converter/runner.py`
- `tests/test_inventory.py`
- `tests/test_cli_smoke.py`
- `docs/build-and-run.md`

### Files to change

- `src/doc_converter/inventory.py`
- `src/doc_converter/runner.py`
- `tests/test_inventory.py`
- `tests/test_cli_smoke.py`
- `docs/build-and-run.md`

### Step-by-step instructions for agent

1. Перестрой inventory API так, чтобы он возвращал totals по scanned, supported и unsupported files.
2. Не меняй current conversion path для supported DOCX/PDF.
3. Запиши unsupported count честно в summary.
4. Добавь `processing-log` events по unsupported inputs с причиной skip.
5. Добавь regression tests на mixed folder.
6. Обнови doc с ожидаемым поведением для unsupported files.

### Definition of Done

- [x] mixed input reports truthful `discovered_files`
- [x] `unsupported_files` больше нуля, если в input есть non-DOCX/PDF files
- [x] `processing-log` содержит skip record для unsupported input
- [x] existing supported-file flow остаётся green

### Validation command

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_inventory tests.test_cli_smoke -v
.\.venv\Scripts\python.exe scripts\run_synthetic_e2e.py --clean
```

```bash
python -m unittest tests.test_inventory tests.test_cli_smoke -v
python scripts/run_synthetic_e2e.py --clean
```

### Expected result

Run summary перестаёт скрывать unsupported inputs и становится пригодным для audit/completeness checks.

### Rollback note

Если новая inventory shape сломает слишком много call sites, откатить API change целиком и вернуть старую форму, затем повторить с меньшим refactor scope.

---

### TASK ID: P1-01

### Название

Сделать `ruff` green и ввести lint gate

### Priority

P1

### Estimated scope

30-60 min

### Статус

- Выполнено.

### Context

Локальный `ruff` падает на 14 issues. Основные ошибки связаны с `E402` в standalone scripts с `sys.path` bootstrap и `F401` в `src/doc_converter/converters/pdf_scan.py`. CI `ruff` не запускает.

### Evidence

- `.github/workflows/windows-ci.yml`: lint step отсутствует
- `scripts/build_sample_chunks.py`
- `scripts/run_folder_e2e.py`
- `scripts/run_sample_pilot.py`
- `scripts/run_synthetic_e2e.py`
- `scripts/validate_run_package.py`
- `src/doc_converter/converters/pdf_scan.py`

### Goal

Сделать `ruff check src tests scripts` стабильно зелёным и включить его в Windows CI.

### Non-goals

Не делать большой packaging/refactor scripts; допускаются явные per-file policy decisions, если они минимальны и объяснимы.

### Files to inspect

- `pyproject.toml`
- `.github/workflows/windows-ci.yml`
- `scripts/build_sample_chunks.py`
- `scripts/run_folder_e2e.py`
- `scripts/run_sample_pilot.py`
- `scripts/run_synthetic_e2e.py`
- `scripts/validate_run_package.py`
- `src/doc_converter/converters/pdf_scan.py`

### Files to change

- `pyproject.toml`
- `.github/workflows/windows-ci.yml`
- `scripts/build_sample_chunks.py`
- `scripts/run_folder_e2e.py`
- `scripts/run_sample_pilot.py`
- `scripts/run_synthetic_e2e.py`
- `scripts/validate_run_package.py`
- `src/doc_converter/converters/pdf_scan.py`

### Step-by-step instructions for agent

1. Зафиксируй `ruff` policy в repo config.
2. Удали unused import в `pdf_scan`.
3. Выбери минимальный и явный способ закрыть `E402` для standalone scripts.
4. Добавь `ruff` step в Windows CI до unit tests.
5. Убедись, что docs или dev instructions не противоречат новой lint policy.

### Definition of Done

- [x] `ruff check src tests scripts` passes locally
- [x] CI workflow runs `ruff`
- [x] No unused imports remain in touched files
- [x] Script bootstrap policy зафиксирована явно, а не случайно

### Validation command

```powershell
ruff check src tests scripts
```

```bash
ruff check src tests scripts
```

### Expected result

Статические проблемы перестают накапливаться незаметно, и CI начинает блокировать lint regressions.

### Rollback note

Если CI wiring ломает workflow, откатить только lint step и config change, не затрагивая business logic.

---

### TASK ID: P1-02

### Название

Добавить `pyright` gate и исправить текущую typing-проблему

### Priority

P1

### Estimated scope

30-60 min

### Статус

- Выполнено.

### Context

`pyrightconfig.json` уже есть, но `pyright` не запускается ни локально, ни в CI. Editor diagnostics уже показывает type mismatch в `tests/test_gui_import.py`.

### Evidence

- `pyrightconfig.json`: typecheck surface declared
- `.github/workflows/windows-ci.yml`: `pyright` step отсутствует
- `tests/test_gui_import.py`: current type mismatch in test assignment

### Goal

Сделать `pyright` частью CI и привести текущий typed surface к зелёному состоянию.

### Non-goals

Не делать полную type-annotation campaign по всему проекту beyond what is needed for green pyright.

### Files to inspect

- `pyrightconfig.json`
- `pyproject.toml`
- `.github/workflows/windows-ci.yml`
- `tests/test_gui_import.py`

### Files to change

- `pyproject.toml`
- `pyrightconfig.json`
- `.github/workflows/windows-ci.yml`
- `tests/test_gui_import.py`

### Step-by-step instructions for agent

1. Добавь `pyright` как dev/build-time dependency или другой repo-local способ гарантировать его наличие в CI.
2. Запусти `pyright` по текущему config.
3. Исправь текущую typing issue в GUI test без ослабления type surface без причины.
4. Добавь `pyright` step в workflow.
5. Убедись, что lint и unit tests после этого тоже остаются зелёными.

### Definition of Done

- [x] `pyright` runs from repo-local setup
- [x] `pyright` passes on `src`, `scripts`, `tests`
- [x] current `test_gui_import` issue fixed
- [x] CI blocks on `pyright` failures

### Validation command

```powershell
pyright
```

```bash
pyright
```

### Expected result

Typecheck перестаёт быть декларативным файлом без исполнения и становится реальным gate.

### Rollback note

Если новый `pyright` scope окажется слишком широким и ломает unrelated slices, откатить только scope expansion и зафиксировать minimal passing config.

---

### TASK ID: P1-03

### Название

Сделать Windows source install reproducible и dependency-clean

### Priority

P1

### Estimated scope

60 min

### Статус

- Выполнено без отдельного lock/constraints файла: reproducible install path зафиксирован через `.[build,dev]`, clean-room Windows venv и `pip check`.

### Context

Локальный `python -m pip check` failed, а lock/constraints files в репозитории не найдены. Это значит, что current green state опирается на mutable local `.venv`.

### Evidence

- `pyproject.toml`: declared deps only
- `.github/workflows/windows-ci.yml`: workflow installs editable package, но не делает `pip check`
- Observed: `python -m pip check failed` on current `.venv`
- Not found in repository: `poetry.lock`, `uv.lock`, `pdm.lock`, `constraints files`

### Goal

Зафиксировать reproducible dependency installation path для Windows source build и сделать `pip check` зелёным на clean env.

### Non-goals

Не вводить новый package manager и не менять runtime scope проекта.

### Files to inspect

- `pyproject.toml`
- `.github/workflows/windows-ci.yml`
- `docs/build-and-run.md`
- `docs/ocr-runtime-windows.md`

### Files to change

- `pyproject.toml`
- `.github/workflows/windows-ci.yml`
- `docs/build-and-run.md`
- `docs/ocr-runtime-windows.md`
- create a new repo-local constraints or lock file

### Step-by-step instructions for agent

1. Собери clean dependency install plan для Windows source build.
2. Добавь repo-local constraints or lock file, совместимый с текущим editable install flow.
3. Убедись, что clean env install по этому plan даёт `python -m pip check` без ошибок.
4. Добавь `pip check` в workflow после install step.
5. Обнови docs так, чтобы они использовали тот же install path.

### Definition of Done

- [x] clean env install path documented in repo
- [x] `pip check` passes on clean env
- [x] workflow runs `pip check`
- [x] docs and CI use one dependency story

### Validation command

```powershell
python -m venv .tmp-audit-venv
.\.tmp-audit-venv\Scripts\python.exe -m pip install --upgrade pip
.\.tmp-audit-venv\Scripts\python.exe -m pip install -e .[build]
.\.tmp-audit-venv\Scripts\python.exe -m pip check
```

```bash
python -m venv .tmp-audit-venv
./.tmp-audit-venv/bin/python -m pip install --upgrade pip
./.tmp-audit-venv/bin/python -m pip install -e .[build]
./.tmp-audit-venv/bin/python -m pip check
```

### Expected result

Новая машина сможет собрать source runtime predictably, а dependency sanity станет проверяемой, а не подразумеваемой.

### Rollback note

Если новый constraints path ломает existing install flow, откатить constraints file и docs вместе, затем пересобрать решение на меньшем scope.

---

### TASK ID: P1-04

### Название

Проверять portable release artefact и EXE smoke в CI

### Priority

P1

### Estimated scope

60 min

### Статус

- Выполнено.

### Context

CI сейчас останавливается на `build-windows`. Portable zip и packaged EXE smoke не подтверждаются workflow, хотя docs заявляют такой smoke.

### Evidence

- `.github/workflows/windows-ci.yml`: `package-release` and EXE smoke absent
- `scripts/package-release.ps1`: packaging script exists
- `docs/release-status.md`: EXE smoke claimed in docs
- Observed: local `package-release` passed and produced `zip/checksum/release-notes` in `dist/release/DocumentConverter-0.2.0`

### Goal

Сделать final artefact validation частью CI: packaging, artefact existence checks и базовый startup smoke для packaged EXE.

### Non-goals

Не внедрять полный installer workflow и не публиковать GitHub Release.

### Files to inspect

- `.github/workflows/windows-ci.yml`
- `scripts/build-windows.ps1`
- `scripts/package-release.ps1`
- `docs/build-and-run.md`
- `docs/release-status.md`

### Files to change

- `.github/workflows/windows-ci.yml`
- `scripts/package-release.ps1`
- `docs/build-and-run.md`
- `docs/release-status.md`
- if needed, create a small smoke helper script under `scripts`

### Step-by-step instructions for agent

1. Добавь CI step для `package-release` после build.
2. Явно проверь наличие zip, sha256 file и `release-notes`.
3. Добавь лёгкий EXE startup smoke, пригодный для headless Windows runner.
4. Если нужен отдельный smoke helper script, сделай его минимальным и deterministic.
5. Обнови docs так, чтобы они совпадали с фактическим CI path.

### Definition of Done

- [x] CI produces and validates portable release artefacts
- [x] CI runs packaged EXE startup smoke
- [x] docs no longer claim manual-only smoke as if it were automated
- [x] workflow fails if packaging or smoke fails

### Validation command

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build-windows.ps1 -Name DocumentConverter
powershell -ExecutionPolicy Bypass -File scripts\package-release.ps1 -Name DocumentConverter -Version 0.2.0 -SkipBuild
```

Linux/macOS: not applicable, Windows-only release path.

### Expected result

Release path становится reproducible и проверяемым до передачи операторам.

### Rollback note

Если EXE smoke окажется нестабильным на CI, откатить только smoke step и helper, сохранив packaging validation.

---

### TASK ID: P2-01

### Название

Убрать дрейф вокруг `workers` contract

### Priority

P2

### Estimated scope

30-60 min

### Статус

- Выполнено; `workers` убран из runtime payload и config, а schema оставлена только как deprecated backward-compatible surface.

### Context

Docs говорят, что false workers removed from public contract, но internal config и schema всё ещё содержат `workers`, а CLI просто жёстко пишет `workers = 1`.

### Evidence

- `src/doc_converter/config.py`
- `src/doc_converter/cli.py`
- `schemas/run.v1.schema.json`
- `docs/current-sprint.md`

### Goal

Сделать один честный contract: либо `workers` полностью удалить из internal/schema surface, либо реализовать его end-to-end. Для текущего scope предпочтителен removal, если parallelism не нужен.

### Non-goals

Не внедрять parallel conversion только ради консистентности, если это не помещается в задачу.

### Files to inspect

- `src/doc_converter/config.py`
- `src/doc_converter/cli.py`
- `schemas/run.v1.schema.json`
- `tests/test_cli_smoke.py`
- `docs/current-sprint.md`

### Files to change

- `src/doc_converter/config.py`
- `src/doc_converter/cli.py`
- `schemas/run.v1.schema.json`
- `tests/test_cli_smoke.py`
- `docs/build-and-run.md`

### Step-by-step instructions for agent

1. Прими одно решение: remove or implement.
2. Предпочтительно убери `workers` из config/run metadata/schema, если он не используется.
3. Синхронизируй tests и docs с финальным contract.
4. Проверь, что run schema и CLI help больше не расходятся.

### Definition of Done

- [x] final public contract documented once
- [x] schema and runtime payload agree
- [x] tests assert final contract
- [x] no dead `workers` field remains by accident

### Validation command

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_cli_smoke -v
.\.venv\Scripts\python.exe scripts\run_synthetic_e2e.py --clean
```

```bash
python -m unittest tests.test_cli_smoke -v
python scripts/run_synthetic_e2e.py --clean
```

### Expected result

Contract drift исчезает, и future maintainers больше не видят phantom capability.

### Rollback note

Если выбранный direction ломает schema consumers, вернуть предыдущее состояние целиком и подготовить separate implementation task.

---

### TASK ID: P2-02

### Название

Убрать повторяющиеся `sys.path` bootstrap blocks из standalone scripts

### Priority

P2

### Estimated scope

60 min

### Статус

- Выполнено.

### Context

Несколько scripts вручную делают `sys.path.insert`, из-за чего появился `E402` lint debt и хрупкая bootstrap semantics.

### Evidence

- `scripts/build_sample_chunks.py`
- `scripts/run_folder_e2e.py`
- `scripts/run_sample_pilot.py`
- `scripts/run_synthetic_e2e.py`
- `scripts/validate_run_package.py`

### Goal

Перевести standalone scripts на единый launcher strategy без копипасты bootstrap path logic.

### Non-goals

Не переписывать всю CLI surface проекта и не менять business semantics scripts.

### Files to inspect

- `scripts/build_sample_chunks.py`
- `scripts/run_folder_e2e.py`
- `scripts/run_sample_pilot.py`
- `scripts/run_synthetic_e2e.py`
- `scripts/validate_run_package.py`
- `pyproject.toml`

### Files to change

- `scripts/build_sample_chunks.py`
- `scripts/run_folder_e2e.py`
- `scripts/run_sample_pilot.py`
- `scripts/run_synthetic_e2e.py`
- `scripts/validate_run_package.py`
- `pyproject.toml`
- `docs/build-and-run.md`

### Step-by-step instructions for agent

1. Выбери единый bootstrap approach: repo-local helper, package module execution или explicit console scripts.
2. Удали дублированный `sys.path.insert` из touched scripts.
3. Сохрани совместимость с текущими documented commands или обнови docs синхронно.
4. Убедись, что `ruff` остаётся зелёным и scripts реально запускаются.

### Definition of Done

- [x] duplicated `sys.path` bootstrap removed from targeted scripts
- [x] scripts still run from documented commands
- [x] `ruff` stays green
- [x] docs explain the final invocation model

### Validation command

```powershell
ruff check src tests scripts
.\.venv\Scripts\python.exe scripts\run_synthetic_e2e.py --clean
.\.venv\Scripts\python.exe scripts\validate_run_package.py runs\synthetic-e2e-output\runs\<new_run_id>
```

```bash
ruff check src tests scripts
python scripts/run_synthetic_e2e.py --clean
python scripts/validate_run_package.py runs/synthetic-e2e-output/runs/<new_run_id>
```

### Expected result

Standalone scripts перестают зависеть от копипастного path bootstrap и становятся проще для сопровождения.

### Rollback note

Если новый launcher strategy ломает documented commands, откатить только bootstrap refactor и оставить lint exceptions как временный fallback.

---

### TASK ID: P2-03

### Название

Проверять integrity OCR traineddata downloads

### Priority

P2

### Estimated scope

30-60 min

### Статус

- Выполнено. `scripts/install-ocr-runtime.ps1` фиксирует expected SHA-256 для `eng`, `rus` и `osd`, проверяет hash после direct download, удаляет mismatch artifact и останавливает установку fail-fast; OCR runtime docs обновлены.

### Context

OCR helper скачивает traineddata по HTTPS, но не проверяет expected digest before use.

### Evidence

- `scripts/install-ocr-runtime.ps1`

### Goal

Добавить checksum verification для `eng`, `rus` и `osd traineddata` и fail-fast на mismatch.

### Non-goals

Не менять preferred install method и не вводить новый package manager.

### Files to inspect

- `scripts/install-ocr-runtime.ps1`
- `docs/ocr-runtime-windows.md`

### Files to change

- `scripts/install-ocr-runtime.ps1`
- `docs/ocr-runtime-windows.md`

### Step-by-step instructions for agent

1. Зафиксируй expected SHA-256 для `eng`, `rus` и `osd traineddata`.
2. После `curl` download вычисляй hash и сравнивай с expected.
3. На mismatch удаляй испорченный файл и прекращай установку с понятной ошибкой.
4. Обнови OCR runtime doc короткой note про integrity check.

### Definition of Done

- [x] helper validates traineddata checksums
- [x] corrupted download causes fail-fast
- [x] docs mention integrity verification
- [x] happy path install flow remains unchanged

### Validation command

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install-ocr-runtime.ps1 -CheckOnly
```

Linux/macOS: not applicable, Windows-only helper.

### Expected result

OCR bootstrap path получает минимальную supply-chain integrity защиту.

### Rollback note

Если checksum values окажутся неверными, откатить только verification block и docs, не трогая остальную helper logic.

---

## 11. PRS Dynamics

- текущий PRS: 70/100
- после P0: 80/100
- после P1: 88/100
- после P2: 92/100

Почему не выше:

- нет доказанного clean-room reproducibility сегодня
- нет полного static/dependency/release gating в CI
- часть confidence снижается из-за отсутствия coverage percent и dependency audit evidence

## 12. Top 5 Next Agent Prompts

1. Исправь production blocker с overlapping input/output paths в `src/doc_converter/runner.py` и `src/doc_converter/gui.py`. Запрети equal path и любую вложенность между input и output, добавь regression tests в `tests/test_cli_smoke.py` и `tests/test_gui_import.py`, обнови `docs/build-and-run.md`. Validate with unittest on these files. Не меняй dedup, OCR или packaging flow.

2. Исправь production blocker со silent skip unsupported files. Перестрой inventory/summary так, чтобы mixed folder честно отражал discovered, supported и unsupported counts. Работай в `src/doc_converter/inventory.py`, `src/doc_converter/runner.py`, обнови tests в `tests/test_inventory.py` и `tests/test_cli_smoke.py`, при необходимости поправь `docs/build-and-run.md`. Validate with targeted unittest and synthetic e2e. Не добавляй новые supported formats.

3. Сделай lint gate production-grade: добейся зелёного `ruff` для `src/tests/scripts` и добавь `ruff` step в `.github/workflows/windows-ci.yml`. Исправь current issues в `scripts/build_sample_chunks.py`, `scripts/run_folder_e2e.py`, `scripts/run_sample_pilot.py`, `scripts/run_synthetic_e2e.py`, `scripts/validate_run_package.py` и `src/doc_converter/converters/pdf_scan.py`. Validate with `ruff check src tests scripts`. Не делай большой refactor launcher architecture.

4. Включи реальный `pyright` gate. Используй `pyrightconfig.json`, добавь `pyright` availability в repo-local dependency flow, исправь current typing issue в `tests/test_gui_import.py` и добавь `pyright` step в `.github/workflows/windows-ci.yml`. Validate with `pyright` and existing unittest. Не разворачивай mass annotation campaign.

5. Сделай setup воспроизводимым и dependency-clean. На основе `pyproject.toml`, `.github/workflows/windows-ci.yml`, `docs/build-and-run.md` и `docs/ocr-runtime-windows.md` добавь repo-local constraints or lock path, добейся clean venv install без ошибок `python -m pip check` и включи `pip check` в CI. Не меняй package manager и не трогай runtime scope приложения.

<!-- markdownlint-enable MD024 -->