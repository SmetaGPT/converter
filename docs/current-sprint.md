# Current Sprint

Последнее обновление: 2026-05-28
Активный спринт: S1.2 — Known formula patterns → data
Статус: completed

Предыдущий приоритетный tranche: S1.1 — Contracts catalog
Статус wave W1: in progress

## 1. Цель спринта

Закрыть второй Wave 1 спринт production roadmap: убрать hard-coded known MathType formula table из `docx.py`, перенести recovery patterns в versioned JSON data, добавить schema/validator/export tooling и сохранить текущий DOCX formula behavior.

## 2. Артефакты спринта

- src/doc_converter/converters/docx.py
- src/doc_converter/formulas/__init__.py
- src/doc_converter/formulas/known.py
- src/doc_converter/formulas/known-patterns.v1.json
- samples/formulas/known-patterns.v1.json
- schemas/formula-known-patterns.v1.schema.json
- scripts/export_known_formulas.py
- scripts/validate_known_formulas.py
- tests/test_known_formula_patterns.py
- pyproject.toml
- docs/current-status.md
- docs/current-sprint.md
- docs/production-roadmap.md
- docs/release-status.md
- docs/agent-feature-spine.json
- docs/agent-telemetry.v1.jsonl

## 3. Задачи спринта

| Задача | Статус |
| --- | --- |
| Завести `formula-known-patterns.v1` schema | Готово |
| Перенести noisy-form recovery в JSON | Готово |
| Перенести known formula representations в JSON | Готово |
| Перенести MathType WMF signature rules в JSON | Готово |
| Добавить package-data copy и loader `doc_converter.formulas.known` | Готово |
| Добавить export/sync script | Готово |
| Добавить validator script | Готово |
| Добавить focused tests for known formula patterns | Готово |
| Сохранить старый suffix predicate как `ends_with` data condition | Готово |

## 4. Validation targets спринта

1. `\.venv\Scripts\python.exe scripts\validate_known_formulas.py` прошёл зелёно: canonical/package data schema-valid и in sync.
2. `\.venv\Scripts\python.exe -m unittest tests.test_known_formula_patterns tests.test_docx_converter` прошёл зелёно: 44 tests, OK.
3. `\.venv\Scripts\python.exe -m unittest discover` прошёл зелёно: 140 tests, OK.
4. `\.venv\Scripts\python.exe -m ruff check src tests scripts` прошёл зелёно.
5. `\.venv\Scripts\python.exe -m pyright` прошёл зелёно: 0 errors, 0 warnings.
6. `get_errors` по S1.2 touched files не показывает ошибок после narrowing/type cleanup.

## 5. Риски спринта

- Canonical data и package-data copy должны оставаться синхронизированными; `scripts/validate_known_formulas.py` проверяет drift, а `scripts/export_known_formulas.py` выполняет copy из canonical source.
- JSON migration сохраняет существующий known-pattern слой, но не заменяет будущую generalized WMF parser работу и не расширяет benchmark thresholds сам по себе.
- При добавлении новых rules нельзя упрощать code predicates до одного `contains_all`: suffix/other predicate details должны явно попадать в data contract.

## 6. Критерий выхода

Спринт закрыт: known formula patterns больше не расширяются через hard-coded `if normalized == ...` table в `docx.py`; JSON data валидируется schema, package copy включён в distribution, focused DOCX regressions подтверждают отсутствие behavioral drift, state/telemetry синхронизируются через harness validator перед коммитом.

## 7. Следующий operational focus

1. Начать S1.3 `Agent run metadata + universal validator` после commit/push S1.2.
2. Для S1.3 держать backward compatibility с существующими run packages и validator scripts.
3. Продолжать выполнять prompt `.github/prompts/execute-production-roadmap-autonomous.prompt.md`: sprint → focused validation → state update → commit → push.
