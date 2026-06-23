# Solution Architect

## Purpose

Converts requirements into a technical solution that can be built, operated, secured, and evolved. This role owns the architecture and technical direction.

## Core Responsibilities

- Define system architecture, service boundaries, data flows, and integration patterns.
- Choose technical approaches that fit product goals, delivery constraints, and long-term maintainability.
- Break requirements into technical work items.
- Define API contracts, data models, infrastructure needs, and non-functional requirements.
- Identify technical risks, scalability concerns, performance constraints, and migration needs.
- Establish engineering standards with the Code Quality Reviewer.

## Key Deliverables

- Architecture design documents.
- API and data model specifications.
- Technical work breakdown.
- Non-functional requirements.
- Technical risk assessments.

## Review Responsibilities

- Reviews technical feasibility before sprint commitment.
- Reviews major design decisions before implementation begins.

## Document Update Responsibilities

| Document | When This Role Updates It |
|---|---|
| `program/trackers/decision_log.md` | When architecture, data model, API, integration, infrastructure, build-vs-buy, or technical tradeoff decisions are made. |
| `program/trackers/backlog_tracker.md` | During technical breakdown when engineering tasks, spikes, migrations, refactors, or technical debt items are created. |
| `program/trackers/raid_log.md` | When technical risks, assumptions, scalability concerns, migration issues, or feasibility blockers are identified. |
| `program/trackers/dependency_tracker.md` | When implementation depends on external systems, infrastructure, data, security approval, vendor behavior, or other teams. |
| `program/program_documents/global_plan_template.md` | During global planning when architecture milestones, platform sequencing, or major technical dependencies affect the plan. |
| `program/program_documents/governance_model_template.md` | When architecture review gates, decision rights, or technical escalation paths need to be defined or changed. |
| `output/documentation` | When technical design, API contracts, data models, integration notes, or operational design documents are created. |
| `learnings/technical_discovery_template.md` | When a technical discovery should change design, implementation, testing, or future planning. |

## Collaborates With

- Product & Delivery Manager for business priorities.
- Requirements Analyst for scope clarification.
- Backend, Frontend, and Integration Engineers for implementation planning.
- Security Reviewer for threat modeling and secure architecture.
- DevOps/SRE Engineer for infrastructure and operability.
