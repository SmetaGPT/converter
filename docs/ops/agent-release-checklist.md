# Agent Release Checklist

Дата: 2026-05-22
Статус: active

## 1. Entry criteria

Перед release-ready closeout должно быть подтверждено:

- target scope понятен;
- relevant changes завершены;
- focused validation выполнен;
- current-status и release-status синхронизированы;
- telemetry обновлена;
- unresolved blockers явно перечислены.

## 2. Pre-release checklist

| Пункт | Статус |
| --- | --- |
| Изменения по задаче или спринту завершены | [ ] |
| Validation summary зафиксирован | [ ] |
| docs/current-status.md обновлён | [ ] |
| docs/current-sprint.md обновлён | [ ] |
| docs/release-status.md обновлён | [ ] |
| docs/agent-telemetry-log.md обновлён | [ ] |
| Repo-memory обновлена при наличии validated learning | [ ] |
| Handoff подготовлен | [ ] |
| Approval points отмечены | [ ] |

## 3. Go / no-go questions

1. Есть ли нерешённый blocker, который делает release misleading?
2. Все ли risky actions либо закрыты, либо остановлены на approval gate?
3. Сможет ли следующая сессия продолжить без broad search?
4. Есть ли достаточно фактов для release-ready формулировки?

## 4. Post-release sanity

| Проверка | Статус |
| --- | --- |
| State layer отражает финальное состояние | [ ] |
| Release status отражает gates и residual risks | [ ] |
| Telemetry содержит финальную запись | [ ] |
| Есть retrospective или шаблон для неё | [ ] |
