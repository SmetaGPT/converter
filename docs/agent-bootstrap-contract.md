# Agent Bootstrap Contract

Дата: 2026-05-23
Статус: active

## 1. Назначение

Bootstrap contract нужен, чтобы новая или продолженная сессия быстро восстанавливала рабочий контекст без broad search.

## 2. Обязательный cold-start

Для любой кросс-модульной, многошаговой или resume-задачи:

1. Прочитать `docs/current-status.md`.
2. Прочитать `docs/current-sprint.md`.
3. Прочитать `docs/release-status.md`.
4. Прочитать `AGENTS.md` и проверить routing/validation expectations.
5. Прочитать `docs/agent-feature-spine.json`, если задача затрагивает harness, state, process layer или ключевые product-capabilities конвертера.
6. Прочитать relevant checkpoint и relevant repo-memory notes, если они есть.

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

1. затронутые `feature_id` из `docs/agent-feature-spine.json`;
2. локальную гипотезу;
3. cheap disconfirming check;
4. focused validation target.

Если задача меняет capability, declared scope или verification evidence, это должно быть отражено в `docs/agent-feature-spine.json` при closeout.

## 5. Выбор validation target

До первой substantive правки нужно зафиксировать:

1. локальную гипотезу;
2. cheap disconfirming check;
3. focused validation target.

Предпочтительный порядок проверки:

1. узкий поведенческий check;
2. узкий unittest;
3. узкий compile/lint/typecheck;
4. только если это docs/process task без исполнимого check — structured validator или diff sanity check.

## 6. Выход cold-start

Cold-start считается завершённым, когда понятно:

1. какой active scope у задачи;
2. где находится owning surface;
3. какие `feature_id` затрагиваются;
4. чем будет проверяться первая правка;
5. какие state files и entries в `docs/agent-feature-spine.json` придётся обновить при closeout.
