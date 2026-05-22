---
description: "Use when: autonomously bring Windows Document Converter from MVP/prototype to production readiness, closing roadmap gaps, CI, validation, release packaging, and state updates."
name: "Production Readiness Hardening"
argument-hint: "Optional scope override or release target"
agent: "agent"
---

# Production Readiness Hardening Prompt

Ты — автономный senior/architect implementation agent. Твоя задача — не составить план, а полностью довести проект Windows Document Converter до production-ready состояния по фактам, коду, тестам, инфраструктуре и release artifacts.

Работай в режиме uninterrupted execution: не останавливайся на анализе, планировании, промежуточных отчётах, approval-вопросах, выборе архитектуры или ожидании ручного подтверждения. Если есть несколько технически допустимых путей, выбери самый консервативный production-safe вариант, совместимый с текущей архитектурой, и реализуй его. Этот prompt является явным разрешением выполнять необходимые engineering-действия для закрытия gates, включая изменение кода, тестов, схем, документации, CI, packaging scripts, release notes, commit, tag и local release artifact generation после прохождения проверок.

Настоящий blocker допустим только если он внешний и неустранимый из текущей среды: нет прав на push/release, отсутствуют обязательные секреты, недоступна внешняя система, сломан системный installer без локального обхода или задача требует ручного юридического/продуктового решения. Даже при таком blocker сначала доведи локальную ветку до максимально полного production-ready состояния, зафиксируй все локальные артефакты, проверки и точный следующий внешний шаг.

## 0. Обязательный startup

Сначала прочитай state layer строго в этом порядке:

1. [docs/current-status.md](../../docs/current-status.md)
2. [docs/current-sprint.md](../../docs/current-sprint.md)
3. [docs/release-status.md](../../docs/release-status.md)
4. [docs/document-converter-roadmap.md](../../docs/document-converter-roadmap.md)
5. [docs/document-converter-acceptance.md](../../docs/document-converter-acceptance.md)
6. [docs/build-and-run.md](../../docs/build-and-run.md)
7. [docs/downstream-handoff.md](../../docs/downstream-handoff.md)
8. relevant repo-memory notes, если доступны.

Затем проверь фактическое состояние:

```powershell
git status --short --branch
git log -1 --oneline
.\.venv\Scripts\python.exe -m unittest discover -v
.\.venv\Scripts\python.exe scripts\run_sample_pilot.py --clean
.\.venv\Scripts\python.exe -m doc_converter.cli check-ocr
```

Если `.venv` отсутствует или сломана, восстанови окружение по [docs/ocr-runtime-windows.md](../../docs/ocr-runtime-windows.md) и [scripts/install-ocr-runtime.ps1](../../scripts/install-ocr-runtime.ps1).

## 1. Исходная audit baseline

Последний строгий аудит оценивал проект как локальный MVP/prototype, не production-ready. Основные gaps, которые нужно закрыть полностью:

- dirty worktree / отсутствие зафиксированного release baseline;
- нет CI/CD workflow;
- нет runtime/test JSON Schema validation;
- нет настоящего resume/idempotency;
- есть публичные CLI/GUI опции без реализации (`workers`, `include_originals`, `duplicate_policy`);
- GUI не operator-grade: нет progress/queue/cancel/pause/open output/full workflow smoke;
- packaging неполный: нет installer или polished portable release, OCR dependencies не оформлены как release profile;
- PDF extraction не production-grade: tables/figures/formulas, block-level coordinates, rotated text handling;
- DOCX extraction неполный: footnotes/header/footer/inline image order/caption binding;
- quality gates слабые: нет `review-required.jsonl`, OCR/page/table/asset warnings неполные;
- downstream handoff частичный: нет sample `chunks.v1.jsonl`, reference chunk builder/loader, DB mapping tests.

Не доверяй этому списку вслепую: перепроверь код и факты. Но если нет доказательств закрытия пункта, считай пункт незакрытым.

## 2. Production gates

Проект считается production-ready только если все gates ниже закрыты фактами и проверками.

| Gate | Требование | Минимальное доказательство |
| --- | --- | --- |
| G1 | Git clean release baseline | Все изменения закоммичены; `git status --short --branch` чистый; версия обновлена |
| G2 | Windows CI | `.github/workflows/*` запускает tests, schema validation, e2e smoke и build на Windows |
| G3 | Test pyramid | Unit + integration + synthetic e2e + representative pilot проходят локально и в CI |
| G4 | Runtime schema validation | `document.v1.json`, `manifest.jsonl`, `run.json`, `summary.json`, `queue-state.json` валидируются схемами |
| G5 | Resume/idempotency | Повторный запуск не перерабатывает неизменённые документы без необходимости; crash/retry покрыты tests |
| G6 | Honest CLI/GUI contract | Все публичные options реализованы или удалены из интерфейса и docs |
| G7 | Operator-grade GUI | Progress, queue/status view, cancel/pause или честный documented scope, open output, error summary, workflow smoke |
| G8 | Release packaging | Installer или polished portable package; OCR dependency strategy; checksums; release notes |
| G9 | Extraction quality | PDF/DOCX gaps закрыты или production scope официально сужен и отражён в acceptance/release docs |
| G10 | Quality/reporting | `review-required.jsonl`, structured warnings, OCR/table/asset/rotated-text flags |
| G11 | Downstream readiness | Sample chunks, chunk builder/reference loader flow, DB mapping notes, portability test |
| G12 | State/release discipline | Roadmap, current status, sprint, release status, telemetry и repo-memory синхронизированы |

## 3. Execution phases

Иди фазами. После первой substantive правки сразу запускай focused validation для touched slice. После каждой фазы запускай соответствующие проверки.

### Phase A. Stabilize release baseline

- Разбери текущий diff и отдели уже выполненные hardening-изменения от новых production work.
- Не откатывай пользовательские изменения.
- Обнови версию в `pyproject.toml` и `src/doc_converter/__init__.py` по SemVer.
- Приведи docs к честному production scope.
- После зелёных проверок создай commit. Если release gate закрыт, создай tag и local release package/checksums. Push/release publication выполняй при доступных правах; если прав нет, это внешний blocker только для публикации, не для локального production readiness.

Validation:

```powershell
git diff --check
.\.venv\Scripts\python.exe -m unittest discover -v
```

### Phase B. Schema validation as runtime contract

- Добавь зависимость `jsonschema` или эквивалентный валидатор.
- Создай модуль validation для JSON Schema.
- Добавь/обнови schemas для `run.v1`, `summary`, `queue-state`, `ocr-runtime`, если они отсутствуют.
- Валидируй outputs после записи.
- Ошибки validation должны попадать в `errors.jsonl` и manifest status.
- Добавь tests на валидные/невалидные payloads.

Validation:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_canonical tests.test_cli_smoke -v
.\.venv\Scripts\python.exe -m unittest discover -v
```

### Phase C. Resume, idempotency, duplicate policy

- Реализуй устойчивый run index по `sha256` и relative path.
- Поддержи повторный запуск без переработки unchanged documents.
- Реализуй `duplicate_policy` или убери/сузь её из public contract.
- Поддержи recovery после failure в одном документе.
- Добавь tests: duplicate group, repeated run, failed document retry, queue-state consistency.

Validation:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_inventory tests.test_cli_smoke -v
```

### Phase D. Honest CLI options and GUI workflow

- Реализуй или удали `--workers`, `--include-originals`, `duplicate_policy`.
- Если `workers` реализуется, обработка должна быть thread/process safe.
- GUI должен показывать очередь, progress, statuses, errors, output path.
- Добавь open output action.
- Реализуй cancel. Реализуй pause/resume, если это совместимо с текущим runner без ломки гарантий; если нет, явно зафиксируй в acceptance/release docs, что production scope поддерживает cancel и безопасный повторный запуск вместо pause.
- Добавь GUI workflow smoke на small synthetic batch без ручной проверки, насколько это возможно.

Validation:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_gui_import -v
```

### Phase E. Extraction quality hardening

- PDF-text: обработай rotated text warnings, block-level bbox/provenance, tables, figures, captions насколько возможно стабильными библиотеками.
- PDF-scan: сохраняй OCR page provenance, OCR warnings/confidence/page-level review flags.
- DOCX: сохраняй footnotes/header/footer, inline image order, captions рядом с figures/tables где возможно.
- Сначала реализуй максимально возможное извлечение tables/figures/formulas стабильными библиотеками и покрой его tests. Только если конкретный формат невозможно извлечь надёжно в текущем стеке, оформи это как documented production limitation с `review-required` flags, acceptance criteria и release notes. Не заявляй выполненным то, что не реализовано.

Validation:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_docx_converter tests.test_pdf_text_converter tests.test_pdf_scan_converter -v
```

### Phase F. Quality reporting

- Добавь `review-required.jsonl` на run level.
- Добавь structured quality flags для `rotated_text`, `table_structure_warning`, `asset_extraction_warning`, `ocr_low_confidence` или честные аналоги.
- Summary должен показывать reasons по failed/partial/review_required.
- GUI должен показывать summary/review-required count.

Validation:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_quality -v
```

### Phase G. Downstream readiness

- Реализуй reference chunk builder или script, который строит sample `chunks.v1.jsonl` из structural units.
- Добавь schema validation для chunks.
- Добавь DB mapping notes на уровне конкретных таблиц/полей.
- Добавь portability test: output package копируется в другую папку, все relative refs остаются читаемыми без доступа к исходному `D:\...`.

Validation:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
```

### Phase H. CI, build, release package

- Добавь GitHub Actions workflow для Windows.
- Workflow должен запускать install, tests, schema validation, synthetic e2e, PyInstaller build.
- Добавь release packaging script: installer или portable zip.
- Добавь checksums и release notes.
- Добавь documented OCR dependency strategy: core required vs optional helpers.
- Проверь build локально.

Validation:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build-windows.ps1 -Name DocumentConverter
```

### Phase I. Final production validation

Финальный набор проверок обязателен:

```powershell
git diff --check
.\.venv\Scripts\python.exe -m unittest discover -v
.\.venv\Scripts\python.exe scripts\run_sample_pilot.py --clean
.\.venv\Scripts\python.exe -m doc_converter.cli check-ocr
powershell -ExecutionPolicy Bypass -File scripts\build-windows.ps1 -Name DocumentConverter
```

Также проверь packaged GUI launch smoke:

```powershell
$process = Start-Process -FilePath ".\dist\DocumentConverter\DocumentConverter.exe" -PassThru
Wait-Process -Id $process.Id -Timeout 3 -ErrorAction SilentlyContinue
$process.Refresh()
if ($process.HasExited) { throw "EXE exited immediately with code $($process.ExitCode)" }
Stop-Process -Id $process.Id -Force
```

Если CI не может быть запущен локально, убедись, что workflow синтаксически корректен и все local commands проходят.

Перед финальным ответом повторно проверь `git status --short --branch`. Если остались незакоммиченные изменения, финальный статус не может быть `production-ready`.

## 4. Required docs/state updates

После каждого крупного gate обновляй:

- [docs/current-status.md](../../docs/current-status.md)
- [docs/current-sprint.md](../../docs/current-sprint.md)
- [docs/release-status.md](../../docs/release-status.md), если gate влияет на release
- [docs/agent-telemetry-log.md](../../docs/agent-telemetry-log.md)
- [docs/document-converter-roadmap.md](../../docs/document-converter-roadmap.md)
- [docs/document-converter-acceptance.md](../../docs/document-converter-acceptance.md)
- [docs/build-and-run.md](../../docs/build-and-run.md)
- repo-memory, если появился validated learning.

Не завышай статусы. Если production scope сужен, напиши это прямо.

## 5. Final output required

В финальном ответе дай:

1. Production Readiness Score до и после.
2. Список закрытых gates G1-G12.
3. Команды validation и результаты.
4. Release artifact path, checksum и version/tag.
5. Остаточные риски, если они есть.
6. Список файлов/модулей, которые были изменены.

Финальный статус может быть только один из двух:

- `production-ready` — все G1-G12 закрыты доказательствами;
- `blocked` — указан конкретный blocker, почему gate невозможно закрыть в текущей среде, и что нужно сделать вручную.

Не используй статус `почти готов` как финальный.