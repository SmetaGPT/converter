# Agent Runbook

Дата: 2026-05-22
Статус: active

## 1. Первый release cycle

Использовать при первом полном проходе agent operating model.

1. Открыть docs/current-status.md и docs/release-status.md.
2. Проверить, что scope релиза совпадает с roadmap или task scope.
3. Проверить completion relevant artifacts.
4. Проверить focused validation и telemetry.
5. Сверить unresolved risks и approval points.
6. Подготовить handoff.
7. Пройти checklist из docs/ops/agent-release-checklist.md.
8. Зафиксировать retrospective.

## 2. Обычный release cycle

1. Синхронизировать state layer.
2. Проверить release checklist.
3. Проверить approval gates.
4. Зафиксировать release-ready summary.
5. Обновить handoff и retrospective, если есть новый процессный learning.

## 3. Approval matrix

| Сценарий | Правило |
| --- | --- |
| Docs/process-only release | Можно закрывать локально при полном state sync |
| Production-like action | Нужен явный approval gate |
| Destructive action | Нужен stop point и отдельная проверка контекста |
| Secret-bearing operation | Не проводить через memory или обычные docs |

## 4. Handoff minimum

Перед передачей следующей сессии нужно оставить:

- current-status;
- release-status;
- telemetry row;
- checkpoint или closeout summary;
- список residual risks и approval points.
