# Agentic Cadence Controls

Three things run out in an agentic program: human attention, tokens, and shared capacity such
as compute. These controls budget all three.

## Attention budget

The human's attention is the scarcest resource. Spend it on decisions only.

| Control | Guidance | Current value |
|---|---|---|
| Review minutes per day | `budgets.human_review_minutes_per_day` in `program.yaml`. | |
| What reaches the human | Consequential steps without a standing authorization, owner decisions, failures, finished results. | |
| What does not | Progress narration, acknowledgements, routine status. Those go to the status file. | |
| Open decisions | Listed in `decisions.md`; a result that depends on an open decision says so in its not-established list. | |

## Token and context budget

Every model call re-reads the whole context. Cost is roughly calls times context, so a large
early read is paid again on every later call until the context is compacted.

| Control | Guidance | Current value |
|---|---|---|
| Per-run token budget | `budgets.per_run_tokens`, or `budget.tokens` on a work item. | |
| Context budget | `budgets.context_tokens`; compact long-running sessions before they reach it. | |
| Shared files every session reads | Keep short and current. Move history out; do not stack superseding rules. | |
| Tier per task | The cheapest tier that can do it (see `agent_tiers.md`). | |
| Large outputs | Write them to files and read the part you need. | |

## Coordination budget

Parallel agents that message each other multiply cost: each message wakes a whole context.

| Control | Guidance | Current value |
|---|---|---|
| Peer messages | Decisions, hand-overs and failures only. No acknowledgements. | `budgets.coordination` |
| Notifications from watchers | One line per state change, not per check. | |
| Status | Append at most three lines per entry; the peer reads it at its next check-in. | |
| One owner per resource | Recorded in `program.yaml` `resources`; nobody else allocates it. | |

## Capacity

Declare shared resources (`resources` in `program.yaml`) with an owner, a capacity and a rule,
for example "four cluster nodes, never idle, one run at a time, successors prepared on local
hardware". Define "launchable" for the project so a successor is always ready.

## Checkpoints

Require a checkpoint:

- before a consequential step not covered by a standing authorization;
- when a budget is about to be exceeded;
- when the result contradicts a pre-registered expectation;
- after the same failure repeats.

Do not add checkpoints after context gathering, before local edits, or after each test. Those
are the agent's own steps.

## Safe unattended work

Usually safe: research, local experiments, benchmark reads on reserved hardware, data jobs
inside the workspace, drafts, analysis, resumes and hand-overs covered by a standing
authorization.

Usually not safe: publication, promotion, destructive operations, data with unresolved rights,
production changes, and anything that spends beyond the budget.

## Cadence Metrics

Track:

- tokens per run and per closed result;
- share of cost started by peer messages and notifications versus by the human;
- open decisions and their age;
- consequential steps that waited for a human, and how long;
- results reworked after an independent check;
- idle time on shared capacity.
