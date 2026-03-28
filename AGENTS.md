# AGENTS.md

## Project name
memex-lab

## Project purpose
memex-lab is a research and execution framework for low market cap Solana memecoins.

The project is built in stages:
1. collector
2. scorer
3. executor

The current priority is:
- build a reliable collector
- log real-time token lifecycle data
- support later scoring and manual decision workflows

Do not optimize for full-auto trading first.
Do not optimize for hype.
Optimize for observability, correctness, and controlled iteration.

---

## Core rules

- Keep all code, comments, and documentation in English.
- Prefer small, scoped changes.
- Do not rewrite large parts of the project unless explicitly requested.
- Do not add unnecessary abstractions early.
- Do not introduce new dependencies unless clearly justified.
- Favor simple, testable modules.
- Preserve existing project structure unless a change is approved.
- If a task is ambiguous, choose the safest minimal implementation.

---

## Working model

This project uses a human-in-the-loop workflow.

Roles:
- Claude Code = planner / reviewer
- Codex = implementer / fixer
- Human = final decision maker

Do not assume autonomous product decisions.
Do not silently change architecture.
Do not expand scope without explicit approval.

---

## Current development order

Always prefer this order of work:

1. collector
2. scorer
3. storage improvements
4. manual alerting
5. executor

Executor logic is not the first milestone.
If a task pushes toward auto-buy or auto-sell too early, push back and suggest a collector/scorer-first path.

---

## Collector goals

Collector should focus on:
- new token detection
- lifecycle event logging
- program log parsing
- trade/event stream ingestion
- bonding curve progress tracking
- migration detection
- normalized event storage

Collector should not:
- place trades
- make irreversible decisions
- hide raw data
- depend on fragile UI scraping if direct program/event data is available

---

## Scorer goals

Scorer should:
- consume collector output
- assign structured signals or scores
- remain explainable
- make it easy to compare tokens consistently

Scorer should not:
- become a black box
- rely on vague heuristics without observable inputs
- mix execution logic into scoring logic

---

## Executor goals

Executor is a later-stage module.

Executor must only be built after:
- collector is stable
- scoring inputs are defined
- manual review flow exists
- risk rules are documented

Any executor work must respect:
- strict risk limits
- explicit kill-switches
- deterministic config
- auditable decisions

---

## Coding standards

- Use clear names.
- Prefer small functions.
- Avoid deep nesting.
- Avoid magic numbers.
- Keep modules focused.
- Use comments only when they explain why, not what.
- Handle errors explicitly.
- Fail loudly when data integrity matters.
- Prefer structured logs over print debugging.

---

## File editing rules

When editing files:
- modify only files relevant to the task
- do not reformat unrelated files
- do not rename files without a reason
- do not move modules unless requested
- do not create duplicate logic in multiple places

When creating files:
- keep names explicit
- place docs under `docs/`
- place raw exports under `data/` unless specified otherwise

---

## Testing rules

Before considering a task complete:
- run the relevant tests if they exist
- if no tests exist, propose the smallest useful test
- provide a manual verification checklist
- mention risks and edge cases

Do not claim success without verification.

---

## Output expectations

For each completed implementation task, provide:
1. what changed
2. why it changed
3. files touched
4. how to test it
5. known limitations

Keep final summaries concise and operational.

---

## Non-goals for now

The following are not current priorities:
- complex dashboards
- heavy optimization
- premature microservices
- advanced AI prediction layers
- social sentiment pipelines
- full production deployment
- full-auto sniper behavior

---

## If unsure

If unsure, choose:
- simpler design
- safer behavior
- better logs
- more observable output
- less automation