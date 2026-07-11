# Adopting Agentic Engineering In A Product Repository

Adopt this framework as a small governance overlay on the product repository. Do
not move the product into this repository and do not copy every template into the
product.

## Three Layers

| Layer | Lives where | Purpose |
|---|---|---|
| Framework catalog | This repository | Reusable capabilities, role profiles, routes, controls, schemas, and templates |
| Project instance | Product repository | The project's selected capabilities, people and agents, evidence policy, current phase, and source of truth |
| Generated views | Product repository | Concise guidance such as `AGENTS.md` and a readable operating-model summary derived from the project instance |

The project instance is authoritative for how one product operates. Generated
views must identify their source and should never acquire hand-maintained policy
that is absent from the project instance.

## Recommended Overlay

```text
my-product/
  src/                               # stays where the product expects it
  tests/
  AGENTS.md                          # project guidance plus managed overlay pointer
  .agentic/
    program.yaml                     # canonical project instance
    records/
      work_items/                     # routed, risk-classified work
      work_packets/                   # bounded execution and provenance
      evidence/                       # subject-bound verification receipts
      decisions/                      # consequential decisions
      learnings/                      # promotion candidates
    generated/
      AGENTS.md                       # disposable execution guidance
      operating-model.md             # disposable human-readable view
```

Existing issue trackers, pull requests, CI systems, decision records, and product
plans remain sources of truth. Reference them from `program.yaml`; do not create a
second backlog or status system. `init` preserves existing root guidance and adds
a managed pointer to `.agentic/generated/AGENTS.md`.

## Initialize, Tailor, And Confirm

Install the CLI with full canonical-schema validation from the framework checkout:

```bash
python3 -m pip install -e .
```

Choose an authoritative product or technical source that already exists in the
target repository. `README.md` is a valid starting source, though a versioned
product plan is preferable for a long-running program.

```bash
agentic init \
  --preset research_platform \
  --source docs/project-plan.md \
  /path/to/my-product
```

Initialization persists the preset's tailoring questions in
`.agentic/program.yaml` with `tailoring.status: pending`. It also records a
framework lock containing the framework version plus catalog, schema, and
runtime/preset behavior digests. Read
the printed questions and use them to revise the project profile, capability
dispositions, actors, reviewers, and permission ceilings. Keep the questions in
the manifest as the record of what was considered, and add a matching non-empty
entry under `tailoring.answers` for every question.

The answers are a YAML list of mappings, not a mapping keyed by question. Copy
each persisted question exactly:

```yaml
tailoring:
  questions:
    - Which environments and seeds are required for reproducibility?
  answers:
    - question: Which environments and seeds are required for reproducibility?
      answer: CI runs three fixed seeds in the pinned CPU and GPU environments.
```

The declared accountable human then confirms the tailored result:

```bash
agentic tailor /path/to/my-product --actor human:owner --confirm
agentic validate /path/to/my-product --strict
```

Strict validation treats pending tailoring as a failure. Confirmation is not an
answer generator: it records that the accountable human reviewed the project-
specific choices already written into the manifest.

## Tailoring Workflow

1. Name the product outcome, target user, accountable human, lifecycle phase, and
   authoritative product or technical plan.
2. Describe the product topology and material risks: interfaces, deployment,
   sensitive data, external effects, production access, and irreversible actions.
3. Select the capabilities the work requires before selecting agents. In the v1
   manifest, mark each capability `active`, `not_applicable`, or `waived`.
4. Represent a conditional capability as currently `not_applicable` with a clear
   activation trigger. Give a scope-based omission a rationale and a
   reconsideration trigger. Time-bound exceptions are `waived`, with an owner,
   expiry, compensating controls, and decision reference where applicable.
5. Map active capabilities to declared humans, agents, or automation. One person
   may cover several functions; the risk policy determines when producer,
   validator, specialist, and approver must be distinct.
6. Confirm that every actor's permission ceiling is sufficient for its assigned
   work but no broader than necessary.
7. Retain the persisted questions, run `agentic tailor --confirm`, then run strict
   validation and commit the overlay with the product.

A new product bet should also have a short discovery record: problem and user
evidence, riskiest assumption, cheapest useful experiment, falsification
threshold, timebox, and a `COMMIT`, `NARROW`, `KILL`, or `PARK` decision.
Routine fixes do not need a new product-discovery document.

## Start Bounded Work

Create the work item only after the program has been tailored and validated:

```bash
agentic new-work WORK-0001 \
  --title "First bounded outcome" \
  --workflow feature \
  --root /path/to/my-product
```

The new canonical YAML deliberately contains placeholder objective and acceptance
text. Its consequence fields begin as `unknown`; this means "not assessed," not
"safe." Edit `.agentic/records/work_items/WORK-0001.yaml` and explicitly set:

- the observable objective and acceptance criteria;
- affected surfaces and paths;
- every consequence fact, including production, identity, sensitive data,
  external writes, reversibility, and blast radius;
- the resulting risk and assurance level;
- required capabilities and permissions; and
- evidence kinds, environments, and minimum assurance.

Then inspect the computed controls and validate:

```bash
agentic route WORK-0001 --root /path/to/my-product
agentic render /path/to/my-product
agentic validate /path/to/my-product --strict
agentic transition WORK-0001 classified \
  --root /path/to/my-product \
  --actor human:owner
```

The transition remains blocked while canonical fields are placeholders or risk
facts are `unknown`.

## Typed Guard Receipts

Workflow guards are recorded in the work item's transition history. A guard that
is satisfied by a canonical field needs no extra assertion. A manually confirmed
guard must cite a typed, resolvable receipt:

- `--evidence-ref EV-*` names passing YAML evidence bound to the work item and
  explicitly authorizing the confirmed guard.
- `--approval-ref DEC-*` names an approving YAML decision bound to the work item
  and explicitly authorizing the confirmed guard.

For example, if starting work requires an explicit review-capacity decision:

```bash
agentic transition WORK-0001 in_progress \
  --root /path/to/my-product \
  --actor human:owner \
  --confirm-guard review_capacity_available \
  --approval-ref DEC-WORK-0001-START
```

Create and validate that decision under `.agentic/records/decisions/` first; its
`subject_refs` must contain `WORK-0001` and its outcome must approve, go, commit,
or explicitly accept risk. Evidence receipts likewise need a passing result and
the matching `work_item_ref`. In both cases, `guard_authorizations` must include
`review_capacity_available`; `agentic new-decision --authorize-guard
review_capacity_available` writes it. Bare confirmation strings are not receipts.

## Framework And Source Updates

The framework lock makes results reproducible against the exact catalog, schema,
runtime, and preset behavior. Check before adopting a new framework checkout;
apply only after reviewing its policy/schema/runtime changes:

```bash
agentic upgrade /path/to/my-product
agentic upgrade /path/to/my-product --apply
agentic validate /path/to/my-product --strict
```

The authoritative plan has a separate version and digest pin. When it changes,
create a single-use approving decision whose owner is the accountable human,
whose `subject_refs` contains the program ID, and whose `source_update` binds the
exact relative path, version, and SHA-256. The authoring command exposes those
fields directly:

```bash
agentic new-decision DEC-SOURCE-0001 \
  --type product --title "Adopt plan version 2" \
  --subject <program-id> \
  --option 'OPTION-ADOPT=Adopt the reviewed source revision.' \
  --outcome approve --selected-option OPTION-ADOPT \
  --rationale "The accountable owner reviewed this exact revision." \
  --owner human:owner \
  --source-path docs/program-plan.md --source-version 2 \
  --source-sha256 <64-hex-sha256> \
  --root /path/to/my-product
```

Then rebaseline through the command rather than editing the digest:

```bash
agentic source-update /path/to/my-product \
  --actor human:owner \
  --decision-ref DEC-SOURCE-0001 \
  --declared-version 2
```

The command records who updated the pin, when, and under which decision. It
retains the prior pin in `source_of_truth.history`, so historical work can keep
its original `source_revision` without being rewritten.

## Canonical Records And Views

`program.yaml` and the YAML envelopes under `.agentic/records/` are authoritative.
Generated Markdown under `.agentic/generated/` is disposable and must be
regenerated after canonical changes. Pull requests and tickets can link to record
IDs, but do not replace required work packets, decisions, evidence, or action
receipts.

## Keep It Thin

- Create an artifact only when it supports a decision, handoff, approval, or
  durable evidence claim.
- Use the smallest canonical record that satisfies the applicable workflow and
  risk policy; do not create records for inactive future work.
- Gates belong at consequential decisions, public capability claims, material
  spend, production changes, and irreversible actions—not at every lifecycle
  stage.
- Treat missing ownership, stale source-of-truth references, broken evidence
  links, and invalid reviewer independence as errors. Treat most completeness
  suggestions as warnings.
- Focus operational detail on the next consequential gate. Do not generate empty
  trackers for hypothetical future work.

## Migrating From The Folder-Copy Model

1. Inventory project-specific edits in copied `team`, `program`, `agentic`, and
   `AGENTS` files. Separate real decisions from unchanged template text.
2. Add `.agentic/program.yaml` to the product repository and encode
   only current decisions: capability dispositions and triggers, assignments,
   routes, evidence rules, permissions, source-of-truth paths, and the next gate.
3. Point the instance at useful existing plans, trackers, tests, and evidence.
   Leave them in place; migration should not rewrite product history.
4. Keep customized role prompts or skills in the product's normal agent/skill
   location and reference them from the instance. Continue to inherit generic
   role guidance from the framework catalog where no customization exists.
5. Persist the tailoring questions, confirm them through the accountable human,
   and generate the root `AGENTS.md` pointer plus readable operating-model views.
   Compare those views with the copied guidance and resolve missing decisions.
6. Create a framework lock and a decision-bound source pin; do not silently treat
   the current checkout or an edited README as an approved rebaseline.
7. Run strict validation before retiring duplicates. Archive superseded copied
   templates only after all live links and responsibilities resolve through the
   overlay.

`examples/fornax/` demonstrates the result for a research system: domain roles
replace generic implementation roles, frontend is explicitly omitted, operator
experience covers the CLI, and physical claims require G2 evidence.
