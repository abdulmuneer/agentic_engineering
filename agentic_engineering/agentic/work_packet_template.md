# Agentic Work Packet Template

Use a work packet for gated work (feature, bug fix, incident, release, and any work item whose
routed risk is high or critical) and as the ticket for an executor-tier agent. Lean `run` work
does not need packets: its README, status file and results file are the ledger, and tools emit
the receipts.

Keep a packet short. Point to receipts; do not paste logs.

## Work Packet

| Field | Value |
|---|---|
| Packet ID | AWP-001 |
| Date | YYYY-MM-DD |
| Linked Item | Work item id |
| Tier | Planner / Worker / Executor |
| Accountable Human |  |
| Agent / Model / Tooling Used |  |
| Permission Class | Read-only / Local write / External read / External write / Sensitive / Production |
| Covering Decision | Decision id or standing authorization id, if consequential |
| Base / Result Commit |  |
| Budget | Tokens or wall time, and what was used |
| Receipts | URIs and checksums emitted by tools |
| Independent Evidence | Gold set / readback / bar fixed before the read / second reader, and what it covers |
| Claims Not Established |  |
| Status | Draft / Ready For Review / Accepted / Rejected / Needs Rework |

## Goal

What outcome was requested, and why it exists.

## For an executor ticket

Command, inputs (pinned), outputs (paths), stop rule, and how the result is read back. No
judgment calls; anything not specified is a stop.

## Results

Numbers, identities, receipts. One paragraph.

## Skipped Checks

Expected checks that were not run and why.

## Claims Not Established

What this result does not show. For example: "not measured on long audio", "bar does not cover
tool calls", "depends on open decision DEC-012".

## Human Review

Only for consequential steps and gated workflows.

| Reviewer | Lens | Decision | Notes |
|---|---|---|---|
|  |  | Accepted / Rejected / Needs Rework |  |

## Promotion Candidate

Should anything from this work become a test, eval, skill, rule, or a retired rule?
