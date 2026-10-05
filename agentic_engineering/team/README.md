# Default Role Lenses

These files describe reusable role lenses, not mandatory headcount or persistent agent identities. Their YAML front matter is machine-readable: each role provides one or more capability IDs from `../catalog/capabilities.yaml`, declares activation triggers, states when independent review is required, and sets a permission ceiling.

Projects select capabilities first and then assign humans, agents, automation, or specialist reviewers in `.agentic/program.yaml`. Domain-specific roles may be added by the product without changing this default pool.

Examples:

- A CLI project may mark `frontend_delivery` not applicable while keeping `experience_design` for operator workflows.
- A research runtime may replace generic backend execution with domain roles while still providing `backend_delivery`, `integration_delivery`, `verification`, and `research_assurance`.
- A production authentication change activates `security_privacy`, high-risk assurance, and human acceptance regardless of team size.

Role lenses are separate from agent tiers (`../agentic/agent_tiers.md`). A lens says which perspective a review needs; a tier says how much judgment an agent is trusted with. A planner-tier agent may carry several lenses on lean work. Gated delivery work still uses the lenses as review gates, with independent evidence or a separate reviewer as the routed assurance level requires.
