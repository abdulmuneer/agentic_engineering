# Agentic Permission Model

Gate on consequence, not on activity. Local, reversible work proceeds without approval. A step
needs a human decision only when it is consequential and no standing authorization covers it.

## Consequential steps

Declare them per project in tailoring. Typical ones:

- spending shared compute or money above the run's budget;
- publishing a model, dataset, package, claim or document outside the workspace;
- promoting a result to a default, a release or a registry;
- using data whose rights, licence or consent are unresolved;
- destructive file, git, database or infrastructure operations;
- production changes, credentials and sensitive data.

Everything else (reading, local edits, local experiments, drafts, analysis, smoke tests on
reserved local hardware) is the agent's to do within its tier and budget.

## Permission Classes

| Class | Description | Human Approval |
|---|---|---|
| Read-only | Read local files, docs, logs, or public references. | Not required. |
| Local write | Edit files inside the workspace, create docs, update tests, run local jobs. | Not required; reviewed through results when it matters. |
| External read | Query web, issue trackers, package registries, cloud metadata, or APIs. | Only when credentials, private data, cost, or rate limits are involved. |
| External write | Create or update issues, PRs, tickets, comments, packages, deployments, or vendor resources. | A decision or a standing authorization that covers it. |
| Sensitive | Secrets, personal data, customer data, security controls, auth, payment, legal, or compliance material. | A decision before access and before action. |
| Production | Production data, infrastructure, deploys, rollbacks, DNS, billing, customer-visible behavior, or monitoring. | A decision before action and release approval. |

## Standing authorizations

Approving the same kind of step item by item is what stalls a program. A standing
authorization is a decision that covers a repeated consequential step:

- **scope** in plain words (for example "resume a yielded training run from its last
  checkpoint on the reserved nodes");
- **permission classes** and **actors** it covers;
- **applies to**: work item ids, workflow ids, or `*`;
- **expiry**: after it, the step needs a fresh decision.

Record it with `agentic new-decision` and `authorization.standing: true`. The runtime accepts it
for any matching work item until it expires. `agentic status` lists standing authorizations
with their expiry. Widen them when a tier has a good record on that step; narrow them after a
failure.

## Default Rules

- Use the least powerful tool that can complete the task.
- Prefer structured tools over broad shell or API access.
- Do not expose secrets in prompts, logs, work packets, or documentation.
- Record consequential actions by receipt: what was done, by whom, under which decision.
- Stop and ask when the task changes permission class and nothing covers the new class.

## Mandatory Stop Conditions

An agent must stop when:

- It needs a consequential step that no decision or standing authorization covers.
- It needs credentials or private data not already authorized.
- It discovers a security, privacy, legal, licence or compliance concern.
- It changes scope from the approved goal.
- It repeatedly fails the same command or check.

An agent does not stop because a local, reversible step lacks a record.

## Approval Record

Decisions live in `.agentic/records/decisions/`. `agentic render` writes `decisions.md` with every decision, its owner, standing flag, scope, expiry, and the work items that cite it, open and expiring ones first.
