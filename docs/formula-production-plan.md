# Formula Production Plan

Дата: 2026-05-26
Статус: execution backlog для post-v0.3.0 hardening формул
Горизонт оценок: 1 senior engineer, Windows-first workflow, оценки в engineer-days

## 1. Подтверждённая база

- Текущий релизный контур v0.3.0 закрыт в declared scope, поэтому формульный follow-up нужно вести как отдельный product-hardening backlog, а не как emergency release fix.
- Деградация качества распознавания формул сейчас вызвана не общим OCR-регрессом, а зависимостью DOCX route от hardcoded MathType WMF signatures и ограниченного WMF text-record extraction. Когда native path не срабатывает, pipeline падает в `docx_text_linearized` с низкой уверенностью.
- Для этого продукта недостаточно визуально восстановить формулу для человека: целевой результат — machine-readable formula contract, чтобы downstream-модель или rule-based evaluator могли подставить исходные значения и применить выражение автоматически. Поэтому приоритет остаётся за `formula.calc_expr` и связанными `variables`/`confidence`, а `display_latex` сам по себе считается лишь промежуточным слоем или partial recovery.
- По реальным якорям уже есть две устойчивые опоры: `421/пр` подтверждает ценность native WMF extraction и signature-based remediation, а `812/пр` подтверждает, что линейные formula units могут давать usable `calc_expr` для downstream расчёта.
- Production-like corpus для benchmark уже известен и доступен: `metod` содержит 52 DOCX, `SP` содержит 343 PDF и 1 DOCX. Это достаточно, чтобы разделить formula-rich positive set и formula-light negative/control set.
- Refreshed full manifest run `runs\formula-benchmark\runs\20260525T193008Z` завершён зелёно после guide/`521/пр` uplift и синхронизации benign gold drift в anchor `421/пр`: `29/29` entries доступны, `11/11` gold checks passed, control `SP` set подтвердил отсутствие ложных formula positives, а corpus totals теперь дают `281` formula units, `181` calc_expr units, `44` native WMF units, `237` heuristic units и `256` low-confidence units.
- Поверх refreshed baseline теперь зафиксирован versioned required gate в `samples/formula-benchmark.thresholds.json`: benchmark по умолчанию оценивает `anchor`, `gate`, `control` и `overall` против этого policy, пишет `tier_summaries` и `required_gate` в report, а `rolling` пока остаётся monitor-only tier до следующего полного rerun после локальных uplifts по `1/пр`, `904/пр` и `534/пр`.
- Полный rerun уже проверен под этим gate: `runs\formula-benchmark\runs\20260526T054732Z` дал `status: ok`, `required_gate.status: passed`, `194/281` `calc_expr` units и `53/281` native WMF units; на `gate` tier это означает `calc_expr_coverage: 0.6776`, `native_coverage: 0.1858`, `low_confidence_rate: 0.929`, то есть policy зафиксирована как рабочий conservative floor, а следующий backlog снова смещается к DOCX residue/parser work, а не к threshold definition.
- Formula-recognition provider и любой LLM path в этой архитектуре остаются не основным route, а последним selective fallback только для тех `formula_image` или residual `formula` units, которые automatic stack (`native parser -> heuristic normalization -> optional local OCR`) не смог довести до machine-readable contract. Практическое правило на текущем этапе: если standard path уже собрал usable `calc_expr`, такой unit не должен уходить в LLM только из-за low-confidence или heuristic provenance.
- Этот refreshed baseline показывает, что последние DOCX slices реально двигают corpus quality, но следующий прирост качества всё ещё лежит прежде всего в formula-rich DOCX cases из `metod`, а не в PDF/control contour: negative set чистый, `521/пр` почти вышел в native path, `904/пр` после follow-up IR slice дошёл до `6/7` native и `7/7` `calc_expr`, а `534/пр` largely closed, но residual `1/пр` и generalized WMF backlog всё ещё держат основной продуктовый риск.
- Focused rerun `runs\formula-benchmark\runs\20260525T194430Z` показал ещё один дешёвый heuristic uplift для `1/пр`: square-bracket grouping в сметных formulas теперь нормализуется в calc-expression path и поднимает документ с `18/49` до `23/49` calc_expr units без нового WMF work. Это сужает остаток `1/пр` до более шумных formulas и убирает bracket syntax из ближайшего backlog.
- Follow-up native WMF slice на `1/пр` уже подтвердил, что документ не является purely-heuristic outlier: rerun `runs\formula-benchmark\runs\20260528T072055Z` восстановил formula `(5)` и `(6)` из inline MathType WMF fractions, поднял документ до `25/49` calc_expr units и дал первый `native_coverage = 0.0408` (`2/49`). Это подтверждает, что следующий прирост по `1/пр` лежит в продолжении native WMF family recovery, а не в раннем расширении LLM path.
- Второй short-fraction slice на `1/пр` закрепил этот вывод: rerun `runs\formula-benchmark\runs\20260528T073325Z` восстановил formula `(8)` как `К_(уст) = t_(max) / t_(min) <= 1,5`, поднял документ до `26/49` calc_expr units и `3/49` native units. Значит remaining `1/пр` residue уже ещё уже локализован в более тяжёлых fraction/sum families, а не в generic linearized noise.
- Третий native slice на `1/пр` добавил и recoverable sum-case: rerun `runs\formula-benchmark\runs\20260528T073910Z` восстановил formula `(3)` как `Н_(ВрП) = sum Н_(ВрЭ)`, поднял документ до `27/49` calc_expr units и `4/49` native units. После этого дешёвые short-signature gains по документу почти исчерпаны, и следующий шаг уже естественно смещается к более сложной formula `(4)` и generalized WMF assembly.
- Четвёртый native slice на `1/пр` закрыл и этот remaining anchor: rerun `runs\formula-benchmark\runs\20260528T074505Z` восстановил formula `(4)` как `Н_(ВрЭ) = ЗТ_(эСР) × 100 / (Ч_(факт) × [100 - (Н_(пзр) + Н_(о) + Н_(тп))] × 60)`, поднял документ до `28/49` calc_expr units и `5/49` native units. Это означает, что ближайший backlog в `1/пр` теперь уже не в одном очевидном short-signature case, а в более общем fraction/layout residue.
- Пятый native slice на `1/пр` закрыл уже и следующий family-level residue без `Н_(тп)`: rerun `runs\formula-benchmark\runs\20260528T080557Z` восстановил formulas `(23)` и `(31)` как `Н_(ВрИ) = ЗТ_(Иср) × 100 / (Ч_(общ) × [100 - (Н_(пзр) + Н_(о))] × 60)` и `Н_(ВрЭл) = ЗТ_(эСРл) × 100 / (Ч_(общ) × [100 - (Н_(пзр) + Н_(о))] × 60)`, поднял документ до `30/49` calc_expr units и `7/49` native units. После этого remaining `1/пр` backlog смещается дальше от этой fraction family к другим noisy average/resource-cost patterns и broader parser generalization.
- Узкая нормализация linearized arithmetic formulas уже дала измеримый прирост без provider и без нового WMF parser: rerun на `gate-metod-guide` поднял `calc_expr_units` с `0` до `21`, а на `gate-metod-521-pr` — с `0` до `1`; наибольшую отдачу дали narrative/chained expression extraction, semicolon clauses и parenthetical formulas, значит часть backlog лежит не только в native WMF recovery.
- Focused native WMF slice на `521/пр` уже показал, что и второй соседний слой реально окупается: rerun `runs\formula-benchmark\runs\20260525T192109Z` поднял документ до `5/6` native formulas и `6/6` calc_expr units через recovery формул `(2)-(6)` из raw MathType WMF signatures. Это подтверждает, что remaining DOCX gap нельзя сводить только к OCR fallback или heuristic cleanup.
- Focused native WMF slice на `904/пр` подтвердил ту же логику на следующем outlier: initial rerun `runs\formula-benchmark\runs\runs\20260525T200228Z` поднял документ с `1/7` до `5/7` native formulas и с `1/7` до `6/7` calc_expr units через recovery формул `(1)`, `(3)`, `(4)`, `(5)` и `(7)`, а follow-up rule-driven IR rerun `runs\formula-benchmark\runs\20260526T205614Z` закрыл formula `(2)` и довёл документ до `6/7` native formulas и `7/7` calc_expr units. Remaining heuristic case теперь ограничен formula `(6)`, поэтому следующий DOCX residue смещается с `904/пр` на `1/пр` и broader WMF backlog.
- Focused native WMF slice на `534/пр` подтвердил третий high-yield DOCX case: rerun `runs\formula-benchmark\runs\runs\20260525T202349Z` поднял документ с `0/5` до `4/5` native formulas и с `2/5` до `5/5` calc_expr units через recovery формул `(1)-(4)`. Этот документ дополнительно показал, что дешёвый rendered-WMF check вместе с surrounding prose нужен для сохранения корректных обозначений вроде `СЦ_(...)`, а не только для решения вопроса "recoverable / not recoverable".
- Для всех validation и benchmark-команд нужно явно использовать `.venv\Scripts\python.exe`; проектный test runner основан на `unittest`, а не на `pytest`.

## 1.1. Как в проекте решается преобразование и расчёт по формулам

- Мы решаем не задачу "красиво показать формулу", а задачу перевода формулы в machine-readable contract, который можно автоматически применить к входным данным. Поэтому целевой артефакт для продукта не картинка и не только `display_latex`, а связка `formula.calc_expr` + `formula.variables` + `confidence/provenance`.
- На входе формула может прийти в нескольких формах: native office math, MathType WMF внутри DOCX, линейная текстовая запись в абзаце, либо отдельный `formula_image` asset. Для downstream это всё равно один тип product-problem: нужно привести разные источники к одному каноническому формульному объекту.
- Первый и основной слой решения — native extraction. Для DOCX route мы сначала пытаемся взять максимально структурный сигнал: OMML/office math, WMF text records, layout hints и surrounding prose. Для MathType WMF конвертер извлекает text chunks, строит token/layout IR, rule-driven assembly восстанавливает формулу и рядом сохраняется provenance, чтобы было видно, из какого native источника она получена.
- Второй слой — heuristic normalization для безопасных случаев, где native path не закрыл формулу полностью, но в документе уже есть usable linearized запись. Здесь pipeline убирает narrative prefixes, reference tails, line-wrap артефакты, квадратные скобки, semicolon clauses и другие синтаксические шумы, после чего строит `calc_expr` для тех выражений, которые можно честно нормализовать без догадки по смыслу.
- После extraction/normalization любая формула приводится к единому contract: `linear_text`, `display_latex`, `calc_expr`, `variables`, `confidence`, `warnings`, `provenance`. Это позволяет downstream не знать, пришла формула из native WMF, из линейного DOCX текста или из selective fallback path: интерфейс в `document.v1.json` остаётся одинаковым.
- Вычисление идёт уже поверх этого contract, а не поверх исходного документа. Document-level evaluator проходит по `document.v1.json`, берёт только формулы с непустым `calc_expr`, подставляет переданные значения переменных, переиспользует уже вычисленные target-ы для зависимых выражений и явно возвращает missing inputs там, где данных не хватает. То есть система не "угадывает" недостающие значения, а честно отделяет calculable formulas от display-only/unresolved.
- `formula_image`, rasterized WMF и low-confidence residue не являются основным путём. Для них допускается selective enrichment: сначала local hints/local OCR backend, и только затем provider fallback. Этот слой нужен, чтобы дозакрывать остаток после automatic stack, а не заменять базовый parser для всего корпуса.
- Качество решения меряется не субъективно, а через benchmark-контур: `calc_expr_coverage` показывает, какая доля формул реально стала вычислимой, `native_coverage` показывает, какую долю мы закрыли структурным путём, `low_confidence_rate` и `provider_dependency_rate` ограничивают цену/риск fallback-ов, а control set страхует от ложных formula positives.
- В текущем состоянии проекта это уже подтверждено на реальных документах: `421/пр` показал ценность native WMF recovery, `812/пр` подтвердил пригодность heuristic `calc_expr` для downstream расчёта, а focused slices на `521/пр`, `904/пр` и `534/пр` показали, что rule-driven WMF parser даёт измеримый прирост именно в machine-readable и calculable coverage, а не только в визуальном качестве.

## 2. Backlog P0 / P1 / P2

### 2.0. Фактический статус по коду на 2026-05-26

| Пункт | Фактический статус | Проверенное evidence в коде / артефактах | Что осталось до закрытия |
| --- | --- | --- | --- |
| `P0-01` | Закрыто | `src/doc_converter/formula_benchmark.py`, `samples/formula-benchmark.thresholds.json`, `docs/build-and-run.md`, `docs/document-converter-acceptance.md`, `docs/release-status.md` уже используют единый gate language и required gate | Ничего |
| `P0-02` | Закрыто | Есть versioned manifest `samples/formula-benchmark.manifest.jsonl` с tier'ами `anchor/gate/control/rolling`, gold fixtures `samples/expected/formulas/421-pr.gold.json`, `812-pr.gold.json`, `sp-control-absence.gold.json` и exporter `scripts/export_formula_gold.py` | Ничего |
| `P0-03` | Закрыто | `src/doc_converter/formula_benchmark.py` теперь пишет отдельные `formula-summary.json` и `formula-summary.md` рядом с `benchmark-report.*`; summary включает per-document unresolved/backlog reasons и totals-level unresolved counts | Ничего |
| `P0-04` | Закрыто | Baseline run `runs/formula-benchmark/runs/20260525T193008Z` и подтверждающий rerun `runs/formula-benchmark/runs/20260526T054732Z` уже сохранены и используются как corpus evidence / threshold baseline | Ничего |
| `P1-01` | Закрыто | Добавлен formal spike note `docs/formula-wmf-ir-spike.md`; в коде введён первый IR слой (`WmfFormulaToken`, `WmfFormulaIR`, `_build_wmf_formula_ir`, `_classify_wmf_formula_ir`, `_assemble_wmf_formula_ir`) и зафиксирован `go` на generalized parser implementation | Ничего |
| `P1-02` | В работе | `src/doc_converter/converters/docx.py` уже умеет извлекать WMF text chunks, coalesce adjacent chunks, хранить WMF IR/provenance и закрывать первые rule-driven families; focused rerun `runs\formula-benchmark\runs\20260526T205614Z` довёл `904/пр` до `6/7` native formulas и `7/7` calc_expr units, а five-step reruns `runs\formula-benchmark\runs\20260528T072055Z`, `runs\formula-benchmark\runs\20260528T073325Z`, `runs\formula-benchmark\runs\20260528T073910Z`, `runs\formula-benchmark\runs\20260528T074505Z` и `runs\formula-benchmark\runs\20260528T080557Z` подняли `1/пр` до `7/49` native units и `30/49` calc_expr units через recovery формул `(3)`, `(4)`, `(5)`, `(6)`, `(8)`, `(23)` и `(31)` | Нужно расширить token/layout-driven IR дальше текущих short- и multi-level fraction families, сократить remaining structural/noisy residue в `1/пр` и продолжить уменьшать unresolved WMF patterns на Tier A/B более общими правилами |
| `P1-03` | Не закрыто, но есть pre-spike implementation evidence | `src/doc_converter/formula_recognition.py` и `tests/test_formula_recognition.py` уже подтверждают один local backend path (`tesseract`) | Не выполнено главное из spike: сравнение минимум двух локальных кандидатов, comparison matrix, reproducibility/latency/license decision и формальное `go / no-go` |
| `P1-04` | Частично закрыто | Formula cascade уже существует: `native parse -> local backend -> provider fallback` реализован в `src/doc_converter/formula_recognition.py`, stage вызывается из `src/doc_converter/runner.py`, а `formula-recognition.jsonl` и manifest counters пишутся автоматически | Ещё не доказано на benchmark evidence, что local backend даёт нужный quality/precision tradeoff и действительно снижает provider dependency на gate set; production role backend пока не принят |
| `P1-05` | Частично закрыто | Reproducible command уже есть через `scripts/run_formula_benchmark.py`, manifest/threshold policy versioned, anchor/control/gate/rolling tiers реально запускаются, docs фиксируют required gate | В `.github/workflows/` пока не видно benchmark-tier automation; в docs не доведена явная matrix `что запускать на PR / локально / перед release`, поэтому nightly-friendly gate ещё не закрыт полностью |
| `P2-01` | Закрыто | `docs/downstream-handoff.md` теперь явно разделяет `calculable_formula`, `display_only_formula`, `unresolved_formula`, фиксирует stable formula fields mapping и downstream classifier rules | Ничего |
| `P2-02` | Частично закрыто | `schemas/run.v1.schema.json` сериализует безопасный block `formula_recognition`, `runner.py` пишет `formula_recognition_attempted/recognized/provider_calls`, docs фиксируют default-off provider policy | Не хватает явных trigger thresholds для operator review, cost/latency guardrails и QC/report breakdown по `local_backend / provider / unresolved` |
| `P2-03` | Частично закрыто | В manifest уже есть `rolling` tier, а threshold policy делает его monitor-only, то есть зачаток rolling sampling существует | Нет явной weekly/release verdict loop с метками `better / same / worse / new pattern`, и rolling sampling ещё не доведён до telemetry/eval contour |

### 2.0.1. Явный автономный остаток

Если агент продолжает работу без нового пользовательского приоритета, default order должен быть таким:

1. Продолжить execution slices `P1-02`: взять noisy structural residue в `1/пр` или следующий repeatable WMF family и закрывать его через rule-driven IR assembly, а не через новую точечную signature ветку.
2. Вернуться к `P1-03` / `P1-04` / `P2-02` одним пакетом: сравнить `tesseract` с ещё одним локальным formula backend, принять production decision и закрепить operator/provider guardrails в QC outputs и docs.
3. Довести `P1-05`: описать и автоматизировать benchmark-tier matrix `PR / local / pre-release` в docs и CI/workflow.
4. Довести `P2-03`: превратить существующий `rolling` tier из monitor-only evidence в регулярный weekly/release review loop с короткими verdict'ами и telemetry integration.

До завершения этих шагов plan должен считаться не закрытым, а находящимся в стадии `parser/generalization + downstream contract hardening`, даже если отдельные focused document slices продолжают давать хороший локальный uplift.

### P0

#### P0-01. Синхронизировать formula acceptance gate и операторский runbook

Оценка: 1.5 дня

Статус: закрыто 2026-05-26 через versioned policy `samples/formula-benchmark.thresholds.json` и synced benchmark/docs language.

Definition of Done:

- `docs/document-converter-acceptance.md`, `docs/release-status.md` и `docs/build-and-run.md` используют один и тот же formula-specific gate language.
- Зафиксирован единый Windows command path для formula validation через `.venv\Scripts\python.exe` и `unittest`/CLI scripts.
- Определены обязательные benchmark-метрики: `native_coverage`, `low_confidence_rate`, `calc_expr_coverage`, `false_positive_rate`, `provider_dependency_rate`.
- В release/risk docs явно отделены `native WMF/OMML`, `local formula OCR` и `provider fallback` как три разных quality layer.

#### P0-02. Завести benchmark manifest и gold-format для формул

Оценка: 2 дня

Definition of Done:

- В репозитории есть versioned manifest для formula benchmark corpus с группами `anchor`, `gate`, `control`, `rolling`.
- Для `421/пр` и `812/пр` есть полный gold на уровне formula units: `linear_text`, `display_latex`, `calc_expr`, `confidence expectation`, `source_format expectation`.
- Для curated subset из `metod` и `SP` подготовлен минимально достаточный gold/label layer для formula presence-absence и quality checks.
- Формат gold-данных совместим с автоматическим сравнением и не требует ручного diff по HTML.

#### P0-03. Добавить formula benchmark artifacts в run-level outputs

Оценка: 2 дня

Definition of Done:

- Отдельный script или runner-stage генерирует `formula-summary.json` и `formula-summary.md` по каждому benchmark run.
- Summary показывает per-document counts по `source_format`, confidence buckets, `calc_expr` coverage и unresolved formulas.
- Для `421/пр` сохраняется автоматическая проверка на banned artifacts: `PPV=`, `t1Ttt`, `k1К`, `ЦСТ=`, `\\mathrm{sum}`.
- Артефакты пригодны для operator review без ручного открытия каждого `document.v1.json`.

#### P0-04. Зафиксировать baseline benchmark на 421/пр, 812/пр и curated production-like set

Оценка: 1.5 дня

Definition of Done:

- Выполнен baseline run на `421/пр`, `812/пр`, curated `metod` set и curated `SP` set.
- Сохранён baseline report с текущими значениями ключевых метрик и списком top unresolved formula patterns.
- Для каждого документа видна причина попадания в backlog: `native parser gap`, `local OCR candidate`, `provider-only`, `false positive`, `calc_expr gap`.
- Baseline report становится точкой сравнения для spike- и implementation-фаз.

### P1

#### P1-01. Провести spike по generalized WMF parser

Оценка: 2 дня

Definition of Done:

- Есть design note по промежуточному представлению WMF text records и layout hints.
- Spike покрывает минимум `421/пр`, `812/пр` и curated WMF assets из `metod`.
- Для unresolved WMF cases есть классификация: `parsable with rules`, `needs richer AST`, `needs OCR fallback`, `not enough signal`.
- Принято чёткое `go / no-go` решение на реализацию generalized parser.

#### P1-02. Реализовать data-driven WMF parser с provenance

Оценка: 4 дня

Definition of Done:

- DOCX converter использует не только hardcoded signatures, но и нормализованный WMF token stream с rule-based assembly.
- Для formula units сохраняется provenance: какой parser path сработал, какие warnings остались, почему confidence высокий или низкий.
- Existing WMF regressions в `tests/test_docx_converter.py` зелёные и дополнены новыми real-pattern cases.
- На anchor docs нет регрессии, а baseline unresolved WMF patterns сокращены по заранее согласованной цели.

#### P1-03. Провести spike по локальному formula OCR backend

Оценка: 2.5 дня

Definition of Done:

- Сравнены минимум два локальных кандидата для formula OCR/caption-free LaTeX recognition.
- Оценены качество, latency, Windows reproducibility, install weight и license fit.
- Определён целевой adapter contract, совместимый с текущим `formula_recognition` stage.
- Принято `go / no-go` решение по локальному backend и правилам его каскадного вызова.

#### P1-04. Интегрировать локальный backend в formula cascade

Оценка: 4 дня

Definition of Done:

- Formula pipeline умеет выполнять `native parse -> local formula OCR -> provider fallback` без смешения ролей.
- Локальный backend включается конфигом, не ломает offline workflow и не требует сетевого вызова.
- Для `formula_image` units и rasterized WMF assets сохраняются единые output fields: `linear_text`, `display_latex`, `calc_expr`, `confidence`, `warnings`, `provenance`.
- Benchmark показывает сокращение provider dependency на целевом gate set без роста false positives.

#### P1-05. Автоматизировать formula regression harness и nightly-friendly gate

Оценка: 1.5 дня

Definition of Done:

- Есть один reproducible benchmark command, который принимает manifest и пишет machine-readable report.
- Anchor docs выполняются как обязательный focused gate для всех изменений в formula-related code.
- Curated `metod`/`SP` subset может запускаться отдельно как расширенный quality gate без ручной переконфигурации.
- Документация описывает, какие benchmark tiers запускаются на PR, локально и перед очередным portable release.

### P2

#### P2-01. Закрыть downstream contract по machine-readable formulas

Оценка: 1.5 дня

Definition of Done:

- `docs/downstream-handoff.md` и schema/docs явно описывают минимальный machine-readable contract для formulas.
- Для downstream ясно разделены display-only formula, calculable formula и unresolved formula.
- Есть правила, когда `calc_expr` обязателен, когда допустим только `display_latex`, и как маркировать partial recovery.
- Operator и downstream consumer получают стабильные поля без угадывания по warnings/free-text.

#### P2-02. Добавить operational guardrails для formula providers и review-load

Оценка: 1 день

Definition of Done:

- В run metadata и QC summary видно, сколько formulas ушло в локальный backend, сколько в provider и сколько осталось unresolved.
- Определены trigger thresholds для operator review и для ручного решения о provider usage.
- У provider path есть явные cost/latency guardrails и default-off policy для обычного regression loop.
- Документация перестаёт смешивать quality improvement work и дорогой live-provider validation.

#### P2-03. Ввести rolling production-like formula sampling

Оценка: 1 день

Definition of Done:

- Есть rolling sample policy для `metod` и `SP`, не зависящая от ad hoc ручного выбора файлов.
- Weekly или release-candidate review фиксирует только отклонения от baseline, а не весь corpus заново.
- Для новых docs сохраняются короткие benchmark verdicts: `better`, `same`, `worse`, `new pattern`.
- Rolling sampling встроен в текущий telemetry/eval contour без отдельной ручной bookkeeping системы.

## 3. Technical Spike Plan

### 3.1. Generalized WMF Parser

Цель:

- Проверить, можно ли заменить рост hardcoded signature catalog на нормализованный parser поверх MathType WMF text records и layout hints.

Гипотеза:

- Для значимой доли unresolved DOCX formulas в WMF уже есть достаточно сигнала, чтобы восстановить не только линейный текст, но и устойчивое `display_latex`/`calc_expr` без OCR.

Scope:

- DOCX formulas, где есть WMF/EMF asset и уже доступен text-record extraction.
- Форматы результата: `linear_text`, `display_latex`, `calc_expr candidate`, `warnings`, `provenance`, `confidence`.

Non-goals:

- Полный MathML/OMML compiler.
- Растерный OCR для обычных scanned PDF formulas.
- Full symbolic math simplification.

Рабочие шаги:

1. Выгрузить representative WMF token streams из `421/пр`, `812/пр` и минимум 20 formula assets из curated `metod` subset.
2. Сформировать intermediate representation: text chunks, font/style hints, позиционные отношения, sub/superscript markers, fraction-like separators, operator clusters.
3. Прототипировать assembly rules для диапазонов, индексов, сумм, дробей, скобочных групп и переменных с кириллицей.
4. Сравнить результат spike с текущим signature-based path и оценить coverage delta по benchmark gold.

Выходные артефакты:

- Design note по IR и parser stages.
- Таблица pattern classes с примерами `solved / partially solved / unsolved`.
- Решение: `implement now`, `narrow to selected patterns`, или `stop and pivot to OCR-assisted path`.

Критерии успеха:

- Anchor docs не теряют уже восстановленные formulas.
- Spike даёт измеримое сокращение unresolved WMF cases на curated benchmark set.
- Новый parser path объясним через provenance, а не через очередной opaque набор signatures.

Критерии остановки:

- Если в большинстве unresolved cases text records слишком бедные или противоречивые, parser не расширяется дальше targeted signatures, а усилие переносится в local OCR fallback.

### 3.2. Local Formula OCR Backend

Цель:

- Проверить, нужен ли репозиторию локальный formula-specific OCR backend для `formula_image` units и rasterized formula assets до дорогостоящего provider fallback.

Кандидаты первого круга:

- Pix2Text как более широкий local formula/image pipeline.
- pix2tex / LaTeX-OCR как узкий baseline для cropped formula images.

Почему именно так:

- Эти классы инструментов ближе всего к observed gap: они решают задачу формульного распознавания как first-class capability, в отличие от общего OCR layer.

Scope:

- Только локальные formula/image backends с воспроизводимой установкой на Windows.
- Только integration contract, который возвращает те же поля, что текущий formula stage.

Non-goals:

- Замена native WMF parser для DOCX, где можно извлечь structured signal без OCR.
- Встраивание тяжёлого VLM/LLM в обычный regression loop.
- Немедленная упаковка в стандартный EXE без успешного quality spike.

Рабочие шаги:

1. Подготовить benchmark set из `formula_image` units, unresolved WMF assets после rasterization и нескольких scanned PDF formula crops.
2. Снять качество и latency на одинаковом corpus: exact/normalized text, LaTeX readability, operator noise, кириллица в индексах.
3. Проверить install reproducibility, зависимости, вес моделей и лицензионный fit для repo/runtime scope.
4. Определить integration policy: когда local backend вызывается всегда, когда только на unresolved native assets, и когда разрешён provider fallback.

Выходные артефакты:

- Candidate comparison matrix.
- Adapter contract для `formula_recognition` stage.
- Решение: `adopt`, `keep optional experimental`, или `reject for now`.

Критерии успеха:

- Локальный backend снимает заметную долю provider-eligible formulas на curated gate set.
- Качество не хуже текущего provider baseline на простых formula-image cases.
- Решение остаётся offline-capable и повторяемым на Windows workstation.

Критерии остановки:

- Если latency, install weight или шум распознавания делают backend непрактичным, он остаётся только как optional lab path, а production roadmap приоритизирует native parser и benchmark discipline.

## 4. Formula Benchmark Plan

### 4.1. Цели benchmark

- Отделить regression в native WMF path от regression в heuristic/local/provider layers.
- Измерять не только точность текста, но и полезность для downstream расчёта.
- Держать отдельный negative/control contour, чтобы не лечить recall ценой всплеска false positives.

### 4.2. Corpus tiers

| Tier | Корпус | Объём | Роль |
| --- | --- | --- | --- |
| A | `runs/single-421-input` + `runs/single-812-input` | 2 документа | Обязательные anchor docs для любой formula-related правки |
| B | curated subset из `D:\ФСНБ\Документы\Загрузка НПА\metod` | 12 из 52 DOCX | Formula-rich и mixed DOCX gate |
| C | curated subset из `D:\ФСНБ\Документы\Загрузка НПА\SP` | 8 PDF + 1 DOCX из 343 PDF + 1 DOCX | Formula-light control и heuristic stress |
| D | rolling sample из `metod` и `SP` | 10 `metod` + 20 `SP` на цикл | Release-candidate и weekly monitoring |

### 4.3. Правила отбора

Для Tier B (`metod`):

- 4 документа с явными MathType/WMF или embedded formula-image паттернами.
- 4 документа с линейными формулами и downstream-relevant arithmetic expressions.
- 2 документа смешанного типа, где формулы встречаются редко и важен контроль false positives.
- 2 коротких или structurally awkward документа для проверки robustness, а не только quality на happy path.

Для Tier C (`SP`):

- 4 formula-light PDF как negative control.
- 2 PDF с тяжёлой таблицей/рисунками, где возможны ложные formula detections.
- 2 более крупных PDF для оценки review load на длинных документах.
- 1 DOCX как дополнительный non-anchor control для native DOCX path вне `metod`.

### 4.4. Аннотация и gold layer

- `421/пр` и `812/пр`: полный gold по всем formula units.
- Curated `metod`: gold по всем formula-bearing fragments и по минимум 2 соседним non-formula fragments на документ.
- Curated `SP`: gold на formula absence для control pages и точечный gold на suspected formula candidates.
- Для каждого gold entry фиксируются ожидаемые поля: `unit_type`, `source_format`, `linear_text`, `display_latex`, `calc_expr`, `confidence bucket`, `should_require_review`.

### 4.5. Метрики

| Метрика | Что показывает |
| --- | --- |
| `formula_unit_recall` | Сколько gold formulas вообще найдено как formula-capable units |
| `formula_unit_precision` | Сколько предсказанных formula units действительно являются формулами |
| `native_coverage` | Долю formulas, закрытых native WMF/OMML path без OCR/provider |
| `low_confidence_rate` | Долю formulas, оставшихся в heuristic или unresolved состоянии |
| `calc_expr_coverage` | Долю formula units, полезных для downstream вычисления |
| `provider_dependency_rate` | Насколько pipeline зависит от дорогого внешнего fallback |
| `false_positive_rate` | Ложные formula detections на control corpus |
| `banned_artifact_count` | Возврат старых мусорных форм вроде `PPV=` или `\\mathrm{sum}` |
| `review_load_per_100_pages` | Насколько operator review остаётся практичным |

### 4.6. Phase gates

#### Gate B0. Baseline capture

- Anchor docs и curated sets запускаются единым benchmark command.
- Baseline report сохранён и versioned.
- Все последующие изменения сравниваются именно с ним, а не с ручными впечатлениями.

#### Gate B1. No-regression gate

- `421/пр` не возвращает старые banned artifacts.
- `812/пр` не теряет уже доступные `calc_expr` для простых линейных формул.
- False positives на Tier C не растут относительно baseline.

Текущая versioned числовая policy поверх baseline `20260525T193008Z`:

- `anchor`: `gold_pass_rate >= 1.0`, `provider_dependency_rate <= 0.0`.
- `gate`: `calc_expr_coverage >= 0.60`, `native_coverage >= 0.13`, `low_confidence_rate <= 0.93`.
- `control`: `false_positive_rate <= 0.0`, `gold_pass_rate >= 1.0`, `provider_dependency_rate <= 0.0`.
- `overall`: `calc_expr_coverage >= 0.64`, `native_coverage >= 0.15`, `low_confidence_rate <= 0.92`, `provider_dependency_rate <= 0.0`.
- `rolling`: monitor-only tier до следующего полного rerun; drift на нём фиксируется как evidence, но пока не блокирует required gate.

#### Gate B2. Native-parser improvement gate

- После P1-02 уменьшается доля unresolved WMF cases на Tier A/B.
- Увеличивается `native_coverage`, а рост достигается не за счёт provider calls.
- Для новых resolved patterns есть provenance и regression tests.

#### Gate B3. Local-backend adoption gate

- После P1-04 снижается `provider_dependency_rate` на formula-image cases.
- Local backend не повышает false positives на control set.
- Время benchmark run остаётся приемлемым для локального повторения.

### 4.7. Предлагаемые benchmark artifacts

- `samples/formula-benchmark.manifest.jsonl`
- `samples/formula-benchmark.thresholds.json`
- `samples/expected/formulas/<doc-id>.gold.json`
- `runs/formula-benchmark/<run-id>/benchmark-report.json`
- `runs/formula-benchmark/<run-id>/benchmark-report.md`
- `runs/formula-benchmark/<run-id>/formula-summary.json`

### 4.8. Операционный ритм

- Любая правка в `src/doc_converter/converters/docx.py`, `src/doc_converter/formula_recognition.py` или formula-related renderer/evaluator запускает Tier A.
- Перед merge крупной formula task или перед новым portable release запускаются Tier A + Tier B + Tier C.
- Tier D используется как rolling monitor, чтобы ловить новые production-like patterns без полного прогонa всего corpus.

## 5. Рекомендуемая последовательность исполнения

1. Закрыть P0-01...P0-04 и получить baseline с единым benchmark language.
2. Сразу после baseline выполнить spike P1-01, потому что он определяет, что именно считать native parser ROI.
3. Если P1-01 даёт положительный сигнал, делать P1-02 до local OCR integration, чтобы не подменить native gap дорогим fallback.
4. Затем провести P1-03 и принимать решение по P1-04 только на benchmark-данных, а не по subjective spot checks.
5. P2 выполнять только после того, как native/local path дают стабильную картину по Tier A/B/C.

## 6. Внешние reference-patterns

- Docling, Marker и MinerU полезны как примеры unified document representation, debug artifacts и benchmark-first workflow.
- OCRmyPDF остаётся примером корректного narrow scope: OCR layer должен улучшать только свой slice и не подменять native document understanding.
- Pix2Text и LaTeX-OCR классы инструментов подходят именно как formula-specific local backend, а не как общий OCR replacement.
