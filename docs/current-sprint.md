# Current Sprint

Последнее обновление: 2026-05-31
Активный спринт: S9.2 — Nightly full e2e
Статус: in_progress

Предыдущий приоритетный tranche: S9.1 — PR-gates и branch protection
Статус: completed
Статус wave W9: in_progress

## 1. Цель спринта

Запустить hosted-runner nightly regression contour поверх закрытого S9.1: synthetic e2e, full formula benchmark monitor, CI-safe formula gate, table-anchor source preflight с real table run при доступных external samples, portable package build, EXE smoke и auto-issue при падении с привязкой к последнему merged PR.

## 2. Артефакты спринта

- .github/PULL_REQUEST_TEMPLATE.md
- .github/workflows/nightly-full-e2e.yml
- .github/workflows/release.yml
- CHANGELOG.md
- samples/manifest.table-anchors.ci.jsonl
- scripts/create_nightly_failure_issue.py
- scripts/render_release_notes.py
- scripts/run_sample_pilot.py
- src/doc_converter/inventory.py
- src/doc_converter/formulas/providers.py
- src/doc_converter/ocr/backends.py
- src/doc_converter/redaction.py
- src/doc_converter/release_notes.py
- src/doc_converter/formula_benchmark.py
- src/doc_converter/run/catalog_writers.py
- src/doc_converter/run/logging.py
- schemas/run.v1.schema.json
- tests/test_config.py
- tests/test_formula_recognition.py
- tests/test_nightly_failure_issue.py
- tests/test_inventory.py
- tests/test_pdf_scan_converter.py
- tests/test_provider_secret_redaction.py
- tests/test_release_notes.py
- tests/test_run_determinism.py
- tests/test_sample_pilot.py
- tests/test_formula_benchmark.py
- memories/repo/backend-notes.md
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
| Сделать table anchor manifest независимым от `cwd`/`D:\...` и добавить hosted source preflight | Готово локально; hosted proof pending |
| Развести full formula monitor и CI-safe required gate | Готово |
| Открыть auto-issue path на failure с контекстом latest merged PR | Готово |
| Собрать tag-driven release automation с changelog-backed release notes и GitHub Release publish path | Готово |
| Исправить hosted full monitor Unicode/monitor-only failure после первого dispatch | Готово; PR #5 merged, fixed run `26707569316` доказал monitor success |
| Добавить hosted-safe preflight для table anchor external sample sources | Готово локально; hosted proof pending |
| Набрать 7 ночей burn-in evidence и убедиться, что auto-issue path не флапает | В работе |

## 4. Validation targets спринта

1. `runTests tests/test_sample_pilot.py tests/test_formula_benchmark.py tests/test_nightly_failure_issue.py` проходит зелёно и фиксирует portability/monitor/auto-issue contracts.
2. `$env:PYTHONPATH = 'src'; .\.venv\Scripts\python.exe scripts\refresh_agent_eval.py` пересобирает generated companions без drift.
3. `$env:PYTHONPATH = 'src'; .\.venv\Scripts\python.exe scripts\validate_harness_assets.py` возвращает `status: ok` с активным feature `ci-nightly-e2e`.
4. Первый `workflow_dispatch` или schedule run `nightly-full-e2e` на GitHub публикует artifact bundle с synthetic run, formula monitor, formula gate, table-anchor run и nightly portable package либо автоматически создаёт issue с диагностикой.
5. Hosted monitor regression repair: `.\.venv\Scripts\python.exe -m unittest tests.test_formula_benchmark -v`, cp1252 reproducer `scripts\run_formula_benchmark.py samples\formula-benchmark.manifest.jsonl --no-thresholds`, focused `ruff` и `pyright` по `formula_benchmark` slice проходят зелёно.
6. Hosted table-source guard: workflow preflight на `samples\manifest.table-anchors.ci.jsonl` возвращает `available=true` при локальных sources и `available=false` + `skipped_missing_input` artifact при missing external sources; `git diff --check` зелёный.

## 5. Риски спринта

- GitHub-hosted runner не видит внешний `D:\ФСНБ\...` corpus, поэтому full formula manifest в nightly идёт в monitor-only режиме без thresholds, а required gate пока держится на CI-safe subset.
- `agent_id` для failure issue будет точным только для PR, где заполнен новый template field; для старых merges helper честно падает назад на `head_ref`, затем author login.
- Exit спринта зависит не от локального validation, а от 7-night burn-in/auto-issue evidence на GitHub.
- First dispatch runs `26707002316` и `26707185880` уже доказали auto-issue path и открыли issue #4, но также выявили hosted Windows stdout/monitor-only bug: non-ASCII JSON падал под cp1252, а `--no-thresholds` возвращал nonzero на monitor drift до CI-safe required gate. Локальный repair pending merge в `agent/s9-2-nightly-monitor-fix`.
- PR #5 auto-merged после зелёного Windows CI run `26707476363`; fixed nightly run `26707569316` прошёл full formula monitor и CI-safe formula gate, но упал на table anchor source staging: локальные `runs\s23-table-anchors-input\sample_*.pdf` не git-tracked и недоступны hosted checkout. Новый guard должен сделать этот hosted gap явным artifact signal, а не blocking crash.
- Для `S9.3` локальный workflow/script proof уже есть, но первый hosted `v*` tag run ещё не зафиксирован в state layer, поэтому wave W9 остаётся открытой до GitHub evidence.
- Параллельный локальный `S5.1` follow-up по `gate-metod-1-pr` больше не blocked: предоставленный source DOCX `D:\Документы\ФСНБ\Документы\для парсера\Российские\metod\Приказ Минстроя России от 09.01.2024 N 1_пр  Об утверждении.docx` и rendered WMF доказали formulas `(10)` и `(13)`, а cold rerun `runs\formula-debug-1pr-source-fresh\runs\20260531T072130Z` закрыл документ до `49/49` `calc_expr` и `26/49` native. Для targeted benchmark proof важно помнить, что reuse одного и того же `output_root` может вернуть stale case через `cache_status: hit`.

## 6. Критерий выхода

Спринт закрыт, когда hosted nightly contour либо проходит 7 ночей подряд, либо детерминированно открывает диагностический issue со ссылкой на failing run и latest merged PR context без ручного вмешательства.

## 7. Следующий operational focus

1. Смержить fix branch `agent/s9-2-nightly-table-source-guard`, чтобы hosted nightly сохранял table-source preflight artifact и продолжал build/package steps при отсутствующих external sample PDFs.
2. Повторить GitHub run `nightly-full-e2e` через `workflow_dispatch` на новом `main`, затем зафиксировать artifact/issue evidence в state layer.
3. Снять первый hosted proof для `.github/workflows/release.yml`: после успешного появления workflow на `main` push `v*` tag должен опубликовать GitHub Release с zip, checksum и notes из `CHANGELOG.md`.
4. Держать `agent_id` field обязательной частью agent PR closeout, чтобы auto-issue path перестал зависеть от fallback inference.
5. Пока hosted proof по S9.x идёт отдельно на GitHub, локально уже закрыты Wave 3 и весь Wave 4 (`S4.1`-`S4.3`), а `S5.1` теперь закрыл девять `1/пр` data-driven slices: work-time/wage/participation formulas `(9)`-`(13)`, average/resource-cost formulas `(24)` и `(25)`, technical-cost family `(15)`, `(17)`, `(19)`, `(20)` и `(22)`, cameral participation formulas `(35)` и `(36)`, additional-cost formula `(37)`, estimated-work participation formulas `(38)` и `(39)` и estimated-work cost formulas `(42)` и `(43)` с сохранённым canonical known-pattern sync.
6. Локальный formula backlog для `gate-metod-1-pr` теперь закрыт: cold rerun `runs\formula-debug-1pr-source-fresh\runs\20260531T072130Z` даёт `49/49` `calc_expr` units и `26/49` native formulas, поэтому следующий независимый local follow-up, если он потребуется до GitHub evidence, надо выбирать уже вне этого `1/пр` residue slice.
7. Реальный внешний blocker сейчас только GitHub-hosted nightly/tag evidence для `S9.2/S9.3`; source DOCX больше не является локальным ограничением.
