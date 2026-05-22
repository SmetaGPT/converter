# Agent Instruction Change Log

Дата инициализации: 2026-05-22
Статус: active

## 1. Назначение

Change log нужен, чтобы procedural memory менялась управляемо, а не спонтанно.

## 2. Правило внесения изменений

Изменение hooks, prompts, AGENTS или routing считается оправданным, если:

1. есть recurring failure или повторяющийся friction point;
2. изменение адресует конкретную проблему;
3. можно объяснить ожидаемый эффект;
4. изменение зафиксировано в этом журнале.

## 3. Журнал изменений

| Дата | Область | Изменение | Основание |
| --- | --- | --- | --- |
| 2026-05-22 | AGENTS.md | Добавлен startup contract для обязательного чтения state layer | Sprint 1: нужен стабильный cold-start |
| 2026-05-22 | Hooks и lifecycle docs | Добавлены pre-task, pre-edit, post-edit, post-task, guardrails и stop budgets | Sprint 3: нужен детерминированный workflow |
| 2026-05-22 | Routing | Добавлены specialist agents и routing matrix | Sprint 4: нужно разделить research, implementation, review и release |

## 4. Change request template

- Дата:
- Наблюдаемый recurring failure:
- Предлагаемое изменение:
- Ожидаемый эффект:
- Какие документы или assets затрагиваются:
