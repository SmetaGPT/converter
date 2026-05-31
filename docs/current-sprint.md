# Current Sprint

Последнее обновление: 2026-05-31
Активный спринт: S10.1 — v1.0 gate
Статус: blocked_external_time_gate

Предыдущий приоритетный tranche: S9.2/S9.3 — nightly full e2e и release automation
Статус: completed with hosted proof
Статус wave W9: completed

## 1. Цель спринта

Довести проект до v1.0 GA только после выполнения всех acceptance gates: route stability, formula benchmark thresholds, security/protocol closure, четыре недели telemetry без unresolved regressions и 30 подряд зелёных portable EXE/package runs.

## 2. Закрытый hosted evidence по W9

- PR #5 auto-merged и исправил hosted formula monitor: Windows CI run `26707476363` success.
- Fixed nightly run `26707569316` на `main` доказал `Run full formula benchmark monitor` success, затем выявил table-source staging gap.
- PR #6 auto-merged и добавил table-anchor source preflight: Windows CI run `26707710691` success.
- Guarded nightly run `26707811922` на `main` completed success; artifact `nightly-full-e2e-artifacts` (`7315270976`, 33,933,125 bytes) содержит `table-anchor-source-preflight.json` со статусом `skipped_missing_input` и missing hosted sources для `sample_009/018/020`.
- Release workflow run `26707894247` completed success on tag `v0.3.0`; GitHub Release `https://github.com/SmetaGPT/converter/releases/tag/v0.3.0` опубликован с portable zip и checksum assets.

## 3. S10.1 exit criteria

| Критерий | Статус | Evidence / blocker |
| --- | --- | --- |
| Все 4 route стабильны; formula benchmark coverage >= 80% calc / >= 70% native | blocked | Требуется отдельный formula threshold uplift/corpus expansion; текущий W9 gate доказывает CI-safe subset, а не v1.0 coverage floor. |
| `docs/security.md` ревьюнут, S7.x закрыты | passed | S7.1/S7.2 закрыты, security docs и Gitleaks gate зелёные. |
| Protocol-абстракции (`Converter`, `Formula`, `OCR`, `Catalog`) имеют >= 2 реализации | passed | W2/W3 закрыли converter registry, `FormulaProvider`, `OcrBackend`, `CatalogWriter`. |
| Контракты `v1` финализированы; `v2` только через deprecation | partial | Stable contracts и schema snapshots есть; перед GA нужен explicit final review. |
| 4 недели telemetry подряд без unresolved regressions | blocked_external_time | Невозможно закрыть в текущей сессии: требуется календарное окно. |
| Portable EXE smoke + package gate зелёные 30 ранов подряд | blocked_external_time | Невозможно закрыть одним запуском; W9 дал hosted release-smoke/nightly/release proofs, но не 30-run streak. |
| Tag `v1.0.0`, release notes, `release-status.md` verdict «v1.0 GA» | not_started | Блокируется предыдущими criteria. |

## 4. Validation targets текущего состояния

1. `nightly-full-e2e` run `26707811922` на `main` завершён `success`.
2. `release` run `26707894247` на tag `v0.3.0` завершён `success` и опубликован GitHub Release с zip/checksum.
3. `$env:PYTHONPATH = 'src'; .\.venv\Scripts\python.exe scripts\refresh_agent_eval.py` пересобирает generated companions без drift.
4. `$env:PYTHONPATH = 'src'; .\.venv\Scripts\python.exe scripts\validate_harness_assets.py` возвращает `status: ok`.

## 5. Риски и blocker

- Главный blocker теперь не S9.x, а S10.1: time-based GA criteria (`4 недели telemetry`, `30` подряд package/smoke runs) нельзя честно выполнить в текущей сессии.
- Formula benchmark v1.0 thresholds (`>=80%` calc / `>=70%` native) требуют отдельного product-hardening tranche; текущий hosted CI-safe gate не подменяет полный GA threshold.
- Hosted runner по-прежнему не видит external `D:\ФСНБ\...` corpus и локальные ignored sample caches; nightly фиксирует это как explicit monitor/preflight artifact, а не как blocking crash.

## 6. Следующий operational focus

1. Зафиксировать S9.2/S9.3 hosted closeout в state PR и смерджить его через стандартный PR gate.
2. Если продолжать roadmap execution, следующий честный work item — S10.1 gate assessment / formula threshold uplift plan, а не ещё один CI repair.
3. Для v1.0 GA заранее накопить 4-week telemetry window и 30-run package/smoke streak; без этого `v1.0.0` tag не должен публиковаться.
