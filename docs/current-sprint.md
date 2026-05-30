# Current Sprint

Последнее обновление: 2026-05-31
Активный спринт: S9.2 — Nightly full e2e
Статус: in_progress

Предыдущий приоритетный tranche: S9.1 — PR-gates и branch protection
Статус: completed
Статус wave W9: in_progress

## 1. Цель спринта

Запустить hosted-runner nightly regression contour поверх закрытого S9.1: synthetic e2e, full formula benchmark monitor, CI-safe formula gate, repo-tracked table anchors, portable package build, EXE smoke и auto-issue при падении с привязкой к последнему merged PR.

## 2. Артефакты спринта

- .github/PULL_REQUEST_TEMPLATE.md
- .github/workflows/nightly-full-e2e.yml
- .github/workflows/release.yml
- CHANGELOG.md
- samples/manifest.table-anchors.ci.jsonl
- scripts/create_nightly_failure_issue.py
- scripts/render_release_notes.py
- scripts/run_sample_pilot.py
- src/doc_converter/formulas/providers.py
- src/doc_converter/ocr/backends.py
- src/doc_converter/release_notes.py
- src/doc_converter/formula_benchmark.py
- src/doc_converter/run/catalog_writers.py
- schemas/run.v1.schema.json
- tests/test_config.py
- tests/test_formula_recognition.py
- tests/test_nightly_failure_issue.py
- tests/test_pdf_scan_converter.py
- tests/test_release_notes.py
- tests/test_sample_pilot.py
- tests/test_formula_benchmark.py
- docs/current-status.md
- docs/current-sprint.md
- docs/production-roadmap.md
- docs/release-status.md
- docs/agent-feature-spine.json
- docs/agent-telemetry-log.md
- docs/agent-telemetry.v1.jsonl
- docs/agent-quality-scorecard.md
- docs/agent-quality-scorecard.v1.json
- docs/agent-weekly-eval.md
- docs/agent-weekly-eval.v1.json

## 3. Задачи спринта

| Задача | Статус |
| --- | --- |
| Поднять отдельный nightly workflow на hosted runner | Готово |
| Сделать table anchor manifest repo-safe и независимым от `cwd`/`D:\...` | Готово |
| Развести full formula monitor и CI-safe required gate | Готово |
| Открыть auto-issue path на failure с контекстом latest merged PR | Готово |
| Собрать tag-driven release automation с changelog-backed release notes и GitHub Release publish path | Готово |
| Набрать 7 ночей burn-in evidence и убедиться, что auto-issue path не флапает | В работе |

## 4. Validation targets спринта

1. `runTests tests/test_sample_pilot.py tests/test_formula_benchmark.py tests/test_nightly_failure_issue.py` проходит зелёно и фиксирует portability/monitor/auto-issue contracts.
2. `$env:PYTHONPATH = 'src'; .\.venv\Scripts\python.exe scripts\refresh_agent_eval.py` пересобирает generated companions без drift.
3. `$env:PYTHONPATH = 'src'; .\.venv\Scripts\python.exe scripts\validate_harness_assets.py` возвращает `status: ok` с активным feature `ci-nightly-e2e`.
4. Первый `workflow_dispatch` или schedule run `nightly-full-e2e` на GitHub публикует artifact bundle с synthetic run, formula monitor, formula gate, table-anchor run и nightly portable package либо автоматически создаёт issue с диагностикой.

## 5. Риски спринта

- GitHub-hosted runner не видит внешний `D:\ФСНБ\...` corpus, поэтому full formula manifest в nightly идёт в monitor-only режиме без thresholds, а required gate пока держится на CI-safe subset.
- `agent_id` для failure issue будет точным только для PR, где заполнен новый template field; для старых merges helper честно падает назад на `head_ref`, затем author login.
- Exit спринта зависит не от локального validation, а от 7-night burn-in/auto-issue evidence на GitHub.
- Для `S9.3` локальный workflow/script proof уже есть, но первый hosted `v*` tag run ещё не зафиксирован в state layer, поэтому wave W9 остаётся открытой до GitHub evidence.

## 6. Критерий выхода

Спринт закрыт, когда hosted nightly contour либо проходит 7 ночей подряд, либо детерминированно открывает диагностический issue со ссылкой на failing run и latest merged PR context без ручного вмешательства.

## 7. Следующий operational focus

1. Дождаться первого GitHub run `nightly-full-e2e` и зафиксировать artifact/issue evidence в state layer.
2. Снять первый hosted proof для `.github/workflows/release.yml`: `v*` tag должен опубликовать GitHub Release с zip, checksum и notes из `CHANGELOG.md`.
3. Держать `agent_id` field обязательной частью agent PR closeout, чтобы auto-issue path перестал зависеть от fallback inference.
4. Пока hosted proof по S9.x идёт отдельно на GitHub, независимые S3.1 и S3.2 уже закрыты локально через `FormulaProvider` / `OcrBackend` / `CatalogWriter` protocols; следующий parallel follow-up теперь S3.3 и measured DOCX/table backlog.
