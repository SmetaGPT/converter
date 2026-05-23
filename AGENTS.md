# AGENTS

## Startup contract

Для любой кросс-модульной, многошаговой или resume-задачи агент обязан начинать с чтения state layer в таком порядке:

1. docs/current-status.md
2. docs/current-sprint.md
3. docs/release-status.md

После этого агент читает:

1. relevant task checkpoint, если он есть;
2. relevant repo-memory notes, если они уже заведены;
3. только затем переходит к локальному поиску по затронутой области.

## Execution discipline

1. Перед первым substantive edit должна быть зафиксирована локальная гипотеза и validation target.
2. Для нетривиальной задачи до первой substantive правки должны быть определены затронутые `feature_id` из `docs/agent-feature-spine.json`.
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
- Harness feature spine: docs/agent-feature-spine.json
- Quality scorecard: docs/agent-quality-scorecard.md, docs/agent-quality-scorecard.v1.json
- Telemetry: docs/agent-telemetry-log.md, docs/agent-telemetry.v1.jsonl
- Weekly eval snapshot: docs/agent-weekly-eval.md, docs/agent-weekly-eval.v1.json

## Safety baseline

До появления формальных guardrails все destructive и production-like действия считаются требующими отдельной остановки и явной проверки контекста.
