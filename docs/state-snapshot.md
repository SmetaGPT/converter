# State Snapshot

Последнее обновление: 2026-06-04
Статус: generated lightweight startup entry point for agent cold-start

## 1. Когда читать этот файл

1. Всегда первым для release-, resume- и действительно кросс-модульных задач.
2. Вместо полного state layer для локальных однофайловых и short explanation задач.
3. Если после чтения всё ещё неясен scope, только тогда эскалировать в docs/current-status.md, docs/current-sprint.md и docs/release-status.md.

## 2. Текущий контур

- Продукт: Windows Document Converter v0.3.0.
- Текущий active gate: S10.1 — v1.0 gate + S11.3 provider-assisted formula GA evidence.
- Текущий blocker: Главный blocker теперь не S9.x, а S10.1: time-based GA criteria (`4 недели telemetry`, `30` подряд package/smoke runs) нельзя честно выполнить в текущей сессии.
- Release status: production-ready within declared scope. W9 hosted nightly + tag-driven release proof завершены. v1.0 GA остаётся blocked на S10.1 (time-based) и provider-assisted formula acceptance gates. Локальные strict-config, provider-hardening и S11.4 coverage-expansion слайсы закрыты. Оставшиеся blockers: S11.3 live provider evidence для малого formula corpus, отсутствие opt-in provider credentials в текущей сессии, external time window.

## 3. Что важно помнить без чтения длинных state docs

- W9 completed with hosted nightly/release proof; S10.1 v1.0 GA gate активен, но blocked на external time-based GA evidence и provider-assisted formula GA evidence; локальные hardening-слайсы S11.1 / S11.2a / S11.2b / S11.4 закрыты; S11.3 ждёт external opt-in provider credentials + time-based GA window.
- production-ready within declared scope. W9 hosted nightly + tag-driven release proof завершены. v1.0 GA остаётся blocked на S10.1 (time-based) и provider-assisted formula acceptance gates. Локальные strict-config, provider-hardening и S11.4 coverage-expansion слайсы закрыты. Оставшиеся blockers: S11.3 live provider evidence для малого formula corpus, отсутствие opt-in provider credentials в текущей сессии, external time window.
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

1. `nightly-full-e2e` run `26707811922` на `main` завершён `success`.
2. `release` run `26707894247` на tag `v0.3.0` завершён `success` и опубликован GitHub Release с zip/checksum.
3. `.\.venv\Scripts\python.exe -m unittest tests.test_build_agent_working_state tests.test_agent_preflight tests.test_classify_agent_scope tests.test_estimate_context_tokens -v` возвращает `OK`.
4. `.\.venv\Scripts\python.exe scripts\build_agent_working_state.py --check` подтверждает compact working-state без drift.
5. `$env:PYTHONPATH = 'src'; .\.venv\Scripts\python.exe scripts\refresh_agent_eval.py` пересобирает generated companions без drift.
