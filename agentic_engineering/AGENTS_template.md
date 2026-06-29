# AGENTS Template

This template defines how the team uses the workspace structure to take an idea from intake to production and then repeat through the next sprint. It supports both human-led work and bounded agentic workflows.

## Folder Structure

| Folder | Purpose |
|---|---|
| `team` | Role definitions and responsibilities for the 12-person responsible minimum team. |
| `agentic` | Agentic operating controls: loop library, permission model, work packet template, cadence controls, skill registry, and eval registry. |
| `program` | Program-level trackers, global program documents, and sprint records. |
| `program/trackers` | Reusable and active trackers for intake, requirements, backlog, delivery, release, risks, decisions, metrics, and reporting. |
| `program/program_documents` | Global planning, program charter, governance, stakeholder context, and other non-sprint program documentation. |
| `program/sprints` | Sprint index and sprint-specific plans, execution notes, demo notes, and retrospectives. |
| `external_knowledge` | Read-only domain knowledge, coding snippets, examples, prior art, and references used to execute the program. |
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

Roles are used as lenses and gates. They may be staffed by humans, supported by agents, or encoded as reusable skills and review prompts. A named accountable human owns approval decisions even when agents perform the execution.

## Agentic Operating Rules

Use agents when they improve throughput without weakening evidence, reviewability, or accountability.

1. **Bound the loop.** Pick a loop from `agentic/loop_library.md` before starting agent work.
2. **Scope permissions.** Classify the task using `agentic/permission_model.md`; require human approval for destructive, external, sensitive, or production-affecting actions.
3. **Limit work in progress.** Apply `agentic/cadence_controls.md` so agents do not outrun human review capacity.
4. **Return a work packet.** Every agent-assisted implementation, review, research, or release task should produce the fields in `agentic/work_packet_template.md`.
5. **Review evidence, not confidence.** Humans should inspect changed files, tests run, skipped checks, assumptions, and residual risks.
6. **Compound learning.** Repeated successful patterns should be promoted into `agentic/skill_registry.md`, `agentic/eval_registry.md`, tests, runbooks, or process updates.

## End-To-End Operating Process

### 1. Capture The Idea

**Primary role:** Product & Delivery Manager  
**Reviewer:** Requirements Analyst

1. Record the idea in `program/trackers/idea_intake_tracker.md`.
2. Define the problem, target users, expected value, urgency, and initial risks.
3. Decide whether the idea is rejected, parked, sent to research, or approved for requirements.

**Deliveries**

- Idea record.
- Initial business value statement.
- Intake decision.

### 2. Consult External Knowledge

**Primary roles:** Requirements Analyst, UX/UI Designer, Solution Architect  
**Support roles:** Security Reviewer, Documentation & Customer Feedback Owner

1. Review existing domain context, prior art, examples, references, and snippets in `external_knowledge`.
2. Cite relevant knowledge in requirements, architecture notes, test notes, or decisions.
3. If new external knowledge is needed, record the need in `program/trackers/dependency_tracker.md` or `program/trackers/raid_log.md`; do not update `external_knowledge` during program execution.

**Deliveries**

- References to relevant existing knowledge.
- Open research needs recorded as dependencies or risks.
- Requirement, design, architecture, or test notes informed by the reference material.

### 3. Convert Idea To Requirements

**Primary role:** Requirements Analyst  
**Reviewers:** Product & Delivery Manager, UX/UI Designer, Solution Architect, QA Engineer, Security Reviewer

1. Write requirements in `program/trackers/requirements_tracker.md`.
2. Define user stories, acceptance criteria, business rules, and edge cases.
3. Confirm security, privacy, accessibility, operational, and testability needs.
4. Move approved work into `program/trackers/backlog_tracker.md`.

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
2. Record important choices in `program/trackers/decision_log.md`.
3. Add technical risks, assumptions, issues, and dependencies to `program/trackers/raid_log.md` and `program/trackers/dependency_tracker.md`.
4. Confirm the implementation can be broken into sprint-sized work.

**Deliveries**

- Architecture notes.
- API and data model specs.
- Technical work breakdown.
- Decisions, risks, and dependencies.

### 6. Plan The Sprint

**Primary role:** Product & Delivery Manager  
**Reviewers:** All sprint roles

1. Refine and prioritize work in `program/trackers/backlog_tracker.md`.
2. Confirm team capacity in `program/trackers/resource_capacity_tracker.md`.
3. Classify work mode: human-led, agent-assisted, or agent-executed with human review.
4. Confirm agentic WIP limits, review capacity, and safe overnight work using `agentic/cadence_controls.md`.
5. Commit sprint work in `program/sprints` using `program/sprints/sprint_record_template.md`.
6. Confirm milestones and release targets in `program/trackers/milestone_release_tracker.md`.

**Deliveries**

- Sprint goal.
- Sprint backlog.
- Capacity view.
- Agentic work mode and cadence plan.
- Milestone and release plan.

### 7. Develop

**Primary roles:** Backend Engineer, Frontend Engineer, Integration Engineer  
**Reviewers:** Solution Architect, Code Quality Reviewer, Security Reviewer, QA Engineer

1. Select the correct implementation loop from `agentic/loop_library.md`.
2. Implement features, fixes, integrations, tests, and supporting documentation in `output/repositories`.
3. Keep source code in a git repository when possible.
4. Link implementation work to backlog items, requirements, decisions, and work packets.
5. Capture context used, files changed, commands run, tests passed or skipped, assumptions, risks, and next actions in a work packet.
6. Capture useful implementation patterns in `learnings` or `output/documentation`.

**Deliveries**

- Source code.
- Tests.
- Integration work.
- Developer documentation.
- Agentic work packet when agents were used.

### 8. Review Code And Security

**Primary roles:** Code Quality Reviewer, Security Reviewer  
**Support roles:** Solution Architect, Engineers

1. Review code for correctness, maintainability, standards, test coverage, and architectural fit.
2. Review the agentic work packet before trusting any summary.
3. Review security-sensitive areas such as authentication, authorization, data handling, secrets, dependencies, and logging.
4. Confirm tool permissions and external side effects were appropriate for the task.
5. Block merge or release when unresolved quality, security, evidence, or permission issues exceed the agreed threshold.

**Deliveries**

- Code review findings.
- Security review findings.
- Agentic evidence review findings.
- Merge approval or required changes.

### 9. Test

**Primary role:** QA / Test Automation Engineer  
**Reviewers:** Product & Delivery Manager, Requirements Analyst

1. Prepare and track testing in `program/trackers/test_readiness_tracker.md`.
2. Run automated, manual, regression, integration, end-to-end, UAT, and security-related tests as needed.
3. Verify acceptance criteria and report defects.
4. Record which checks were run by agents, which were run by humans, and which were skipped.
5. Promote repeated defect patterns into tests or evals.
6. Confirm release quality or recommend no-go.

**Deliveries**

- Test plans.
- Test results.
- Defect reports.
- Eval or regression promotion candidates.
- Release quality assessment.

### 10. Prepare Release

**Primary roles:** DevOps/SRE Engineer, Product & Delivery Manager  
**Reviewers:** QA Engineer, Security Reviewer, Documentation & Customer Feedback Owner

1. Update `program/trackers/release_deployment_checklist.md`.
2. Confirm deployment steps, rollback plan, monitoring, logging, alerts, support readiness, and documentation.
3. Confirm agent-generated or agent-assisted changes have complete work packets and no unresolved high-risk findings.
4. Prepare release notes and user documentation in `output/documentation`.
5. Make the go/no-go decision in `program/trackers/milestone_release_tracker.md`.

**Deliveries**

- Release checklist.
- Deployment plan.
- Rollback plan.
- Documentation and release notes.
- Agentic release evidence.
- Go/no-go decision.

### 11. Deploy To Production

**Primary role:** DevOps/SRE Engineer  
**Approvers:** Product & Delivery Manager, QA Engineer, Security Reviewer

1. Deploy using the approved release process.
2. Store release artifacts in `output/release_packages` when applicable.
3. Run smoke tests and monitor logs, metrics, and alerts.
4. Communicate deployment status through `program/trackers/stakeholder_communication_tracker.md`.

**Deliveries**

- Production deployment.
- Release artifact record.
- Smoke test result.
- Deployment communication.

### 12. Monitor, Support, And Learn

**Primary roles:** DevOps/SRE Engineer, Documentation & Customer Feedback Owner  
**Support roles:** Product & Delivery Manager, QA Engineer, Engineers

1. Monitor production behavior, support tickets, user feedback, defects, and incidents.
2. Record customer themes and known issues in `output/documentation` or `program/trackers/backlog_tracker.md`.
3. Capture discoveries in `learnings/learning_log.md`.
4. Identify whether the discovery should become a test, eval, skill, permission rule, runbook, or process improvement.
5. Create postmortems for incidents using `learnings/incident_postmortem_template.md`.

**Deliveries**

- Monitoring notes.
- Support feedback.
- Learning log entries.
- Skill, eval, test, or process promotion candidates.
- Follow-up backlog items.

### 13. Retrospective And Next Sprint

**Primary role:** Product & Delivery Manager  
**Participants:** Whole team

1. Record improvement actions in `program/trackers/retrospective_action_tracker.md`.
2. Convert repeat issues into backlog items, tests, documentation, automation, skills, evals, permission rules, or standards.
3. Review agentic metrics: accepted output, rework, review burden, token or CI cost, human interruptions, and unresolved risks.
4. Re-prioritize the backlog based on shipped value, open risks, customer feedback, technical debt, and agentic operating load.
5. Start the next sprint at Step 6, or return to Step 1 for new ideas.

**Deliveries**

- Retrospective actions.
- Updated backlog.
- Updated risks and decisions.
- Updated skills, evals, or agentic controls when needed.
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
- Agentic work packets are complete for agent-generated or agent-assisted changes.
- Tool permissions, external actions, and skipped checks are reviewed.
- Product gives final go approval.
