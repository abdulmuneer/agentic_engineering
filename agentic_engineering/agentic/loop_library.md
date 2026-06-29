# Agentic Loop Library

Use this library to choose the right bounded loop before starting agent work.

## Loop Rules

- Every loop has an accountable human.
- Every loop has a stop condition.
- Every loop returns a work packet.
- High-risk loops require permission review before execution.
- Repeated successful loops should be promoted into skills.

## Discovery Loop

Use when the goal is to understand a domain, codebase area, incident, user problem, or possible approach.

Inputs:

- Question or problem statement.
- Relevant files, docs, logs, tickets, or source boundaries.

Allowed outputs:

- Findings.
- Options.
- Risks.
- Recommended next step.

Evidence required:

- Sources inspected.
- Confidence level.
- Unknowns.

Stop conditions:

- The agent needs external access not approved.
- Findings conflict with current source or requirements.
- The question becomes a product or governance decision.

## Requirements Loop

Use when turning an idea into testable requirements.

Inputs:

- Idea record.
- User or system actor.
- Business value.
- Constraints.

Allowed outputs:

- User stories.
- Acceptance criteria.
- Edge cases.
- Dependency and risk notes.

Evidence required:

- Traceability to source idea.
- Observable acceptance criteria.
- Security, privacy, accessibility, and operational considerations.

Stop conditions:

- Business value is unclear.
- Acceptance evidence cannot be defined.
- Scope becomes too large for sprint planning.

## Design And Architecture Loop

Use when exploring UX, system design, integration, data model, or non-functional requirements.

Allowed outputs:

- Alternatives.
- Tradeoffs.
- Architecture notes.
- UX flow notes.
- Decision-log candidates.

Evidence required:

- Constraints considered.
- Options rejected.
- Risk and dependency list.

Stop conditions:

- New infrastructure, data migration, or security-sensitive decisions appear.
- The design changes approved scope.

## Implementation Loop

Use when making bounded code, documentation, configuration, or test changes.

Allowed outputs:

- Diffs.
- Tests.
- Documentation updates.
- Work packet.

Evidence required:

- Files changed.
- Commands run.
- Tests passed or failed.
- Skipped checks.
- Residual risks.

Stop conditions:

- The diff touches unrelated areas.
- The agent cannot reproduce the target failure.
- The agent needs destructive or external write access.
- The same failure repeats.

## Review Loop

Use when reviewing code, security, UX, architecture, documentation, or release readiness.

Allowed outputs:

- Findings ordered by severity.
- Required changes.
- Approval or rejection recommendation.

Evidence required:

- Files or artifacts inspected.
- Risk rationale.
- Missing tests or evidence.

Stop conditions:

- The reviewer lacks required context.
- Findings require product, security, or release owner decision.

## Test And Eval Loop

Use when adding or running tests, creating evals, hardening regression coverage, or validating acceptance criteria.

Allowed outputs:

- Test plan.
- Automated tests.
- Manual verification steps.
- Eval cases.
- Defect reports.

Evidence required:

- Requirement or risk being tested.
- Test command or method.
- Expected and actual result.

Stop conditions:

- Environment is unstable.
- Test data is missing.
- The agent changes production code when only tests were authorized.

## Release Readiness Loop

Use before deployment or release packaging.

Allowed outputs:

- Release checklist update.
- Rollback notes.
- Monitoring notes.
- Documentation and support readiness notes.

Evidence required:

- CI status.
- Regression status.
- Security status.
- Rollback plan.
- Work packets for agent-assisted changes.

Stop conditions:

- High-risk work packet is incomplete.
- Rollback is unclear.
- Monitoring or support readiness is missing.

## Learning Promotion Loop

Use after repeated issues, successful workflows, incidents, reviews, or retrospectives.

Allowed outputs:

- Skill candidate.
- Eval candidate.
- Test candidate.
- Runbook update.
- Process improvement.

Evidence required:

- Repeated pattern or high-impact event.
- Expected future benefit.
- Owner and review date.

Stop conditions:

- The learning is speculative and not grounded in evidence.
- The asset would duplicate existing guidance.
