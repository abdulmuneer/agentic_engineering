---
name: agentic-engineering
description: Bootstrap, tailor, validate, operate, audit, and upgrade the Agentic Engineering workflow in product repositories using the agentic CLI and canonical .agentic records. Use when an agent needs to initialize a governed agent program, select a preset and capabilities, define humans and agent tiers, budgets and resources, create or route work (lean runs or gated work), record decisions and standing authorizations, close results with receipts, transition workflow state, diagnose validation failures, or review framework/source drift.
---

# Agentic Engineering

Use the skill as the intent-aware orchestration layer. Use the installed `agentic`
CLI, catalogs, schemas, and validators as the enforcement layer. Never duplicate
or weaken those controls in ad hoc files or prose, and never re-create them as a
prose protocol for parallel agents to re-read: that is where the first version's
cost came from.

Judgment is delegated; consequences are verified. Gate consequential steps only,
keep one ledger, reference tool-emitted receipts, and treat human attention,
tokens, coordination and shared capacity as budgets.

## Resolve the mode

- **Bootstrap:** The product has no `.agentic/program.yaml`, or the user asks to
  adopt the framework. Read [references/bootstrap.md](references/bootstrap.md).
- **Operate:** A confirmed overlay exists and the user wants to create, execute,
  review, or transition work. Read
  [references/operating-loop.md](references/operating-loop.md).
- **Audit:** The user asks for status, diagnosis, readiness, or compliance. Run
  read-only validation and inspect canonical records; do not mutate state.
- **Upgrade or rebaseline:** The framework lock or authoritative source changed.
  Read the relevant section in
  [references/operating-loop.md](references/operating-loop.md) and require the
  explicit decision records described there.

For every mode, read [references/invariants.md](references/invariants.md) before
making consequential changes.

## Establish context

1. Resolve the product root and read applicable `AGENTS.md` files.
2. Inspect Git status and preserve unrelated or pre-existing changes.
3. Locate `.agentic/program.yaml`, the declared source-of-truth file, and
   canonical records. Treat `.agentic/generated/` as disposable.
4. Confirm that `agentic` is available. If it is missing, locate the framework
   checkout or installed package and ask before installing it.
5. Run `agentic validate <product-root> --strict` when an overlay exists. Use the
   report to determine the next safe action; do not hand-edit around an error.

## Orchestrate work

### Bootstrap a product

Follow [references/bootstrap.md](references/bootstrap.md) completely. Select the
closest preset, initialize the overlay, propose project-specific capability and
actor assignments, persist all tailoring questions, and obtain real answers.

Do not run `agentic tailor --confirm` until the declared accountable human has
explicitly approved the populated tailoring model. Confirmation records a human
gate; it is not a formatting step.

### Operate a program

Follow [references/operating-loop.md](references/operating-loop.md). Use the
lean `run` workflow for low- and medium-risk research and bounded engineering;
use `discovery` when the problem or value hypothesis is unvalidated, and gated
delivery workflows for high- or critical-risk work, releases and incidents.

For a lean run, do the work, then close it with results (reference, receipts,
claims not established). Check in with `agentic status`. Run the validator at
transitions, not inside the work loop.

For gated work, use CLI authoring commands for new records and bounded edits to
canonical YAML. After each material mutation:

1. Run `agentic route` for affected work when risk or scope changed.
2. Run `agentic render <product-root>`.
3. Run `agentic validate <product-root> --strict --max-issues 20`.
4. Transition only when every guard is satisfied by canonical state, an exact
   typed receipt, or an unexpired standing authorization that covers it.

### Audit a program

Run strict validation, then report:

- current work and workflow states;
- pending human decisions, tailoring answers, and expiring standing
  authorizations;
- unresolved risk facts, permissions, and waivers;
- missing packet, evidence, review, or action receipts;
- framework/source lock drift; and
- the smallest safe next action.

Do not implement fixes during an audit unless the user also asks for changes.

## Preserve human authority

Stop and request explicit direction before the following, unless an unexpired
standing authorization covers the exact step:

- confirming tailoring;
- marking a discovery outcome committed, narrowed, killed, or parked;
- accepting or waiving risk;
- granting elevated permissions;
- applying a framework upgrade;
- rebasing the authoritative source; or
- performing external, sensitive, destructive, or production actions.

Do not stop for local, reversible work. Agents may prepare records,
recommendations and proposed standing authorizations. They may not impersonate
the accountable human or manufacture approvals.

## Finish with evidence

Do not claim success from a narrative summary. A lean run finishes with results
that reference receipts and list the claims not established. Gated work finishes
only after the relevant canonical records exist and strict validation passes. Report created or changed
record IDs, the current workflow state, validation results, unresolved human
gates, and the next permitted transition.
