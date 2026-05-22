# Agent Tool Interface Audit

Дата: 2026-05-22
Статус: initial audit

## 1. Цель

Зафиксировать, где агентный инструментальный интерфейс уже понятен, а где нужны дополнительные контракты, path rules и hook reminders.

## 2. Наблюдения по текущему toolset

| Инструмент | Наблюдение | Что делать |
| --- | --- | --- |
| apply_patch | Хорошо подходит для точечных правок и создания файлов | Сохранять правило: все ручные edits идут через apply_patch |
| get_errors | Полезен как узкая валидация даже для markdown-only слоёв | Встроить в post-edit discipline для docs/process changes |
| list_dir | Быстро подтверждает фактическую структуру | Использовать как cheap check при создании артефактов |
| memory | Repo-memory живёт отдельно от workspace files | Явно различать shared docs и local memory scopes |
| run_in_terminal | Полезен для runtime checks, но может давать шумный вывод | Использовать только когда нужен реальный command-level сигнал |
| read_file | Требует диапазоны и лучше работает на конкретных anchor files | Избегать широкого чтения без гипотезы |

## 3. Выявленные friction points

1. Markdown linting даёт структурные ошибки даже на process docs, поэтому docs нужно валидировать так же дисциплинированно, как код.
2. На Windows абсолютные пути в инструментах безопаснее и менее двусмысленны.
3. Repo-memory нельзя воспринимать как обычную папку workspace: у неё свой lifecycle и правила записи.
4. Без явных prompts агент может забыть обновить state layer после успешной задачи.

## 4. Исправления, введённые этим спринтом

- pre-task hook требует чтения state layer;
- pre-edit hook требует локальную гипотезу и validation target;
- post-edit hook запрещает widening scope до validation;
- post-task hook требует state update, telemetry и memory update;
- reusable prompts поддерживают kickoff, closeout и blocker handling.

## 5. Следующие улучшения

- связать routing со specialist agents;
- добавить instruction refinement log по recurring failures;
- расширить tool audit на реальные code paths после появления backend/frontend слоёв.
