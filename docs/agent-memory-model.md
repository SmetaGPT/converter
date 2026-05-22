# Agent Memory Model

Дата: 2026-05-22
Статус: active

## 1. Зачем нужен memory layer

Memory layer нужен для трёх задач:

1. сокращать cold-start и resume cost;
2. предотвращать повтор одних и тех же технических ошибок;
3. отделять устойчивые знания от разового шума конкретной сессии.

## 2. Слои памяти

| Слой | Где живёт | Что хранит |
| --- | --- | --- |
| User memory | /memories/ | Долгоживущие пользовательские предпочтения и cross-repo learnings |
| Session memory | /memories/session/ | Краткоживущий контекст текущего разговора |
| Repo memory | /memories/repo/ | Проверенные знания о конкретном репозитории |
| Git-tracked state | docs/*.md, AGENTS.md, .github/* | Source-of-truth процесс, статус, lifecycle, routing |

## 3. Типы памяти

| Тип | Смысл | Где хранить по умолчанию |
| --- | --- | --- |
| Semantic | Факты о проекте, командах, структуре, окружении | Repo memory или git-tracked docs |
| Episodic | Что происходило в конкретной задаче или сессии | Task checkpoints, session memory, telemetry |
| Procedural | Как агент должен работать | AGENTS.md, hooks, instructions, routing docs |

## 4. Shared vs local memory

| Категория | Где хранить | Правило |
| --- | --- | --- |
| Shared knowledge | Git-tracked docs или /memories/repo/ | Хранить, если знание пригодится следующей сессии или команде |
| Local-only working context | /memories/session/ | Хранить только пока задача активна |
| Personal preferences пользователя | /memories/ | Не дублировать в repo memory |

## 5. Правила размещения знаний

1. Статус, roadmap progression и release state живут в git-tracked docs.
2. Короткие validated learnings о репозитории живут в /memories/repo/.
3. Временные догадки и незавершённые размышления не попадают в repo memory.
4. Procedural memory меняется не через memory notes, а через контролируемое обновление AGENTS, hooks, instructions и change log.

## 6. Когда агент обязан писать новый learning

Новый learning обязан быть записан, если одновременно выполняются условия:

1. ошибка или приём повторяемы;
2. вывод подтверждён практикой, а не предположением;
3. знание с высокой вероятностью пригодится следующей задаче;
4. оно укладывается в короткую атомарную запись.

## 7. Где что искать при resume

1. docs/current-status.md
2. docs/current-sprint.md
3. docs/release-status.md
4. relevant task checkpoint
5. /memories/repo/* по затронутой области
6. /memories/session/* только если задача ещё активна

## 8. Текущее разбиение repo memory

| Файл | Назначение |
| --- | --- |
| /memories/repo/agent-ops.md | Правила работы агента в этом репозитории |
| /memories/repo/backend-notes.md | Проверенные backend- и pipeline-наблюдения |
| /memories/repo/frontend-notes.md | Проверенные frontend-наблюдения |
| /memories/repo/deployment-notes.md | Проверенные deployment и release notes |

## 9. Антипаттерны

- складировать длинные пересказы сессий в repo memory;
- хранить speculative решения как проверенный факт;
- дублировать один и тот же learning в трёх местах;
- подменять memory layer state layer;
- вносить procedural rules в memory notes вместо управляемых документов процесса.
