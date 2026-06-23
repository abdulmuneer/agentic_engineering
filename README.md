# Agentic Engineering Operating System

This workspace defines a practical operating model for taking a software idea from initial concept to production deployment using a responsible minimum team structure.

The goal is to make the work repeatable: every idea should move through clear ownership, review gates, delivery planning, implementation, testing, deployment, monitoring, and learning.

## What This Repository Contains

| Folder | Purpose |
|---|---|
| `team` | Defines the 12 core roles needed to run a responsible minimum software organization. |
| `program` | Contains program-management templates and trackers for planning, execution, releases, risks, decisions, and reporting. |
| `external_knowledge` | Stores domain knowledge, coding snippets, examples, prior art, and external references that help the team execute well. |
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

1. Add the idea to `program/idea_intake_tracker.md`.
2. Add supporting context to `external_knowledge` if research, examples, or domain knowledge are needed.
3. Convert the approved idea into requirements in `program/requirements_tracker.md`.
4. Add delivery work to `program/backlog_tracker.md`.
5. Plan the sprint in `program/sprint_plan_tracker.md`.
6. Build and store work products under `output`.
7. Capture discoveries in `learnings`.

## Production Discipline

A production release should not proceed unless requirements, design, architecture, code quality, security, QA, deployment, documentation, and support readiness have been reviewed by the responsible roles.

This repository is not just a folder structure. It is intended to be a working playbook for repeatable software delivery.

