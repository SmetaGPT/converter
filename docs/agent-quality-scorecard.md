# Agent Quality Scorecard

Дата инициализации: 2026-05-22
Статус: baseline initialized

## 1. Назначение

Scorecard нужен как единая точка, в которой видны:

- базовый уровень процесса до внедрения roadmap;
- ожидаемые изменения по спринтам;
- фактические сдвиги после появления telemetry и eval loop.

## 2. Базовые критерии качества

| Критерий | Что проверяем |
| --- | --- |
| Context reacquire | Скорость входа в задачу и корректность понимания текущего состояния |
| Execution discipline | Наличие явной гипотезы, порядка действий и stop budgets |
| Validation | Наличие focused validation и качество результата |
| State hygiene | Обновление state layer и release layer |
| Memory hygiene | Полезность и краткость новых learnings |
| Routing quality | Попадание задачи в корректный режим работы |
| Closeout quality | Наличие handoff, self-review и следующих шагов |

## 3. Baseline snapshot

| Показатель | Baseline на 2026-05-22 | Комментарий |
| --- | ---: | --- |
| Context reacquire | 1/5 | Статус приходится собирать практически с нуля |
| Execution discipline | 1/5 | Lifecycle не закреплён |
| Validation | 1/5 | Focused validation не обязателен |
| State hygiene | 0/5 | State files отсутствуют |
| Memory hygiene | 1/5 | User memory есть, repo-memory отсутствует |
| Routing quality | 0/5 | Specialist modes отсутствуют |
| Closeout quality | 0/5 | Нет handoff и release loop |

## 4. Ожидаемый дельта-профиль по спринтам

| Спринт | Основная ожидаемая дельта |
| --- | --- |
| Sprint 0 | Появляется baseline и фиксируются gaps |
| Sprint 1 | Появляется state-entry-point и telemetry |
| Sprint 2 | Repo-memory начинает снижать повторные ошибки |
| Sprint 3 | Lifecycle и validation становятся детерминированными |
| Sprint 4 | Routing уменьшает смешение режимов |
| Sprint 5 | Качество становится измеримым на eval set |
| Sprint 6 | Full-cycle delivery закрывается до release-ready состояния |

## 5. Правила обновления

1. Baseline не переписывается, а только дополняется фактами следующих спринтов.
2. Все пересчёты должны ссылаться на telemetry, checkpoints или evals.
3. Если оценка изменилась, рядом фиксируется причина изменения.

## 6. Текущий working snapshot после Sprint 4

| Показатель | Текущая оценка | Основание |
| --- | ---: | --- |
| Context reacquire | 4/5 | Есть current-status, current-sprint, release-status и checkpoint schema |
| Execution discipline | 4/5 | Есть lifecycle, hooks и stop budgets |
| Validation | 4/5 | Focused validation закреплён и уже использовался на process docs |
| State hygiene | 4/5 | State layer и telemetry ведутся последовательно |
| Memory hygiene | 4/5 | Memory model, hygiene rules и repo-memory созданы |
| Routing quality | 4/5 | Research, implementation, review и release разделены |
| Closeout quality | 3/5 | Есть closeout prompt и telemetry, но release loop ещё не завершён |

## 7. Sprint delta log

| Спринт | Изменение | Наблюдаемый эффект |
| --- | --- | --- |
| Sprint 1 | Создан state layer | Cold-start стал опираться на явные entry points |
| Sprint 2 | Создана memory discipline | Появился устойчивый knowledge layer |
| Sprint 3 | Создан deterministic lifecycle | Validation и risky actions стали формализованы |
| Sprint 4 | Добавлен routing | Режимы работы разделены по ролям |

## 8. Следующий шаг

После Sprint 5 этот документ должен получить первый score-based review на реальном наборе задач из eval set.
