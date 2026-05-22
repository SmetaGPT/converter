# Agent Pilot Retrospective

Дата: 2026-05-22
Цикл: rollout roadmap sprint 0-6
Статус: completed

## 1. Pilot scope

В качестве pilot full-cycle использован сам rollout agent operating model по шагам roadmap. Внутри этого цикла были последовательно выполнены:

1. baseline и inventory;
2. state foundation;
3. memory discipline;
4. deterministic workflow и hooks;
5. specialist routing;
6. evaluation loop;
7. release discipline.

## 2. Что сработало

- docs-first подход позволил строить процесс без внешней платформы;
- state layer быстро стал рабочей точкой входа;
- get_errors оказался достаточным focused validation даже для process-only репозитория;
- разделение memory layer и git-tracked state убрало смешение статуса и знаний.

## 3. Что не сработало идеально

- markdown lint defects проявились уже на первых baseline-файлах;
- без явной фиксации переходов между спринтами state layer быстро устаревает;
- release loop нельзя считать доказанным на production-like сценариях без следующего пилота на реальных delivery tasks.

## 4. Потери контекста

Существенных потерь контекста после появления state layer не было. До этого слоя cold-start был бы значительно тяжелее.

## 5. Пропуски validation

Критичных пропусков после введения lifecycle не было. Единственный ранний дефект был локально пойман markdown-проверкой и превращён в regression entry.

## 6. Выводы для следующей волны

1. Нужен следующий пилот уже на реальных backend/frontend или document-processing задачах.
2. При появлении кода repo-memory нужно дополнять validated commands и environment gotchas по слоям.
3. Scorecard надо переводить с экспертной оценки на фактические weekly eval scores.
