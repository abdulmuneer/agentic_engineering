# Agentic Operating Controls

This folder turns the package from a classical delivery scaffold into an agentic operating system.

Use these files when humans delegate work to agents, use MCP tools, run subagents, or convert repeated work into reusable skills and evals.

## Files

| File | Purpose |
|---|---|
| `loop_library.md` | Defines bounded loops for discovery, requirements, implementation, review, testing, release, and learning. |
| `work_packet_template.md` | Standard evidence packet returned by agent-assisted work. |
| `permission_model.md` | Tool and action risk classes, approval rules, and stop conditions. |
| `cadence_controls.md` | WIP limits, review windows, checkpoints, and safe overnight classifications. |
| `skill_registry.md` | Registry for reusable skills and prompts promoted from repeated work. |
| `eval_registry.md` | Registry for tests and evals that verify agentic workflows and product behavior. |

## Operating Principle

Agents may execute work, but humans own goals, permissions, review, and release approval.

The default path is:

1. Choose a loop.
2. Scope permissions.
3. Run bounded work.
4. Return a work packet.
5. Review evidence.
6. Promote useful learning into skills, tests, evals, or process changes.
