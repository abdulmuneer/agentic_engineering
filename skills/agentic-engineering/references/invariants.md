# Non-Negotiable Invariants

## Canonical state

- Treat `.agentic/program.yaml` and `.agentic/records/**/*.yaml` as authority.
- Treat `.agentic/generated/` as disposable output. Regenerate it; never edit it.
- Keep product plans, code, tickets, and CI in their existing systems and link
  them by stable IDs instead of creating a duplicate backlog.

## Accountability

- Keep product, risk, permission, source, upgrade, and release accountability
  human-owned.
- Treat roles as review lenses and capabilities, not mandatory headcount.
- Delegate judgment by actor tier; keep executors within their tickets.
- Never record a decision, answer, acceptance, or approval that did not occur.

## Risk and permissions

- Gate consequential steps only. Never block local, reversible work for want of a
  record or approval.
- A standing authorization covers only its scope, actors, `applies_to` and
  unexpired window.
- Keep `run` work at low or medium risk; route higher risk through a gated
  workflow.

- Resolve unknown consequence facts before leaving an initial state.
- Apply the highest routed risk and assurance requirement; never lower it by
  assertion.
- Require a decision-backed, expiring waiver with compensating controls for an
  allowed downgrade. Never downgrade critical risk.
- Keep actor permissions within declared ceilings. Require scoped approval and
  an action receipt for elevated operations.

## Evidence

- Accept only passing, packet-bound, output-bound evidence for workflow gates.
- Preserve failed, inconclusive, and not-run results; do not relabel them as pass.
- Enforce producer/reviewer/context separation at routed assurance levels, or
  satisfy it with independent evidence (gold set, readback, bar fixed before the
  read). Independent evidence never replaces required human acceptance.
- A bar covers every claim the result makes; list what is not established.
- Reference tool-emitted receipts; do not author evidence files per step.
- Bound claims to what evidence actually observed. Explicitly retain forbidden
  claims such as production readiness when they were not established.

## Reproducibility and drift

- Enforce the framework lock over catalogs, schemas, runtime, and presets.
- Preserve source revision history. Require an exact, single-use decision for a
  source rebaseline.
- Stop on lock, source, schema, generated-view, or relationship drift. Use the
  supported command to repair the relevant layer rather than suppressing it.

## Cost

- Treat human attention, tokens, coordination and shared capacity as budgets.
- Keep shared guidance short and current; replace superseded rules instead of
  stacking them.

## Completion

- Do not equate code changes or an agent summary with completion.
- For gated work, require the correct packet status, evidence plan coverage,
  review receipts, decisions, workflow history, and strict validation.
- For a lean run, require results with a reference, receipts and the claims not
  established.
- Report unresolved human gates and the next permitted transition explicitly.
