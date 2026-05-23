# Agent Regressions

Дата: 2026-05-23
Статус: active

## 1. Failure taxonomy

| Код | Тип провала | Признак |
| --- | --- | --- |
| R01 | Lost context | Агент не смог быстро восстановить состояние задачи |
| R02 | Skipped validation | После edit не было focused validation |
| R03 | Wrong routing | Задача пошла не тем режимом |
| R04 | Stale memory | Решение опиралось на устаревший learning |
| R05 | Over-search | Поиск продолжался после достаточной локализации |
| R06 | State drift | Изменения сделаны, но status layer не обновлён |
| R07 | Weak handoff | Следующая сессия не может продолжить без broad search |
| R08 | Retroactive traceability debt | Историческую задачу приходится вручную маппить к `feature_id` и evidence paths |
| R09 | Proxy-only eval confidence | Generated snapshot выглядит сильным, но qualitative sample ещё не проведён |

## 2. Regression log

| Дата | Код | Сценарий | Причина | Recovery pattern | Статус |
| --- | --- | --- | --- | --- | --- |
| 2026-05-22 | R02 | Первые baseline docs прошли через edit с markdown lint defects | В docs-only срезе не был заранее учтён markdown style contract | Сразу запускать get_errors по touched .md files после первого docs edit | Mitigated |
| 2026-05-23 | R08 | Первый weekly review потребовал retrospective feature mapping для ранних задач Sprint 1/3/4 и real E2E slice | Эти задачи были выполнены до machine-readable feature spine и обязательной traceability discipline | Держать `feature_id` внутри bootstrap/sprint/checkpoint flow и делать backfill для legacy slices только один раз | Mitigated |
| 2026-05-23 | R09 | Generated weekly snapshot сначала выглядел сильнее, чем позволяла telemetry coverage | Weekly eval companion был собран раньше, чем historical structured telemetry закрыла все required feature slices | Не считать weekly loop завершённым без qualitative sample и проверки coverage gaps в generated snapshot | Mitigated |

## 3. Recovery patterns

| Тип провала | Корректирующее действие |
| --- | --- |
| Lost context | Усилить state layer или task checkpoint |
| Skipped validation | Усилить post-edit discipline и telemetry |
| Wrong routing | Уточнить routing matrix |
| Stale memory | Переписать или удалить устаревший learning |
| Over-search | Поджать stop budgets и требовать локальную гипотезу |
| State drift | Усилить post-task hook |
| Weak handoff | Заполнять checkpoint и closeout prompt |
