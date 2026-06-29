# Eval Registry

Use this registry to track tests, evals, and review checks that verify product behavior and agentic workflows.

## Eval Types

| Type | Purpose |
|---|---|
| Unit / Integration / E2E | Deterministic product behavior. |
| Regression | Prevent recurrence of known defects. |
| Security / Abuse case | Validate controls and misuse resistance. |
| Agent workflow eval | Check whether an agent follows instructions, permissions, and output format. |
| Human review checklist | Ensure judgment-heavy work is inspected consistently. |

## Eval Registry

| Eval ID | Name | Type | Linked Requirement / Risk / Skill | Command Or Method | Owner | Status | Review Cadence |
|---|---|---|---|---|---|---|---|
| EVAL-001 |  | Unit / Integration / E2E / Regression / Security / Agent Workflow / Review Checklist |  |  |  | Proposed / Active / Deprecated | Sprint / Release / Monthly |

## Promotion Rules

- A production defect should become a regression test or documented reason why it cannot.
- A repeated agent failure should become an agent workflow eval or permission rule.
- A repeated review finding should become a checklist, static check, test, or skill update.
