# Agentic Permission Model

Use this model before allowing an agent to use tools, edit files, access external systems, or affect production.

## Permission Classes

| Class | Description | Human Approval |
|---|---|---|
| Read-only | Read local files, docs, logs, or public references. | Usually not required after task approval. |
| Local write | Edit files inside the workspace, create docs, update tests. | Required through work packet review before merge. |
| External read | Query web, issue trackers, package registries, cloud metadata, or APIs. | Required when credentials, private data, cost, or rate limits are involved. |
| External write | Create or update issues, PRs, tickets, comments, packages, deployments, or vendor resources. | Required before action. |
| Sensitive | Access secrets, personal data, customer data, security controls, auth, payment, legal, or compliance material. | Required before access and before action. |
| Production | Affect production data, infrastructure, deploys, rollbacks, DNS, billing, customer-visible behavior, or monitoring. | Required before action and release approval. |

## Default Rules

- Use the least powerful tool that can complete the task.
- Prefer read-only discovery before write actions.
- Prefer structured tools over broad shell or API access.
- Do not expose secrets in prompts, logs, work packets, or documentation.
- Record external writes and production-affecting actions in the work packet.
- Stop and ask when the task changes permission class.

## Mandatory Stop Conditions

An agent must stop when:

- It needs destructive file, git, database, infrastructure, or production operations not already approved.
- It needs credentials or private data not already authorized.
- It discovers a security, privacy, legal, or compliance concern.
- It cannot verify its output.
- It changes scope from the approved goal.
- It repeatedly fails the same command or check.

## Approval Record

| Approval ID | Linked Item | Permission Class | Approved Action | Approver | Date | Notes |
|---|---|---|---|---|---|---|
| APPR-001 |  |  |  |  | YYYY-MM-DD |  |
