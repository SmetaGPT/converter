# Current Sprint

Последнее обновление: 2026-05-30
Активный спринт: S9.1 — PR-gates и branch protection
Статус: completed

Предыдущий приоритетный tranche: S7.2 — Secret scan CI
Статус: completed
Статус wave W9: in_progress

## 1. Цель спринта

Сделать merge автономным при зелёных required checks: `main` защищён branch protection, PR template требует state/telemetry closeout, а same-repo PR с label `agent:autonomous` получает auto-merge без ручного `gh pr merge`.

## 2. Артефакты спринта

- .github/PULL_REQUEST_TEMPLATE.md
- .github/workflows/windows-ci.yml
- .github/workflows/autonomous-pr-auto-merge.yml
- scripts/package-release.ps1
- scripts/validate_ocr_preflight_cli.py
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
| Зафиксировать PR template с обязательными feature/state/validation полями | Готово |
| Включить strict branch protection и required contexts на `main` | Готово |
| Довести `windows-ci` и `release-smoke` до стабильного required gate на GitHub | Готово |
| Включить label-driven auto-merge для same-repo non-draft PR | Готово |
| Синхронизировать state docs, feature spine, telemetry и generated companions | Готово |

## 4. Validation targets спринта

1. `gh api repos/SmetaGPT/converter/branches/main/protection` показывает `strict = true`, `required_approving_review_count = 0` и required contexts `secret-scan`, `lint`, `typecheck`, `unit-tests`, `harness-validator`, `formula-benchmark-gate`, `document-package-validator`, `release-smoke`.
2. `gh api repos/SmetaGPT/converter/actions/runs/26690514184` подтверждает final green bootstrap run после release-smoke hardening на GitHub.
3. Same-repo non-draft PR с label `agent:autonomous` получает `autoMergeRequest` через `.github/workflows/autonomous-pr-auto-merge.yml` и merge-ится автоматически после всех required checks.
4. `$env:PYTHONPATH = 'src'; .\.venv\Scripts\python.exe scripts\refresh_agent_eval.py` пересобирает generated companions без drift.
5. `$env:PYTHONPATH = 'src'; .\.venv\Scripts\python.exe scripts\validate_harness_assets.py` возвращает `status: ok`, `features: 42`, `validated: 42`, `telemetry_entries: 75`.

## 5. Риски спринта

- Required contexts жёстко привязаны к именам job-ов в `.github/workflows/windows-ci.yml`; любое переименование нужно синхронизировать с branch protection.
- `pull_request_target` auto-merge можно доказать только на PR, открытом после того, как workflow уже живёт на base branch; bootstrap и proof нельзя сливать в один PR.
- Nightly full e2e и release automation ещё не закрыты, поэтому после S9.1 следующий critical path смещается в S9.2/S9.3.

## 6. Критерий выхода

Спринт закрыт: `main` защищён strict required checks, PR template требует feature/state/validation closeout, а same-repo demo PR с label `agent:autonomous` merge-ится автоматически без human review и без ручной merge-команды.

## 7. Следующий operational focus

1. Открыть critical-path sprint S9.2 и запустить nightly full e2e.
2. Затем открыть S9.3 и перевести release automation на стабильный nightly/regression контур.
3. Держать required-check names и label contract синхронными с workflow definitions.
4. Держать `src/doc_converter/formula_benchmark.py` как отдельный non-critical follow-up по oversize debt.
5. После critical path продолжать measured table backlog и richer DOCX semantics.
