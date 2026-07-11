# Project Overlay Template

Copy the contents of this directory into the root of an existing product repository. Keep the product source in its natural locations; `.agentic` is an operating-control overlay, not a wrapper around the source tree.

## Canonical Records

- `.agentic/program.yaml` declares project topology, source-of-truth version, capability coverage, actors, and permission ceilings.
- `.agentic/records/work_items` contains routed, risk-classified units of work.
- `.agentic/records/work_packets` records bounded execution context, output, risk, and verification references.
- `.agentic/records/evidence` contains subject-bound evidence receipts.
- `.agentic/records/decisions` records consequential decisions, including commit, narrow, kill, park, go, and no-go outcomes.
- `.agentic/records/learnings` converts observed patterns into tests, evals, skills, runbooks, policy, or process changes.

YAML is canonical only for enforceable facts such as identifiers, state, links, risk, evidence, and approvals. Keep analysis, design rationale, plans, findings, and postmortems in Markdown and link them from records.

The sample records are deliberately complete and schema-valid placeholders. Replace their values, retain `schema_version: 1` and `framework_version: 0.1.0`, and validate them against `schemas/v1`.

`DISC-0001.yaml` demonstrates the canonical discovery branch. It keeps the problem, target actor, hypothesis, falsification rule, experiment, and eventual `commit`, `narrow`, `kill`, or `park` decision together as one traceable product-discovery record.

Do not maintain a second handwritten status table. Derive status and generated `AGENTS.md` guidance from the program record and transition histories so declared plans cannot drift from the canonical source.
