# Agentic Loop Library

Use this library to choose the right bounded loop before starting agent work.

This document explains the loops. The machine-readable state transitions and guards live in `../catalog/workflows`; an initialized project's routed work item selects the applicable workflow.

## Loop Rules

- Every loop has an accountable human and a stop condition.
- Low- and medium-risk research and engineering use the lean run loop. The gated loops below
  are for high- and critical-risk work, releases and incidents.
- Lean runs return a results file; gated loops and executor tickets return a work packet.
- Consequential steps need a decision or a standing authorization, in any loop.
- Repeated successful loops should be promoted into skills.

## Run Loop (lean, `run` workflow)

Use for research questions, experiments, benchmark reads, data jobs and bounded engineering
whose routed risk is low or medium. The runtime rejects high- or critical-risk work in this
workflow.

The ledger is three files in the run's folder:

- `README.md`: why the run exists, the recipe, pinned inputs, the bar fixed before the read,
  the consequential steps and the decisions that cover them, the budget;
- `status.md`: four header lines (Owner, Updated, Next, Blocker), then dated entries of at most
  three lines;
- `results.md`: numbers, identities, receipts (URI and checksum), and the claims not
  established.

States: `draft` -> `running` -> `closed`, or `stopped` with partial findings. A negative result
closes a run.

Evidence required:

- Receipts emitted by tools, referenced from `results.md` and the work item's `results`.
- Independent evidence where being wrong would cost something: a gold set, a readback, or a
  bar fixed before the read that covers every claim the result makes.
- The claims not established.

Stop conditions:

- A consequential step that no decision or standing authorization covers.
- The budget is about to be exceeded.
- The same failure repeats.
- The result contradicts the pre-registered expectation and the next step depends on it.

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

## Incident Loop

Use when a service, security, data, safety, or operational event requires containment and recovery.

Allowed outputs:

- Impact and incident record.
- Containment or mitigation receipts.
- Recovery verification.
- Stakeholder communication.
- Postmortem and corrective actions.

Evidence required:

- Current impact and incident authority.
- Actions taken, actor, time, and affected subject.
- Recovery and monitoring evidence.
- Residual risk and follow-up ownership.

Stop conditions:

- Emergency authority is unclear.
- The proposed action expands blast radius or permission class without approval.
- Recovery cannot be verified.
- A security, privacy, legal, or safety escalation requires a specialist human.

## Learning Promotion Loop

Use after repeated issues, successful workflows, incidents, reviews, or retrospectives.

Allowed outputs:

- Skill candidate.
- Eval candidate.
- Test candidate.
- Runbook update.
- Process improvement.
- Hook or check that enforces a rule outside the agent's loop.
- Retirement of a rule, memory entry or document section that no longer earns its context.

Evidence required:

- Repeated pattern or high-impact event.
- Expected future benefit.
- Owner and review date.

Stop conditions:

- The learning is speculative and not grounded in evidence.
- The asset would duplicate existing guidance.

Retire as well as promote. Every agent re-reads shared guidance on every call, so a rule that
is superseded, stale or never triggered is a standing cost. When a new rule supersedes an old
one, replace it rather than stacking both.
