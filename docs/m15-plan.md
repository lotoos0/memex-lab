# M15 Plan

## Milestone name
M15 - Pipeline Orchestration

## Objective
Add a thin orchestration layer that can run predefined offline workflow sequences using the existing tools in the correct order.

M15 is not a new scoring system.
M15 is not a scheduler.
M15 is not automation in the background.
M15 is not a long-running service.

M15 should reduce command friction and make repeated review workflows easier and safer to execute.

---

## Why M15 exists

The project already has:
- scorer
- selector
- candidate audit
- review feedback
- console
- comparison and audit tools

That means the project already has all the pieces needed for a full review workflow.

What it still lacks is a safe and repeatable way to execute the most common sequences without manually chaining multiple tools every time.

M15 exists to:
- reduce command repetition
- reduce ordering mistakes
- make common workflows explicit
- improve operational consistency

The goal is not hidden automation.
The goal is reproducible manual orchestration.

---

## M15 scope

### In scope
- define a small set of named workflows
- execute them step-by-step
- stop cleanly on failure
- print concise summaries
- optionally expose the orchestration through CLI first

### Out of scope
- background scheduling
- parallel execution
- retries with backoff
- automatic healing
- execution logic
- prediction logic
- web services
- databases
- cloud deployment
- job queues

---

## Orchestration philosophy

The orchestration layer must call existing tools.
It must not reimplement their logic.

Each step should:
- invoke an existing CLI/module
- capture exit status
- stop the workflow if a required step fails
- print a clear summary at the end

The underlying tools remain the source of truth.

---

## Required workflows

Start with exactly three workflows in v0:

### 1. full_v2_review_flow
Purpose:
Run the full scorer v2 → selector v2 → candidate audit → review feedback report chain.

Steps:
1. `python -m scorer --score-version v2`
2. `python -m selector --selection-version v2`
3. `python -m candidateaudit --input-path data/review_candidates_v2.jsonl --report-output-path data/reports/candidate_audit_v2.json --queue-now-output-path data/review_queue_now_v2.jsonl --queue-if-time-output-path data/review_queue_if_time_v2.jsonl`
4. `python -m reviewfeedback.report`

### 2. refresh_candidates_only
Purpose:
Refresh selector v2 output and its audit without rescoring.

Steps:
1. `python -m selector --selection-version v2`
2. `python -m candidateaudit --input-path data/review_candidates_v2.jsonl --report-output-path data/reports/candidate_audit_v2.json --queue-now-output-path data/review_queue_now_v2.jsonl --queue-if-time-output-path data/review_queue_if_time_v2.jsonl`

### 3. feedback_report_only
Purpose:
Regenerate review feedback report only.

Steps:
1. `python -m reviewfeedback.report`

No user-defined workflows in v0.

---

## Required behavior

### 1. Sequential execution
- steps run in order
- later steps do not run if an earlier required step fails

### 2. Clear summary
At the end, print:
- workflow name
- total steps
- passed steps
- failed step if any
- output paths if relevant
- overall success/failure

### 3. Deterministic command definitions
Workflow steps must be stored explicitly in code.
No dynamic command construction beyond fixed path arguments.

### 4. No hidden state
The orchestrator should not maintain caches, databases, or progress files.

---

## CLI requirements

The orchestrator should support:

### List workflows
Example:
- `python -m orchestrator --list`

### Run workflow
Example:
- `python -m orchestrator --workflow full_v2_review_flow`

Optional installed script:
- `memex-orchestrator`

No interactive prompt in v0.

---

## Output requirements

### Stdout
Concise and operational:
- which workflow ran
- which steps passed
- which step failed if any
- final status

### Optional JSON report
Allowed but not required in v0.
If added, keep it minimal.

Default recommendation for v0:
- stdout only
- no extra artifact unless clearly useful

---

## Success criteria

M15 is successful if:
- workflows run in the correct order
- a failed step stops the workflow
- the summary is clear
- no tool logic is duplicated
- the workflows meaningfully reduce command friction

---

## Failure criteria

M15 is failing if:
- orchestration reimplements module logic
- workflows continue after a required failure
- too many workflow variants are added
- scope drifts into scheduler/service territory
- output is confusing or noisy

---

## Constraints

- keep Python as the implementation language
- keep orchestration offline
- do not refactor scorer, selector, candidateaudit, reviewfeedback, or console unless strictly necessary
- keep code and docs in English
- prefer a small explicit workflow table over abstraction-heavy design

---

## Risks

### Risk: orchestration becomes a hidden second control layer
Mitigation:
- workflows only wrap existing commands
- keep definitions explicit and visible

### Risk: too many workflows create confusion
Mitigation:
- start with exactly three workflows

### Risk: error handling becomes vague
Mitigation:
- stop on first failed required step
- print the exact failing command

### Risk: orchestration becomes obsolete if console evolves
Mitigation:
- the orchestrator can later be called by the console rather than replaced by it

---

## Deliverables

M15 should produce:
- one orchestration module
- three predefined workflows
- CLI entrypoint for listing and running workflows
- updated manual verification steps

---

## Final rule

M15 must remain a thin workflow runner over existing tools.
It must not become a scheduler, service, or second implementation of pipeline logic.