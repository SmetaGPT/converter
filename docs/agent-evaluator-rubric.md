# Agent Evaluator Rubric

Дата: 2026-05-23
Статус: active

## 1. Назначение

Rubric нужен для проверки качества завершения задачи по внешним критериям, а не по субъективному ощущению готовности.

## 2. Шкала

Каждый критерий оценивается по шкале 0-2:

- `0` — критерий не выполнен или нет evidence;
- `1` — выполнен частично или с заметными пробелами;
- `2` — выполнен полно и подтверждён evidence.

## 3. Критерии

| Критерий | Что оценивается |
| --- | --- |
| Scope control | Была ли задача локализована и удержан ли bounded slice |
| Feature traceability | Привязаны ли работа и closeout к затронутым `feature_id` и evidence paths |
| Hypothesis quality | Была ли явная локальная гипотеза и cheap disconfirming check |
| Validation quality | Был ли после правки выполнен самый узкий подходящий executable check |
| Evidence quality | Есть ли проверяемые артефакты, а не только narrative summary |
| State hygiene | Обновлены ли current-status, current-sprint, telemetry и при необходимости release-status |
| Closeout quality | Зафиксированы ли residual risks, next step и resume breadcrumbs |

## 4. Интерпретация

| Сумма | Интерпретация |
| --- | --- |
| 0-4 | weak closeout |
| 5-9 | acceptable with gaps |
| 10-14 | strong closeout |

## 5. Минимальное правило

Задача не должна считаться сильным closeout, если отсутствует executable validation, state update или traceability до затронутых `feature_id`.
