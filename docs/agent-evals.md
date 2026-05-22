# Agent Evals

Дата: 2026-05-22
Статус: active

## 1. Назначение

Eval loop нужен, чтобы оценивать качество агентной работы по явным критериям, а не по впечатлению от последнего ответа.

## 2. Источники оценки

| Источник | Роль |
| --- | --- |
| docs/agent-eval-tasks.md | Набор типовых сценариев |
| docs/agent-telemetry-log.md | Фактические сигналы по validation и state update |
| docs/current-status.md | Проверка качества state hygiene |
| docs/agent-quality-scorecard.md | Сводный baseline и текущие оценки |
| docs/agent-regressions.md | Повторяющиеся failure modes |

## 3. Grading criteria

| Критерий | Вопрос | Шкала |
| --- | --- | --- |
| Context | Агент быстро и правильно понял текущее состояние? | 0-2 |
| Correctness | Выводы и изменения технически верны? | 0-2 |
| Completeness | Задача закрыта end-to-end, а не частично? | 0-2 |
| Validation | Был ли narrow validation target и факт проверки? | 0-2 |
| State update | Обновлены ли status, sprint, telemetry и release state при необходимости? | 0-2 |
| Routing | Была ли задача направлена в корректный режим? | 0-2 |
| Closeout | Был ли нормальный handoff и residual risk? | 0-2 |

Максимум за задачу: 14 баллов.

## 4. Интерпретация результата

| Баллы | Интерпретация |
| --- | --- |
| 12-14 | Хороший проход без существенных process gaps |
| 9-11 | Рабочий результат, но есть process debt |
| 6-8 | Задача выполнена нестабильно, нужен review процесса |
| 0-5 | Серьёзный провал, нужен regression entry и correction |

## 5. Минимальный weekly eval loop

1. Выбрать 3-5 задач из разных категорий.
2. Оценить их по критериям выше.
3. Зафиксировать recurring failures.
4. Проверить, нужно ли изменить prompts, hooks, AGENTS или memory discipline.
5. Обновить scorecard.

## 6. Self-review после задачи

После каждой нетривиальной задачи агент должен коротко ответить:

1. Что сработало.
2. Где был лишний поиск или ремонт.
3. Не был ли пропущен validation или state update.
4. Нужен ли новый memory note или change-log entry.

Подробный шаблон: docs/agent-self-review-template.md.
