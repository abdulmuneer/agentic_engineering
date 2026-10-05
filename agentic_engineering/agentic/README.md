# Agentic Operating Controls

The prose here explains the controls. Their executable definitions live in `../catalog`, their schemas in `../schemas/v1`, and project-specific state in an initialized product's `.agentic/` overlay.

Use these files when humans delegate work to agents, run subagents or worker models, or convert repeated work into reusable skills and evals.

## Files

| File | Purpose |
|---|---|
| `lessons_from_practice.md` | What happened when the first version ran a real research program, and why the controls changed. Read first. |
| `agent_tiers.md` | Planner, worker and executor tiers: what each decides, receives and is held to. |
| `loop_library.md` | The lean run loop and the gated loops for discovery, requirements, implementation, review, testing, release, incidents and learning. |
| `permission_model.md` | Consequence-based gating, standing authorizations and stop conditions. |
| `cadence_controls.md` | Attention, token, context and coordination budgets, capacity, and checkpoints. |
| `work_packet_template.md` | The packet for gated work and executor tickets; lean runs use the run ledger instead. |
| `skill_registry.md` | Registry for reusable skills and prompts promoted from repeated work. |
| `eval_registry.md` | Registry for tests and evals that verify agentic workflows and product behavior. |

## Operating Principle

Judgment is delegated; consequences are verified. Humans own goals, priority, promotion, risk acceptance and anything outward-facing that no standing authorization covers. Agents decide the rest within written rules, at the level their tier allows.

The default path is:

1. Say why the work exists and which steps are consequential.
2. Give it to the cheapest tier that can do it, with a budget.
3. Let it run; stop only at consequential steps without a standing authorization.
4. Verify the result with independent evidence where being wrong would cost something.
5. Close with a results file: numbers, receipts, and the claims not established.
6. Promote useful learning into skills, tests or rules, and retire guidance that no longer earns its context.
