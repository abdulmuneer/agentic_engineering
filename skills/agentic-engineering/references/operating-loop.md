# Operate The Program
## Choose a workflow

- Use `run` for low- or medium-risk research, experiments, benchmark reads, data
  jobs and bounded engineering. It needs no packets or evidence records.
- Use `discovery` for an unvalidated problem, actor, or value hypothesis.
- Use `feature` for an approved capability outcome with high or critical risk.
- Use `research_spike` for a bounded unknown whose answer must be reviewed before
  anything depends on it.
- Use `bug_fix`, `incident`, or `release` for their named operational contexts.

Inspect the selected workflow catalog before transitioning. Do not guess state
names or guards.

## Lean run

1. `agentic new-work <id> --workflow run --title "<outcome>" --root <root>`;
   set objective, acceptance and consequence facts. Keep the run's README,
   status and results files in its folder; do not write a parallel journal.
   Record the computed risk with `agentic route <id> --root <root> --write`.
2. Transition to `running`. Do the work. A consequential step (compute above
   budget, publication, promotion, data rights, destructive, production) cites a
   decision or an unexpired standing authorization; otherwise stop and ask.
3. Verify where being wrong would cost something: a gold set, a readback, or a
   bar fixed before the read that covers every claim.
4. Fill `results`: `ref`, tool-emitted `receipts` (uri, sha256), and
   `not_established`. Transition to `closed`, or to `stopped` with partial
   findings. A negative result closes a run.
5. Check in with `agentic status <root>`; run `validate --max-issues 20` only at
   transitions or when something looks wrong. Do not run the validator inside the
   work loop.

## Gated work

## Create and assess work

```bash
agentic new-work <work-id> \
  --title "<bounded observable outcome>" \
  --workflow <workflow> \
  --type <type> \
  --root <product-root>
```

Replace placeholders in the canonical work YAML. Resolve every `unknown` risk
fact, define observable acceptance, select required capabilities, bound
permissions, and specify evidence tuples. Then run:

```bash
agentic route <work-id> --root <product-root>
agentic render <product-root>
agentic validate <product-root> --strict
```

## Record decisions before relying on them

Use `agentic new-decision`. Bind the decision to its exact subject, name a human
owner, list reviewed evidence, and record one selected option. For a manual
transition guard, add `--authorize-guard <guard-id>` and cite that decision with
`--approval-ref` during the transition.

Elevated permission decisions must additionally bind permission classes, actor
IDs, exact action scope, and expiry. A generic approval is insufficient.

## Issue bounded work packets

Use `agentic new-packet` only after routing stabilizes. Give each packet one
producer, one run ID, a bounded goal, requested and forbidden claims, explicit
outputs, capability scope, permission scope, and context. Split independent work
across packets; do not make every packet responsible for every acceptance item.

Keep packets `draft` until the recorded output exists. A work item cannot enter
review while a linked packet remains draft.

## Attach evidence

Use `agentic new-evidence` after observing the result. Evidence must:

- name exactly one packet and its work item;
- bind its subject to a declared packet output;
- use an explicit result rather than implied success;
- cover the planned acceptance, kind, and environment tuple;
- authorize only claims requested by that packet; and
- identify producer, run, context, artifacts, and human acceptance required by
  the routed assurance level.

For external-write, sensitive, or production work, record a separate action
receipt produced by the authorized actor. It must repeat the packet, exact action
scope, authorization decision, and observation time inside the authorization
window.

## Transition

```bash
agentic transition <work-id> <target-state> \
  --root <product-root> \
  --actor <declared-actor-id>
```

If a guard cannot be derived from canonical fields, cite a passing evidence
receipt or approving decision whose `guard_authorizations` contains that exact
guard. Never use an unrelated work-bound receipt as a substitute.

## Upgrade or rebaseline

- Run `agentic upgrade <product-root>` read-only first. Apply with `--apply` only
  after explicit human review of catalog, schema, runtime, and preset changes.
- Rebaseline the authoritative source only through a single-use approving
  decision bound to the program ID and exact relative path, version, and SHA-256.
  Use `agentic source-update`; never hand-edit the digest.

## Budgets and coordination

- Use the cheapest tier that can do a task; give executors fully specified
  tickets.
- Respect `budgets` in `program.yaml`. Stop at a checkpoint before exceeding one.
- Message peers only for decisions, hand-overs and failures. Status goes in the
  status file for the next check-in.

## Cadence for gated work
Repeat:

```text
edit canonical record
→ route
→ execute bounded packet
→ attach evidence and decisions
→ render
→ validate --strict
→ transition
```
