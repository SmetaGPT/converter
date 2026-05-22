# Agent Lifecycle

Дата: 2026-05-22
Статус: active

## 1. Цель

Lifecycle нужен, чтобы каждая нетривиальная задача проходила через один и тот же контур: понять, локализовать, изменить, проверить, обновить state, закрыть handoff.

## 2. Канонический поток

1. Pre-task: прочитать state layer и relevant memory.
2. Localize: выбрать конкретный anchor и сузить область.
3. Hypothesize: сформулировать локальную проверяемую гипотезу.
4. Pre-edit: зафиксировать validation target до первого edit.
5. Edit: внести минимальное изменение по текущей гипотезе.
6. Post-edit: сразу выполнить focused validation.
7. Repair or confirm: либо локально исправить тот же slice, либо зафиксировать успех.
8. Post-task: обновить state, telemetry, memory и closeout.

## 3. Hook mapping

| Фаза | Hook | Обязательный выход |
| --- | --- | --- |
| Старт задачи | .github/hooks/pre-task.json | scope, active sprint, validation intent |
| Перед первой правкой | .github/hooks/pre-edit.json | hypothesis, disconfirming check, validation target |
| После правки | .github/hooks/post-edit.json | validation result |
| Закрытие задачи | .github/hooks/post-task.json | state update, telemetry, memory update, handoff |

## 4. Обязательные инварианты

1. Без конкретного anchor нельзя начинать широкий edit.
2. Без локальной гипотезы нельзя открывать первую substantive правку.
3. После первой substantive правки следующая обязательная операция — validation.
4. Без state update задача считается закрытой не полностью.

## 5. Что считается focused validation

Предпочтительный порядок:

1. самый узкий поведенческий check;
2. узкий тест по затронутому срезу;
3. узкий compile, lint или typecheck;
4. только если ничего нет — diff-oriented sanity check.

## 6. Closeout minimum

При закрытии нетривиальной задачи должны быть зафиксированы:

- что сделано;
- как проверено;
- какие state files изменены;
- какой следующий шаг или residual risk;
- есть ли новый validated learning.
