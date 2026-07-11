# Executable Kernel

This package turns the handbook into a small, vendor-neutral operating-model
compiler. It does not spawn agents or decide whether evidence is intellectually
sufficient. It makes project tailoring, routing, provenance, separation of
duties, and source-of-truth consistency inspectable and enforceable.

## Commands

| Command | Purpose |
|---|---|
| `agentic init` | Install a pending `.agentic/` overlay, persist tailoring questions, and pin the framework. |
| `agentic tailor` | Record accountable-human confirmation of the project-specific operating model. |
| `agentic new-work` | Create a canonical YAML draft with placeholders and unknown consequence facts. |
| `agentic new-packet` | Create a draft execution packet and atomically link it to work. |
| `agentic new-decision` | Record an explicit decision, optional permission grant or risk acceptance, and backlinks. |
| `agentic new-evidence` | Record an explicit-result evidence or action receipt and link it to a packet. |
| `agentic route` | Compute effective risk, minimum assurance, capabilities, evidence, and permission ceiling. |
| `agentic transition` | Move work through a workflow using canonical fields and typed guard receipts. |
| `agentic validate` | Validate the project, source pin, framework lock, records, evidence, independence, and views. |
| `agentic validate-framework` | Validate catalogs, role metadata, workflows, schemas, and presets. |
| `agentic render` | Regenerate disposable operating-model, coverage, active-work, and AGENTS views. |
| `agentic upgrade` | Compare or update the version plus catalog/schema/behavior framework lock. |
| `agentic source-update` | Rebaseline the authoritative plan through a bound accountable decision. |

Run framework validation from the repository without installation:

```bash
python3 -m agentic_engineering.runtime validate-framework agentic_engineering
```

Install the `agentic` command:

```bash
python3 -m pip install -e .
```

## Bootstrap Sequence

The authoritative source named by `--source` must already exist inside the
product repository.

```bash
agentic init \
  --preset cli_tool \
  --source README.md \
  /path/to/product
```

`init` prints and persists the preset's questions. Edit
`/path/to/product/.agentic/program.yaml` so its profile, capability dispositions,
actors, reviewers, and permission ceilings answer them. The initialized program
must contain a non-empty `tailoring.answers` entry for every question and remains
pending until its declared accountable human confirms it:

```yaml
tailoring:
  questions:
    - Does the tool authenticate to remote systems or store credentials?
  answers:
    - question: Does the tool authenticate to remote systems or store credentials?
      answer: Tokens stay in the operating-system keychain and are never logged.
```

`answers` is a list of `question`/`answer` mappings; copy each question exactly.

```bash
agentic tailor /path/to/product --actor human:owner --confirm
agentic validate /path/to/product --strict
```

Strict validation fails while tailoring is pending. `init` also writes a managed
pointer in the product's root `AGENTS.md`; generated guidance remains under
`.agentic/generated/`.

## Work Records And Transitions

```bash
agentic new-work WORK-0001 \
  --title "First bounded outcome" \
  --workflow feature \
  --root /path/to/product
```

The draft uses `unknown` for unassessed consequence facts and placeholder text
for its objective and acceptance. Edit the canonical YAML under
`.agentic/records/work_items/`, assess every fact, and reconcile risk, assurance,
capabilities, permissions, and the evidence plan with the computed route:

```bash
agentic route WORK-0001 --root /path/to/product
agentic render /path/to/product
agentic validate /path/to/product --strict
```

Transitions consume canonical fields. A guard that cannot be derived from those
fields requires `--confirm-guard` plus a typed receipt:

```bash
agentic transition WORK-0001 in_progress \
  --root /path/to/product \
  --actor human:owner \
  --confirm-guard review_capacity_available \
  --approval-ref DEC-WORK-0001-START
```

Evidence receipts must be passing and bound to the work item. Approval references
must resolve to an approving decision whose `subject_refs` includes the work item.
Each manually confirmed guard must also appear in that receipt's
`guard_authorizations`; bare confirmation strings, missing IDs, and unrelated
receipts are rejected.

## Author Downstream Records

Create packets only after the work route, risk, capabilities, permissions, and
evidence plan agree. The command creates a draft and never claims completion:

```bash
agentic new-packet AWP-WORK-0001 \
  --work WORK-0001 \
  --producer agent:delivery \
  --run-id RUN-WORK-0001 \
  --goal "Implement only the named acceptance behavior" \
  --claim acceptance:AC-WORK-0001-1 \
  --output-ref src/example.py \
  --output-summary "Bounded implementation output" \
  --root /path/to/product
```

Decisions are explicit records, including decisions used as guard receipts:

```bash
agentic new-decision DEC-WORK-0001-START \
  --type delivery \
  --title "Confirm review capacity" \
  --subject WORK-0001 \
  --option 'OPTION-START=Start the bounded packet.' \
  --outcome approve \
  --selected-option OPTION-START \
  --rationale "A named reviewer has capacity for this packet." \
  --owner human:owner \
  --authorize-guard review_capacity_available \
  --root /path/to/product
```

Evidence has no default result. Run the named check first, then record the result
that actually occurred; `fail`, `inconclusive`, and `not_run` never satisfy an
acceptance gate:

```bash
agentic new-evidence EV-WORK-0001-TEST \
  --work WORK-0001 \
  --packet AWP-WORK-0001 \
  --kind deterministic_test \
  --producer agent:review \
  --run-id RUN-VERIFY-WORK-0001 \
  --result pass \
  --observed-at 2026-07-10T12:00:00Z \
  --acceptance-ref AC-WORK-0001-1 \
  --claim acceptance:AC-WORK-0001-1 \
  --subject-ref src/example.py \
  --command "python -m unittest" \
  --environment local \
  --root /path/to/product
```

At A1 and above, packet and evidence authors must also supply a distinct
`--context-digest`; A2 and A3 add independent-producer and human-approval
requirements. Elevated permissions require an unexpired authorization decision,
then a separate action receipt.

Canonical project and record contracts are YAML envelopes under `.agentic/`.
Markdown files under `.agentic/generated/` are disposable renderings.

## Reproducible Upgrades And Source Rebaselines

`program.framework_lock` contains the framework version plus catalog, schema,
and executable-behavior digests. Check first, apply deliberately, then validate:

```bash
agentic upgrade /path/to/product
agentic upgrade /path/to/product --apply
agentic validate /path/to/product --strict
```

The authoritative source has a separate version and digest. Its approving
decision is single-use and must bind the accountable human, program ID, proposed
relative path, version, and exact SHA-256:

```bash
agentic new-decision DEC-SOURCE-0001 \
  --type product \
  --title "Adopt plan version 2" \
  --subject <program-id> \
  --option 'OPTION-ADOPT=Adopt the reviewed source revision.' \
  --outcome approve \
  --selected-option OPTION-ADOPT \
  --rationale "The accountable owner reviewed this exact revision." \
  --owner human:owner \
  --source-path docs/program-plan.md \
  --source-version 2 \
  --source-sha256 <64-hex-sha256> \
  --root /path/to/product
```

Then apply that exact approval:

```bash
agentic source-update /path/to/product \
  --actor human:owner \
  --decision-ref DEC-SOURCE-0001 \
  --declared-version 2
```

The prior source pin is retained in `source_of_truth.history`, so historical work
keeps its original `source_revision` while new work binds to the current version.

The runtime requires both PyYAML and `jsonschema`; validation fails loudly when
the canonical-schema validator is unavailable.
