# Agent Routing Matrix

Дата: 2026-05-22
Статус: active

## 1. Цель

Routing matrix нужна, чтобы задачи не попадали в случайный режим и не смешивали research, implementation, review и release.

## 2. Основное соответствие

| Тип задачи | Режим по умолчанию | Почему |
| --- | --- | --- |
| Сравнить варианты, изучить библиотеку, понять причину | Research Agent | Нужен read-heavy режим без преждевременных правок |
| Внести локальную правку по понятной гипотезе | Implementation Agent | Нужен bounded edit с обязательным validation |
| Провести review change set или process assets | Review Agent | Нужен findings-first output |
| Подготовить release-ready состояние и release handoff | Release Agent | Нужен отдельный delivery-oriented режим |

## 3. Secondary routing rules

| Ситуация | Правило маршрутизации |
| --- | --- |
| Причина бага не ясна | Начать с Research, потом передать в Implementation |
| Требуется и правка, и последующий review | Сначала Implementation, затем отдельный Review |
| Задача дошла до checklist, runbook и approval gates | Переключиться в Release |
| Scope слишком широк для pilot implementation | Сначала Research, затем разбить на локальные slices |

## 4. Tool restrictions по режимам

| Режим | Предпочтительные инструменты | Ограничения |
| --- | --- | --- |
| Research | read_file, list_dir, grep_search, semantic_search, fetch_webpage | Не начинать edits без явного переключения режима |
| Implementation | apply_patch, get_errors, targeted reads, narrow terminal validation | Не расширять blast radius за пределы локального slice |
| Review | read_file, grep_search, get_errors, diff-oriented inspection | Не вносить substantive edits вместо findings |
| Release | read_file, get_errors, targeted terminal checks, state docs | Не выполнять publication или destructive actions без approval |

## 5. Output expectations

| Режим | Ожидаемый выход |
| --- | --- |
| Research | facts, options, recommendation, next mode |
| Implementation | changed artifacts, validation, state update, residual risk |
| Review | findings, assumptions, overall risk |
| Release | readiness, blockers, approval points, handoff |

## 6. Pilot rule для implementation mode

Implementation Agent остаётся в pilot-статусе, пока:

- не накоплен достаточный набор успешных tasks с focused validation;
- не подтверждено, что routing уменьшает хаотичные tool calls;
- не закрыт Sprint 5 eval loop.

До этого момента implementation mode не используется как default для неопределённых или широко размытых задач.
