# Current Sprint

Последнее обновление: 2026-05-29
Активный спринт: S2.1 — Split converters/docx.py
Статус: completed

Предыдущий приоритетный tranche: S1.3 — Agent run metadata + universal validator
Статус wave W2: in_progress

## 1. Цель спринта

Убрать DOCX monolith `src/doc_converter/converters/docx.py`, перевести route на smaller package modules и сохранить текущий public API/import surface для `runner`, `formula_recognition` и regression tests.

## 2. Артефакты спринта

- src/doc_converter/converters/docx/__init__.py
- src/doc_converter/converters/docx/pipeline.py
- src/doc_converter/converters/docx/inline_glyph.py
- src/doc_converter/converters/docx/formulas/__init__.py
- src/doc_converter/converters/docx/formulas/text.py
- src/doc_converter/converters/docx/formulas/wmf.py
- tests/test_docx_converter.py
- tests/test_cli_smoke.py
- tests/test_formula_recognition.py
- docs/current-status.md
- docs/current-sprint.md
- docs/production-roadmap.md
- docs/release-status.md
- docs/agent-feature-spine.json
- docs/agent-telemetry-log.md
- docs/agent-telemetry.v1.jsonl

## 3. Задачи спринта

| Задача | Статус |
| --- | --- |
| Заменить `src/doc_converter/converters/docx.py` на package `converters/docx/` | Готово |
| Разнести pipeline, inline glyph и formula helpers по smaller modules | Готово |
| Сохранить public imports через `src/doc_converter/converters/docx/__init__.py` | Готово |
| Обновить monkeypatch targets в DOCX tests там, где pipeline зовёт submodule-local helper | Готово |
| Подтвердить focused и full validation без behavioral drift | Готово |
| Зафиксировать remaining file-size debt как следующий architecture backlog | Готово |

## 4. Validation targets спринта

1. `\.venv\Scripts\python.exe -m unittest tests.test_docx_converter` прошёл зелёно: 37 tests, OK.
2. `\.venv\Scripts\python.exe -m unittest tests.test_cli_smoke tests.test_formula_recognition` прошёл зелёно: 31 test, OK.
3. `$env:PYTHONPATH = 'src'; .\.venv\Scripts\python.exe -m unittest discover -s tests` прошёл зелёно: 142 tests, OK.
4. `\.venv\Scripts\python.exe -m ruff check src tests scripts` прошёл зелёно.
5. `\.venv\Scripts\python.exe -m pyright` прошёл зелёно: 0 errors, 0 warnings.
6. `Get-ChildItem src\doc_converter\converters\docx -Recurse -File -Include *.py | Where-Object { (Get-Content $_.FullName).Length -gt 800 }` вернул пустой результат.

## 5. Риски спринта

- Package-level re-export сохраняет compatibility, но internal monkeypatching теперь должно указывать на реальные submodule symbols, если implementation импортирует helper напрямую.
- Repo-wide file-size debt после закрытия S2.1 остаётся в `src/doc_converter/runner.py` и `src/doc_converter/formula_benchmark.py`; это уже не DOCX monolith risk, а следующий architecture tranche.
- Full unittest discover в этом shell-контуре надёжнее запускать с явным `PYTHONPATH=src`, чтобы discovery не терял import context для `src/`.

## 6. Критерий выхода

Спринт закрыт: монолит `src/doc_converter/converters/docx.py` удалён, DOCX route работает через package `src/doc_converter/converters/docx/`, публичный import surface сохранён через `__init__.py`, package scope больше не содержит файлов > 800 строк, а focused/full gates остаются зелёными.

## 7. Следующий operational focus

1. Начать S2.2 `Split runner.py`.
2. После S2.2 вывести `src/doc_converter/formula_benchmark.py` из oversize-состояния отдельным architecture slice.
3. Затем вернуться к measured table benchmark backlog и richer DOCX table semantics.
4. Продолжать выполнять prompt `.github/prompts/execute-production-roadmap-autonomous.prompt.md`: sprint → focused validation → state update → commit → push.
