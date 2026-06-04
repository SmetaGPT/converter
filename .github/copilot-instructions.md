# Copilot Instructions — Конвертер файлов

Эти правила обязательны и имеют приоритет. Цель — минимальный расход токенов.

## Бюджет контекста (главное)

1. По умолчанию — **fast path**: начинать с named file/symbol/test/error. НЕ читать state layer, repo-memory, telemetry, пока локальный routing не покажет, что задача реально шире.
2. Тяжёлые файлы читать только **grep-точечно по нужной секции**, никогда целиком без явной необходимости: `docs/current-status.md`, `docs/release-status.md`, `docs/agent-feature-spine.json`, `docs/agent-telemetry.v1.jsonl`, `docs/agent-telemetry-log.md`, `docs/production-roadmap.md`, `docs/formula-production-plan.md`.
3. Полные исторические версии статусов лежат в `docs/archive/` — открывать только если grep по дайджесту недостаточно.
4. Extended path (release / resume / подтверждённо кросс-модульная задача): сначала `docs/agent-working-state.v1.json` + `docs/state-snapshot.md`, затем grep-точечно по нужным state-докам.

## Гигиена документов

- `docs/current-status.md`, `docs/current-sprint.md` и `docs/release-status.md` держать компактными (дайджест + ссылки). Разросшуюся историю уводить в `docs/archive/`, не раздувать сами файлы.
- Не дублировать длинные тексты в новые markdown-отчёты без явной просьбы пользователя.

## Прочее

- Полный процессный контракт: `AGENTS.md`. Не пересказывать его в ответах.
