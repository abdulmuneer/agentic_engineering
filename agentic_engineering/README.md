# Agentic Engineering Operating System

This workspace defines a practical operating model for taking a software idea from initial concept to production deployment using a responsible minimum team structure and bounded agentic workflows.

The goal is to make the work repeatable and reviewable: every idea should move through clear ownership, review gates, delivery planning, implementation, testing, deployment, monitoring, and learning. When agents are used, their work should arrive as bounded work packets with context, evidence, risks, and human approval gates.

## What This Repository Contains

| Folder | Purpose |
|---|---|
| `team` | Defines the 12 core roles needed to run a responsible minimum software organization. |
| `agentic` | Defines agentic loops, work packets, permission classes, cadence controls, skill promotion, and eval tracking. |
| `program` | Contains program-level trackers, global program documents, and sprint records. |
| `external_knowledge` | Read-only reference material such as domain knowledge, coding snippets, examples, prior art, and external references. |
| `output` | Stores the actual work produced by the program, including source repositories, documentation, deliverables, and release packages. |
| `learnings` | Captures discoveries, postmortems, technical lessons, and process improvements during execution. |
| `AGENTS_template.md` | Describes the full step-by-step process for moving an idea through the team and into production. |

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

## Operating Flow

Work should move through this lifecycle:

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

1. Add the idea to `program/trackers/idea_intake_tracker.md`.
2. Consult `external_knowledge` for existing research, examples, domain knowledge, and prior art.
3. Convert the approved idea into requirements in `program/trackers/requirements_tracker.md`.
4. Add delivery work to `program/trackers/backlog_tracker.md`.
5. Plan the sprint in `program/sprints` using `program/sprints/sprint_record_template.md`.
6. Choose the work mode: human-led, agent-assisted, or agent-executed with human review.
7. Build and store work products under `output`.
8. Capture discoveries in `learnings`, and promote repeatable patterns into `agentic`.

## Production Discipline

A production release should not proceed unless requirements, design, architecture, code quality, security, QA, deployment, documentation, and support readiness have been reviewed by the responsible roles.

If agentic work contributed to the release, the release should also have complete work packets, reviewed tool permissions, recorded verification evidence, and no unresolved agent-generated risks above the release threshold.

This repository is not just a folder structure. It is intended to be a working playbook for repeatable software delivery.
