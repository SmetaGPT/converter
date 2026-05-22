# Agent Guardrails

Дата: 2026-05-22
Статус: active

## 1. Назначение

Guardrails нужны, чтобы автономность не превращалась в бесконтрольные risky actions.

## 2. Классы действий

| Класс | Примеры | Правило |
| --- | --- | --- |
| Safe read-only | list_dir, read_file, get_errors, memory view | Разрешено без approval |
| Safe edit | docs, prompts, hooks, локальные недеструктивные правки | Разрешено при наличии локальной гипотезы и validation plan |
| Sensitive edit | смена workflow rules, routing, release process | Разрешено, но требует явного state update и telemetry |
| Risky local action | удаление файлов, массовые rename, destructive git commands | Stop point и отдельная проверка контекста |
| Production-like action | deploy, release publication, destructive infra operations | Только через approval gate |

## 3. Действия с нулевой толерантностью без approval

- git reset --hard;
- git checkout -- для чужих изменений;
- удаление данных без обратимого плана;
- публикация релиза или деплой;
- ввод секретов в memory или документы;
- запуск destructive commands против production-like среды.

## 4. Обязательные stop points

Stop point обязателен, если:

1. действие необратимо или трудно обратимо;
2. операция влияет на release-ready состояние;
3. действие касается секретов, credentials или внешней среды;
4. blast radius выходит за текущий локальный slice.

## 5. Поведение при риске

1. Остановить выполнение risky шага.
2. Зафиксировать подтверждённые факты.
3. Сформулировать безопасную альтернативу или минимальный следующий шаг.
4. Указать, требуется ли approval.

## 6. Минимальный safe baseline для этого репозитория

Пока репозиторий построен вокруг документов и process assets, основной риск связан не с прод-средой, а с поломкой operating model. Поэтому любые изменения в AGENTS, hooks, routing docs и release docs требуют явной фиксации в state и telemetry.
