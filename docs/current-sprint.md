# Current Sprint

Последнее обновление: 2026-05-28
Активный спринт: S0.1 — Зелёный baseline и строгий линт
Статус: completed

Предыдущий приоритетный tranche: Table benchmark anchor baseline
Статус wave W0: completed

## 1. Цель спринта

Закрыть первый спринт production roadmap: убрать нестабильный DOCX inline-glyph test baseline, зафиксировать явную ruff/pyright конфигурацию и подтвердить, что основной unittest контур снова даёт устойчивый зелёный сигнал.

## 2. Артефакты спринта

- tests/test_docx_converter.py
- src/doc_converter/converters/pdf_scan.py
- pyproject.toml
- docs/current-status.md
- docs/current-sprint.md
- docs/production-roadmap.md
- docs/agent-telemetry.v1.jsonl

## 3. Задачи спринта

| Задача | Статус |
| --- | --- |
| Очистить `INLINE_GLYPH_CACHE` перед каждым DOCX converter test | Готово |
| Стабилизировать assertion для additional inline math glyphs | Готово |
| Убрать ruff `F401` в `pdf_scan` | Готово |
| Добавить явную `[tool.ruff]` конфигурацию | Готово |
| Добавить явную `[tool.pyright]` конфигурацию | Готово |
| Подтвердить 5 подряд зелёных `unittest discover` | Готово |

## 4. Validation targets спринта

1. `runTests tests/test_docx_converter.py::test_docx_recognizes_additional_inline_math_symbol_drawings` прошёл зелёно.
2. `runTests tests/test_docx_converter.py` прошёл зелёно.
3. `\.venv\Scripts\python.exe -m unittest discover` прошёл 5 раз подряд: 130 tests, OK в каждом прогоне.
4. `\.venv\Scripts\python.exe -m ruff check src tests scripts` прошёл зелёно.
5. `\.venv\Scripts\python.exe -m pyright` прошёл зелёно: 0 errors, 0 warnings.
6. `get_errors` по `tests/test_docx_converter.py`, `src/doc_converter/converters/pdf_scan.py` и `pyproject.toml` не показывает ошибок.

## 5. Риски спринта

- `pyproject.toml` фиксирует `E501`, `W191` и `W292` как deferred formatting-only debt под `quality.lint-strict`, чтобы S0.1 не превращался в широкое переформатирование всего репозитория.
- Strict `I/UP/B/SIM` ruff families ещё не включены в blocking gate; они остаются отдельным lint-hardening follow-up, иначе спринт резко расширяется за пределы baseline stabilization.
- Tkinter в unittest всё ещё печатает benign `ThemeChanged` stderr после destroy, но тесты завершаются `OK`; это не блокирует S0.1.

## 6. Критерий выхода

Спринт закрыт: baseline tests устойчиво зелёные, ruff/pyright gates проходят, DOCX inline-glyph flake больше не валит full `unittest discover`, state/telemetry должны быть синхронизированы через harness validator перед коммитом.

## 7. Следующий operational focus

1. Начать Wave 1 roadmap: S1.1 `Contracts catalog`.
2. Не расширять S0.1 deferred lint debt без отдельного formatting/lint-hardening спринта.
3. Продолжать выполнять prompt `.github/prompts/execute-production-roadmap-autonomous.prompt.md`: sprint → focused validation → state update → commit → push.
