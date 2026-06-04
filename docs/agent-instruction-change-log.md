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
| 2026-06-03 | AGENTS.md, bootstrap docs | Startup contract переведён на `docs/state-snapshot.md` и fast path для локальных задач | Реальный token spend показал, что полный state layer слишком дорог для однофайловых и коротких задач |
| 2026-06-03 | scripts, .vscode | Добавлены `scripts/classify_agent_scope.py` и task `Agent: classify scope` для автоматического выбора fast path против full state startup | После перевода на state snapshot следующий recurring friction point остался в ручном выборе scope на старте задачи |
| 2026-06-03 | scripts, validator, state docs | Добавлены `scripts/build_state_snapshot.py` и drift-check в `scripts/validate_harness_assets.py` для автоматической сборки `docs/state-snapshot.md` | После cheap startup routing следующий recurring friction point остался в ручной синхронизации короткого state entry point |
| 2026-06-03 | scripts, observability docs | Добавлен `scripts/estimate_context_tokens.py` для rough оценки startup/context budget по файлам и тексту | Доступные VS Code/Copilot debug logs не отдают exact prompt/completion token usage, поэтому для process tuning нужен локальный estimator вместо ложной точности |
| 2026-06-03 | scripts, observability docs | В `scripts/estimate_context_tokens.py` добавлен excerpt-mode по первым N строкам | Full-file оценки полезны для upper bound, но для типичного agent read budget нужен более реалистичный excerpt-based mode |
| 2026-06-03 | scripts, observability docs | Добавлен `scripts/agent_preflight.py`, который собирает scope, startup path, first validation и rough budget в одном запуске | После появления classifier и estimator следующий recurring friction point остался в ручном склеивании этих сигналов в один startup decision |
| 2026-06-03 | scripts, observability docs | Добавлены `scripts/build_agent_handoff.py` и handoff-блок в `scripts/agent_preflight.py`, чтобы wrapper сразу отдавал compact resume-summary | После unified preflight следующий recurring friction point остался в ручном восстановлении anchor, residual risk и next step при продолжении работы в новом чате |
| 2026-05-22 | Hooks и lifecycle docs | Добавлены pre-task, pre-edit, post-edit, post-task, guardrails и stop budgets | Sprint 3: нужен детерминированный workflow |
| 2026-05-22 | Routing | Добавлены specialist agents и routing matrix | Sprint 4: нужно разделить research, implementation, review и release |

## 4. Change request template

- Дата:
- Наблюдаемый recurring failure:
- Предлагаемое изменение:
- Ожидаемый эффект:
- Какие документы или assets затрагиваются:
