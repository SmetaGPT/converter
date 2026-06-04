# Agent Session Exit Checklist

Дата: 2026-05-23
Статус: active

## 1. Назначение

Checklist нужен, чтобы нетривиальная задача не закрывалась на локальной правке без validation и state hygiene.

## 2. Минимум перед closeout

1. Зафиксирована локальная гипотеза или её опровержение.
2. Выполнен хотя бы один focused validation step после последней substantive правки.
3. Если есть исполнимый узкий check, он использован вместо diff-only sanity check.
4. Зафиксированы residual risks или следующий шаг, если scope закрыт не полностью.
5. Если changed capability, scope или evidence затрагивают spine, обновлён `docs/agent-feature-spine.json`.

## 3. Обязательные обновления

После нетривиальной задачи нужно обновить:

1. `docs/state-snapshot.md`.
2. `docs/current-status.md`, если изменился operational status, blocker или done-state.
3. `docs/current-sprint.md`, если изменился active plan, validation target или blocker.
4. `docs/agent-telemetry-log.md`.
5. `docs/agent-telemetry.v1.jsonl`.
6. `docs/release-status.md`, если изменился release contour или declared scope.
7. `docs/agent-feature-spine.json`, если изменился capability status, coverage или evidence.
8. repo-memory, если появился новый validated learning.

## 4. Resume breadcrumbs

Если задача не завершена полностью, перед выходом нужно оставить:

1. текущий anchor;
2. последнюю validation action и результат;
3. следующий минимальный шаг;
4. touched files или owned surface.

## 5. Что считается clean exit

Сессия считается закрытой чисто, когда:

1. результат верифицирован на подходящем уровне;
2. state layer отражает факт изменений;
3. traceability до затронутых `feature_id` и evidence не потеряна;
4. следующий агент может продолжить без broad search;
5. нет завышенного статуса относительно фактической validation evidence.
