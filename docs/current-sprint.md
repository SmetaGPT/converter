# Current Sprint

Последнее обновление: 2026-05-30
Активный спринт: S7.2 — Secret scan CI
Статус: completed

Предыдущий приоритетный tranche: S7.1 — Threat model и input hardening
Статус: completed
Статус wave W7: completed

## 1. Цель спринта

Сделать leak gate обязательной частью CI: чистый git-backed репозиторный контур проходит, а искусственно вставленный API-key canary валится до merge.

## 2. Артефакты спринта

- .gitleaks.toml
- .github/workflows/windows-ci.yml
- docs/security.md
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
| Добавить required Gitleaks scan в `windows-ci` | Готово |
| Зафиксировать global allowlist только для known test fixtures и `.env.example` | Готово |
| Добавить deterministic product-specific rule для `OPENROUTER_API_KEY` / `FORMULA_RECOGNITION_API_KEY` | Готово |
| Подтвердить локально clean repo pass и synthetic git canary fail | Готово |
| Синхронизировать `docs/security.md`, roadmap, feature spine и telemetry | Готово |

## 4. Validation targets спринта

1. Official Windows Gitleaks binary локально прошёл `gitleaks git --config .gitleaks.toml --exit-code 1 .`: `clean_exit = 0`.
2. Тот же `gitleaks git --config .gitleaks.toml --exit-code 1 .` в synthetic temporary git repo с env-style synthetic canary assignment вернул `canary_exit = 1`.
3. `$env:PYTHONPATH = 'src'; .\.venv\Scripts\python.exe scripts\refresh_agent_eval.py` пересобрал generated companions без drift.
4. `$env:PYTHONPATH = 'src'; .\.venv\Scripts\python.exe scripts\validate_harness_assets.py` вернул `status: ok`, `features: 40`, `validated: 40`, `telemetry_entries: 74`.

## 5. Риски спринта

- Required secret-scan gate теперь покрывает committed git content и known fixture allowlist, но не заменяет workstation hygiene для untracked local artifacts и внешних release bundles вне git history.
- PDF/XLSX routes пока не имеют столь же явных parser-level size limits, как DOCX archive и WMF parser.
- Repo-wide file-size debt вне critical path по-прежнему локализован в `src/doc_converter/formula_benchmark.py`.

## 6. Критерий выхода

Спринт закрыт: `windows-ci` ставит Gitleaks и выполняет required git-backed secret scan `gitleaks git --config .gitleaks.toml --exit-code 1 .`, allowlist остаётся узким и покрывает только known fake fixtures/examples, clean repo проходит, а synthetic API-key canary валится.

## 7. Следующий operational focus

1. Открыть critical-path sprint S9.1 и закрыть PR-gates и branch protection.
2. Затем продолжить S9.x automation, не смешивая его с remaining measured hardening backlog.
3. После security baseline решить отдельным tranche parser-level limits для PDF/XLSX, если они станут release-critical.
4. Держать `src/doc_converter/formula_benchmark.py` как отдельный non-critical follow-up по oversize debt.
5. После critical path продолжать measured table backlog и richer DOCX semantics.
