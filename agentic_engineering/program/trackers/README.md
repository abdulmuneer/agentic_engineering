# Trackers

This folder stores reusable human-readable tracker templates. In projects using the executable kernel, canonical state lives in `.agentic/records` and tracker/status tables should be generated from those records. Do not maintain the same fact manually in both places.

## Trackers

| File | Purpose |
|---|---|
| `idea_intake_tracker.md` | Captures raw ideas before requirements work begins. |
| `requirements_tracker.md` | Tracks approved requirements, user stories, acceptance criteria, and review state. |
| `backlog_tracker.md` | Tracks product, engineering, defect, research, and technical debt work. |
| `roadmap_tracker.md` | Connects strategy to delivery horizons. |
| `sprint_plan_tracker.md` | Reusable sprint planning template; actual sprint records should be stored under `../sprints`. |
| `raid_log.md` | Tracks risks, assumptions, issues, and dependencies. |
| `dependency_tracker.md` | Tracks internal and external delivery dependencies. |
| `decision_log.md` | Records important product, technical, security, and delivery decisions. |
| `resource_capacity_tracker.md` | Tracks role and person capacity by sprint or planning period. |
| `milestone_release_tracker.md` | Tracks milestones, releases, readiness, and go/no-go status. |
| `status_report_template.md` | Template for regular program status reports. |
| `change_request_tracker.md` | Tracks approved and proposed scope, schedule, risk, and cost changes. |
| `test_readiness_tracker.md` | Tracks QA readiness, test execution, and linked defects. |
| `release_deployment_checklist.md` | Release and deployment readiness checklist. |
| `stakeholder_communication_tracker.md` | Tracks stakeholder communication moments and follow-up. |
| `metrics_kpi_tracker.md` | Tracks product, quality, delivery, reliability, support, and security metrics. |
| `retrospective_action_tracker.md` | Tracks improvement actions from retrospectives, releases, and incidents. |

## Agentic Tracking

When agents are used, trackers should link to:

- The selected loop in `../../agentic/loop_library.md`.
- The permission class in `../../agentic/permission_model.md`.
- The completed work packet from `../../agentic/work_packet_template.md`.
- Any skill or eval promotion candidate in `../../agentic/skill_registry.md` or `../../agentic/eval_registry.md`.
