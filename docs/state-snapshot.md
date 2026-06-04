# State Snapshot

Последнее обновление: 2026-06-04
Статус: generated lightweight startup entry point for agent cold-start

## 1. Когда читать этот файл

1. Всегда первым для release-, resume- и действительно кросс-модульных задач.
2. Вместо полного state layer для локальных однофайловых и short explanation задач.
3. Если после чтения всё ещё неясен scope, только тогда эскалировать в docs/current-status.md, docs/current-sprint.md и docs/release-status.md.

## 2. Текущий контур

- Продукт: Windows Document Converter v0.3.0.
- Текущий active gate: S10.1 — v1.0 gate + S11.3 formula GA evidence.
- Текущий blocker: Главный blocker: S10.1/S11.3 blocked на external time gate и opt-in provider credentials; без 4 недель telemetry, 30 подряд package/smoke runs и live provider evidence GA нельзя честно закрыть в текущей сессии.
- Release status: production-ready within declared scope; v1.0 GA blocked на S10.1 external time gate и S11.3 live provider evidence/credentials.

## 3. Что важно помнить без чтения длинных state docs

- Cold-start now begins with docs/state-snapshot.md; full current-status/current-sprint/release-status are read only for release, resume or truly cross-module tasks before local search.
- A new session can reacquire the repo, environment, release scope and next validation path without broad search.

## 4. Fast-path routing

- Локальная задача в одном файле, одном тесте или вокруг одной ошибки: не читать полный state layer.
- Resume, release, process/state docs, CI/release gates или неочевидный owning surface: дочитать полный state layer.
- Если задача меняет capability/process contract, определить feature_id из docs/agent-feature-spine.json до substantive edit.

## 5. Полный state layer читать, если

1. задача продолжает незавершённую работу или явно просит resume/handoff
2. задача меняет state/release/process docs или harness assets
3. локальный маршрут показал, что изменение реально cross-module
4. validation target зависит от текущего sprint/release blocker

## 6. Ближайшие validation anchors

1. Hosted proofs зелёные: `nightly-full-e2e` на `main`, `release` на tag `v0.3.0`.
2. Harness checks зелёные: narrow unittest bundle, `build_agent_working_state.py --check`, `refresh_agent_eval.py`, `validate_harness_assets.py`.
3. S11.3 preflight подтвердил внешний blocker: provider credentials в текущем env отсутствуют.
