# Дорожная карта: автономный агентный контур разработки

_Дата: 22 мая 2026_  
_Версия: 2.0_  
_Горизонт: 7 спринтов_  
_Формат: repo-native operating system для AI-агента полного цикла_

---

## 1. Назначение документа

Этот документ фиксирует план внедрения агентного контура, в котором AI-агент способен поддерживать полный цикл разработки внутри репозитория:

- понимать, что уже сделано;
- понимать, что делается сейчас;
- понимать, что будет делаться дальше;
- работать повторяемо и с минимальной потерей контекста между сессиями;
- проходить через реализацию, проверку, фиксацию статуса, release discipline и накопление памяти.

Документ нужен как рабочая дорожная карта для контроля внедрения, а не как теоретическое описание.

---

## 2. Целевая модель

В конце этой программы у проекта должен появиться устойчивый агентный operating model:

1. У агента есть единый и всегда актуальный state layer.
2. У агента есть многоуровневая память: user, repo, session.
3. У агента есть повторяемый lifecycle выполнения задачи.
4. У агента есть специализированные режимы работы: research, implementation, review, release.
5. У агента есть guardrails и остановки перед рискованными действиями.
6. У агента есть evaluation loop и наблюдаемость качества.
7. У агента есть release loop, а не только coding loop.

---

## 3. Принципы внедрения

План опирается на актуальные best practices для LLM-агентов в разработке:

- сначала простые composable workflows, а не сложная внешняя agent-платформа;
- явное состояние важнее неявной "памяти модели";
- память должна быть короткой, структурированной и пригодной к повторному использованию;
- инструменты, hooks и prompts должны быть понятны агенту как хороший ACI, а не как набор скрытой магии;
- любая автономность должна быть связана с validation loop;
- многоагентность нужна только там, где реально есть routing по ролям;
- опасные действия должны проходить через guardrails и human approval.
- baseline и telemetry должны появиться до масштабирования агентной системы;
- состояние задачи должно быть checkpoint-friendly: его можно восстановить после паузы без повторного широкого исследования;
- procedural memory должна развиваться контролируемо, через review изменений в инструкциях и prompts.

---

## 5. Метрики успеха

После внедрения должны измеримо улучшиться следующие показатели:

| Метрика | Целевое значение |
|---|---:|
| Холодный reacquire контекста до рабочего понимания задачи | до 5 минут |
| Завершённые задачи с обновлением state-документа | 100% |
| Кодовые задачи с focused validation | не ниже 90% |
| Повторные environment-ошибки после фиксации в repo-memory | стремится к 0 |
| Задачи с явным handoff / closeout | 100% |
| Выпуски с checklist и runbook | 100% |
| Задачи, где агент смог пройти полный цикл без потери контекста между сессиями | не ниже 80% |
| Resume из checkpoint без повторного broad search | не ниже 80% |
| Задачи с зафиксированным validation target до первого edit | не ниже 90% |
| Повторные broad-search циклы после старта реализации | стремится к 0 |
| Manual interventions по процессу на задачу | снижается по спринтам |
| Стоимость/latency агентного цикла, если появится внешний runtime | отслеживается с baseline |

---

## 6. Границы первой волны

### Входит в первую волну

- baseline и inventory;
- state layer;
- memory discipline;
- lightweight telemetry и task checkpoints;
- hooks и prompts;
- specialist agents;
- eval loop;
- release loop;
- контрольные документы и ритуалы.

### Не входит в первую волну

- отдельная внешняя agent-platform поверх SDK;
- векторная БД и тяжёлая semantic memory инфраструктура;
- полностью автоматический production deploy без human approval;
- самостоятельное принятие продуктовых решений агентом без контрольных точек;
- автономные destructive infra-операции.

---

## 7. Спринтовая дорожная карта

### Sprint 0 — Baseline and Inventory

**Цель:** зафиксировать исходное состояние агентного контура до изменений, чтобы дальнейшие улучшения можно было измерить.

**Задачи:**

- провести inventory существующих `.github/prompts/`, `.github/instructions/`, `AGENTS.md`, `CLAUDE.md` и repo-memory;
- выделить 10-15 типовых задач проекта для будущего eval set;
- зафиксировать текущие значения метрик: cold-start, validation coverage, handoff completeness, повторные environment-ошибки;
- описать текущий task lifecycle агента как есть;
- определить gaps между текущим workflow и целевой моделью.

**Артефакты спринта:**

- `docs/agent-baseline.md`;
- `docs/agent-assets-inventory.md`;
- первая версия `docs/agent-eval-tasks.md`;
- baseline-секция в `docs/agent-quality-scorecard.md`.

**Definition of Done:**

- понятно, какие агентные assets уже существуют и какие дублируются;
- есть минимальный набор задач для будущего сравнения качества;
- есть исходные значения ключевых метрик;
- дальнейшие спринты можно проверять не только субъективно, но и относительно baseline.

**Контроль:**

- повторяемый cold-start на одной типовой задаче;
- выборочный replay 2-3 прошлых задач по существующим prompt/state артефактам;
- фиксация gaps в конце baseline-документа.

---

### Sprint 1 — State Foundation

**Цель:** сделать состояние проекта и активной работы явным, коротким и обязательным для чтения.

**Задачи:**

- закрепить [docs/current-status.md](docs/current-status.md) как главный operational state file;
- ввести единый документ активного спринта;
- ввести единый документ ближайшего релиза;
- определить обязательный минимум обновления state после завершения задач;
- зафиксировать, какие документы являются source of truth для продукта, статуса и релизного состояния.
- ввести минимальный task checkpoint schema для восстановления работы после паузы;
- начать lightweight telemetry: дата задачи, тип задачи, touched areas, validation target, validation result, state update.

**Артефакты спринта:**

- `docs/current-status.md`;
- `docs/current-sprint.md`;
- `docs/release-status.md`;
- `docs/agent-task-checkpoint-template.md`;
- `docs/agent-telemetry-log.md` или другой лёгкий журнал, выбранный на Sprint 0;
- обновлённый `AGENTS.md` с правилом чтения state layer на старте кросс-модульной работы.

**Definition of Done:**

- у проекта есть один главный status-entry-point;
- у активной работы есть один sprint-entry-point;
- у ближайшего релиза есть один release-entry-point;
- агент может за один проход понять: что уже сделано, что открыто, что следующее.
- задача может быть возобновлена из checkpoint без повторного broad search;
- минимальная telemetry пишется уже с первого спринта.

**Контроль:**

- cold-start проверка на новой задаче;
- замер времени до восстановления контекста;
- проверка, что закрытие задач реально обновляет state files.
- проверка 3 task checkpoints на полноту и пригодность для resume.

---

### Sprint 2 — Memory Discipline

**Цель:** превратить память из случайных заметок в управляемую систему знаний.

**Задачи:**

- нормализовать repo-memory по категориям: backend, frontend, infra, release, agent-ops;
- разделить память по типам: semantic, episodic, procedural;
- разделить shared memory, которая живёт в git-tracked docs/prompts, и local memory, которая остаётся в `/memories/`;
- описать правила, что хранится в user/session/repo memory;
- ввести шаблон записи lessons learned;
- ввести memory hygiene: retention, compaction, deletion, запрет на секреты и персональные данные;
- выделить устойчивые environment gotchas и validated commands;
- определить правило, когда агент обязан записывать новый learning в память.

**Артефакты спринта:**

- `/memories/repo/agent-ops.md`;
- `/memories/repo/backend-notes.md`;
- `/memories/repo/frontend-notes.md`;
- `/memories/repo/deployment-notes.md`;
- `docs/agent-memory-model.md`.
- `docs/agent-memory-hygiene.md`;
- `docs/agent-lessons-template.md`.

**Definition of Done:**

- память разделена по уровням и не дублирует сама себя;
- повторяющиеся технические ошибки уходят в repo-memory;
- агент знает, где искать продуктовый статус, где средовые грабли, где release-практики;
- новые знания после задач попадают в память по единым правилам.
- sensitive data, secrets, tokens и персональные данные не попадают в memory layer;
- procedural memory изменяется только через контролируемые изменения prompts/instructions.

**Контроль:**

- выборочная проверка последних 5 задач: был ли новый learning и был ли он зафиксирован;
- проверка, что память короткая, атомарная и реально полезна при возобновлении работы.
- проверка, что shared learnings не остаются только в локальной памяти, если они важны для команды.

---

### Sprint 3 — Deterministic Workflow и Hooks

**Цель:** закрепить обязательный lifecycle задачи не только инструкциями, но и детерминированной автоматизацией.

**Задачи:**

- создать `.github/hooks/`;
- провести ACI/tool audit: какие инструменты агент путает, где нужны примеры, absolute paths, safety checks и более понятные контракты;
- ввести pre-task hook для загрузки state/memory контекста;
- ввести pre-edit hook для фиксации локальной гипотезы и validation target;
- ввести post-edit hook для напоминания о focused validation;
- ввести post-task hook для обновления state и memory;
- ввести guardrails для destructive действий, prod-like команд и risk-sensitive операций.
- ввести stop budgets: лимит broad search до гипотезы, лимит repair loops на один slice, лимит действий без validation.

**Артефакты спринта:**

- `.github/hooks/*.json`;
- `docs/agent-lifecycle.md`;
- `docs/agent-guardrails.md`;
- `docs/agent-tool-interface-audit.md`;
- `docs/agent-stop-budgets.md`;
- reusable prompts для kickoff, closeout и blocker handling.

**Definition of Done:**

- агент проходит через один и тот же lifecycle на каждой задаче;
- после первого substantive edit всегда идёт validation step;
- опасные действия получают stop point или human approval;
- закрытие задачи включает state update и handoff, а не только diff.
- агент не может бесконечно расширять поиск или ремонтировать один slice без эскалации;
- tool/ACI проблемы зафиксированы и превращены в исправления hooks/prompts/instructions.

**Контроль:**

- выборочные task replay и audit trail по 3–5 задачам;
- проверка, что hooks уменьшают пропуски validation и обновления статуса.
- проверка, что stop budgets реально срабатывают на ambiguous tasks.

---

### Sprint 4 — Specialist Agents и Routing

**Цель:** разделить режимы работы агента по ролям, чтобы повысить качество и предсказуемость.

**Задачи:**

- создать `.github/agents/`;
- выделить specialist agents первой волны: research, review, release;
- добавить implementation agent как pilot только после проверки lifecycle hooks на реальных задачах;
- описать routing rules: какую задачу в какой режим направлять;
- определить tool restrictions и output contracts для каждого режима;
- перенести часть накопленных phase-prompts в reusable agent assets.

**Артефакты спринта:**

- `.github/agents/research.agent.md`;
- `.github/agents/implement.agent.md` в pilot-статусе;
- `.github/agents/review.agent.md`;
- `.github/agents/release.agent.md`;
- `docs/agent-routing-matrix.md`.

**Definition of Done:**

- для основных классов задач есть специализированный режим работы;
- review не смешивается с implementation;
- release tasks не идут тем же режимом, что и обычная правка кода;
- agent-routing описан явно и понятен команде;
- implementation agent не расширяет blast radius до того, как lifecycle и validation discipline стали стабильными.

**Контроль:**

- прогон типовых задач по разным категориям;
- проверка, что routing уменьшает лишние tool calls, broad search и хаотичную работу.

---

### Sprint 5 — Evaluation, Observability и Self-Review

**Цель:** сделать качество агентной работы измеримым, а не субъективным.

**Задачи:**

- собрать минимальный eval set по типовым задачам проекта;
- определить grading criteria: контекст, точность, полнота, validation, state update, release impact;
- ввести lightweight post-task self-review;
- описать failure taxonomy: lost context, skipped validation, wrong routing, stale memory, over-search;
- завести журнал агентных regressions и recovery patterns.
- ввести controlled instruction-refinement loop: предложения по изменению prompts/instructions появляются из recurring failures и проходят review;
- связать eval set с baseline из Sprint 0 и telemetry из Sprint 1.

**Артефакты спринта:**

- `docs/agent-evals.md`;
- `docs/agent-regressions.md`;
- `docs/agent-quality-scorecard.md`;
- `docs/agent-instruction-change-log.md`;
- набор контрольных задач для регулярной проверки качества.

**Definition of Done:**

- качество агентной работы можно оценить по явным критериям;
- известные типы провалов описаны и отслеживаются;
- после завершения задачи есть короткий self-review слой;
- команда видит, где агент реально помогает, а где нужна доработка процесса.
- изменения procedural memory не происходят спонтанно, а проходят через понятный change log;
- eval показывает динамику относительно baseline, а не только текущую субъективную оценку.

**Контроль:**

- еженедельный разбор 3–5 агентных задач;
- фиксация повторяющихся ошибок и их снижение по спринтам.

---

### Sprint 6 — Full-Cycle Delivery и Release Discipline

**Цель:** довести агента до режима полного цикла, где он поддерживает не только кодинг, но и выпуск.

**Задачи:**

- оформить release loop на базе уже существующих ops/predeploy/release артефактов, не создавая параллельный процесс;
- связать task closeout, checklist, runbook и post-release sanity;
- описать handoff rules между сессиями;
- определить approval points для production-like операций;
- создать runbook на первый и обычный релизный цикл;
- провести пилот на 3–5 реальных задачах полного цикла и собрать retrospective.

**Артефакты спринта:**

- `docs/ops/agent-release-checklist.md`;
- `docs/ops/agent-runbook.md`;
- `docs/agent-handoffs.md`;
- `docs/agent-retrospective-template.md`.
- обновлённые ссылки из существующих ops/release документов, если они уже покрывают часть процесса.

**Definition of Done:**

- агент сопровождает задачу до release-ready состояния;
- handoff между сессиями не требует повторного большого исследования;
- для risky production-like шагов есть явные approval gates;
- после пилота есть список усилений для следующей волны.
- agent release loop не дублирует существующие release документы, а расширяет и связывает их.

**Контроль:**

- пилотные end-to-end задачи;
- контрольный dry run по release checklist;
- retrospective по потерям контекста, пропускам validation и качеству handoff.

---

## 8. Сквозные ритуалы контроля

Чтобы roadmap не превратился в статичный документ, для каждого спринта действуют одинаковые контрольные ритуалы.

### В начале спринта

- фиксируется цель спринта;
- фиксируется список артефактов, которые должны появиться;
- фиксируются метрики и способ проверки результата.
- фиксируется baseline или expected delta по метрикам, если спринт меняет процесс.

### В течение спринта

- все завершённые задачи обновляют state layer;
- все новые устойчивые learnings попадают в repo-memory;
- risky actions проходят через approval gates.
- каждая нетривиальная задача получает task checkpoint: цель, текущая гипотеза, подтверждённые факты, touched surface, последний validation result, блокер, следующий шаг, approval state;
- telemetry фиксирует validation target, validation result и state update.

### В конце спринта

- проверяется Definition of Done;
- проверяются артефакты спринта;
- собираются regressions и lessons learned;
- обновляется [docs/current-status.md](docs/current-status.md) и следующий спринт.
- сверяются изменения с baseline и scorecard;
- предложения по изменению instructions/prompts проходят через instruction change log.

---

## 9. Главные риски

| Риск | Что может пойти не так | Как снижаем |
|---|---|---|
| Переусложнение | вместо полезного operating model получится тяжёлый фреймворк | держать первую волну repo-native и простой |
| Избыточная память | память превратится в свалку длинных текстов | атомарные заметки и короткие repo-memory файлы |
| Ложная автономность | агент будет делать много шагов без роста качества | eval loop, focused validation, stop conditions |
| Отсутствие контроля | roadmap останется документом без операционного применения | state layer, hooks, checklist, sprint review |
| Смешение ролей | research, coding и review снова сольются в один хаотичный режим | specialist agents и routing matrix |
| Непереносимая память | важные знания останутся только в локальной памяти агента | shared/local split и git-tracked state docs |
| Prompt drift | инструкции начнут меняться без контроля и ухудшат качество | controlled instruction-refinement loop |
| Метрики ради метрик | telemetry будет накапливаться, но не влиять на решения | scorecard review и спринтовые expected deltas |

---

## 10. Ожидаемый итог программы

По завершении всех шести спринтов проект должен получить не просто "набор полезных инструкций", а полноценный агентный operating system внутри репозитория.

Он должен обеспечивать:

- быстрый вход в контекст;
- стабильную память;
- предсказуемый task lifecycle;
- контроль качества через eval и validation;
- поддержку полного цикла разработки до release-ready состояния;
- накопление знаний между задачами и сессиями без постоянного переоткрытия контекста.

---

## 11. Первый практический шаг

Если запускать roadmap без распыления, стартовая последовательность должна быть такой:

0. Sprint 0: снять baseline и провести inventory текущих агентных assets.
1. Sprint 1: закрепить state files и сделать их обязательными.
2. Sprint 2: нормализовать memory model.
3. Sprint 3: ввести hooks, lifecycle discipline, ACI audit и stop budgets.

Именно после этого имеет смысл расширять систему specialist agents, eval loop и release automation.