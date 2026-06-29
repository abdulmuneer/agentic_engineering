# Agentic Cadence Controls

Use these controls so agents do not outrun human attention, review capacity, or recovery.

## Review Windows

Define review windows for agent outputs:

| Window | Purpose | Reviewer | Max Work Packets |
|---|---|---|---|
| Morning | Review overnight or queued outputs. |  |  |
| Midday | Resolve ambiguous work and unblock agents. |  |  |
| End of day | Decide what can run safely later. |  |  |

## WIP Limits

| Limit | Default Guidance | Current Limit |
|---|---|---|
| Active agent runs | No more than can be reviewed in the next review window. |  |
| Unreviewed work packets | Stop starting work when review queue is full. |  |
| Diff size per packet | Keep small enough for meaningful review. |  |
| Autonomous runtime before checkpoint | Require checkpoint before large edits or risky actions. |  |
| Open decisions | Do not let agents proceed through unresolved product, security, or release decisions. |  |

## Checkpoints

Require a checkpoint:

- After context gathering.
- Before large edits.
- Before database, infrastructure, or auth changes.
- Before external writes.
- After first failing test is reproduced.
- After verification.
- Before merge, release, or production action.

## Safe Overnight Work

Usually safe:

- Read-only research.
- Test generation without production code edits.
- Documentation drafts from already merged changes.
- Log clustering and support-ticket summarization.
- Dependency impact analysis without applying updates.

Usually not safe:

- Auth, payment, security, or privacy changes.
- Production deployments or rollbacks.
- Database migrations.
- Broad refactors.
- External writes.
- Work that cannot be reviewed quickly the next morning.

## Cadence Metrics

Track:

- Unreviewed work packets.
- Time from agent completion to human decision.
- Rework rate.
- Review interruption count.
- Skipped checks.
- Night or weekend approval count.
- Agent work rejected for scope drift.
