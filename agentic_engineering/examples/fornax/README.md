# Fornax Project-Instance Example

This directory is a small, self-contained fixture showing how an R&D system can
specialize the generic framework without copying the framework around its source
tree.

It demonstrates:

- domain functions for runtime integration, distributed scheduling, numerical
  correctness, networking/security, operations, and evidence custody;
- an explicitly omitted frontend capability;
- active operator-experience coverage without inventing a graphical frontend;
- risk-proportional separation between evidence producer and validator; and
- a G2 physical-distributed-correctness evidence record linked to a bounded work
  item.

The records are illustrative test data, not claims about the live Fornax project.
The authoritative plan for this fixture is `project-plan-v4.md`. Its
`program.yaml` is already tailored and confirmed, and its framework lock pins the
catalog, schemas, runtime, and presets used to validate the records.

## Inspect The Valid Fixture

From the framework repository, install the CLI and its required schema validator
before running the fixture:

```bash
python3 -m pip install -e .
agentic validate agentic_engineering/examples/fornax --strict
agentic route WI-G2-001 --root agentic_engineering/examples/fornax --json
sed -n '1,220p' agentic_engineering/examples/fornax/evidence/EV-G2-001.yaml
```

Expected validation result: zero errors and zero warnings. The route is `high`
risk with `A2` minimum assurance and an `external_write` permission ceiling. The
evidence record names its packet, work item, and acceptance criteria; binds the
observed artifact digest to the packet output; records a distinct validation
run; and separates authorized claims from explicitly forbidden claims. The
external-write action receipt copies the packet ID and exact decision scope and
falls inside the authorization window. Manually confirmed transition guards are
bound to guard-specific evidence or decision receipts.

The work packet producer is the runtime-integration agent. Its verification set
contains an integration-test receipt from numerical correctness, an experiment
ledger from evidence custody, and an isolated technical-lead review; the
accountable human accepts the bounded result. Changing a verification producer
to the implementation agent causes A2 assurance validation to fail.

## Exercise Drift Rejection

The `invalid/` subtree is deliberately invalid and must not be interpreted as a
second project instance. It exists so validation tests can prove that a manifest
declaring plan v3 while pointing at the v4 plan is rejected as stale.

```bash
agentic validate \
  agentic_engineering/examples/fornax/invalid/stale-manifest \
  --json
```

Expected result: a non-zero exit and a `source-version-drift` error stating that
the manifest declares version 3 while the authoritative source declares version
4. The validator must not silently refresh the source pin. A real project would
record an approving decision and use `agentic source-update`.
