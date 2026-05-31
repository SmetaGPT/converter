# Release Status

Последнее обновление: 2026-05-31
Релизный контур: Windows Document Converter v0.3.0
Статус: production-ready within declared scope; локальный critical path теперь blocked only by external GitHub-hosted nightly/tag evidence after full S5.1 `1/пр` closeout

## 1. Цель релиза

Довести репозиторий до состояния, в котором агентный контур поддерживает полный цикл: baseline, state, memory, lifecycle, routing, evaluation и release discipline.

## 2. Текущая стадия

Сейчас проект находится в post-release table and formula hardening state поверх production-ready v0.3.0: converter уже имеет runtime schema validation, resume/reuse для неизменённых файлов, duplicate skip без перезаписи canonical package, operator-grade GUI surface, reference chunk builder, Windows CI, synthetic e2e и portable release packaging. После v0.2.0 реализованы semantic metadata enhancement для `document.v1.json`, heuristic semantic extraction для DOCX/PDF tables/formulas/figures и DOCX footnotes/header/footer, native XLSX route для workbook/sheet/cell/formula packages, env-based formula-recognition provider config с безопасной сериализацией run metadata, formula-recognition postprocess с local WMF hint extraction и OpenRouter fallback, optional Windows schedule helper для eval refresh, root-level `processed-documents-catalog.json` и `processed-documents-catalog.xlsx` для operator navigation, first-class human-readable Markdown/HTML export из canonical package и GUI HTML QC path, а portable package пересобран как v0.3.0. Поверх formula tranche уже закрыт первый table-hardening sprint: `pdf_text` и `pdf_scan` теперь используют shared table parser с dominant row width normalization, continuation-line merge и explicit `table_structure_warning` для unresolved ragged tables, а DOCX `table_cell` units сохраняют multiline text и formula-like cell metadata. Следом закрыт и первый table benchmark anchor baseline: `sample_009` и `sample_018` получили executable expected specs с row/cell metrics, `sample_020` зафиксирован как reproducible OCR-blocked scan baseline, а новый validator `scripts/validate_sample_expectations.py` превращает representative sample expectations из статичных JSON fixtures в воспроизводимый quality loop. Formula benchmark harness, versioned gates и opt-in local formula OCR backend `FORMULA_RECOGNITION_LOCAL_BACKEND=tesseract` остаются отдельным воспроизводимым quality loop для следующего formula backlog. Дополнительно harness layer теперь имеет machine-readable feature spine, bootstrap contract, clean-exit checklist, sprint contract template, evaluator rubric и CI-backed validator для этих артефактов, а feature spine покрывает и core product-capabilities конвертера, связан с task-flow через `feature_id` traceability, дополнен schema-backed telemetry JSONL companion, generated scorecard companion, generated weekly eval companion, machine-readable weekly review source, one-command refresh wrapper и guarded schedule helper для этого eval contour.

Critical-path operator surface S6.1 закрыт: CLI по умолчанию остаётся human-readable для ручного использования, а `--output-format=json` выдаёт fixed `cli-result.v1` envelope с exit-code matrix `0/10/20/30/40/50`. Дополнительно появились `doctor` и `dry-run`, поэтому агент может различать `input_invalid`, `environment_invalid`, `review_required` и `partial` без парсинга prose и без пробного запуска полного conversion path.

Следом закрыт и S6.2 structured telemetry tranche: каждый run теперь эмитит schema-backed `telemetry.jsonl` по `log.v1` через central logger adapter, а `scripts/validate_run_package.py` валидирует этот event stream вместе с остальными run-package артефактами. Legacy `processing-log.jsonl` и `errors.jsonl` пока сохранены как compatibility mirrors, поэтому operator/debug привычки не ломаются одномоментно.

Следом закрыт и S7.1 security baseline: `validate_run_directories` теперь fail-closed отклоняет symlink-based path confusion на `input_dir`/`output_dir`/`runs_dir`, DOCX archive admission ограничен по entry count и суммарному uncompressed size до `python-docx`, WMF parser ограничен по размеру blob и количеству records, а `docs/security.md` фиксирует threat model, subprocess inventory и font/path policy для untrusted документов.

Следом закрыт и S7.2 secret-scan CI tranche: `windows-ci` теперь устанавливает Gitleaks и выполняет required git-backed scan `gitleaks git --config .gitleaks.toml --exit-code 1 .`. Конфиг расширяет default rules узким product-specific rule для `OPENROUTER_API_KEY` / `FORMULA_RECOGNITION_API_KEY`, а global allowlist intentionally покрывает только known fake fixtures и `.env.example`, поэтому clean repo проходит без ручного baseline файла, а synthetic git canary валится детерминированно.

Следом закрыт и S9.1 PR-gates tranche: `main` теперь защищён strict required contexts `secret-scan`, `lint`, `typecheck`, `unit-tests`, `harness-validator`, `formula-benchmark-gate`, `document-package-validator` и `release-smoke`, PR template фиксирует feature/state/validation closeout, а `.github/workflows/autonomous-pr-auto-merge.yml` на base branch включает squash auto-merge для same-repo non-draft PR с label `agent:autonomous`.

Следом открыт и S9.2 nightly tranche: `.github/workflows/nightly-full-e2e.yml` запускает synthetic e2e, full formula benchmark monitor без thresholds, CI-safe formula gate, repo-tracked table anchors, EXE smoke и nightly portable package, а `scripts/create_nightly_failure_issue.py` создаёт failure issue с latest merged PR context и explicit/fallback `agent_id` trace.

Следом локально закрыт и S9.3 release-automation tranche: `.github/workflows/release.yml` публикует portable release по `v*` tag, `scripts/package-release.ps1` больше не держит hard-coded notes, а рендерит `release-notes.md` из git-tracked `CHANGELOG.md` через тестируемый `src/doc_converter/release_notes.py` / `scripts/render_release_notes.py`.

Параллельно с ожиданием hosted evidence по S9.x локально закрыт и независимый S3.1: `src/doc_converter/formulas/providers.py` вводит `FormulaProvider` protocol и три реализации (`LocalTesseractProvider`, `OpenRouterProvider`, `NullProvider`), а `run_formula_recognition_postprocess` теперь использует provider chain вместо hard-coded backend/provider ветвления.

Следом локально закрыт и S3.2 provider-surface follow-up: `src/doc_converter/ocr/backends.py` вводит `OcrmypdfBackend` и `NullOcrBackend`, `src/doc_converter/run/catalog_writers.py` выносит `JsonCatalogWriter` и `XlsxCatalogWriter`, а `ConverterOptions` теперь сереализует `ocr_backend` / `catalog_writers`, так что OCR scan path и root catalog emission больше не зависят от hard-coded side-effect веток.

Следом локально закрыт и S3.3 redaction tranche: `src/doc_converter/redaction.py` теперь редактирует значения env vars `*API_KEY*/*TOKEN*/*SECRET*` на границах artifact serialization, а `tests/test_provider_secret_redaction.py` сканирует целый temp run directory и formula-recognition sidecar, включая legacy `errors.jsonl`/`processing-log.jsonl`, чтобы compatibility mirrors не оставались обходным leak path.

Следом локально закрыт и S4.1 determinism tranche: `src/doc_converter/inventory.py` теперь закрепляет порядок на finalized inventory records и duplicate groups по deterministic key `relative_path + sha256`, а `tests/test_run_determinism.py` форсирует два разных iterator order и всё равно получает идентичный clean-run `manifest.jsonl`.

Следом локально реализован и S4.2 incremental benchmark tranche: `src/doc_converter/formula_benchmark.py` теперь reuse-ит per-entry case results по versioned cache key из asset hash + manifest fingerprint + `benchmark_version`, `tests/test_formula_benchmark.py` подтверждает cache hit для unchanged rerun и miss на manifest/gold drift, а `required_gate` каждый run агрегируется заново из cached case reports. Full-corpus timing smoke не был повторён в этой сессии, потому что heavy local command получил usage-limit rejection до старта.

Следом локально реализован и S4.3 font-bundling tranche: shared `src/doc_converter/font_bundle.py` выровнял path resolution между `document-converter doctor`, DOCX inline-glyph matcher и frozen layouts, `assets/fonts/` теперь несёт bundled `DejaVuSans.ttf` и `LICENSE_DEJAVU`, а `scripts/build-windows.ps1` и оба PyInstaller spec-файла включают `assets` в packaged output. Focused bundled-font proof, полный `tests.test_docx_converter` + `tests.test_cli_smoke` slice и build smoke `DocumentConverter-next` подтвердили, что runtime больше не зависит только от `C:/Windows/Fonts`.

Локально продолжен и следующий formula follow-up из S5.1: canonical known-pattern contract в `samples/formulas/known-patterns.v1.json` и экспортируемая package copy теперь дополнительно закрывают noisy work-time/wage formulas `(10)` и `(13)` и estimated-work cost formulas `(42)` и `(43)` вместе с уже ранее закрытыми `1/пр` slices `(9)`-`(12)`, `(15)`, `(17)`, `(19)`, `(20)`, `(22)`, `(24)`, `(25)`, `(35)`-`(39)` как machine-readable `calc_expr` и display LaTeX без новых parser-side веток. Focused regressions `test_formula_representation_recovers_noisy_1pr_wage_and_worker_time_formulas`, `test_formula_representation_recovers_noisy_1pr_estimated_work_participation_family`, `test_formula_representation_recovers_noisy_1pr_estimated_work_cost_family`, broader `tests.test_docx_converter` + `tests.test_known_formula_patterns` (`104/104`) и `scripts/validate_known_formulas.py` прошли зелёно при `21` noisy recovery mappings и `47` formula representations. Newly mounted source DOCX `D:\Документы\ФСНБ\Документы\для парсера\Российские\metod\Приказ Минстроя России от 09.01.2024 N 1_пр  Об утверждении.docx` enabled rendered WMF inspection for `(10)` and `(13)`, а cold rerun `runs\formula-debug-1pr-source-fresh\runs\20260531T072130Z` поднял `gate-metod-1-pr` до `49/49` calc_expr units и `26/49` native formulas; same-output-root rerun, который всё ещё показывал `47/49`, оказался benign `formula_benchmark` cache hit, а не parser regression.

Текущий blocker для продолжения autonomous roadmap теперь действительно только внешний GitHub-hosted: критический путь всё ещё ждёт nightly/tag evidence для `S9.2/S9.3`. Source DOCX для `gate-metod-1-pr` больше не missing, локальный `1/пр` residue закрыт, и дальнейший local follow-up должен выбирать уже другой независимый sprint вместо продолжения этого formula slice.

Готово:

- baseline;
- inventory;
- eval task seed;
- initial quality scorecard;
- state foundation;
- memory discipline;
- deterministic workflow и hooks;
- specialist agents и routing;
- evaluation и self-review;
- Windows Document Converter hardening Sprint 13-16;
- runtime schema validation для `run/document/manifest/summary/queue-state/ocr-runtime/chunks`;
- `review-required.jsonl`, richer summary reasons и portable run-package validation;
- structured CLI operator surface: `cli-result.v1`, exit-code matrix, `doctor` и `dry-run`.
- security hardening baseline: `docs/security.md`, symlink-safe startup path admission, DOCX archive limits и WMF parser limits.
- required secret-scan gate: `windows-ci` ставит Gitleaks, использует `.gitleaks.toml`, сохраняет узкий allowlist для fixtures/examples и валит synthetic API-key canary.
- protected PR gate surface на `main`: strict branch protection удерживает required contexts `secret-scan`, `lint`, `typecheck`, `unit-tests`, `harness-validator`, `formula-benchmark-gate`, `document-package-validator`, `release-smoke`, а PR template требует feature/state/validation closeout.
- label-driven autonomous merge: `.github/workflows/autonomous-pr-auto-merge.yml` на `main` через `pull_request_target` включает squash auto-merge для same-repo non-draft PR с label `agent:autonomous`.
- hosted nightly infrastructure: `.github/workflows/nightly-full-e2e.yml` запускает synthetic e2e, full formula monitor без thresholds, CI-safe formula gate, repo-safe table anchors, EXE smoke, nightly portable package и auto-issue helper с latest merged PR context.
- stable ordering guarantee: `inventory.py` теперь закрепляет supported/unsupported ordering и duplicate primary по deterministic key, а clean rerun manifest держится идентичным даже при принудительно разном iterator order.
- incremental formula benchmark cache: `formula_benchmark.py` reuse-ит unchanged cases через versioned cache key и при этом всё равно пересчитывает full `required_gate` из свежего aggregate report; manifest/gold drift снова ведёт к case rebuild.
- bundled inline-glyph font set: `document-converter doctor` и DOCX inline-glyph matcher теперь используют общий bundle resolver, repo несёт `DejaVuSans.ttf` + лицензию в `assets/fonts`, а PyInstaller build paths включают этот bundle в packaged output вместо неявной зависимости от системных Windows fonts.
- Windows CI workflow, synthetic e2e и portable release package с checksum/release notes.
- schema-backed semantic metadata block в `document.v1.json`, подтверждённый real-folder e2e на 52 DOCX из `metod`.
- machine-readable `docs/agent-feature-spine.json` и validator `scripts/validate_harness_assets.py`, встроенный в CI.
- machine-readable feature coverage для core product-capabilities converter runtime и operator surface.
- machine-readable telemetry companion `docs/agent-telemetry.v1.jsonl` с schema validation и проверкой known `feature_id`.
- generated scorecard companion `docs/agent-quality-scorecard.v1.json`, синхронизированный с telemetry JSONL, feature spine и human-readable markdown section.
- generated weekly eval companion `docs/agent-weekly-eval.v1.json` и `docs/agent-weekly-eval.md`, собираемый из scorecard и structured telemetry вместо ручного weekly proxy review.
- first completed qualitative weekly review, который подтвердил strong closeout по реальным sampled tasks и закрыл bootstrap-phase gaps в eval loop.
- machine-readable sampled weekly reviews в `docs/agent-weekly-reviews.v1.json`, которые делают qualitative sampling частью schema-backed evidence, а не только markdown narrative.
- one-command refresh wrapper `scripts/refresh_agent_eval.py` и optional schedule helper `scripts/register-agent-eval-schedule.ps1`, который можно подключить к Windows Scheduled Task.
- production-audit remediation bundle: overlap/self-ingestion guard, truthful unsupported-input reporting, repo-local `ruff`/`pyright` install surface, shared script bootstrap, deprecated-only `workers` compatibility, OCR traineddata SHA-256 verification и Windows CI gates для `pip check`, `ruff`, `pyright`, EXE smoke и portable release artifact.
- post-release semantic/package bundle v0.3.0: DOCX formulas/header/footer/footnote units, PDF text/OCR heuristic table/formula/figure units и portable release `DocumentConverter-0.3.0`.
- native XLSX route: `.xlsx` поддерживается как `xlsx_native`, листы/строки/ячейки сохраняются в structural units, а Excel formula strings и cached values попадают в structured `cell` payload.
- env-based formula-recognition config: `.env.local`/`.env` и process env overrides автоматически подхватываются в runtime; explicit `FORMULA_RECOGNITION_*` keys и shorthand `LLM_PROVIDER`/provider-specific model key/`FORMULA_MODEL` совместимы, а `run.json` получает только безопасный `formula_recognition` block без `api_key`. Если есть `OPENROUTER_API_KEY`, но нет отдельного `FORMULA_MODEL`, formula slice по умолчанию использует `openai/gpt-4o`.
- formula-recognition postprocess: runner теперь может дообогащать `formula_image` units через local WMF hint extraction и OpenRouter fallback, сохраняя результаты в `document.v1.json` и `formula-recognition.jsonl` без утечки секрета в артефакты run package; multimodal response закреплён через strict `json_schema`.
- pluggable OCR and catalog surface: `pdf_scan` dispatch-ит OCR через `OcrBackend`, root catalog emission dispatch-ит через `CatalogWriter`, а config-driven smoke подтверждает `ocr_backend="null"` и `catalog_writers=("json",)` без drift в default operator outputs.
- secret redaction guarantee: все run/package/provider artifact boundaries проходят через `redact_secrets`, а dedicated artifact-scan test закрывает утечки не только в primary JSON, но и в legacy compatibility mirrors и XLSX catalog output.
- deterministic formula benchmark harness: versioned `samples/formula-benchmark.manifest.jsonl`, gold fixtures и scripts `run_formula_benchmark.py` / `export_formula_gold.py` now anchor formula quality on reproducible artifacts instead of ad hoc visual comparison; benchmark runs are BOM-safe and disable live provider inheritance by default.
- executable formula threshold gate: versioned policy `samples/formula-benchmark.thresholds.json` теперь загружается benchmark harness по умолчанию, report пишет `tier_summaries` + `required_gate`, а baseline `20260525T193008Z` закреплён как текущий numeric floor/ceiling для `anchor`, `gate`, `control` и `overall`; `rolling` остаётся monitor-only до следующего полного rerun.
- refreshed full rerun under required gate: `runs\formula-benchmark\runs\20260526T054732Z` подтвердил новый contract end-to-end без provider leakage и поднял corpus totals до `194/281` calc_expr units и `53/281` native WMF units, сохранив `11/11` gold passed, `control.false_positive_rate = 0.0` и `required_gate.status = passed`.
- opt-in local formula OCR backend: `FORMULA_RECOGNITION_LOCAL_BACKEND=tesseract` inserts a local raster OCR fallback between native WMF hints and live provider calls, and `run.json` safely serializes `local_backend` without exposing secrets.
- initial generalized WMF parser hardening step: known MathType matcher now coalesces adjacent WMF chunks with matching style metadata before signature matching, and the first rule-driven aggregate-price IR slice now closes `904/пр` formula `(2)` without adding a new exact-formula branch; broader token/layout parser work remains open.
- heuristic calc normalization for narrative/chained DOCX formulas: linearized examples with trailing references, textual prefixes, equality-result tails, semicolon clauses and parenthetical formulas can now emit expression-only or cleaned assignment `calc_expr`; narrow benchmark reruns improved `gate-metod-guide` from `0/25` to `21/25` and `gate-metod-521-pr` from `0/6` to `1/6` without touching provider/native coverage.
- native WMF recovery for `521/пр`: focused MathType signature rules now restore formulas `(2)-(6)` as native `mathtype_wmf_text_records` with structured `linear_text`/`display_latex`/`calc_expr`; focused rerun lifted `gate-metod-521-pr` to `5/6` native formulas and `6/6` calc_expr units, proving that a substantial part of the remaining DOCX gap is still recoverable from raw WMF signal.
- heuristic bracket normalization for `1/пр`: square brackets in linearized estimate formulas are now treated as ordinary grouping in the calc-expression path; focused rerun lifted `gate-metod-1-pr` from `18/49` to `23/49` calc_expr units without touching native WMF coverage, which means the remaining misses in that document are no longer simple grouping-syntax fallout.
- native WMF recovery for `1/пр`: inline drawings for formulas `(5)` and `(6)` turned out to be recoverable MathType fractions rather than plain text noise; focused rerun `20260528T072055Z` lifted `gate-metod-1-pr` to `25/49` calc_expr units and gave the document its first `2/49` native formulas, which shifts the next parser work from generic heuristic cleanup to the remaining short-fraction and sum families in the same document.
- follow-up short-fraction recovery for `1/пр`: formula `(8)` also proved recoverable through the same native WMF path; focused rerun `20260528T073325Z` lifted the document to `26/49` calc_expr units and `3/49` native formulas by restoring `К_(уст) = t_(max) / t_(min) <= 1,5`, so the remaining residue is now concentrated in heavier structural families like formula `(4)` rather than in small fractions.
- native sum-case recovery for `1/пр`: formula `(3)` also turned out to be a recoverable WMF pattern rather than noise; focused rerun `20260528T073910Z` restored `Н_(ВрП) = sum Н_(ВрЭ)`, lifted the document to `27/49` calc_expr units and `4/49` native formulas, and left the next parser work concentrated almost entirely in the multi-level fraction family around formula `(4)`.
- native multi-level fraction recovery for `1/пр`: formula `(4)` also proved recoverable through the WMF path once the surrounding where-clause and table/search artifacts were lined up; focused rerun `20260528T074505Z` restored `Н_(ВрЭ) = ЗТ_(эСР) × 100 / (Ч_(факт) × [100 - (Н_(пзр) + Н_(о) + Н_(тп))] × 60)`, lifted the document to `28/49` calc_expr units and `5/49` native formulas, and moved the next parser work from a single known anchor to broader fraction/layout residue.
- noisy fraction-family recovery for `1/пр`: formulas `(23)` and `(31)` also proved recoverable once the noisy linearized signature was tied back to the same denominator skeleton as formula `(4)` but without `Н_(тп)`; focused rerun `20260528T080557Z` restored `Н_(ВрИ) = ЗТ_(Иср) × 100 / (Ч_(общ) × [100 - (Н_(пзр) + Н_(о))] × 60)` and `Н_(ВрЭл) = ЗТ_(эСРл) × 100 / (Ч_(общ) × [100 - (Н_(пзр) + Н_(о))] × 60)`, lifted the document to `30/49` calc_expr units and `7/49` native formulas, and pushed the remaining residue away from this fraction family toward other noisy average/resource-cost patterns.
- noisy average/resource-cost recovery for `1/пр`: the same data-driven known-pattern contract now closes formulas `(24)` and `(25)` as `ЗТ_(Иср) = sum_(ф=1)^n_(ф) ЗТ_(1факт) / n_(ф)` and `ЗТ_(1факт) = ЗТ_(Vфакт) / V_(ф)`; focused and broader local regressions (`test_formula_representation_recovers_noisy_1pr_average_family`, full `tests.test_docx_converter`, full `tests.test_known_formula_patterns`) passed, so the next `1/пр` backlog moved beyond this average/resource-cost pair.
- noisy technical-cost recovery for `1/пр`: the same canonical known-pattern layer now also closes formulas `(15)`, `(17)`, `(19)`, `(20)` and `(22)` as machine-readable sums and ratio/product expressions for technical means, amortization, repair, machine and material costs; focused `test_formula_representation_recovers_noisy_1pr_technical_cost_family`, broader local regressions (`45/45`) and `scripts/validate_known_formulas.py` passed after repairing canonical/package sync, so the remaining `1/пр` residue is pushed further away from this resource-cost block toward other noisy formulas and broader parser work.
- noisy work-time and participation recovery for `1/пр`: the same canonical known-pattern layer now also closes formulas `(9)` and `(11)` as `Н_(тп) = Т_(тп) × 100 / Т_(вр)` and `К_(ср) = К_(уч) / Ч_(факт)`; focused regressions on both formulas, broader local regressions (`98/98`) and `scripts/validate_known_formulas.py` passed with canonical/package data still in sync, so the remaining `1/пр` residue moves further away from these straightforward ratio cases toward noisier formulas like `(10)`, `(12)` and `(13)` or broader parser work.
- noisy participation-coefficient recovery for `1/пр`: the same canonical known-pattern layer now also closes formula `(12)` as `К_(уч) = ТК × Ч_(i) × Т_(1раб) / Н_(ВрП)`; focused `test_formula_representation_recovers_noisy_1pr_participation_formula`, broader local regressions (`99/99`) and `scripts/validate_known_formulas.py` passed with canonical/package data still in sync, so the remaining nearby residue narrows further to formulas like `(10)` and `(13)` where the local evidence is still less decisive.
- noisy cameral participation recovery for `1/пр`: the same canonical known-pattern layer now also closes formulas `(35)` and `(36)` as `К_(срК) = К_(учК) / Ч_(общ)` and `К_(учК) = ТК × Ч_(i) × Т_(КАМ1) / Т_(КАМобщ)`; focused `test_formula_representation_recovers_noisy_1pr_cameral_participation_family`, broader local regressions (`100/100`) and `scripts/validate_known_formulas.py` passed with canonical/package data still in sync, so the remaining residue shifts further away from repeated participation-family shapes and back toward evidence-blocked formulas like `(10)` and `(13)` or the later noisy formulas `(37)`-`(39)`.
- noisy additional-cost recovery for `1/пр`: the same canonical known-pattern layer now also closes formula `(37)` as `Н_(ДЗ) = ДЗ × 100 / С_(р)`; focused `test_formula_representation_recovers_noisy_1pr_additional_cost_formula`, broader local regressions (`101/101`) and `scripts/validate_known_formulas.py` passed with canonical/package data still in sync, so the remaining nearby residue shifts further away from standalone percentage-ratio cases and toward evidence-blocked formulas `(10)` and `(13)` or the later noisy participation formulas `(38)` and `(39)`.
- noisy estimated-work participation recovery for `1/пр`: the same canonical known-pattern layer now also closes formulas `(38)` and `(39)` as `К_(учО) = ТК_(о) × Ч_(Оi) × Т_(Оi) / Т_(Ообщ)` and `К_(срО) = К_(учО) / Ч_(Ообщ)`; focused `test_formula_representation_recovers_noisy_1pr_estimated_work_participation_family`, broader local regressions (`102/102`) and `scripts/validate_known_formulas.py` passed with canonical/package data still in sync, despite the OCR `П/О` confusion inside noisy token `(39)`, so the remaining local residue narrows mainly to evidence-blocked formulas `(10)` and `(13)` plus the still-unreplayed benchmark threshold path.
- first table-hardening sprint: `pdf_text` and `pdf_scan` now share one table normalization contract with dominant-width inference, continuation-line merge and explicit `table_structure_warning` for unresolved ragged tables; DOCX `table_cell` units preserve multiline text and can carry machine-readable `formula` metadata when a formula-like line is present inside the cell.
- table benchmark anchor baseline: `src/doc_converter/sample_expectations.py` и `scripts/validate_sample_expectations.py` делают representative sample expectations executable; `samples/manifest.table-anchors.jsonl` и expected specs для `sample_009`/`sample_018`/`sample_020` закрепляют measured table contour, а fresh run `runs\table-anchors\runs\20260528T092227Z` подтверждает `sample_009`/`sample_018` как stable text-layer anchors и `sample_020` как OCR-blocked scan baseline.
- native WMF recovery for `904/пр`: visual inspection plus raw WMF chunk signatures first turned another noisy DOCX outlier into a narrow native slice, and follow-up rule-driven IR assembly closed formula `(2)` as well; focused rerun `20260526T205614Z` now leaves the document at `6/7` native formulas and `7/7` calc_expr units, with only formula `(6)` remaining on the heuristic plain-text path.
- native WMF recovery for `534/пр`: rendered WMF plus nearby prose disambiguated another formula-rich DOCX outlier; focused rerun lifted `gate-metod-534-pr` from `0/5` to `4/5` native formulas and from `2/5` to `5/5` calc_expr units, leaving only formula `(5)` on the heuristic plain-text path.
- formula-recognition/operator HTML follow-up: postprocess теперь покрывает `formula_image` и residual `formula` units без machine-readable `calc_expr`, packaged EXE ищет `.env.local` рядом с `sys.executable`, а human-readable HTML больше не отправляет в MathJax low-confidence heuristic formulas и показывает распознанные `formula_image` units как readable formula block со ссылкой на исходный asset.
- heuristic calc layer for DOCX formulas: generic `docx_text_linearized` formulas теперь могут получать `calc_expr` и `variables` без hardcoded formula signature, если выражение удалось безопасно нормализовать в линейную arithmetic form; fresh `812/пр` run подтвердил это для формул `ДЗ_(вП)` и `С_(Свлс) = ПЗ1_(п) + ПЗ2_(п) x S_(влс)`.
- safe calc evaluator and richer DOCX arithmetic syntax: operator can now evaluate `calc_expr` through CLI `evaluate-formula`, while heuristic DOCX parsing additionally supports percentages `%` and powers `^`; on Windows the supported operator path is `--values-file` with BOM-safe JSON reading.
- dependency-aware document formula evaluation: operator can now run `evaluate-document-formulas` against `document.v1.json`, get per-formula machine-readable statuses and reuse already computed targets inside the same document; DOCX parser also collapses line-wrap multiply artifacts like `x x` before tokenization so wrapped formulas keep a usable `calc_expr`.
- first-class human-readable QC export: shared renderer `src/doc_converter/human_readable.py` now emits both `human-readable.md` and `human-readable.html`; dedicated `scripts/export_human_readable_html.py` can export a single canonical package or an entire `run_dir` into `human-readable-index.html`, and the GUI exposes this path via an `HTML QC` button for immediate browser-based quality review.
- root-level processed documents catalog: каждый run сохраняет `processed-documents-catalog.json` и `processed-documents-catalog.xlsx` с исходным именем файла, папкой документа, итоговым статусом/issue и hyperlinks на основные обработанные артефакты.
- frozen schema packaging: Windows EXE теперь получает локальный каталог `schemas` в bundle, а runtime schema resolver ищет схемы и в `dist\...\_internal\schemas`, поэтому operator GUI больше не падает на старте обработки из-за missing `run.v1.schema.json`.
- production roadmap S0.1 baseline stabilization: DOCX inline-glyph unittest flake закрыт на уровне тестового cache discipline и canonical variant assertions; `ruff check src tests scripts`, `pyright` и 5 подряд `unittest discover` проходят зелёно.
- production roadmap S1.1 contracts catalog: downstream-facing `processed-documents-catalog.v1`, `chunks.v1`, `chunk-source.v1` и `formula-recognition.v1` зафиксированы в `docs/contracts.md`, drift защищён snapshot-тестом, а run-package validator проверяет `formula-recognition.jsonl` sidecars.
- production roadmap S1.2 known formula patterns data: MathType known-pattern recovery больше не зашит в `docx.py`; canonical JSON + package data, schema validation, export/sync script и regression tests позволяют добавлять новые known formulas через data artifact.
- production roadmap S1.3 agent run metadata + universal validator: новые run packages теперь schema-valid только с `agent_run_metadata`, CLI/runner фиксируют `agent_id/agent_version/task_id/parent_run_id`, `validate_run_package.py` сохраняет legacy validation path через fallback metadata, а `scripts/validate_document_package.py` валидирует все `document.v1.json` и optional `formula-recognition.jsonl` sidecars в run directory.
- production roadmap S2.1 DOCX package split: монолит `src/doc_converter/converters/docx.py` заменён на `src/doc_converter/converters/docx/` с smaller modules `pipeline.py`, `inline_glyph.py`, `formulas/text.py` и `formulas/wmf.py`; package `__init__.py` сохраняет прежний import surface, а focused DOCX, CLI/formula-recognition и full-suite gates подтверждают отсутствие behavioral drift.
- production roadmap S2.2 runner package split: orchestration, startup path validation, resume reuse, processed catalog и formula postprocess вынесены в `src/doc_converter/run/`, а `src/doc_converter/runner.py` остался thin import-compatible wrapper для CLI/GUI и тестов.
- production roadmap S2.3 shared tables package: dominant-width inference, continuation merge и `table_structure_warning` вынесены в `src/doc_converter/tables/`; `pdf_text` и `pdf_scan` теперь используют один parser, а fresh table-anchor run `20260529T162149Z` сохраняет `sample_009/018` expectations без regressions.
- production roadmap S2.4 converter protocol and route registry: `inventory` и `run.orchestration` теперь dispatch-ят через shared `doc_converter.converters` registry + `ConverterProtocol`, runner tests патчат lookup layer, а opt-in dummy `txt` converter regression доказывает extensibility без изменения default supported-format contract.

Следующий backlog:

- production roadmap S9.2: nightly burn-in evidence и первый GitHub-hosted run поверх уже заведённого nightly workflow.
- production roadmap S9.3: release automation поверх стабильного nightly/regression контура.
- отдельный security follow-up: parser-level hardening для PDF/XLSX только если эти surfaces станут release-critical.
- production roadmap S5.1: formula corpus expansion и повышение benchmark thresholds поверх уже закрытых S4.2/S4.3 foundations.
- отдельный architecture follow-up: вывести `src/doc_converter/formula_benchmark.py` из oversize-состояния без ломки benchmark CLI/report contracts.
- table benchmark follow-up на `sample_009`, `sample_018` и `sample_020`: next sprint должен не создавать baseline с нуля, а снижать `table_structure_warning` density на text-layer anchors, вывести explicit negative/control false-positive contour и устранить OCR blocker на `sample_020`, чтобы scan route тоже вошёл в measured table loop.
- richer DOCX table semantics: после formula-in-cell closure следующий backlog лежит в header-like rows, merged-cell hints и richer review signals для operator QC.
- formula production hardening formalized в `docs/formula-production-plan.md`: broader generalized WMF parser (P1-02), remaining structural residue в `1/пр` beyond the already closed noisy fraction/average-resource-cost/technical-cost/work-time/field-participation/cameral-participation/additional-cost/estimated-work-participation families, local OCR production decision/guardrails и rolling verdict loop остаются отдельным следующим contour после table benchmark loop.
- optional OCR helper profile (`jbig2`, `pngquant`, `verapdf`) по мере необходимости.
- installer polish или следующий versioned portable package только при новом installable feature bundle.
- tuning heuristic semantic extraction по результатам новых production-like пакетов.

## 3. Релизные блоки

| Блок | Статус |
| --- | --- |
| Baseline and inventory | Готово |
| State foundation | Готово |
| Memory discipline | Готово |
| Deterministic workflow и hooks | Готово |
| Specialist agents и routing | Готово |
| Evaluation и self-review | Готово |
| Release discipline | Готово |

## 4. Release gates

| Gate | Условие |
| --- | --- |
| Gate 1 | Все state docs заведены и согласованы — выполнено |
| Gate 2 | Repo-memory описана и инициализирована — выполнено |
| Gate 3 | Lifecycle hooks и stop budgets описаны — выполнено |
| Gate 4 | Routing matrix и specialist agents заведены — выполнено |
| Gate 5 | Eval loop и regression log заведены — выполнено |
| Gate 6 | Release checklist и runbook готовы — выполнено |

## 5. Approval points

До Sprint 6 все risky production-like действия считаются вне рамки автоматического исполнения. Их approval points должны быть описаны в release documentation и guardrails.

## 7. Текущий release risk

Предыдущие critical-path risks по structured CLI/operator contract, structured runtime telemetry contract, input hardening baseline, missing leak gate и protected merge surface закрыты в S6.1-S9.1; ближайший critical path теперь смещён на burn-in нового nightly full e2e и на hosted proof уже добавленной release automation в S9.2-S9.3.

Leak-gate risk закрыт предметно: CI теперь проверяет git-tracked репозиторный контур через Gitleaks без broad filesystem scan по локальным `.venv`/`dist` артефактам, а custom rule доказан synthetic canary-run без ослабления default secret rules.

Nightly infrastructure уже заведена, но burn-in evidence ещё нет: hosted runner не видит внешний `D:\ФСНБ\...` corpus, поэтому full formula manifest идёт как monitor-only contour без thresholds, а required regression gate остаётся на CI-safe subset. Отдельный remaining risk в auto-issue path тоже локализован: `agent_id` будет точным для новых PR с заполненным template field, а исторические merges используют fallback на `head_ref` и author login.

Release automation path уже есть в git-tracked виде, но первый hosted proof ещё не снят: стабильный `v0.x.y` tag обязан иметь точную секцию в `CHANGELOG.md`, после чего `.github/workflows/release.yml` должен пересобрать portable zip, checksum и опубликовать GitHub Release без ручной публикации. Пока этого GitHub evidence нет, remaining risk для S9.3 чисто операционный, а не кодовый.

Formula roadmap risk теперь сузился до двух реальных внешних доказательств: formulas `(10)` и `(13)` по `gate-metod-1-pr` остаются evidence-blocked без локально доступного source DOCX/дополнительного артефакта, а benchmark threshold uplift нельзя честно перевыполнить без fresh rerun на этом исходнике. После локального закрытия formulas `(37)`-`(39)` других неблокированных `1/пр` slices в текущей среде больше не осталось.

Formula/OCR/catalog provider abstractions и artifact redaction boundary больше не блокируют v1.0 acceptance по этой оси: у `FormulaProvider`, `OcrBackend` и `CatalogWriter` уже есть как минимум по две реализации, а redaction path закрывает и primary artifacts, и compatibility mirrors.

Операционных blocker-ов для релиза v0.3.0 не осталось. Последний внешний production audit больше не оставляет runtime- или CI-blocker: self-ingestion guard и unsupported accounting закрыты в runtime, OCR traineddata direct downloads проверяются по pinned SHA-256, а lint/type/pip/package smoke выполняются в штатном workflow. Runner monolith risk тоже закрыт: orchestration теперь живёт в smaller `run/` modules, а compatibility surface сохраняется через thin wrapper. Route-coupling risk закрыт следующим архитектурным шагом: `inventory` и `run.orchestration` теперь используют shared converter registry вместо hard-coded format-specific imports и route branches. Table parser ownership тоже приведён к архитектурному baseline: dominant-width inference, continuation merge и `table_structure_warning` больше не размазаны по converters, а живут в shared `tables/` package с подтверждённым fresh anchor run `20260529T162149Z`. OCR/backend coupling risk тоже сузился: `pdf_scan` теперь dispatch-ит side effects через `OcrBackend`, а root catalog emission идёт через `CatalogWriter`. Secret leak risk по run/package artifacts тоже локализован: общий redaction helper закрывает primary JSON/JSONL, legacy compatibility mirrors и XLSX catalog output одним boundary-level правилом. Stable-ordering risk тоже локально закрыт: finalized inventory ordering и duplicate primary selection больше не зависят от filesystem iterator order, а dedicated rerun test удерживает identical `manifest.jsonl` для clean runs. Incremental benchmark risk тоже сузился: unchanged formula cases больше не требуют повторного conversion path, manifest/gold drift инвалидирует cache key, а `required_gate` пересчитывается на каждом rerun поверх полного набора case reports. Полный corpus timing proof для `<30s` в этой сессии не переизмерен из-за local usage-limit rejection на heavy run, поэтому performance threshold остаётся operational follow-up, а не code-correctness blocker. Новый table benchmark contour остаётся measured: `sample_009` и `sample_018` держат executable row/cell baseline, warning density всё ещё высокая, а `sample_020` по-прежнему OCR-blocked scan baseline с `partial_success` и `OCRmyPDF failed`. Значит ближайший release-risk по tables теперь ещё уже локализован: не parser drift между routes, а warning-heavy parse, missing negative/control false-positive contour и OCR blocker на одном scan anchor. Protected merge risk тоже закрыт предметно: `main` держит strict required contexts, а same-repo PR с label `agent:autonomous` может получить auto-merge через workflow на base branch. Release automation risk тоже сузился: кодовый path закрыт через `release.yml` + changelog-backed `release-notes.md`, и дальше нужен только первый hosted tag proof. Следующий critical-path release-risk смещается в основном на отсутствие nightly full e2e burn-in и hosted evidence по S9.2/S9.3, а не на уже закрытые S6.x/S7.x/S9.1/S3.1/S3.2/S3.3/S4.1/S4.2 controls. Formula benchmark manifest по-прежнему зелёный на curated `metod`/`SP` set и подтверждён run `20260526T054732Z` под executable policy `samples/formula-benchmark.thresholds.json`, поэтому formula backlog можно возвращать после operator-surface tranche. Optional OCR helpers `jbig2`, `pngquant`, `verapdf` остаются необязательными и не блокируют core OCR path. Для harness layer остаточный риск теперь в основном операционный: thresholds уже executable и перепроверены, но telemetry, generated scorecard, generated weekly eval, machine-readable weekly reviews и schedule helper всё ещё требуют дисциплины обновления, а из repo-wide file-size debt остался только `src/doc_converter/formula_benchmark.py`.

## 8. Последняя сборка

- Команда: `powershell -ExecutionPolicy Bypass -File scripts\build-windows.ps1 -Name DocumentConverter`.
- Результат: `dist\DocumentConverter\DocumentConverter.exe`.
- Размер EXE: около 7.04 MB.
- Статус: build succeeded; automated launch smoke passed.

## 9. Portable release package

- Команда: `powershell -ExecutionPolicy Bypass -File scripts\package-release.ps1 -Name DocumentConverter -Version 0.3.0 -SkipBuild`.
- Результат: `dist\release\DocumentConverter-0.3.0\DocumentConverter-0.3.0-windows-portable.zip`.
- Дополнительно: `.sha256.txt` checksum и `release-notes.md`, которые теперь рендерятся из `CHANGELOG.md`.
- SHA-256: `846177da652775571b97575ecd5006a7d9b01d3eaff985b5dfd8116ccce0fea4`.
- Стратегия релиза: portable zip, installer не требуется для v0.3.0.

## 9.1 Release automation

- Trigger: `push` тега `v*`.
- Workflow: `.github/workflows/release.yml`.
- Публикуемые артефакты: portable zip, `.sha256.txt`, GitHub Release notes из `CHANGELOG.md`.
- Локальная smoke-проверка: `powershell -ExecutionPolicy Bypass -File scripts\package-release.ps1 -Name DocumentConverter -Version 0.3.0-nightly -SkipBuild`.
- Remaining gap: нужен первый hosted `v*` tag proof в GitHub Actions/Release UI.

## 10. Последний representative pilot

- Команда: `.\.venv\Scripts\python.exe scripts\run_sample_pilot.py --clean`.
- Результат: 21 processed, 21 success, 0 partial_success, 0 failed.
- Routes: `docx_native: 8`, `pdf_text: 10`, `pdf_scan: 3`.
- Route mismatches: 0.

## 11. OCR runtime preflight

- Команда: `.\.venv\Scripts\python.exe -m doc_converter.cli check-ocr`.
- Текущий статус: `ready`.
- Tools: `ocrmypdf` в `.venv\Scripts`, `tesseract` и `gswin64c` через `scoop`.
- Languages: `eng`, `rus`, `osd` доступны.

## 12. OCR runtime install path

- Check-only команда: `powershell -ExecutionPolicy Bypass -File scripts\install-ocr-runtime.ps1 -CheckOnly`.
- Предпочтительный path: `.venv + scoop`, без elevated PowerShell, если `scoop` доступен.
- Fallback path: `winget + choco`, если `scoop` отсутствует.
- Integrity check: direct `eng`, `rus`, `osd` traineddata downloads проверяются по pinned SHA-256; mismatch artifact удаляется и установка останавливается fail-fast.
- Документация: `docs/ocr-runtime-windows.md`.

## 12.1 Weekly eval schedule helper

- Check-only команда: `powershell -ExecutionPolicy Bypass -File scripts\register-agent-eval-schedule.ps1 -CheckOnly`.
- Назначение: optional Windows Scheduled Task поверх `scripts\refresh_agent_eval.py --check --check-markdown`.
- Safety: без `-CheckOnly` helper не заменяет существующую task без явного `-Force`.

## 13. Synthetic E2E и GUI smoke

- Synthetic e2e: `.\.venv\Scripts\python.exe scripts\run_synthetic_e2e.py --clean` даёт schema-valid run package, `processed-documents-catalog.json`, `processed-documents-catalog.xlsx` и `chunks.v1.jsonl`.

- Python startup smoke: `.\.venv\Scripts\python.exe -m unittest tests.test_gui_import -v`.
- EXE startup smoke: `dist\DocumentConverter\DocumentConverter.exe` стартует как процесс и не завершается мгновенно.

## 14. Harness assets validation

- Команда: `.\.venv\Scripts\python.exe scripts\validate_harness_assets.py`.
- Результат: `status: ok`, `features: 51`, `validated: 50`, `active: 1`, `backlog: 0`, `telemetry_entries: 93`.
- Назначение: ранний провал CI при потере feature spine, feature-traceability markers в шаблонах, machine-readable telemetry companion, generated scorecard companion, generated weekly eval companion, machine-readable weekly reviews source, markdown structured companion sync, qualitative weekly review evidence или core product-capabilities ссылок.

## 15. Latest Audit Remediation

- Команды: `.\.venv\Scripts\python.exe -m pip check`, `.\.venv\Scripts\python.exe -m ruff check src tests scripts`, `.\.venv\Scripts\python.exe -m pyright`, `.\.venv\Scripts\python.exe -m unittest discover -v`, `.\.venv\Scripts\python.exe scripts\run_synthetic_e2e.py --clean`, `powershell -ExecutionPolicy Bypass -File scripts\build-windows.ps1 -Name DocumentConverter`, `powershell -ExecutionPolicy Bypass -File scripts\smoke-test-windows-exe.ps1 -ExePath dist\DocumentConverter\DocumentConverter.exe`, `powershell -ExecutionPolicy Bypass -File scripts\package-release.ps1 -Name DocumentConverter -Version 0.3.0 -SkipBuild`, `powershell -ExecutionPolicy Bypass -File scripts\register-agent-eval-schedule.ps1 -CheckOnly`, `powershell -ExecutionPolicy Bypass -File scripts\install-ocr-runtime.ps1 -CheckOnly`, OCR traineddata mismatch smoke.
- Результат: все проверки passed; synthetic run `runs\synthetic-e2e-output\runs\20260523T101722Z`, build/smoke/package прошли на локальной `.venv`, frozen schema lookup подтвердил `dist\DocumentConverter\_internal\schemas`, schedule helper check-only прошёл, OCR helper check-only и mismatch smoke прошли, portable release сформирован в `dist\release\DocumentConverter-0.3.0`.
- Clean-room setup: отдельная внешняя Python 3.12 venv с `pip install -e .[build,dev]` и `pip check` тоже прошла успешно.
- Local env note: предыдущий `pip check` fail был вызван contaminated `cp313` wheels для `charset-normalizer` и `fonttools` внутри старой `.venv`; force-reinstall этих двух пакетов восстановил корректный `cp312` state без изменений project dependencies.
- DOCX inline symbol recognition hotfix: `src/doc_converter/converters/docx.py` теперь линейризует run-level `subscript`/`superscript`, пытается распознавать маленькие inline WMF/EMF/PNG drawings как Unicode-символы и оставляет `[INLINE_DRAWING:filename]` только как fallback; targeted `tests.test_docx_converter` и fresh smoke на реальном `421/пр` подтверждают, что canonical package теперь сохраняет `j = 1 ÷ J, где:` без silent gap внутри формулы.
- DOCX inline symbol vocabulary expansion: recognizer теперь покрывает дополнительные операторы, кванторы и геометрические/логические glyphs (`+`, `-`, `=`, `<`, `>`, `∏`, `∂`, `∇`, `∅`, `∀`, `∃`, `∝`, `∥`, `⊥`, `∠`, `⊕`, `⊗`, `∴`, `∵`); новый regression test прогоняет их через весь DOCX route и подтверждает нормальную Unicode-линеаризацию.
- DOCX MathType WMF formula extraction: для формульных WMF-картинок `421/пр` converter теперь сначала читает MathType WMF text records и только затем падает в glyph/raster fallback; targeted regression и single-doc smoke подтвердили восстановление простых диапазонов и обозначений с индексами, а сложные суммовые формулы зафиксированы как следующий scope для `LaTeX/MathML + calculation AST` вместо plain text-only extraction.
- DOCX formula representation round-trip: canonical `formula` unit теперь может хранить `display_latex`, `calc_expr`, `variables`, `confidence` и `warnings`; fresh `421/пр` run создал machine-readable formula block для формулы 1.1 и `scripts/export_human_readable.py` восстановил её в `human-readable.md` как KaTeX-compatible block с расчётным code expression.
- DOCX formula stability remediation: after visual comparison, repeated MathType WMF signatures in `421/пр` now restore formulas 1, 1.2, 2, 3.1, 4 and 5 as structured LaTeX/calc expressions; normalized range formulas no longer duplicate linear text in readable export, and final Markdown/HTML checks show no `PPV=`, `t1Ttt`, `k1К`, `ЦСТ=` or `\mathrm{sum}` artifacts.
- DOCX heuristic calc-expression remediation: generic `docx_text_linearized` formulas now emit `calc_expr`/`variables` for safe linear arithmetic expressions, including identifiers with digits in the base token (`ПЗ1_(п)`, `ПЗ2_(п)`); fresh single-doc run on `812/пр` confirmed real formulas `ДЗ_(вП)` and `С_(Свлс)` as machine-computable output and regenerated `human-readable.md` from the updated canonical package.
- First-class HTML QC export: `src/doc_converter/human_readable.py` now acts as a shared readable renderer, `scripts/export_human_readable_html.py` builds per-document `human-readable.html` plus a run-level `human-readable-index.html`, and GUI operators can open this QC view directly через кнопку `HTML QC`; real run validation updated both `human-readable.html` and the new index for `812/пр`.
- GUI output-path autofill: when the operator changes the input folder, GUI now suggests a sibling output directory `<input>_output` automatically, while preserving a manually chosen separate output folder; runtime overlap/self-ingestion guard remains unchanged.
- Formula evaluation operator path: `src/doc_converter/formula_eval.py` and CLI subcommand `evaluate-formula` now evaluate the normalized `calc_expr` layer with a safe arithmetic subset only; real Windows validation confirmed the path with BOM-safe JSON values file and produced `S_Svls = 1340.0` for a calc_expr shape extracted from `812/пр`.
- Document-level formula evaluation path: `src/doc_converter/formula_eval.py` and CLI subcommand `evaluate-document-formulas` now walk `document.v1.json`, resolve intra-document formula dependencies through already computed targets and report unresolved inputs per formula; real Windows validation on `812/пр` found 41 `calc_expr` units, computed `S_Svls = 1340.0` and honestly surfaced 40 unresolved formulas without external values.
- XLSX native route validation: real workbook `Расчет стоимости этапов.xlsx` produced schema-valid run `runs\xlsx-sample-output-20260524T011906\runs\20260523T221907Z` with `status=success`, `route=xlsx_native`, 13 sheets, 8533 cell units, 1711 formula cells and 0 missing cached formula values. Residual risk: formulas are preserved, not recalculated by `openpyxl`.
- Env-based formula-recognition config: `src/doc_converter/config.py` now auto-loads `.env.local`/`.env` and process env overrides for both explicit `FORMULA_RECOGNITION_*` keys and shorthand OpenRouter-style aliases like `LLM_PROVIDER`, `OPENROUTER_MODEL`, `FORMULA_MODEL` and `OPENROUTER_API_KEY`; if OpenRouter credentials are present and no dedicated formula override is set, formula recognition defaults to `openai/gpt-4o`, while `src/doc_converter/runner.py` still writes only `provider`, `model` and `configured` to `run.json` without serializing the secret.
- Formula-recognition postprocess: `src/doc_converter/formula_recognition.py` now enriches `formula_image` units after extraction, first using local WMF/MathType hints and then OpenRouter fallback for unresolved assets; the OpenRouter call now asks for strict `json_schema` output so the returned formula block is more reliable for machine-readable downstream calculations. Automated validation still uses mocked provider responses only, so live provider quality and cost need an operator-triggered real run.
