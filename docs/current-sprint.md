# Current Sprint

Последнее обновление: 2026-05-28
Активный спринт: S1.1 — Contracts catalog
Статус: completed

Предыдущий приоритетный tranche: S0.1 — Зелёный baseline и строгий линт
Статус wave W1: in progress

## 1. Цель спринта

Закрыть первый Wave 1 спринт production roadmap: зафиксировать downstream-facing stable v1 contracts, добавить недостающий `formula-recognition.v1` schema contract, защитить schema drift snapshot-тестом и связать catalog с downstream handoff.

## 2. Артефакты спринта

- docs/contracts.md
- docs/downstream-handoff.md
- docs/agent-feature-spine.json
- schemas/formula-recognition.v1.schema.json
- schemas/__snapshot__/stable-contracts.v1.json
- tests/test_contracts_stability.py
- scripts/validate_run_package.py
- pyproject.toml
- docs/current-status.md
- docs/current-sprint.md
- docs/production-roadmap.md
- docs/agent-telemetry.v1.jsonl

## 3. Задачи спринта

| Задача | Статус |
| --- | --- |
| Добавить `docs/contracts.md` с producer → consumer matrix | Готово |
| Залинковать contracts catalog из `docs/downstream-handoff.md` | Готово |
| Добавить `formula-recognition.v1.schema.json` | Готово |
| Зафиксировать stable schema fingerprints в `schemas/__snapshot__/` | Готово |
| Добавить `tests/test_contracts_stability.py` | Готово |
| Расширить `validate_run_package.py` на `formula-recognition.jsonl` sidecars | Готово |
| Зарегистрировать `contracts-stable-v1` в feature spine | Готово |

## 4. Validation targets спринта

1. `runTests tests/test_contracts_stability.py` прошёл зелёно.
2. `\.venv\Scripts\python.exe -m unittest tests.test_contracts_stability` прошёл зелёно: 3 tests, OK.
3. `\.venv\Scripts\python.exe scripts\validate_run_package.py runs\formula-benchmark\runs\20260525T175329Z\cases\anchor-421-pr\output\runs\20260525T175329Z` вернул `status: ok`.
4. `\.venv\Scripts\python.exe scripts\validate_harness_assets.py` прошёл зелёно после refresh generated companions.
5. `\.venv\Scripts\python.exe -m unittest discover` прошёл зелёно: 133 tests, OK.
6. `\.venv\Scripts\python.exe -m ruff check src tests scripts` прошёл зелёно.
7. `\.venv\Scripts\python.exe -m pyright` прошёл зелёно: 0 errors, 0 warnings.
8. `get_errors` по S1.1 touched files не показывает ошибок после type annotation fix.

## 5. Риски спринта

- Stable schema snapshot intentionally requires explicit hash update when a v1 contract changes; breaking shape changes должны идти через `*.v2.schema.json`.
- `chunk-source.v1` пока оставляет `additionalProperties: true`, потому что downstream annotations ещё развиваются отдельно от converter runtime.
- `validate_run_package.py` теперь имеет intentional repo-local `src` bootstrap; ruff `E402` для этого standalone script добавлен в уже существующий per-file ignore bucket.

## 6. Критерий выхода

Спринт закрыт: stable downstream contracts catalog существует и залинкован из handoff, `formula-recognition.v1` sidecar получил schema validation, drift snapshot-тест зелёный, run-package validator проверяет новый sidecar contract при наличии, state/telemetry синхронизированы через harness validator.

## 7. Следующий operational focus

1. Начать S1.2 `Known formula patterns → data` после commit/push S1.1.
2. При переносе known MathType patterns сохранить текущую benchmark/stability semantics и не менять formula recovery behavior без focused tests.
3. Продолжать выполнять prompt `.github/prompts/execute-production-roadmap-autonomous.prompt.md`: sprint → focused validation → state update → commit → push.
