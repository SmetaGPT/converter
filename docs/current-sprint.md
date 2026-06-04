# Current Sprint

Последнее обновление: 2026-06-04
Активный спринт: S10.1 — v1.0 gate + S11.3 formula GA evidence
Статус: blocked на external time gate и provider credentials; локальный hardening S11.1/S11.2a/S11.2b/S11.4 закрыт
feature_ids: `release-v1`, `formula-recognition-postprocess`, `formula-benchmark-incremental`, `compact-working-state`

## 1. Цель спринта

Довести проект до v1.0 GA после закрытия formula GA gate, 4-week telemetry window и 30-run package/smoke streak.

## 2. Закрытый hosted evidence по W9

- W9 hosted proof завершён: nightly success на `main`, release success на tag `v0.3.0`, portable GitHub Release опубликован.
- Детали hosted fixes и артефактов вынесены в архив и не нужны для cold-start.

## 3. S10.1 exit criteria

| Критерий | Статус | Evidence / blocker |
| --- | --- | --- |
| Все 4 route стабильны; provider-assisted formula gate >=80% calc, >=90% display, <=10% review_required; native-only monitor non-regressing | blocked | Code path закрыт; pending только S11.3 live pilot/report и time-based GA evidence. Baseline: `calc_expr=0.6776`, `native=0.1858`. |
| Контракты `v1` финализированы; `v2` только через deprecation | partial | Stable contracts и schema snapshots есть; нужен финальный GA review. |
| 4 недели telemetry подряд без unresolved regressions | blocked_external_time | Текущий window: `2026-05-22` .. `2026-05-31`; нужно >=4 недель. |
| Portable EXE smoke + package gate зелёные 30 ранов подряд | blocked_external_time | W9 proofs зелёные, но 30-run streak ещё не накоплен. |
| Tag `v1.0.0`, release notes, `release-status.md` verdict «v1.0 GA» | not_started | Ждёт закрытия всех предыдущих criteria. |

Passed gates: security review/S7.x закрыты; protocol abstractions имеют >=2 реализации.

## 4. Validation targets текущего состояния

1. Hosted proofs зелёные: `nightly-full-e2e` на `main`, `release` на tag `v0.3.0`.
2. Harness checks зелёные: narrow unittest bundle, `build_agent_working_state.py --check`, `refresh_agent_eval.py`, `validate_harness_assets.py`.
3. S11.3 preflight подтвердил внешний blocker: provider credentials в текущем env отсутствуют.

## 5. Риски и blocker

- Главный blocker: S10.1/S11.3 blocked на external time gate и opt-in provider credentials; без 4 недель telemetry, 30 подряд package/smoke runs и live provider evidence GA нельзя честно закрыть в текущей сессии.
- S11.3 остаётся внешним blocker: live pilot/report неисполняемы без credentials.
- Hosted runner не видит external `D:\ФСНБ\...` corpus и локальные ignored sample caches; nightly фиксирует это как monitor artifact, а не как blocking crash.

## 6. Следующий operational focus

1. Следующий исполнимый work item — S11.3 provider-assisted formula GA evidence после появления credentials.
2. Параллельно нужно накопить 4-week telemetry window и 30-run package/smoke streak; до этого `v1.0.0` tag публиковать нельзя.
