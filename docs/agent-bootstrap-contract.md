# Agent Bootstrap Contract

Дата: 2026-05-23
Статус: active

## 1. Назначение

Bootstrap contract нужен, чтобы новая или продолженная сессия быстро восстанавливала рабочий контекст без broad search.

## 2. Обязательный cold-start

Для любой release-, resume- или действительно кросс-модульной задачи:

1. Прочитать `docs/agent-working-state.v1.json`.
2. Прочитать `docs/state-snapshot.md`.
3. Если задача меняет state/release/process layer, продолжает незавершённую работу или snapshot показывает релевантный blocker/gate, дочитать только нужные секции в `docs/current-status.md`, `docs/current-sprint.md` и `docs/release-status.md`.
4. Прочитать `AGENTS.md` и проверить routing/validation expectations.
5. Прочитать `docs/agent-feature-spine.json`, если задача затрагивает harness, state, process layer или declared capability.
6. Прочитать relevant checkpoint и relevant repo-memory notes, если они есть и нужны текущему scope.

Для локальной однофайловой, narrow bugfix или short explanation задачи действует fast path: начинать с named file/symbol/test/error и не читать полный state layer, пока локальный маршрут не показал, что owning surface шире.

## 3. Runtime reacquire

Минимум для Windows Document Converter:

1. Рабочая директория: корень репозитория.
2. Основной интерпретатор: `.venv\Scripts\python.exe`.
3. Базовые команды:
   - full tests: `.\.venv\Scripts\python.exe -m unittest discover -v`
   - OCR preflight: `.\.venv\Scripts\python.exe -m doc_converter.cli check-ocr`
   - synthetic e2e: `.\.venv\Scripts\python.exe scripts\run_synthetic_e2e.py --clean`
   - harness docs check: `.\.venv\Scripts\python.exe scripts\validate_harness_assets.py`

## 4. Выбор validation target

До первой substantive правки нужно зафиксировать:

1. затронутые `feature_id` из `docs/agent-feature-spine.json`, если задача действительно меняет capability/process/state contract;
2. локальную гипотезу;
3. cheap disconfirming check;
4. focused validation target.

Если задача меняет capability, declared scope или verification evidence, это должно быть отражено в `docs/agent-feature-spine.json` при closeout.

Предпочтительный порядок проверки:

1. узкий поведенческий check;
2. узкий unittest;
3. узкий compile/lint/typecheck;
4. только если это docs/process task без исполнимого check — structured validator или diff sanity check.

## 5. Выход cold-start

Cold-start считается завершённым, когда понятно:

1. какой active scope у задачи;
2. где находится owning surface;
3. какие `feature_id` затрагиваются;
4. чем будет проверяться первая правка;
5. какие state files и entries в `docs/agent-feature-spine.json` придётся обновить при closeout.
