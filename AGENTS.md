# AGENTS

## Startup contract

Принцип: читать минимум контекста. По умолчанию — fast path. Тяжёлые state-файлы (`current-status.md`, `release-status.md`, `agent-feature-spine.json`) читать НЕ целиком, а точечно через grep по нужной секции/feature_id. Целиком грузить файл только если grep явно недостаточно.

Fast path (по умолчанию для любой задачи, включая bugfix, explanation, локальные правки):

1. начинать с named file/symbol/test/error;
2. НЕ читать state layer, repo-memory и telemetry, пока локальный routing не показал, что задача реально шире;
3. расширять cold-start только при явных признаках cross-module / release / resume scope.

Extended path (только для release / resume / подтверждённо кросс-модульной задачи):

1. прочитать `docs/agent-working-state.v1.json` и `docs/state-snapshot.md` — это default state entry bundle;
2. при необходимости — grep-точечно по `docs/current-status.md`, `docs/current-sprint.md`, `docs/release-status.md` (искать конкретную секцию/blocker, не читать файл целиком);
3. relevant task checkpoint и repo-memory notes — только если они напрямую относятся к текущему scope.

## Execution discipline

1. Перед первым substantive edit должна быть зафиксирована локальная гипотеза и validation target.
2. Для нетривиальной cross-module/process/state задачи до первой substantive правки должны быть определены затронутые `feature_id` — искать их grep-точечно в `docs/agent-feature-spine.json`, не читая файл целиком.
3. Сразу после первого substantive edit должна выполняться focused validation, если она доступна.
4. После завершения задачи должны обновляться state files, telemetry и при необходимости `docs/agent-feature-spine.json`.
5. Если выявлен новый validated learning, он должен попасть в repo-memory.

## Detailed process references

- Bootstrap contract: docs/agent-bootstrap-contract.md
- Feature spine: docs/agent-feature-spine.json
- Quality scorecard: docs/agent-quality-scorecard.md, docs/agent-quality-scorecard.v1.json
- Weekly eval snapshot: docs/agent-weekly-eval.md, docs/agent-weekly-eval.v1.json
- Lifecycle: docs/agent-lifecycle.md
- Exit checklist: docs/agent-session-exit-checklist.md
- Sprint contract: docs/agent-sprint-contract-template.md
- Evaluator rubric: docs/agent-evaluator-rubric.md
- Guardrails: docs/agent-guardrails.md
- Stop budgets: docs/agent-stop-budgets.md
- Tool-interface audit: docs/agent-tool-interface-audit.md
- Routing matrix: docs/agent-routing-matrix.md
- Specialist agents: .github/agents/
- Evals: docs/agent-evals.md
- Self-review: docs/agent-self-review-template.md
- Instruction change log: docs/agent-instruction-change-log.md
- Handoffs: docs/agent-handoffs.md
- Release docs: docs/ops/
- Retrospective: docs/agent-pilot-retrospective.md, docs/agent-retrospective-template.md
- Reusable prompts: .github/prompts/

## Source of truth

- Roadmap программы: Agent_made.md
- Главный operational status: docs/current-status.md
- Активный спринт: docs/current-sprint.md
- Release status: docs/release-status.md
- Hot working state: docs/agent-working-state.v1.json
- Harness feature spine: docs/agent-feature-spine.json
- Quality scorecard: docs/agent-quality-scorecard.md, docs/agent-quality-scorecard.v1.json
- Telemetry: docs/agent-telemetry-log.md, docs/agent-telemetry.v1.jsonl
- Weekly eval snapshot: docs/agent-weekly-eval.md, docs/agent-weekly-eval.v1.json

## Safety baseline

До появления формальных guardrails все destructive и production-like действия считаются требующими отдельной остановки и явной проверки контекста.
