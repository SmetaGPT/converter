# Agent Handoffs

Дата: 2026-05-22
Статус: active

## 1. Цель

Handoff нужен, чтобы следующая сессия продолжила работу без повторного broad search.

## 2. Когда handoff обязателен

- задача не завершена в текущей сессии;
- есть blocker или approval gate;
- изменён процессный или release-critical слой;
- задача завершена, но есть явный следующий шаг или residual risk.

## 3. Минимальный пакет handoff

| Компонент | Смысл |
| --- | --- |
| Цель | Что должно быть достигнуто |
| Текущая гипотеза или итог | На каком понимании остановились |
| Подтверждённые факты | Что уже известно и проверено |
| Touched surface | Какие файлы или области затронуты |
| Validation result | Что уже проверено |
| Blocker или residual risk | Что мешает или что осталось рискованным |
| Next step | С чего продолжать |
| Approval state | Нужно ли внешнее разрешение |

## 4. Формы handoff

1. Обновление state layer.
2. Task checkpoint.
3. Closeout summary.
4. Release-ready handoff через release-status и checklist.

## 5. Антипаттерны

- handoff в виде длинного narrative без next step;
- описание изменений без validation result;
- отсутствие explicit blocker;
- reliance only on chat history.
