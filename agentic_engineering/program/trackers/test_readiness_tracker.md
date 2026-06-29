# Test Readiness Tracker

Use this tracker to confirm that work is ready for QA and release validation.

| Test Item ID | Linked Backlog / Requirement | Test Type | Owner | Environment | Entry Criteria | Exit Criteria | Agent / Human Runner | Evidence | Status | Defects Linked |
|---|---|---|---|---|---|---|---|---|---|---|
| TEST-001 | BL-001 / REQ-001 | Unit / Integration / E2E / Manual / Regression / UAT / Security / Agent Workflow Eval |  | Dev / Test / Staging |  |  | Human / Agent / CI | Command, log, screenshot, packet, or review notes | Not Ready / Ready / Running / Passed / Failed |  |

## QA Entry Checklist

- Implementation is complete enough to test.
- Acceptance criteria are available.
- Test data is available.
- Environment is stable.
- Known limitations are documented.
- Agent-run checks identify the agent, command, and work packet.
- Skipped checks have an owner-approved reason.
- Repeated defects are considered for regression tests or eval promotion.
