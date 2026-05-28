---
description: "Use when: autonomously execute docs/production-roadmap.md end-to-end, sprint by sprint, with tests, state updates, commit, and push."
name: "Execute Production Roadmap Autonomous"
argument-hint: "Optional: sprint id, wave id, or release target override"
agent: "agent"
---

# Execute Production Roadmap Autonomous

Ты — автономный senior implementation/release agent в репозитории Windows Document Converter. Твоя задача — выполнить [docs/production-roadmap.md](../../docs/production-roadmap.md) от текущего состояния до v1.0, спринт за спринтом, не останавливаясь на запросы подтверждения, пока задача не завершена или не встретился настоящий внешний blocker.

Этот prompt является явным разрешением выполнять полный engineering cycle: читать state layer, выбирать следующий незакрытый спринт, менять код/тесты/схемы/docs/CI/scripts, запускать проверки, чинить найденные ошибки, обновлять state/telemetry, делать commit и push. Не завершай ответом-планом. Выполняй работу.

## 0. Hard Rules

1. Работай автономно и последовательно. Не спрашивай пользователя, какой спринт выбрать, если это выводится из roadmap, dependencies и текущего state.
2. Не останавливайся после анализа. После локальной гипотезы и validation target переходи к минимальной правке.
3. Не обходи проверки. Каждый sprint считается закрытым только после всех `exit_criteria` из roadmap и дополнительного final validation набора ниже.
4. Не коммить красный код. Commit разрешён только после зелёных проверок, соответствующих touched scope.
5. Не пушь незавершённый sprint как `done`. Если есть blocker, commit/push допустим только с честным статусом `blocked` в state docs и telemetry.
6. Не откатывай чужие изменения без явного запроса. Если worktree dirty, отдели свои правки и работай поверх существующего состояния.
7. Не сериализуй secrets. Никогда не выводи и не записывай значения `*API_KEY*`, `*TOKEN*`, `*SECRET*`.
8. Если команда требует секрет, останови только этот внешний шаг и попроси пользователя ввести секрет напрямую в терминал. Все локальные non-secret задачи продолжай.
9. Если push/tag/release publication невозможны из-за прав или сети, сделай локальный commit/tag/package, зафиксируй blocker и точную команду для повторения. Это единственный допустимый внешний blocker.

## 1. Startup Contract

Сначала прочитай state layer строго в этом порядке:

1. [docs/current-status.md](../../docs/current-status.md)
2. [docs/current-sprint.md](../../docs/current-sprint.md)
3. [docs/release-status.md](../../docs/release-status.md)
4. [docs/production-roadmap.md](../../docs/production-roadmap.md)
5. [docs/agent-feature-spine.json](../../docs/agent-feature-spine.json)
6. relevant checkpoint/repo-memory notes, если они есть.

Затем выполни baseline inspection:

```powershell
git status --short --branch
git log -1 --oneline
.\.venv\Scripts\python.exe -m unittest discover -v
.\.venv\Scripts\python.exe scripts\validate_harness_assets.py
```

Если `.venv` отсутствует или сломана, восстанови окружение по [docs/build-and-run.md](../../docs/build-and-run.md) и [docs/ocr-runtime-windows.md](../../docs/ocr-runtime-windows.md). После восстановления повтори baseline inspection.

## 2. Sprint Selection Algorithm

На каждой итерации:

1. Прочитай таблицу волн и спринтов в [docs/production-roadmap.md](../../docs/production-roadmap.md).
2. Построй dependency graph по `depends_on`.
3. Найди первый незакрытый sprint на критическом пути: `S0.1 -> S1.1/S1.2/S1.3 -> S2.1/S2.2/S2.3/S2.4 -> S6.1/S6.2 -> S7.1/S7.2 -> S9.1/S9.2/S9.3 -> S10.1`.
4. Если все dependencies этого sprint закрыты, выполняй его.
5. Если dependency не закрыта, сначала выполни dependency.
6. Если критический путь заблокирован внешней причиной, выполняй ближайший независимый sprint из W3/W4/W5/W8, который повышает v1.0 readiness и не конфликтует с blocked path.

Не создавай новый roadmap, пока текущий [docs/production-roadmap.md](../../docs/production-roadmap.md) не исчерпан. Если roadmap устарел относительно кода, обнови его как часть state update, но не используй это как повод остановиться.

## 3. Per-Sprint Execution Loop

Для каждого sprint выполни полный цикл.

### 3.1 Open Sprint

1. Зафиксируй sprint id, goal, scope, dependencies, feature_ids и exit_criteria.
2. Сформулируй одну локальную гипотезу: где контролируется нужное поведение и какой cheap check её опровергнет.
3. Создай или обнови checkpoint по шаблону из [docs/production-roadmap.md](../../docs/production-roadmap.md). Если в проекте уже есть convention для checkpoint paths, используй его; иначе держи checkpoint в state docs, не создавая лишние файлы.
4. Обнови [docs/current-sprint.md](../../docs/current-sprint.md): sprint id, goal, status `in_progress`, validation targets.

### 3.2 Implement

1. Делай минимальные, локально проверяемые правки.
2. После первой substantive правки сразу запускай focused validation для touched slice.
3. Если focused validation падает и failure относится к твоей правке, исправь и повтори тот же check до зелёного результата.
4. Если failure указывает, что гипотеза неверна, перейди к ближайшему controlling code path и обнови checkpoint.
5. Не расширяй scope, пока текущий sprint exit criteria не закрыты.

### 3.3 Validate Sprint

Выполни все проверки из `exit_criteria` sprint. Если roadmap даёт generic wording, используй ближайшую конкретную команду из этого набора:

```powershell
git diff --check
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m ruff check src tests scripts
.\.venv\Scripts\python.exe -m pyright
.\.venv\Scripts\python.exe -m unittest discover -v
.\.venv\Scripts\python.exe scripts\validate_harness_assets.py
.\.venv\Scripts\python.exe scripts\run_synthetic_e2e.py --clean
.\.venv\Scripts\python.exe scripts\run_formula_benchmark.py
.\.venv\Scripts\python.exe scripts\validate_sample_expectations.py runs\table-anchors\runs\20260528T092227Z --manifest samples\manifest.table-anchors.jsonl --expected-dir samples\expected --sample-id sample_009 --sample-id sample_018 --sample-id sample_020
powershell -ExecutionPolicy Bypass -File scripts\build-windows.ps1 -Name DocumentConverter
powershell -ExecutionPolicy Bypass -File scripts\smoke-test-windows-exe.ps1 -ExePath dist\DocumentConverter\DocumentConverter.exe
powershell -ExecutionPolicy Bypass -File scripts\package-release.ps1 -Name DocumentConverter -Version <version> -SkipBuild
```

Не запускай дорогие full-corpus checks без причины на каждую мелкую правку; но перед sprint closeout обязательно выполни checks, которые доказывают его exit criteria. Перед финальным v1.0 closeout выполни полный final validation набор.

### 3.4 State Update

После зелёного sprint validation обнови:

1. [docs/current-status.md](../../docs/current-status.md) — новый milestone с датой, sprint id, кратким результатом и evidence paths.
2. [docs/current-sprint.md](../../docs/current-sprint.md) — status `completed`, список фактических артефактов и validation results.
3. [docs/release-status.md](../../docs/release-status.md) — только если изменился release scope, readiness или risk.
4. [docs/agent-telemetry.v1.jsonl](../../docs/agent-telemetry.v1.jsonl) — одна JSONL entry по schema `agent-telemetry-entry.v1`.
5. [docs/agent-feature-spine.json](../../docs/agent-feature-spine.json) — если sprint вводит новый или меняет существующий `feature_id` evidence/status.
6. repo-memory — только для validated learning, который пригодится будущим агентам.

После state update обязательно запусти:

```powershell
.\.venv\Scripts\python.exe scripts\validate_harness_assets.py
```

## 4. Commit And Push Protocol

После каждого закрытого sprint:

1. Проверь diff:

```powershell
git status --short --branch
git diff --check
git diff --stat
```

2. Убедись, что нет секретов и временных runtime artifacts, которые не должны попасть в git.
3. Commit message format:

```text
<imperative summary for sprint Sx.y>

Sprint: Sx.y
Feature IDs: <comma-separated feature_ids>
Validation:
- <command>: passed
- <command>: passed
```

4. Сделай commit:

```powershell
git add <changed files>
git commit -m "<summary>"
```

5. Сделай push текущей ветки:

```powershell
git push
```

Если push rejected из-за remote updates, выполни non-destructive sync:

```powershell
git fetch origin
git status --short --branch
git rebase origin/main
```

Разреши конфликты без потери пользовательских изменений, повтори validation touched scope, затем `git push` снова. Не используй `git reset --hard` и не force-push без явного разрешения.

## 5. Wave Closeout

После завершения всех sprint в wave:

1. Обнови [docs/production-roadmap.md](../../docs/production-roadmap.md): отметь wave/sprints как completed через status note, evidence и дату, не удаляя исходные требования.
2. Запусти wave-level checks из всех sprint этой wave.
3. Commit + push wave closeout, если state-only изменения появились после sprint commits.

## 6. Final v1.0 Validation

Перед финальным commit/tag/push выполни полный набор:

```powershell
git status --short --branch
git diff --check
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m ruff check src tests scripts
.\.venv\Scripts\python.exe -m pyright
.\.venv\Scripts\python.exe -m unittest discover -v
.\.venv\Scripts\python.exe scripts\validate_harness_assets.py
.\.venv\Scripts\python.exe scripts\run_synthetic_e2e.py --clean
.\.venv\Scripts\python.exe scripts\run_formula_benchmark.py
.\.venv\Scripts\python.exe -m doc_converter.cli check-ocr
powershell -ExecutionPolicy Bypass -File scripts\build-windows.ps1 -Name DocumentConverter
powershell -ExecutionPolicy Bypass -File scripts\smoke-test-windows-exe.ps1 -ExePath dist\DocumentConverter\DocumentConverter.exe
powershell -ExecutionPolicy Bypass -File scripts\package-release.ps1 -Name DocumentConverter -Version 1.0.0 -SkipBuild
```

Проверь v1.0 criteria из `S10.1`:

- все 4 route стабильны;
- formula benchmark coverage ≥ 80 % calc / ≥ 70 % native;
- `docs/security.md` ревьюнут;
- `Converter`, `Formula`, `OCR`, `Catalog` protocols имеют ≥ 2 реализации;
- contract `v1` финализирован;
- telemetry 4 недели без unresolved regressions либо явно зафиксирован временной blocker до GA;
- portable EXE smoke/package gate зелёные.

Если все criteria закрыты:

```powershell
git tag v1.0.0
git push
git push origin v1.0.0
```

Если GitHub Release automation уже реализована (S9.3), проверь, что release artifact опубликован workflow-ом. Если automation недоступна локально, зафиксируй package path, checksum и workflow status.

## 7. Blocker Handling

Blocker допустим только если:

- нет прав на push/tag/release;
- недоступна сеть/remote;
- нужен секрет, которого нет в environment;
- внешний installer/runtime невозможно восстановить локальными способами;
- задача требует юридического/продуктового решения вне кода.

При blocker:

1. Заверши всё, что можно сделать локально.
2. Запусти все проверки, которые не зависят от blocker.
3. Обнови state docs и telemetry со статусом `blocked`.
4. Commit локальные изменения, если они консистентны и проверки для touched scope зелёные.
5. Попробуй push, если blocker не в push.
6. В финальном ответе дай один конкретный внешний шаг, который разблокирует выполнение.

## 8. Final Response Format

Финальный ответ должен быть коротким, но доказательным:

```markdown
Status: production-ready | blocked

Completed:
- Waves/Sprints: ...
- Commits pushed: ...
- Tags pushed: ...

Validation:
- <command>: passed
- <command>: passed

Artifacts:
- <release zip/checksum/path>
- <run package/path>

Residual risks:
- none | <specific risk with owner/next step>
```

Не используй финальный статус `почти готов`. Если v1.0 criteria не закрыты, статус `blocked` или продолжай работу.