# External Knowledge Folder

This folder stores outside knowledge that helps the team execute the program and development work.

Treat this folder as read-only during program execution. Team roles may consult and cite material here, but they should not edit documents in this folder.

## Suggested Structure

| Folder | Purpose |
|---|---|
| `domain_knowledge` | Business, industry, regulatory, user, and workflow context. |
| `coding_snippets` | Reusable implementation examples, commands, scripts, and patterns. |
| `examples` | Sample inputs, outputs, payloads, screenshots, demos, or workflows. |
| `prior_art` | Competitor notes, previous internal attempts, reference products, and known approaches. |
| `references` | Links, papers, standards, vendor docs, and API references. |

## Rules

- Do not update documents in this folder as part of sprint or program execution.
- If new knowledge is needed, record the need in `../program/trackers/dependency_tracker.md` or `../program/trackers/raid_log.md`.
- If a discovery is made during execution, capture it in `../learnings`, `../output/documentation`, or the relevant program tracker.
- Do not store secrets, credentials, private customer data, or license-restricted material here.
