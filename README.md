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

This template is meant to preserve engineering judgment while making the operating approach explicit enough to copy into a real project.

## Principles

- **Accountability stays human.** Tools and agents can perform work, but approval, prioritization, and production responsibility remain assigned to people.
- **Evidence beats confidence.** A completed task should point to changed files, tests run, skipped checks, decisions made, and remaining risks.
- **Roles are lenses, not bureaucracy.** The 12-role structure captures the perspectives needed to ship responsibly; it does not require a 12-person team.
- **Permissions should match risk.** Read-only research, local edits, external writes, production changes, and sensitive data access need different controls.
- **Learning should compound.** Repeated mistakes become tests or guardrails. Repeated success becomes a reusable workflow.

## Start Here

- [Template README](agentic_engineering/README.md) explains the full structure.
- [Operating process](agentic_engineering/AGENTS_template.md) describes the end-to-end workflow.
- [Team roles](agentic_engineering/team) define the role lenses and review responsibilities.
- [Program trackers](agentic_engineering/program/trackers) cover intake, requirements, backlog, delivery, risks, decisions, metrics, and release readiness.
- [Delegated workflow controls](agentic_engineering/agentic) cover loops, permissions, work packets, cadence, reusable skills, and evaluation checks.

## How To Use It

1. Copy `agentic_engineering/` into a product or project workspace.
2. Start with `program/trackers/idea_intake_tracker.md`.
3. Turn approved ideas into requirements, backlog items, risks, and decisions.
4. Use the role files in `team/` as review lenses during planning and delivery.
5. Store produced work under `output/`.
6. Capture discoveries, postmortems, and process improvements under `learnings/`.
7. Promote useful repeatable patterns into the workflow controls.

## What It Is Not

This is not a framework tied to a specific vendor, assistant, IDE, or orchestration tool. It is also not a replacement for engineering judgment. It is a file-based operating system that helps a team keep intent, context, evidence, and accountability close to the work.

## Layout

```text
.
├── README.md
└── agentic_engineering/
    ├── AGENTS_template.md
    ├── agentic/
    ├── external_knowledge/
    ├── learnings/
    ├── output/
    ├── program/
    └── team/
```

Use `agentic_engineering/` as the folder to copy, adapt, or drop into another workspace.
