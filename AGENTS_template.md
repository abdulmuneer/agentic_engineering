# AGENTS Template

This template defines how the team uses the workspace structure to take an idea from intake to production and then repeat through the next sprint.

## Folder Structure

| Folder | Purpose |
|---|---|
| `team` | Role definitions and responsibilities for the 12-person responsible minimum team. |
| `program` | Program-management trackers for intake, planning, execution, release, status, decisions, risks, and retrospectives. |
| `external_knowledge` | Domain knowledge, coding snippets, examples, prior art, and references used to execute the program. |
| `output` | Produced work, including source repositories, documentation, deliverables, and release packages. |
| `learnings` | Lessons, discoveries, postmortems, and process improvements captured during execution. |

## Team Roles

| Role File | Role |
|---|---|
| `team/product_delivery_manager.md` | Product & Delivery Manager |
| `team/requirements_analyst.md` | Requirements Analyst |
| `team/ux_ui_designer.md` | UX/UI Designer |
| `team/solution_architect.md` | Solution Architect |
| `team/backend_engineer.md` | Backend Engineer |
| `team/frontend_engineer.md` | Frontend Engineer |
| `team/integration_engineer.md` | Integration Engineer |
| `team/code_quality_reviewer.md` | Code Quality Reviewer |
| `team/qa_test_automation_engineer.md` | QA / Test Automation Engineer |
| `team/security_reviewer.md` | Security Reviewer |
| `team/devops_sre_release_engineer.md` | DevOps / SRE / Release Engineer |
| `team/documentation_customer_feedback_owner.md` | Documentation & Customer Feedback Owner |

## End-To-End Operating Process

### 1. Capture The Idea

**Primary role:** Product & Delivery Manager  
**Reviewer:** Requirements Analyst

1. Record the idea in `program/idea_intake_tracker.md`.
2. Define the problem, target users, expected value, urgency, and initial risks.
3. Decide whether the idea is rejected, parked, sent to research, or approved for requirements.

**Deliveries**

- Idea record.
- Initial business value statement.
- Intake decision.

### 2. Gather External Knowledge

**Primary roles:** Requirements Analyst, UX/UI Designer, Solution Architect  
**Support roles:** Security Reviewer, Documentation & Customer Feedback Owner

1. Add domain context, prior art, examples, references, and snippets to `external_knowledge`.
2. Record each useful source in `external_knowledge/knowledge_index.md`.
3. Link relevant knowledge to requirements, architecture, tests, or decisions.

**Deliveries**

- Knowledge index entries.
- Domain notes.
- Prior-art summaries.
- Technical references or snippets.

### 3. Convert Idea To Requirements

**Primary role:** Requirements Analyst  
**Reviewers:** Product & Delivery Manager, UX/UI Designer, Solution Architect, QA Engineer, Security Reviewer

1. Write requirements in `program/requirements_tracker.md`.
2. Define user stories, acceptance criteria, business rules, and edge cases.
3. Confirm security, privacy, accessibility, operational, and testability needs.
4. Move approved work into `program/backlog_tracker.md`.

**Deliveries**

- Requirements.
- Acceptance criteria.
- Backlog items.
- Linked risks, assumptions, and dependencies.

### 4. Design The User Experience

**Primary role:** UX/UI Designer  
**Reviewers:** Product & Delivery Manager, Requirements Analyst, Frontend Engineer, QA Engineer

1. Create user flows, screen flows, wireframes, or prototypes.
2. Confirm usability, accessibility, error states, empty states, and interaction behavior.
3. Feed implementation requirements into the backlog.

**Deliveries**

- User flows.
- UI designs.
- Interaction notes.
- Usability review findings.

### 5. Design The Technical Solution

**Primary role:** Solution Architect  
**Reviewers:** Security Reviewer, DevOps/SRE Engineer, Code Quality Reviewer, Engineering team

1. Define architecture, data model, APIs, integrations, infrastructure needs, and non-functional requirements.
2. Record important choices in `program/decision_log.md`.
3. Add technical risks, assumptions, issues, and dependencies to `program/raid_log.md` and `program/dependency_tracker.md`.
4. Confirm the implementation can be broken into sprint-sized work.

**Deliveries**

- Architecture notes.
- API and data model specs.
- Technical work breakdown.
- Decisions, risks, and dependencies.

### 6. Plan The Sprint

**Primary role:** Product & Delivery Manager  
**Reviewers:** All sprint roles

1. Refine and prioritize work in `program/backlog_tracker.md`.
2. Confirm team capacity in `program/resource_capacity_tracker.md`.
3. Commit sprint work in `program/sprint_plan_tracker.md`.
4. Confirm milestones and release targets in `program/milestone_release_tracker.md`.

**Deliveries**

- Sprint goal.
- Sprint backlog.
- Capacity view.
- Milestone and release plan.

### 7. Develop

**Primary roles:** Backend Engineer, Frontend Engineer, Integration Engineer  
**Reviewers:** Solution Architect, Code Quality Reviewer, Security Reviewer, QA Engineer

1. Implement features, fixes, integrations, tests, and supporting documentation in `output/repositories`.
2. Keep source code in a git repository when possible.
3. Link implementation work to backlog items, requirements, and decisions.
4. Capture useful implementation patterns in `external_knowledge/coding_snippets` or `learnings`.

**Deliveries**

- Source code.
- Tests.
- Integration work.
- Developer documentation.

### 8. Review Code And Security

**Primary roles:** Code Quality Reviewer, Security Reviewer  
**Support roles:** Solution Architect, Engineers

1. Review code for correctness, maintainability, standards, test coverage, and architectural fit.
2. Review security-sensitive areas such as authentication, authorization, data handling, secrets, dependencies, and logging.
3. Block merge or release when unresolved quality or security issues exceed the agreed threshold.

**Deliveries**

- Code review findings.
- Security review findings.
- Merge approval or required changes.

### 9. Test

**Primary role:** QA / Test Automation Engineer  
**Reviewers:** Product & Delivery Manager, Requirements Analyst

1. Prepare and track testing in `program/test_readiness_tracker.md`.
2. Run automated, manual, regression, integration, end-to-end, UAT, and security-related tests as needed.
3. Verify acceptance criteria and report defects.
4. Confirm release quality or recommend no-go.

**Deliveries**

- Test plans.
- Test results.
- Defect reports.
- Release quality assessment.

### 10. Prepare Release

**Primary roles:** DevOps/SRE Engineer, Product & Delivery Manager  
**Reviewers:** QA Engineer, Security Reviewer, Documentation & Customer Feedback Owner

1. Update `program/release_deployment_checklist.md`.
2. Confirm deployment steps, rollback plan, monitoring, logging, alerts, support readiness, and documentation.
3. Prepare release notes and user documentation in `output/documentation`.
4. Make the go/no-go decision in `program/milestone_release_tracker.md`.

**Deliveries**

- Release checklist.
- Deployment plan.
- Rollback plan.
- Documentation and release notes.
- Go/no-go decision.

### 11. Deploy To Production

**Primary role:** DevOps/SRE Engineer  
**Approvers:** Product & Delivery Manager, QA Engineer, Security Reviewer

1. Deploy using the approved release process.
2. Store release artifacts in `output/release_packages` when applicable.
3. Run smoke tests and monitor logs, metrics, and alerts.
4. Communicate deployment status through `program/stakeholder_communication_tracker.md`.

**Deliveries**

- Production deployment.
- Release artifact record.
- Smoke test result.
- Deployment communication.

### 12. Monitor, Support, And Learn

**Primary roles:** DevOps/SRE Engineer, Documentation & Customer Feedback Owner  
**Support roles:** Product & Delivery Manager, QA Engineer, Engineers

1. Monitor production behavior, support tickets, user feedback, defects, and incidents.
2. Record customer themes and known issues in `output/documentation` or `program/backlog_tracker.md`.
3. Capture discoveries in `learnings/learning_log.md`.
4. Create postmortems for incidents using `learnings/incident_postmortem_template.md`.

**Deliveries**

- Monitoring notes.
- Support feedback.
- Learning log entries.
- Follow-up backlog items.

### 13. Retrospective And Next Sprint

**Primary role:** Product & Delivery Manager  
**Participants:** Whole team

1. Record improvement actions in `program/retrospective_action_tracker.md`.
2. Convert repeat issues into backlog items, tests, documentation, automation, or standards.
3. Re-prioritize the backlog based on shipped value, open risks, customer feedback, and technical debt.
4. Start the next sprint at Step 6, or return to Step 1 for new ideas.

**Deliveries**

- Retrospective actions.
- Updated backlog.
- Updated risks and decisions.
- Next sprint plan.

## Production Gate Summary

A release should not proceed unless these are complete:

- Requirements accepted by Product and Requirements.
- UX reviewed where user experience is affected.
- Architecture reviewed for significant technical changes.
- Code reviewed by the Code Quality Reviewer.
- Security reviewed for sensitive or risky changes.
- QA confirms acceptance criteria and regression status.
- DevOps/SRE confirms deployment, rollback, monitoring, and support readiness.
- Documentation and release notes are ready.
- Product gives final go approval.

