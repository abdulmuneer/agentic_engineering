# Future Of Agentic Engineering, Part 2: Human Skill Changes

Main summary: [future_of_agentic_engineering.md](future_of_agentic_engineering.md)
Previous: [Part 1 - Principles And Methodologies](future_of_agentic_engineering_part_1_principles_methodologies.md)
Next: [Part 3 - Cadence And Mental Discipline](future_of_agentic_engineering_part_3_cadence_mental_discipline.md)

## Purpose

Part 1 argued that agentic engineering changes the unit of execution from a human task to a verifiable loop. This document asks what that does to the human in the loop.

The answer is not that narrow specialists disappear. The answer is that the highest-leverage human increasingly needs enough breadth to drive the whole system: product intent, requirements, design, architecture, implementation, quality, security, release, operations, and learning.

## Core Thesis

Before agentic systems, specialization was often efficient because human throughput was scarce and coordination costs were high. A product manager, requirements analyst, designer, backend engineer, QA engineer, security reviewer, and release engineer each had a defensible lane.

In agentic systems, execution capacity becomes more elastic. A single human can ask for requirements, design alternatives, code changes, tests, release notes, and security review in the same working session. The limiting skill shifts from "Can I personally perform every specialized task?" to "Can I recognize what good looks like across the lifecycle, steer agents toward it, and reject plausible but wrong work?"

This creates a new human profile: the accountable orchestrator-generalist. The person does not need to be the best coder, tester, designer, architect, security reviewer, and release engineer. But they need enough fluency in each discipline to set the goal, choose the right agentic method, inspect evidence, and know when to escalate to a deeper expert.

## Determinism In An Agentic System

The user raised a key phrase: humans may need breadth so they can drive the system in a deterministic way. Strict determinism is not the right expectation for LLM outputs. Even with low temperature, context changes, tool state changes, model updates, and ambiguous instructions can alter behavior.

The practical goal is bounded repeatability:

- The problem is framed consistently.
- Inputs and context are explicit.
- Tools and permissions are scoped.
- Outputs are structured where possible.
- Tests and checks are reproducible.
- Decisions and assumptions are recorded.
- Human review gates are clear.
- Production rollback and monitoring exist.

The human's job is to make the outcome deterministic enough for the risk level. A prototype can tolerate more variance than a database migration, payment flow, authentication change, or production release.

## The Skill Shift

### From Doing To Framing

The old high-value skill was often task execution: write the code, file the bug, design the screen, create the test plan. Those skills still matter, but the agentic multiplier rewards problem framing more.

Good framing includes:

- Defining the user or system actor.
- Stating the outcome.
- Naming constraints.
- Separating requirements from guesses.
- Specifying acceptance evidence.
- Naming non-goals.
- Giving the agent the right context, not all context.

A weak goal creates broad, confident work that is expensive to review. A strong goal creates narrow, testable work.

### From Prompting To Context Engineering

"Prompt engineering" is too small a term for durable agentic work. The real skill is context engineering:

- Which files, docs, issues, tests, logs, and design records should the agent read?
- Which instructions belong in a global file, a role file, a skill, a one-time prompt, or a tool schema?
- What should be remembered across sessions?
- What should be discarded because it is stale or speculative?
- What evidence should be required before the agent is allowed to continue?

Codex skills and MCP resources make this concrete. They allow reusable instructions, scripts, references, and external context to become part of the agent's working environment. The human designs that environment.

### From Local Expertise To Lifecycle Fluency

The local package's 12-role model is useful as a map of required judgment:

| Lens | What the human must be able to ask |
|---|---|
| Product | Does this matter to a user or business outcome? |
| Requirements | Can this be tested and scoped? |
| UX | Will the workflow make sense under real use? |
| Architecture | Does the design fit the system and future change? |
| Backend | Are data, APIs, validation, and failure modes correct? |
| Frontend | Are states, accessibility, and interaction behavior handled? |
| Integration | Do systems, environments, and third parties line up? |
| Code quality | Is the change simple, maintainable, and covered? |
| QA | What would prove this works and does not regress? |
| Security | What can be abused, leaked, bypassed, or misconfigured? |
| DevOps/SRE | Can this be deployed, observed, rolled back, and supported? |
| Documentation/feedback | Will users and support understand what changed? |

The agentic human does not need to perform each role manually every time. They need enough vocabulary and judgment to invoke, compare, and verify those perspectives.

### From Reviewing Output To Reviewing Evidence

Human review used to focus heavily on artifacts: code, test plans, designs, tickets. Agentic review must focus on the evidence trail:

- What context did the agent inspect?
- What assumptions did it make?
- What files did it change?
- What tests did it run?
- What tests did it skip?
- What failure did it observe?
- What tradeoff did it choose?
- What is still uncertain?

This is a different review skill. A large polished answer can be less trustworthy than a smaller answer with clear evidence and known limits.

### From Coordination To Orchestration

Traditional coordination means moving work among humans. Agentic orchestration means shaping a workflow among humans, agents, tools, and gates.

The orchestrator decides:

- Which tasks are safe for autonomy.
- Which tasks need parallel agents.
- Which tasks need a specialist human.
- Which tools are allowed.
- Which checks must pass.
- When to stop and ask.
- When to throw away an agent's work.

This is closer to directing a small operating system than managing a queue of tickets.

## Breadth Does Not Mean Shallow Generalism

There are two bad interpretations of the coming skill shift.

The first is "everyone must become a full-stack genius." That is unrealistic and unnecessary.

The second is "agents remove the need for expertise." That is dangerous.

The better model is a comb-shaped skill profile:

- One or two deep domains where the human can judge expert-level quality.
- Broad working literacy across the lifecycle.
- Strong systems thinking.
- Strong taste for evidence, simplicity, and user value.
- Ability to encode lessons into instructions, tests, skills, templates, and tools.

Deep specialists can become much more valuable if they can convert expertise into reusable agentic assets. A great QA engineer can create test-generation skills, defect taxonomies, risk checklists, and release gates. A security reviewer can create threat-model prompts, abuse-case templates, dependency scanning workflows, and least-privilege tool policies. A designer can create design-review lenses and accessibility checks.

The specialists most at risk are those whose value is mostly local execution without explicit judgment, reusable standards, or cross-functional communication.

## Skill Stack For The Human In The Loop

### 1. Product And Problem Framing

The human must identify the real job to be done. Agentic systems can produce many solutions to the wrong problem. Product judgment becomes more valuable because the cost of generating plausible work falls.

Practice:

- Write one-sentence problem statements.
- Separate user pain from proposed solution.
- Define a success metric before asking for implementation.
- Ask agents to generate alternatives before picking the first path.

### 2. Requirements And Acceptance Criteria

Agentic execution needs crisp stopping conditions. Requirements should become executable checks where possible.

Practice:

- Convert fuzzy goals into `Given / When / Then` acceptance criteria.
- Name edge cases and non-goals.
- Require tests or manual verification steps with each change.
- Maintain traceability from goal to diff to test evidence.

### 3. Code Reading And Diff Judgment

Even non-specialist orchestrators need code-reading fluency. They must be able to inspect diffs, spot accidental blast radius, understand test failures, and ask useful review questions.

Practice:

- Read diffs before summaries.
- Ask why each changed file needed to change.
- Check whether tests prove the stated behavior.
- Look for hidden coupling, migration risk, and error handling.

### 4. Testing And Evaluation Literacy

Testing is no longer a separate downstream phase. It is the control system for agentic work.

Practice:

- Know the difference between unit, integration, end-to-end, regression, security, and exploratory tests.
- Use evals for behavior that cannot be captured by normal deterministic tests.
- Treat flaky tests as workflow debt.
- Ask agents to add failing tests before fixes when appropriate.

### 5. Security And Permission Design

Agents with tools are operational actors. The human must think in terms of least privilege, secrets, sensitive data, dependency risk, and irreversible actions.

Practice:

- Scope tool access to the task.
- Require confirmation for destructive or externally visible actions.
- Keep credentials out of prompts and logs.
- Ask for threat models on sensitive features.

### 6. Architecture And Systems Thinking

Agents are good at local edits and can be weak at preserving long-term architecture unless the architecture is explicit.

Practice:

- Maintain architecture records and boundaries.
- Ask agents to explain how a change fits the system.
- Prefer small, reversible changes.
- Escalate when the agent proposes new infrastructure, data models, or major abstractions.

### 7. Economic Judgment

Agentic work has costs: tokens, tool calls, cloud resources, review time, opportunity cost, and risk. Cheap generation can become expensive integration.

Practice:

- Decide when a task deserves a deep run, quick run, or no run.
- Watch diff size, context size, and review time.
- Compare token cost against expected value and human time saved.
- Stop loops that are accumulating uncertainty.

### 8. Communication And Decision Logging

Agentic systems create many intermediate artifacts. The human must convert them into durable knowledge.

Practice:

- Record decisions with options considered and rationale.
- Update instructions when a repeated failure appears.
- Promote stable workflows into skills.
- Keep summaries short enough for future agents to use.

## A Maturity Model For Human-Agent Skill

| Level | Human behavior | Risk |
|---|---|---|
| Operator | Asks for tasks and accepts summaries | High trust in plausible output |
| Reviewer | Reads diffs and asks for tests | Better quality, still reactive |
| Orchestrator | Designs loops, scopes tools, sequences agents, demands evidence | Strong leverage and control |
| System designer | Converts repeated lessons into skills, evals, templates, tools, and governance | Organization-level compounding |

The goal is not to make every human a system designer immediately. The goal is to move serious agentic work beyond operator mode.

## Implications For The Future Package

The package should later evolve in ways that train and support the orchestrator-generalist:

- Keep role lenses, but express them as invocable agent skills and review gates.
- Add a human orchestration guide that teaches when to use single-agent, multi-agent, skill, MCP, or human escalation.
- Add acceptance-evidence templates for each workflow.
- Add a permission model for safe tool use.
- Add review-load and rework metrics so human bottlenecks are visible.
- Add "promotion paths" from ad hoc prompts to reusable skills.

## Sources

- [Principles behind the Agile Manifesto](https://agilemanifesto.org/principles.html)
- [DORA Research: 2025 State of AI-assisted Software Development](https://dora.dev/research/2025/dora-report/)
- [DORA: Choosing measurement frameworks to fit your organizational goals](https://dora.dev/research/2025/measurement-frameworks/)
- [OpenAI Codex: Prompting](https://developers.openai.com/codex/prompting)
- [OpenAI Codex: Agent Skills](https://developers.openai.com/codex/skills)
- [Model Context Protocol: Tools](https://modelcontextprotocol.io/specification/2025-06-18/server/tools)
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)
- [World Economic Forum: Future of Jobs Report 2025](https://www.weforum.org/publications/the-future-of-jobs-report-2025/)
- [UNESCO AI competency frameworks for teachers and students](https://www.unesco.org/en/digital-education/ai-future-learning/competency-frameworks)
- [Human-In-The-Loop Software Development Agents: Challenges and Future Directions](https://arxiv.org/abs/2506.11009)

## How This Informs Part 3

If the human role shifts from task performer to orchestrator-generalist, the working cadence changes. Humans cannot match agents by working longer. They need disciplines for batching, delegation, review, sleep, attention, and recovery.
