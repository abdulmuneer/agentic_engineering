# Lean Research Example

A research overlay on the revised framework. It passes `agentic validate --strict`
and is part of `make validate`.

| File | Shows |
|---|---|
| `program.yaml` | `research_platform` preset at low baseline risk; actors with tiers (planner, worker, executor), models, turn caps and token budgets; `budgets`; one shared resource (`gpu-cluster`, owned by the planner, "never idle; one run at a time"). |
| `work/RUN-0001.yaml` | A closed lean `run`: no packets or evidence records; `results` with a reference to the results file, tool-emitted receipts (URI and SHA-256), and the claims not established. |
| `decisions/DEC-RESUME-AFTER-CHECKPOINT.yaml` | A standing authorization: resuming a yielded run from its checkpoint is approved for every `run` item, for the named actors and permission class, until it expires. |
| `work/REL-0001.yaml` | A release in its first state. Publication is consequential, so it goes through the gated `release` workflow, not `run`. |
| `generated/` | Disposable views, including `decisions.md`. |

Check-in view:

```text
$ agentic status agentic_engineering/examples/lean-research
REL-0001 release draft tier=high gates=none
RUN-0001 run closed tier=low gates=none
revisit DEC-RESUME-AFTER-CHECKPOINT at=2026-12-01T00:00:00Z
standing DEC-RESUME-AFTER-CHECKPOINT expires=2027-01-01T00:00:00Z applies_to=run
```

Compare with `../fornax`, which shows the gated path with packets, evidence and
reviewer independence.
