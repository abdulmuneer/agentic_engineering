# Agentic Engineering

<img src="https://abdulmuneer.github.io/assets/images/agentic-manifesto.png" alt="Agentic Engineering manifesto" width="720">

This repository is a practical operating system for building software with small, accountable teams and bounded delegated workflows. It turns a software idea into a structured program: intake, requirements, design, architecture, implementation, review, testing, release, monitoring, and learning.

The goal is not to add ceremony. The goal is to make high-velocity engineering work reviewable, repeatable, and safe enough to use on real products.

For more context, read the companion blog post: [Agentic Engineering](https://abdulmuneer.github.io/agentic-engineering/).

## What This Repo Is Trying To Do

Modern software work is no longer limited by a single person's hands on a keyboard. Teams can delegate research, drafting, coding, testing, documentation, and operational tasks to a mix of people, tools, and automated assistants. That increases throughput, but it also increases review burden, coordination cost, and the risk of accepting work that was never properly checked.

This repository provides a working structure for that environment:

- Define the outcome before execution starts.
- Keep ownership explicit, even when work is delegated.
- Break work into reviewable packets with context, evidence, assumptions, and risks.
- Use role-based review gates for product, design, architecture, code quality, security, QA, release, and documentation.
- Track decisions, dependencies, risks, capacity, test readiness, and release readiness in plain files.
- Convert repeated lessons into reusable processes, checks, tests, and templates.

In short: this repo is about making delegated software delivery disciplined instead of chaotic.

## Why It Exists

Software teams already know the fundamentals: clear requirements, small batches, good architecture, tests, security review, release discipline, observability, and learning from production. Those fundamentals become more important when execution gets faster.

Without structure, faster execution can produce more unfinished work, more unreviewed changes, and more hidden rework. With structure, the same speed can become a compounding advantage: better context, better checks, better runbooks, better review habits, and better future execution.

This framework preserves engineering judgment while making the operating approach explicit, project-specific, and machine-checkable.

## Principles

- **Accountability stays human.** Tools and agents can perform work, but approval, prioritization, and production responsibility remain assigned to people.
- **Evidence beats confidence.** A completed task should point to changed files, tests run, skipped checks, decisions made, and remaining risks.
- **Roles are lenses, not bureaucracy.** The 12-role structure captures the perspectives needed to ship responsibly; it does not require a 12-person team.
- **Permissions should match risk.** Read-only research, local edits, external writes, production changes, and sensitive data access need different controls.
- **Learning should compound.** Repeated mistakes become tests or guardrails. Repeated success becomes a reusable workflow.

## How The Executable Kernel Works

The repository separates three kinds of material:

| Layer | Source Of Truth | Purpose |
|---|---|---|
| Framework kernel | `agentic_engineering/catalog`, `team`, `schemas/v1`, `runtime`, and `presets` | Reusable capabilities, role lenses, workflows, controls, schemas, and executable enforcement. |
| Project instance | A product repository's `.agentic/program.yaml` and `.agentic/records` | The selected capabilities, accountable humans, agents, work, evidence, decisions, and learnings for that product. |
| Generated views | `.agentic/generated` | Disposable AGENTS guidance, capability coverage, operating-model, and active-work views. |

The invariant is capability coverage, evidence, and accountability—not a fixed number of roles or agents.

## Quickstart

```bash
python3 -m pip install -e .
make check
agentic init --preset research_platform --source README.md /path/to/product
```

`init` writes a pending project instance, persists the preset's tailoring
questions, pins the framework catalog, schemas, and runtime behavior, and adds a managed pointer in
the product's root `AGENTS.md`. It does not claim that the preset is already a
project-specific operating model. Review the printed questions, then edit
`.agentic/program.yaml` to reflect the real profile, capability dispositions,
actors, reviewers, and permission ceilings. Add one non-empty
`tailoring.answers` entry for every persisted question.

`tailoring.answers` is a YAML list of `question`/`answer` mappings. Copy each
persisted question exactly so confirmation can match it:

```yaml
tailoring:
  questions:
    - Which environments and seeds are required for reproducibility?
  answers:
    - question: Which environments and seeds are required for reproducibility?
      answer: CI runs three fixed seeds in the pinned CPU and GPU environments.
```

```bash
agentic tailor /path/to/product --actor human:owner --confirm
agentic validate /path/to/product --strict
```

Strict validation intentionally fails on the pending-tailoring warning until the
accountable human confirms it. The initialized `.agentic/` directory is an
overlay: product source stays at the product root and is not nested inside this
framework.

## Start Here

- [Template README](agentic_engineering/README.md) explains the full structure.
- [Codex skill](skills/agentic-engineering/SKILL.md) orchestrates bootstrap,
  operation, audit, and governed upgrades through the executable kernel.
- [Adoption guide](agentic_engineering/guides/adoption.md) explains tailoring and migration.
- [Fornax example](agentic_engineering/examples/fornax/README.md) demonstrates domain-specific roles, evidence, and drift rejection.
- [Operating process](agentic_engineering/AGENTS_template.md) describes the end-to-end workflow.
- [Team roles](agentic_engineering/team) define the role lenses and review responsibilities.
- [Executable catalogs](agentic_engineering/catalog) define risk-adaptive workflows and control policies.
- [Canonical schemas](agentic_engineering/schemas/v1) define project and record contracts.
- [Program trackers](agentic_engineering/program/trackers) cover intake, requirements, backlog, delivery, risks, decisions, metrics, and release readiness.
- [Delegated workflow controls](agentic_engineering/agentic) cover loops, permissions, work packets, cadence, reusable skills, and evaluation checks.

## How To Use It

1. Initialize an overlay using the closest preset.
2. Answer the persisted questions by tailoring `.agentic/program.yaml`: update
   the profile and actors, then activate, waive, or mark each capability not
   applicable with an explicit rationale and reconsideration trigger.
3. Have the declared accountable human confirm the result with `agentic tailor
   --confirm`, then run strict validation.
4. Create a canonical YAML work item. Replace the draft objective and acceptance
   placeholders and assess every `unknown` consequence fact before attempting a
   transition.
5. Route the assessed work by workflow, consequence, permissions, and assurance.
6. Execute bounded work packets and attach subject-bound evidence and approval
   receipts. Manual guard confirmations must cite a passing `--evidence-ref` or an
   approving `--approval-ref` bound to that work item and explicitly listing the
   guard in `guard_authorizations`.
7. Render human-readable views from canonical state, then validate before review
   or release and promote accepted learnings into durable controls.

Useful commands:

```bash
agentic new-work WORK-0001 --title "First bounded outcome" --root /path/to/product
# Edit .agentic/records/work_items/WORK-0001.yaml: objective, acceptance,
# consequence facts, risk, evidence plan, capabilities, and permissions.
agentic route WORK-0001 --root /path/to/product
agentic render /path/to/product
agentic validate /path/to/product --strict
agentic transition WORK-0001 classified --root /path/to/product --actor human:owner
# Continue with `agentic new-decision`, `agentic new-packet`, and
# `agentic new-evidence`; each command writes canonical YAML and backlinks.
agentic render /path/to/product
agentic validate /path/to/product --strict
```

`program.yaml` and records below `.agentic/records/` are canonical YAML.
Generated Markdown is a disposable view; pull requests and issue trackers may
link to canonical IDs but do not replace required records.

The project instance also contains a framework lock over catalogs, schemas, and
runtime/preset behavior. Check it before adopting a new framework checkout, and
update it explicitly after reviewing the change:

```bash
agentic upgrade /path/to/product
agentic upgrade /path/to/product --apply
agentic validate /path/to/product --strict
```

Do not hand-edit the authoritative-source digest after its plan changes. Create a
single-use approving decision bound to the program ID and the exact proposed
source path, version, and digest:

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
  --root /path/to/product
```

Then rebaseline through the accountable command:

```bash
agentic source-update /path/to/product \
  --actor human:owner \
  --decision-ref DEC-SOURCE-0001 \
  --declared-version 2
```

The prior pin remains in `source_of_truth.history`; existing work retains its
historical `source_revision`, while newly created work uses the current version.

## What It Is Not

This is not tied to a specific vendor, assistant, IDE, or orchestration tool. The executable kernel routes and validates work; it does not replace product, engineering, security, or release judgment.

## Layout

```text
.
├── README.md
├── pyproject.toml
├── tests/
├── skills/
│   └── agentic-engineering/
└── agentic_engineering/
    ├── catalog/
    ├── schemas/v1/
    ├── presets/
    ├── runtime/
    ├── templates/overlay/
    ├── examples/fornax/
    ├── team/
    ├── agentic/
    ├── program/
    └── guides/
```
