# Current Sprint

Последнее обновление: 2026-05-31
Активный спринт: S10.1 — v1.0 gate + S11.3 provider-assisted formula GA evidence
Статус: blocked_external_provider_credentials_and_time_gate; S11.1/S11.2a/S11.2b/S11.4 local hardening completed, S11.3 awaits live credentials
feature_ids: `release-v1`, `formula-recognition-env-config`, `formula-recognition-postprocess`, `formula-benchmark-incremental`, `tests-negative-samples`, `tests-property-based`, `tests-docx-fixtures`

Предыдущий приоритетный tranche: S9.2/S9.3 — nightly full e2e и release automation
Статус: completed with hosted proof
Статус wave W9: completed

## 1. Цель спринта

Довести проект до v1.0 GA только после выполнения всех acceptance gates: route stability, provider-assisted formula GA gate, security/protocol closure, четыре недели telemetry без unresolved regressions и 30 подряд зелёных portable EXE/package runs.

## 2. Закрытый hosted evidence по W9

- PR #5 auto-merged и исправил hosted formula monitor: Windows CI run `26707476363` success.
- Fixed nightly run `26707569316` на `main` доказал `Run full formula benchmark monitor` success, затем выявил table-source staging gap.
- PR #6 auto-merged и добавил table-anchor source preflight: Windows CI run `26707710691` success.
- Guarded nightly run `26707811922` на `main` completed success; artifact `nightly-full-e2e-artifacts` (`7315270976`, 33,933,125 bytes) содержит `table-anchor-source-preflight.json` со статусом `skipped_missing_input` и missing hosted sources для `sample_009/018/020`.
- Release workflow run `26707894247` completed success on tag `v0.3.0`; GitHub Release `https://github.com/SmetaGPT/converter/releases/tag/v0.3.0` опубликован с portable zip и checksum assets.

## 3. S10.1 exit criteria

| Критерий | Статус | Evidence / blocker |
| --- | --- | --- |
| Все 4 route стабильны; provider-assisted formula gate >=80% calc, >=90% display, <=10% review_required; native-only monitor non-regressing | blocked | S11.1/S11.2a/S11.2b code path уже закрыт: provider chain имеет cache, budget/cost guardrails и explicit review semantics, а declared strict `ruff`/`pyright` config снова зелёный. Остаются S11.3 live pilot + provider-assisted benchmark report и time-based GA evidence. Старый full benchmark report `runs/formula-benchmark/runs/20260526T054732Z/benchmark-report.json` остаётся baseline: `gate.calc_expr_coverage = 0.6776`, `gate.native_coverage = 0.1858`. |
| `docs/security.md` ревьюнут, S7.x закрыты | passed | S7.1/S7.2 закрыты, security docs и Gitleaks gate зелёные. |
| Protocol-абстракции (`Converter`, `Formula`, `OCR`, `Catalog`) имеют >= 2 реализации | passed | W2/W3 закрыли converter registry, `FormulaProvider`, `OcrBackend`, `CatalogWriter`. |
| Контракты `v1` финализированы; `v2` только через deprecation | partial | Stable contracts и schema snapshots есть; перед GA нужен explicit final review. |
| 4 недели telemetry подряд без unresolved regressions | blocked_external_time | Текущий telemetry window: `2026-05-22` .. `2026-05-31`, 10 календарных дней; требуется минимум 4 недели. |
| Portable EXE smoke + package gate зелёные 30 ранов подряд | blocked_external_time | Невозможно закрыть одним запуском; W9 дал hosted release-smoke/nightly/release proofs, но не 30-run streak. |
| Tag `v1.0.0`, release notes, `release-status.md` verdict «v1.0 GA» | not_started | Блокируется предыдущими criteria. |

## 4. Validation targets текущего состояния

1. `nightly-full-e2e` run `26707811922` на `main` завершён `success`.
2. `release` run `26707894247` на tag `v0.3.0` завершён `success` и опубликован GitHub Release с zip/checksum.
3. `$env:PYTHONPATH = 'src'; .\.venv\Scripts\python.exe scripts\refresh_agent_eval.py` пересобирает generated companions без drift.
4. `$env:PYTHONPATH = 'src'; .\.venv\Scripts\python.exe scripts\validate_harness_assets.py` возвращает `status: ok`.
5. Focused S11.2b validation прошла: `.\.venv\Scripts\python.exe -m unittest tests.test_config tests.test_formula_recognition tests.test_contracts_stability tests.test_cli_smoke.CliSmokeTests.test_runner_invokes_formula_recognition_postprocess_when_configured tests.test_cli_smoke.CliSmokeTests.test_run_metadata_serializes_local_formula_backend_without_api_key -v` вернул `OK` (`32` tests), а focused `ruff` и `pyright` по touched files вернули `0` issues.
6. S11.1 strict alignment validation прошла: full `.\.venv\Scripts\python.exe -m ruff check src tests scripts` и full `.\.venv\Scripts\python.exe -m pyright` вернули `0` issues.
7. S11.3 preflight показал реальный внешний blocker: `MATHPIX_APP_ID`, `MATHPIX_APP_KEY`, `OPENROUTER_API_KEY` и `FORMULA_RECOGNITION_API_KEY` в текущем окружении отсутствуют; локальный benchmark hook есть, но live provider evidence без этих opt-in credentials не исполним.
8. S11.4 local coverage closeout прошёл: `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m unittest tests.test_property_based tests.test_negative_sample_expectations -v` (`4` tests `OK`), coverage smoke, full `unittest discover` (`206` tests, `4` skipped), full `ruff`, full `pyright` (`0` errors) и `pip check` зелёные.

## 5. Риски и blocker

- Главный blocker теперь не S9.x, а S10.1: time-based GA criteria (`4 недели telemetry`, `30` подряд package/smoke runs) нельзя честно выполнить в текущей сессии.
- Formula benchmark v1.0 gate теперь должен быть provider-assisted: `calc_expr >= 0.80`, `display_latex >= 0.90`, `review_required <= 0.10`, provider failures graceful; native-only `0.70` переведён в monitor debt для малого корпуса.
- Для малого корпуса документов с формулами (<100) product strategy изменена: вместо расширения known-patterns как production path используется `Mathpix → OpenRouter/LLM normalizer → deterministic validation`; S11.1/S11.2a/S11.2b уже закрыли strict/config and operational hardening, S11.4 закрыл локальный negative/property coverage gap, остаются S11.3 live pilot metrics и provider-assisted benchmark evidence.
- Текущий session blocker для S11.3 уже не в коде: в env отсутствуют все opt-in provider credentials, поэтому live provider pilot/report нельзя честно запустить из этой workspace-сессии.
- Hosted runner по-прежнему не видит external `D:\ФСНБ\...` corpus и локальные ignored sample caches; nightly фиксирует это как explicit monitor/preflight artifact, а не как blocking crash.

## 6. Следующий operational focus

1. S9.2/S9.3 hosted closeout уже зафиксирован и смержен через PR #7 (`f778d0e`).
2. Следующий исполнимый engineering work item — S11.3 provider-assisted formula GA evidence, но он ждёт opt-in credentials: live pilot на 10-20 документах, provider-assisted benchmark/report и review-load metrics.
3. Локально доступный S11.4 closeout уже выполнен; следующий local-only backlog при отсутствии credentials — S11.5 harness consolidation или S11.6 oversize/perf proof, но они не снимают S10.1 time/provider blockers.
4. Для v1.0 GA также заранее накопить 4-week telemetry window и 30-run package/smoke streak; без этого `v1.0.0` tag не должен публиковаться.
