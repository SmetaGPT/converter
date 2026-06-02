# Agent Quality Scorecard

Дата инициализации: 2026-05-22
Статус: baseline initialized, structured companion active, first weekly review completed

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
| Closeout quality | 4/5 | Есть closeout prompt, telemetry, generated weekly eval и первый completed qualitative review |

## 7. Sprint delta log

| Спринт | Изменение | Наблюдаемый эффект |
| --- | --- | --- |
| Sprint 1 | Создан state layer | Cold-start стал опираться на явные entry points |
| Sprint 2 | Создана memory discipline | Появился устойчивый knowledge layer |
| Sprint 3 | Создан deterministic lifecycle | Validation и risky actions стали формализованы |
| Sprint 4 | Добавлен routing | Режимы работы разделены по ролям |

## 8. Первый qualitative weekly review

На 2026-05-23 проведён первый полный weekly review поверх generated snapshot, а не только поверх proxy signals.

Sampling summary:

- Sprint 1 state foundation: `12/14`;
- Sprint 3 workflow hooks: `12/14`;
- Sprint 4 specialist routing: `12/14`;
- SP folder e2e: `13/14`;
- Generated weekly eval companion: `14/14`.

Средний qualitative результат: `12.6/14`, что соответствует strong closeout по действующему rubric.

Корректировка assumptions:

1. `Closeout quality` поднят до `4/5`, потому что weekly eval теперь замкнут end-to-end: есть generated companions, telemetry coverage закрыта и выполнен первый complete review loop.
2. `Validation`, `Execution discipline` и `Routing quality` пока не поднимаются выше текущего значения, потому что ранние исторические задачи всё ещё несут retrospective traceability debt.
3. Для этого репозитория generated weekly snapshot теперь можно использовать как основной weekly shortcut, но только вместе с lightweight qualitative sampling, когда затрагивается harness/process слой.

## 9. Structured companion

Machine-readable companion: `docs/agent-quality-scorecard.v1.json`.

Текущий observed snapshot из structured telemetry:

- as_of_date: `2026-05-31`;
- telemetry entries: `105`;
- validated features in spine: `56`;
- referenced features in telemetry: `57`;
- observed signals: `Validation 5/5, State hygiene 5/5, Feature traceability 5/5, Feature coverage 5/5`.

Этот companion не заменяет qualitative review и eval loop. Он нужен как быстрый machine-readable слой для weekly checks и CI-backed drift detection.
