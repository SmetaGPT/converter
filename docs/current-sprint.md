# Current Sprint

Последнее обновление: 2026-05-28
Активный спринт: Table benchmark anchor baseline
Статус: completed

Предыдущий приоритетный tranche: Table hardening execution
Статус wave 1: completed

## 1. Цель спринта

Перевести table hardening из targeted regressions в executable anchor-based quality loop: добавить validator для representative sample expectations, зафиксировать subset manifest и expected specs для `sample_009`, `sample_018`, `sample_020`, прогнать реальный benchmark-like pilot и превратить table backlog в измеримый baseline, а не только в narrative plan.

## 2. Артефакты спринта

- src/doc_converter/sample_expectations.py
- scripts/validate_sample_expectations.py
- tests/test_sample_expectations.py
- samples/manifest.table-anchors.jsonl
- samples/expected/sample_009.expected-units.json
- samples/expected/sample_018.expected-units.json
- samples/expected/sample_020.expected-units.json
- samples/expected/README.md
- docs/current-status.md
- docs/current-sprint.md
- docs/release-status.md
- docs/agent-telemetry-log.md
- docs/agent-telemetry.v1.jsonl

## 3. Задачи спринта

| Задача | Статус |
| --- | --- |
| Добавить executable validator для representative sample expectations | Готово |
| Поддержать subset validation по `sample_id` и processing expectations | Готово |
| Завести reproducible subset manifest для table anchors | Готово |
| Расширить expected specs `sample_009` и добавить `sample_018` / `sample_020` | Готово |
| Прогнать реальный table-anchor pilot и проверить validator на fresh `run_dir` | Готово |
| Зафиксировать OCR-blocked baseline для `sample_020` вместо неявной narrative проблемы | Готово |
| Синхронизировать state и telemetry под новый benchmark contour | Готово |

## 4. Validation targets спринта

1. `runTests` для `tests/test_sample_expectations.py` проходит без падений.
2. Реальный narrow pilot `\.venv\Scripts\python.exe scripts\run_sample_pilot.py --manifest samples\manifest.table-anchors.jsonl --output runs\table-anchors --input runs\table-anchors-input --clean` отрабатывает на `sample_009`, `sample_018`, `sample_020` без route mismatch.
3. `\.venv\Scripts\python.exe scripts\validate_sample_expectations.py runs\table-anchors\runs\20260528T092227Z --manifest samples\manifest.table-anchors.jsonl --expected-dir samples\expected --sample-id sample_009 --sample-id sample_018 --sample-id sample_020` проходит зелёно.
4. `get_errors` по новым `src/`, `tests/`, `scripts/` и `samples/` файлам не показывает новых проблем.
5. `\.venv\Scripts\python.exe scripts\refresh_agent_eval.py` и `\.venv\Scripts\python.exe scripts\validate_harness_assets.py` проходят после state/telemetry sync.

## 5. Риски спринта

- `sample_020` пока не даёт scan-table metrics из-за `OCRmyPDF failed`, поэтому benchmark contour по scan route пока фиксирует blocked baseline, а не успешный quality floor;
- `sample_009` и `sample_018` удерживают row/cell integrity, но почти все их таблицы всё ещё несут `table_structure_warning`, значит baseline пока измеряет устойчивость shape, а не quality-ready clean parse;
- explicit false-positive contour пока ещё proxy-based: `wide_row_ratio` и `single_cell_row_ratio` уже дают guardrail, но отрицательные/control anchors для tables ещё не вынесены в отдельный executable слой;
- DOCX table semantics за пределами formula-in-cell всё ещё не закрыты: header-like rows, merged cells и richer review signals остаются следующим deterministic contract.

## 6. Критерий выхода

Спринт считается закрытым, когда delivery loop подтверждает одновременно:

- representative sample expectations стали executable validator-driven loop, а не просто ручными JSON fixtures;
- subset manifest `samples/manifest.table-anchors.jsonl` воспроизводит table-anchor pilot без ad hoc selection;
- `sample_009` и `sample_018` имеют проверяемый table baseline по row/cell metrics и proxy false-positive thresholds;
- `sample_020` зафиксирован как честный blocked baseline с reproducible `partial_success`, `OCRmyPDF failed.` и нулевыми table units;
- state/telemetry docs синхронизированы и harness validator не показывает drift.

## 7. Следующий operational focus

1. Разобрать и устранить `OCRmyPDF failed` path на `sample_020`, чтобы scan-table anchor перешёл из blocked baseline в измеримый quality contour.
2. Снизить warning-heavy residue на `sample_009` и `sample_018`, а не только удерживать row/cell integrity.
3. Добавить explicit negative/control false-positive contour для tables поверх уже заведённых proxy metrics.
4. Дотянуть DOCX table semantics на header-like rows, merged-cell hints и richer review signals без слома `document.v1` contract.
5. Проверить human-readable QC на normalized/ragged tables и formula-in-cell cases, чтобы operator видел те же структурные решения, что и canonical package.
6. После стабилизации table metrics вернуться к generalized WMF parser и remaining formula residue в `1/пр`.
7. Поддерживать machine-readable telemetry companion, feature spine и generated eval companions без drift на следующем sprint.
