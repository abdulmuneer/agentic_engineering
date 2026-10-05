# Agent Tiers

Match control to the capability of the agent doing the work. One level of control for every
agent either wastes a capable agent or trusts a weak one.

Declare the tier on each agent actor in `.agentic/program.yaml` (`tier`, `model`, `turn_cap`,
`budget_tokens`). The runtime enforces the executor limits below.

| Tier | Typical agent | Decides | Receives | Control |
| --- | --- | --- | --- | --- |
| Planner | The strongest available model, long context, one per track | Specs, recipes, gates and bars, which arm wins, what runs next, within written rules and standing authorizations | The why (program goal, owner rulings), the queue, its run folder | Consequential steps need a decision; results are checked by independent evidence |
| Worker | A smaller or cheaper model, bounded context | How to finish a bounded task: a search, a benchmark build, a code change | A self-contained brief with the files it needs and a stop condition | Turn cap, fixed scope, returns a short report, never wakes peers |
| Executor | A local or cheapest model, or a script runner | Nothing beyond the ticket | A fully specified ticket: command, inputs, outputs, stop rule | `local_write` at most; may not own or review a capability; output is checked by readback |

Humans own goals, priority, promotion, risk acceptance, data rights and anything outward-facing
that no standing authorization covers.

## Rules

- **Brief for the tier.** A planner gets the reason a run exists; an executor gets the exact
  command. Giving an executor judgment or a planner a form are both mistakes.
- **Pick the cheapest tier that can do the task.** Bounded searches and mechanical runs go down a
  tier. Use the stronger model when the task needs judgment, not by default.
- **Verify at the consequence, not at every step.** A planner's choice is checked by a gold set,
  a readback or a bar fixed before the read, at the point where it would cost something to be
  wrong.
- **Coordination is a cost.** Every message to a peer session wakes its whole context. Send
  decisions, hand-overs and failures; put everything else where the peer reads it at its next
  check-in.
- **Trust follows the record.** When a tier repeatedly gets a class of task right, widen its
  standing authorizations. When it fails, narrow them and record the lesson.
