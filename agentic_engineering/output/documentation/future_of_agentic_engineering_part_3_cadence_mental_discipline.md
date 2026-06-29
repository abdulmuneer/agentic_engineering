# Future Of Agentic Engineering, Part 3: Cadence And Mental Discipline

Main summary: [future_of_agentic_engineering.md](future_of_agentic_engineering.md)
Previous: [Part 2 - Human Skill Changes](future_of_agentic_engineering_part_2_human_skill_changes.md)
Next: [Part 4 - Compounding And Equilibrium](future_of_agentic_engineering_part_4_compounding_equilibrium.md)

## Purpose

Part 2 described the human shift from narrow execution toward orchestration. This document asks how humans adjust to a new cadence: agents can work, retry, fork, summarize, and generate while humans still need sleep, attention, social context, judgment, and recovery.

## Core Thesis

The cadence problem is not that agents are fast. The problem is asymmetry.

When all workers are human, everyone shares similar biological constraints. People need breaks, sleep, conversation, and time to form judgment. When agents enter the loop, execution can continue across nights, weekends, and parallel branches. This creates an illusion that the human should keep up by extending their workday.

That is the wrong adaptation. Humans should not try to match agent cadence. They should redesign the working system so agent work arrives in reviewable batches, with evidence, limits, and stopping points.

The new discipline is not hustle. It is control of tempo.

## Historical Parallels

### Automation And The Irony Of Supervision

Lisanne Bainbridge's "Ironies of Automation" remains relevant: automation can remove routine manual work while leaving humans responsible for rare, difficult, high-stakes interventions. The operator becomes less practiced at the manual task, yet is expected to take over when automation fails.

Agentic engineering has the same pattern. Agents can handle routine code edits, summaries, tests, and documentation, but the human may be asked to intervene precisely when the problem is ambiguous, cross-cutting, or risky. That means the human needs active situational awareness, not passive trust.

Lesson: do not let agents run so far ahead that the human loses the thread.

### Aviation Autopilot

Modern aircraft automation reduces workload for normal flight but creates mode-awareness problems. Pilots must understand what the automation is doing, what mode it is in, and when to intervene.

Agentic engineering equivalent:

- What task is the agent actually pursuing?
- Which files did it touch?
- Which assumptions did it make?
- Which tools did it use?
- Which checks passed?
- Which check was skipped?
- Is it still in exploration, implementation, repair, or review mode?

Lesson: every long-running agentic workflow needs visible mode state.

### Factory Automation And Stop-The-Line

Lean production did not merely make machines faster. It created mechanisms such as standard work, visible queues, WIP limits, and stop-the-line authority. Speed was made safe through observability and interruption rights.

Agentic engineering equivalent:

- Limit concurrent agent runs.
- Make queues visible.
- Require checkpoint summaries.
- Allow humans and agents to stop work when evidence is poor.
- Promote repeated defects into process changes.

Lesson: throughput without stop rules becomes quality debt.

### DevOps, On-Call, And SRE

DevOps and SRE already faced asymmetric cadence. Services run continuously, incidents happen at night, and alerts can interrupt human recovery. SRE responded with error budgets, toil reduction, alert quality, runbooks, incident roles, and blameless postmortems.

Agentic systems need the same mindset. Agents are not production services, but they create operational load: notifications, diffs, branches, tool approvals, failed tests, and review queues.

Lesson: agentic work needs an operational model, not just a chat interface.

### Financial Markets And High-Frequency Trading

Automated trading made speed a strategic weapon, but it also required circuit breakers, risk limits, kill switches, and compliance controls. The fastest actor is not automatically the best actor; uncontrolled speed can amplify mistakes.

Agentic engineering equivalent:

- Set budget limits.
- Use sandboxed environments.
- Require approval for external actions.
- Stop runaway loops.
- Apply stronger controls to production-affecting tasks.

Lesson: speed needs governors.

## The New Working Cadence

### From Continuous Attention To Scheduled Review

Humans should avoid living inside the agent stream. Instead, they should define review windows.

Example cadence:

- Morning: inspect overnight agent outputs, accept/reject/prioritize.
- Midday: run focused interactive sessions for ambiguous tasks.
- Afternoon: review diffs, tests, and decisions.
- End of day: queue bounded overnight tasks with explicit stop conditions.

The key is that agent work should wait for human review rather than constantly interrupting the human.

### From Chat Threads To Work Packets

Long agent conversations become hard to review. Work should be packaged as:

- Goal.
- Context used.
- Files changed.
- Tests run.
- Evidence.
- Risks.
- Open questions.
- Recommended next action.

This mirrors the package's existing trackers, but with agent-specific evidence added.

### From Parallelism To WIP Limits

Agentic systems make it easy to run many branches at once. That is dangerous if human review capacity is fixed.

A simple rule: do not start more agent work than can be reviewed within the next review window.

Useful limits:

- Maximum active branches.
- Maximum unreviewed diff size.
- Maximum autonomous runtime.
- Maximum token or tool budget.
- Maximum open decisions.
- Maximum unresolved test failures.

The limit should be set by human review bandwidth, not agent availability.

### From Real-Time Supervision To Checkpointing

Humans should not need to watch every tool call. They need checkpoints at natural boundaries:

- After context gathering.
- Before large edits.
- After first failing test is reproduced.
- Before database or infrastructure changes.
- After verification.
- Before merge, release, or external side effect.

Checkpointing keeps humans in control without turning them into full-time babysitters.

## Mental Disciplines To Nurture

### 1. Tempo Discipline

Tempo discipline is the ability to decide whether work should be synchronous, asynchronous, parallel, paused, or stopped.

Training questions:

- Does this need my live judgment?
- Can this run safely while I sleep?
- What is the maximum acceptable drift before review?
- What evidence must be produced before I look again?

### 2. Attention Budgeting

Attention is the scarce resource. Agentic systems should spend tokens to save human attention, not generate more artifacts than a human can absorb.

Training questions:

- What is the one decision I need to make next?
- What can be summarized?
- What must be inspected directly?
- Which alerts should be silenced because they do not require action?

### 3. Trust Calibration

The human must neither distrust everything nor accept everything. Trust should depend on task risk, evidence quality, agent track record, and verification strength.

Training questions:

- What did the agent actually verify?
- Is the output grounded in current files and tests?
- Is this a familiar low-risk pattern or a novel high-risk change?
- Would I approve this if a junior engineer submitted it?

### 4. Situational Awareness

Situational awareness means knowing the current goal, system state, risk state, and next decision. It decays when too many agents run without summaries.

Training habits:

- Keep a visible active-work list.
- Use short end-of-session handoffs.
- Record assumptions and decisions.
- Re-read the diff and tests before trusting the summary.

### 5. Stop Discipline

Stopping is an active skill. Humans need to stop agents that are looping, widening scope, accumulating uncertainty, or producing work that cannot be reviewed.

Stop signals:

- The agent changes unrelated files.
- The agent cannot reproduce the failure.
- Tests are skipped without explanation.
- The diff grows faster than understanding.
- The same error repeats.
- The task requires a product or security decision that was not delegated.

### 6. Recovery Discipline

Humans need recovery because agentic work can create ambient urgency. There is always another run that could be started.

Training habits:

- Define an end-of-day queue, not an endless session.
- Avoid reviewing high-risk changes when tired.
- Use sleep as a design constraint.
- Separate exploratory runs from approval decisions.
- Keep weekends and breaks protected unless production risk demands otherwise.

## Thought Experiment: The Overnight Agent

Suppose a human starts five overnight agents:

1. One refactors authentication.
2. One updates dependencies.
3. One writes tests.
4. One creates release notes.
5. One investigates support tickets.

By morning, all five report success. The naive human now has more work, not less: large diffs, possible conflicts, uncertain assumptions, and review pressure.

A better setup:

- Authentication agent may only inspect, propose, and write a risk plan.
- Dependency agent may update one package group and run the dependency test suite.
- Test agent may add tests but not change production code.
- Release notes agent may draft from merged commits only.
- Support agent may cluster issues and propose backlog items, not edit code.

The second setup respects cadence. It lets agents work while preserving human reviewability.

## Practical Operating Rules

### Before Starting Agents

- Define the outcome.
- Define allowed files or systems.
- Define stop conditions.
- Define evidence required.
- Define review time.
- Define budget.

### During Work

- Prefer checkpoints over live monitoring.
- Keep parallel agents independent.
- Prevent multiple agents from editing the same area unless isolated.
- Stop when the agent changes task class.
- Capture useful discoveries immediately.

### After Work

- Review diffs before summaries.
- Read failed-test logs.
- Record decisions.
- Promote repeated fixes into skills or tests.
- Delete abandoned branches and stale artifacts.

## Cadence Metrics

Agentic teams should track human cadence explicitly:

| Metric | Why it matters |
|---|---|
| Unreviewed agent outputs | Shows whether agents outrun humans |
| Average diff size per review | Predicts review fatigue and defect risk |
| Agent rework rate | Shows poor framing or weak verification |
| Human interruption count | Measures attention damage |
| Time from agent completion to human decision | Reveals bottlenecks |
| Autonomous runtime before checkpoint | Captures drift risk |
| Night/weekend approval count | Signals sustainability risk |

These metrics should sit beside delivery and quality metrics, not below them.

## Implications For The Future Package

The package should later gain cadence controls:

- Work packet templates for agent outputs.
- WIP limits for active agent runs.
- Checkpoint definitions by task type.
- Review-readiness criteria for agent-generated work.
- "Safe overnight work" and "requires live human" classifications.
- End-of-session handoff templates.
- Human attention and review-load metrics.

The package's existing sprint and tracker model can evolve into a control surface for agentic cadence.

## Sources

- [Lisanne Bainbridge, Ironies of Automation](https://web.archive.org/web/20200717054958if_/https://www.ise.ncsu.edu/wp-content/uploads/2017/02/Bainbridge_1983_Automatica.pdf)
- [Google SRE Book: Eliminating Toil](https://sre.google/sre-book/eliminating-toil/)
- [Google SRE Book: Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/)
- [Principles behind the Agile Manifesto](https://agilemanifesto.org/principles.html)
- [DORA Research: 2024 Accelerate State of DevOps Report](https://dora.dev/research/2024/dora-report/)
- [OpenAI Codex: Prompting](https://developers.openai.com/codex/prompting)
- [OpenAI Codex: Subagents](https://developers.openai.com/codex/subagents)
- [Model Context Protocol: Tools](https://modelcontextprotocol.io/specification/2025-06-18/server/tools)
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)

## How This Informs Part 4

Once humans learn to control cadence, agentic systems can compound: every lesson becomes a test, skill, template, tool, or architectural improvement. But compounding cannot continue forever. The next question is what stabilizes the system and who benefits when those limits appear.
