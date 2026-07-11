# Agentic Engineering Operating System

This workspace defines a practical operating model for taking a software idea from initial concept to production deployment using a responsible minimum team structure and bounded agentic workflows.

The goal is to make the work repeatable and reviewable: every idea should move through clear ownership, review gates, delivery planning, implementation, testing, deployment, monitoring, and learning. When agents are used, their work should arrive as bounded work packets with context, evidence, risks, and human approval gates.

## What This Repository Contains

| Folder | Purpose |
|---|---|
| `catalog` | Machine-readable capabilities, workflows, risk, assurance, permission, and evidence policies. |
| `schemas/v1` | Canonical contracts for programs, work items, work packets, evidence, decisions, and learnings. |
| `presets` | Starting profiles for web products, CLI tools, research platforms, and regulated services. |
| `runtime` | Vendor-neutral CLI for initialization, routing, transition checks, validation, and generated views. |
| `templates/overlay` | The `.agentic/` control-plane template installed beside product source. |
| `examples` | Valid and deliberately invalid reference instances, including Fornax. |
| `team` | Defines the 12 default role lenses and the capabilities they provide. |
| `agentic` | Defines agentic loops, work packets, permission classes, cadence controls, skill promotion, and eval tracking. |
| `program` | Contains legacy/manual tracker templates, program documents, and sprint records. |
| `external_knowledge` | Read-only reference material such as domain knowledge, coding snippets, examples, prior art, and external references. |
| `output` | Stores the actual work produced by the program, including source repositories, documentation, deliverables, and release packages. |
| `learnings` | Captures discoveries, postmortems, technical lessons, and process improvements during execution. |
| `AGENTS_template.md` | Describes the full step-by-step process for moving an idea through the team and into production. |

## Source-Of-Truth Model

- Framework definitions live in `catalog`, `schemas/v1`, and `team`.
- A product's enforceable operating state lives in `.agentic/program.yaml` and `.agentic/records`.
- Files under `.agentic/generated` are derived views and must not be edited by hand.
- Narrative plans and technical documents remain Markdown and are linked by canonical records.
- `program.framework_lock` binds validation to exact catalog, schema, runtime,
  and preset-behavior digests; `agentic upgrade` is the supported lock refresh.
- `program.source_of_truth` pins the authoritative plan's version and digest;
  `agentic source-update` requires a single-use accountable decision scoped to
  its exact path, version, and digest, while retaining prior pins as history.

## Team Model

The structure is based on 12 specialized roles:

1. Product & Delivery Manager
2. Requirements Analyst
3. UX/UI Designer
4. Solution Architect
5. Backend Engineer
6. Frontend Engineer
7. Integration Engineer
8. Code Quality Reviewer
9. QA / Test Automation Engineer
10. Security Reviewer
11. DevOps / SRE / Release Engineer
12. Documentation & Customer Feedback Owner

Each role has its own file in `team` describing purpose, responsibilities, deliverables, review responsibilities, and collaboration points.

In the agentic version of this package, roles are lenses and gates, not necessarily separate people. A human orchestrator may invoke these perspectives through agents, skills, templates, reviews, or specialist humans. The accountable human still owns the final decision.

## Agentic Operating Model

Agentic work follows five rules:

1. Start with a clear outcome and acceptance evidence.
2. Choose an appropriate loop from `agentic/loop_library.md`.
3. Scope tools and permissions using `agentic/permission_model.md`.
4. Return work as a reviewable packet using `agentic/work_packet_template.md`.
5. Convert repeated lessons into tests, skills, evals, documentation, or process changes.

The CLI makes these rules enforceable:

```bash
agentic validate-framework agentic_engineering
agentic init --preset cli_tool --source README.md /path/to/product
```

The initialized manifest is intentionally pending. Use the questions printed by
`init` to tailor the profile, capabilities, actors, reviewers, and permissions in
`.agentic/program.yaml`. Record `tailoring.answers` as a YAML list whose entries
each contain the exact persisted `question` and a non-empty `answer`; the
adoption guide shows the complete shape. Then confirm and validate:

```bash
agentic tailor /path/to/product --actor human:owner --confirm
agentic validate /path/to/product --strict
agentic new-work WORK-0001 --title "First bounded outcome" --root /path/to/product
# Edit the work item's canonical objective, acceptance, consequence, and route fields.
agentic route WORK-0001 --root /path/to/product
agentic render /path/to/product
agentic validate /path/to/product --strict
```

New work begins with `unknown` consequence facts and placeholder objective and
acceptance text. Assess those fields in the canonical YAML before moving it out
of its initial state.

## Operating Flow

The lifecycle below is a completeness map, not a mandatory linear pipeline. Each work item selects a workflow such as discovery, research spike, feature, bug fix, incident, or release; risk controls determine the gates.

1. Capture the idea.
2. Gather external knowledge.
3. Convert the idea into requirements.
4. Design the user experience.
5. Design the technical solution.
6. Plan the sprint.
7. Develop the product increment.
8. Review code and security.
9. Test the work.
10. Prepare the release.
11. Deploy to production.
12. Monitor, support, and learn.
13. Feed learning into the next sprint.

The detailed process is documented in `AGENTS_template.md`.

## How To Start With A New Idea

1. Initialize an overlay using `guides/adoption.md`; keep product source in its
   existing repository layout.
2. Answer the persisted questions through changes to `.agentic/program.yaml`,
   then have the declared accountable human run `agentic tailor --confirm`.
3. Run strict validation. A pending tailoring state, stale plan pin, or framework
   lock mismatch must be resolved before execution.
4. Start uncertain product work in the `discovery` workflow; replace its
   placeholders with a problem, actor, falsifiable hypothesis, bounded experiment,
   falsification condition, and evidence plan.
5. Start delivery work as a canonical YAML work item. Replace its objective and
   acceptance placeholders and explicitly assess every `unknown` risk fact.
6. Route the assessed item, execute a bounded work packet, and attach typed YAML
   evidence, decision, approval, or action receipts as required.
7. Transition only when canonical fields satisfy the guard or a passing evidence
   receipt / approving decision is supplied, bound to the work item, and names
   that guard in `guard_authorizations`.
8. Render and validate before human acceptance, merge, or release; promote
   repeated lessons into durable controls.

Check or update the reproducibility lock with `agentic upgrade`. When the
authoritative plan itself changes, first record an approving decision bound to
the program ID and exact proposed path/version/digest, then use
`agentic source-update`; do not replace the recorded digest by hand.

## Production Discipline

A production release should not proceed unless requirements, design, architecture, code quality, security, QA, deployment, documentation, and support readiness have been reviewed by the responsible roles.

If agentic work contributed to the release, the release should also have complete work packets, reviewed tool permissions, recorded verification evidence, and no unresolved agent-generated risks above the release threshold.

This repository is not just a folder structure. It is intended to be a working playbook for repeatable software delivery.
