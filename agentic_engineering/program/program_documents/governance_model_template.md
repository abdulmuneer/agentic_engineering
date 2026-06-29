# Governance Model Template

## Decision Rights

| Decision Area | Primary Owner | Required Reviewers | Escalation Path |
|---|---|---|---|
| Product priority | Product & Delivery Manager | Requirements Analyst |  |
| Architecture | Solution Architect | Code Quality Reviewer, Security Reviewer, DevOps/SRE |  |
| Security | Security Reviewer | Solution Architect, DevOps/SRE |  |
| Release go/no-go | Product & Delivery Manager | QA, Security, DevOps/SRE |  |
| Agent tool permissions | Accountable Human | Security Reviewer, DevOps/SRE, relevant role lens |  |
| Agentic skill promotion | Skill Owner | Code Quality Reviewer, QA, Security where relevant |  |
| Agentic eval promotion | QA / Test Automation Engineer | Requirements Analyst, Code Quality Reviewer, Security where relevant |  |

## Review Cadence

| Review | Cadence | Participants | Output |
|---|---|---|---|
| Roadmap review |  |  |  |
| Requirements review |  |  |  |
| Architecture review |  |  |  |
| Release readiness |  |  |  |
| Retrospective |  |  |  |
| Agentic work packet review | Per review window | Accountable Human, required role lenses | Accepted / rejected / needs rework |
| Skill and eval registry review | Monthly / Release | Skill owners, QA, Security, Product | Active / deprecated / needs update |

## Escalation Rules

- Stop agent work and escalate when the task changes permission class.
- Escalate to Security for secrets, customer data, authentication, authorization, payments, compliance, or abuse-risk concerns.
- Escalate to DevOps/SRE for production, infrastructure, deployment, rollback, DNS, monitoring, or cloud-cost concerns.
- Escalate to Product when agent findings change scope, user impact, priority, or release commitments.

## Approval Gates

- Agentic work packet complete before merge or release.
- Human approval recorded before external write, sensitive, or production actions.
- Verification evidence reviewed before accepting agent-generated changes.
- Skipped checks explicitly accepted by the accountable human.
- New reusable skills or evals assigned an owner and review date before activation.
