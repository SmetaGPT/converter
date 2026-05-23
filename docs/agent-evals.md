# Agent Evals

Дата: 2026-05-23
Статус: active

## 1. Назначение

Eval loop нужен, чтобы оценивать качество агентной работы по явным критериям, а не по впечатлению от последнего ответа.

## 2. Источники оценки

| Источник | Роль |
| --- | --- |
| docs/agent-eval-tasks.md | Набор типовых сценариев |
| docs/agent-telemetry-log.md, docs/agent-telemetry.v1.jsonl | Фактические сигналы по validation, state update и feature traceability |
| docs/current-status.md | Проверка качества state hygiene |
| docs/agent-quality-scorecard.md, docs/agent-quality-scorecard.v1.json | Сводный baseline, текущие оценки и observed structured signals |
| docs/agent-weekly-eval.md, docs/agent-weekly-eval.v1.json | Generated weekly snapshot с findings, coverage gaps и next actions |
| docs/agent-weekly-reviews.v1.json | Machine-readable sampled task scores для qualitative weekly review |
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

1. Обновить generated companions командой `scripts/refresh_agent_eval.py`.
2. Посмотреть findings и coverage gaps в `docs/agent-weekly-eval.md`.
3. Если snapshot показывает gaps, findings или неделя затрагивает harness/process layer, выбрать 3-5 задач из разных категорий.
4. Если snapshot сильный и неделя была рутинной для этого репозитория, достаточно 1-2 spot checks вместо полного набора.
5. Оценить sampled tasks по rubric и зафиксировать recurring failures.
6. Проверить, нужно ли изменить prompts, hooks, AGENTS или memory discipline.
7. При необходимости обновить scorecard assumptions или добавить regression entry.

## 6. Generated weekly eval companion

- Machine-readable snapshot: `docs/agent-weekly-eval.v1.json`.
- Human-readable snapshot: `docs/agent-weekly-eval.md`.
- Machine-readable sampled reviews: `docs/agent-weekly-reviews.v1.json`.
- Refresh command: `.\.venv\Scripts\python.exe scripts\refresh_agent_eval.py`.
- Drift check: `.\.venv\Scripts\python.exe scripts\refresh_agent_eval.py --check --check-markdown`.
- Granular fallback: `scripts/build_agent_scorecard.py --sync-markdown` и `scripts/build_agent_weekly_eval.py`.
- Optional schedule helper: `powershell -ExecutionPolicy Bypass -File scripts\register-agent-eval-schedule.ps1 -CheckOnly`; без `-CheckOnly` helper регистрирует Windows Scheduled Task и требует `-Force` для замены существующей task.

Этот companion не заменяет ручной task sampling, но убирает ручной пересчёт базовых signals и coverage gaps.

## 7. Self-review после задачи

После каждой нетривиальной задачи агент должен коротко ответить:

1. Что сработало.
2. Где был лишний поиск или ремонт.
3. Не был ли пропущен validation или state update.
4. Нужен ли новый memory note или change-log entry.

Подробный шаблон: docs/agent-self-review-template.md.

## 8. Первый completed weekly review

Дата review: 2026-05-23.

Machine-readable sampled scores для этого review: `docs/agent-weekly-reviews.v1.json`.

Sampling выполнен по реальным задачам из разных категорий, чтобы generated weekly snapshot не оставался proxy-only слоем.

Все значения ниже по шкале 0-2 из `docs/agent-evaluator-rubric.md`.

| Задача | Scope | Trace | Hyp | Val | Evidence | State | Closeout | Total | Интерпретация |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Sprint 1 state foundation | 2 | 1 | 1 | 2 | 2 | 2 | 2 | 12 | strong closeout |
| Sprint 3 workflow hooks | 2 | 1 | 1 | 2 | 2 | 2 | 2 | 12 | strong closeout |
| Sprint 4 specialist routing | 2 | 1 | 1 | 2 | 2 | 2 | 2 | 12 | strong closeout |
| SP folder e2e | 2 | 1 | 2 | 2 | 2 | 2 | 2 | 13 | strong closeout |
| Generated weekly eval companion | 2 | 2 | 2 | 2 | 2 | 2 | 2 | 14 | strong closeout |

Средний результат выборки: `12.6/14`.

Выводы цикла:

- generated weekly snapshot после telemetry backfill можно считать надёжным operational shortcut для этого репозитория;
- исторические задачи до feature spine и явной lifecycle discipline всё ещё теряют 1 балл по traceability и hypothesis quality;
- менять `AGENTS.md` не требуется: действующий operational contract уже достаточен, проблема была в telemetry coverage и отсутствии первого completed review.
