# Lessons From Practice

The first version of this framework was applied to a machine-learning research program: model
training on a shared GPU cluster, benchmark reads, data jobs and model publication, run by
several capable agent sessions in parallel with one accountable human. This file records what
happened and what changed as a result. The changes are in the lean `run` workflow, actor tiers,
standing authorizations, independent evidence, budgets and resources described elsewhere in
this package.

## What happened

- **Gates stalled the work.** On a one-day engineering project every work item and every work
  packet stayed in `draft` while the real work (a native inference port, numerical checks
  against a reference engine, profiles and a benchmark matrix) finished. Each transition needed
  packet-bound evidence and a human approval per item. The project's narrative journal carried
  the truth; the records lagged behind it and were never closed.
- **Records exploded.** Evidence written per step grew to hundreds of megabytes of text that the
  owner later deleted by hand.
- **Tokens exploded.** When the same model was written into a research repository as prose
  (task ids, claims, journals, lifecycle gates, execution packets) and run by many parallel
  executor sessions, those sessions spent several hundred million tokens in three days. The cost
  grew with the number of sessions times the protocol and evidence each one re-read on every
  call. Every call re-reads the whole context, so a large early read is paid again on every later
  call until the context is compacted.
- **The validator was not the main cost.** Measured on the CLI adoption, `validate` reports were
  small (0.1k to 1.4k tokens). Governance took about a quarter of the tool calls, front-loaded in
  the first hours, mostly reading framework documentation.

The owner replaced the heavy protocol with a short one: a program file that says why each run
exists, a queue that says what runs when, one folder per run with a README (gates and
recipe), a status file (four header lines, at most three lines per entry) and a results file
that closes the run. Tools emit receipts (launch receipts, checksums, storage readbacks) and
the files point to them. The human decides promotion, priority and data rights; agents decide
everything else within written rules. Work moved faster and cost less.

## What the framework assumed

The first version treated agents as untrusted executors. An agent's own assertion of
independence did not count, an agent could not validate, only a human could approve, and every
transition needed a typed receipt. All judgment moved into the schema and to the human. With
capable agents this has two effects: the human becomes the bottleneck at every gate, and the
agents spend their intelligence filling forms instead of deciding.

## What it got right

Agents do make confident mistakes, and the research program showed several:

- a learned-latency table that was wrong until a hand-annotated gold set caught it;
- a quantisation bar that measured transcription and translation but not tool calls, so a
  package that broke tool calls passed it;
- timestamps written 35 to 60 minutes off by peer sessions;
- a decision left open while a model that depended on it was promoted.

The lean protocol caught these with a check where it mattered (gold sets, readbacks, checksums,
a bar fixed before the read), not with a gate on every step. Two things the first version had
and the lean protocol lacked are worth keeping: an explicit decision record with owner, scope
and expiry, and an explicit list of claims a result does not establish.

## What changed

| Principle | First version | Revised |
| --- | --- | --- |
| Trust | Agents untrusted; humans approve every gate | Judgment delegated by actor tier; consequences verified |
| Gating | Every transition of every item | Consequential steps only: compute above budget, publication, promotion, data rights, destructive or production actions |
| Approval | One decision per item and guard | Standing authorizations with scope, actors and expiry |
| Independence | A distinct actor and context | Independent evidence: a gold set, a readback, a bar fixed before the read |
| Evidence | Authored YAML per step | Tool-emitted receipts by reference; claims not established listed |
| Ledger | Records plus a separate journal | One ledger; other views generated from it |
| Cost | Not modelled | Token, context and coordination budgets per tier |
| Capacity | Not modelled | Resources with an owner, a capacity and a rule |
| Learning | Promote lessons | Promote and retire; guidance that only grows is a cost |

## Signals that the process is too heavy

- Work finishes while its records stay in an early state.
- A narrative file is more current than the canonical records.
- Agents ask for approval of steps that are local and reversible.
- Governance files appear in every agent's context but change rarely.
- Peer messages and status notifications cost more than the human's own turns.
- Evidence directories grow faster than results.

## Signals that the process is too light

- A decision is open while work that depends on it is promoted.
- A bar passes a result that a user would reject.
- A number in a status line has no receipt behind it.
- Two sessions use the same resource without one owner.
