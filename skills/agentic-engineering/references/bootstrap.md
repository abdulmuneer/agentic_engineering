# Bootstrap A Product

## Preconditions

- Require an existing product repository and a source-of-truth document inside
  it. Prefer a versioned product or technical plan; accept `README.md` for an
  initial experiment.
- Name a real accountable human. Do not assign accountability to an agent.
- Inspect existing root guidance before initialization. Never use `--force`
  merely to simplify setup.

## Select the closest preset

| Preset | Start here when |
|---|---|
| `web_product` | The product has a browser or graphical user-facing surface. |
| `cli_tool` | The main product surface is a command-line or operator workflow. |
| `research_platform` | The product centers on experiments, scientific claims, or reproducibility. |
| `regulated_service` | Regulated data, compliance, or controlled production operation is central. |

Choose the closest preset and tailor it. Do not create a new preset for a
one-off variation; promote a reusable preset only after repeated use.

## Initialize

From an environment with the framework installed:

```bash
agentic init \
  --preset <preset> \
  --source <relative-source-path> \
  <product-root>
```

Initialization must leave `tailoring.status: pending`.

## Tailor the operating model

Edit `<product-root>/.agentic/program.yaml` and verify:

1. `profile` reflects lifecycle phase, surfaces, deployment targets, data
   classes, and risk domains.
2. Every capability is `active`, `not_applicable`, or `waived`.
3. Every active capability has a human owner and appropriate executors/reviewers.
4. Every omission has a rationale and reconsideration trigger.
5. Every waiver has a human-owned decision, expiry, and compensating controls.
6. Every actor declares its kind, capabilities, and least-privilege ceiling.
7. Domain-specific actors provide catalog capabilities rather than bypassing
   them with job-title prose.

Persist answers as a list and copy each question exactly:

```yaml
tailoring:
  questions:
    - Which environments are required for reproducibility?
  answers:
    - question: Which environments are required for reproducibility?
      answer: CI uses the pinned CPU and GPU environments with three fixed seeds.
```

Never infer missing answers. Ask the user.

## Confirm and validate

After explicit accountable-human approval:

```bash
agentic tailor <product-root> --actor <accountable-human-id> --confirm
agentic render <product-root>
agentic validate <product-root> --strict
```

Bootstrap is complete only when strict validation has zero errors and warnings,
the generated operating model matches canonical state, and the first bounded
discovery or delivery item is identified.
