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
2. Сразу после первого substantive edit должна выполняться focused validation, если она доступна.
3. После завершения задачи должны обновляться state files и telemetry.
4. Если выявлен новый validated learning, он должен попасть в repo-memory.

## Detailed process references

- Lifecycle: docs/agent-lifecycle.md
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
- Telemetry: docs/agent-telemetry-log.md

## Safety baseline

До появления формальных guardrails все destructive и production-like действия считаются требующими отдельной остановки и явной проверки контекста.
