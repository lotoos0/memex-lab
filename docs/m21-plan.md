# M21 Plan

## Milestone name
M21 - Pipeline Health Checks

## Objective
Add a thin pipeline health check layer that inspects the current project artifacts and reports whether the system appears fresh, complete, and operationally ready for review work.

M21 is not monitoring.
M21 is not alerting.
M21 is not a scheduler.
M21 is not a dashboard.

M21 should answer:
- are the key artifacts present
- do they look fresh enough
- are key outputs aligned in time/order
- is the operator likely working on an outdated or incomplete pipeline state

---

## Why M21 exists

The system already has:
- workflows
- reports
- metrics
- snapshot
- console and orchestrator

That means it can generate and summarize outputs.

What it still lacks is a simple readiness signal:
- are the artifacts there
- are they recent enough
- were upstream steps likely run before downstream steps
- is the current state good enough to trust operationally

M21 exists to:
- reduce silent stale-data usage
- expose obvious pipeline freshness issues
- give one compact readiness report
- support safer manual operation

The goal is not background ops infrastructure.
The goal is explicit manual readiness checks.

---

## M21 scope

### In scope
- inspect file presence
- inspect file modified times
- compare relative freshness/order of key artifacts
- produce one aggregate health report
- print one concise stdout summary

### Out of scope
- background monitoring
- notifications
- auto-remediation
- orchestrator changes
- console integration in this milestone
- historical tracking
- external services
- databases
- scoring/selection logic changes

---

## Health philosophy

M21 must remain simple and explicit.

It should:
- inspect a small set of important artifacts
- produce clear present/missing/stale-ish style signals
- surface obvious ordering problems

It must not:
- pretend to know the market
- infer hidden system state
- trigger workflows automatically
- make decisions for the operator

This is a readiness helper, not an ops platform.

---

## Required artifact set

M21 should inspect a focused set of artifacts such as:

### Core pipeline artifacts
- `data/scored_snapshots_v2.jsonl`
- `data/review_candidates_v2.jsonl`
- `data/reports/candidate_audit_v2.json`
- `data/reports/review_loop_metrics.json`
- `data/reports/operator_snapshot.json`

### Optional additional artifacts
- `data/reports/selector_scorer_alignment_v2.json`
- `data/reports/review_feedback_report.json`

This should stay small.
Do not turn M21 into a full file inventory.

---

## Required checks

### 1. Presence checks
For each tracked artifact:
- present: true/false

### 2. Modified-time checks
For each tracked artifact:
- modified_at
- age_seconds or age_minutes

### 3. Ordering sanity checks
Examples:
- `review_candidates_v2.jsonl` should not be older than `scored_snapshots_v2.jsonl` by an obviously wrong margin if candidates were expected after scoring
- `candidate_audit_v2.json` should not be older than `review_candidates_v2.jsonl` if audit is expected after selection
- `operator_snapshot.json` should not be older than all source reports if it is being used as the current view

These checks should be simple and explicit, not heuristic-heavy.

### 4. Overall readiness summary
Examples:
- `ready`
- `degraded`
- `not_ready`

This should be rule-based and explainable.

---

## Readiness rules

Keep them simple.

Suggested idea:
- `not_ready`
  - one or more core pipeline artifacts missing
- `degraded`
  - all core artifacts present, but one or more freshness/order checks fail
- `ready`
  - all core artifacts present and no freshness/order warnings triggered

No more than a handful of rules.

---

## Required output file

Write one report:
- `data/reports/pipeline_health.json`

No extra artifacts in v0.

---

## Required snapshot/report sections

### 1. overall_status
- readiness_state
- warning_count
- error_count

### 2. artifact_status
Per tracked artifact:
- path
- present
- modified_at
- age_seconds

### 3. ordering_checks
A small list or object of named checks:
- pass/fail
- short reason

### 4. missing_artifacts
List of missing required artifacts

### 5. warnings
Small list of warning strings or codes

Keep it compact and aggregate-oriented.

---

## Required stdout summary

Print a concise summary such as:
- readiness state
- missing required artifact count
- warning count
- most important stale/order issue if any

The operator should be able to answer:
- “Can I trust the current pipeline state enough to work with it?”
without opening the JSON file.

---

## Success criteria

M21 is successful if:
- it produces one compact readiness report
- it catches obvious missing/stale/order problems
- it stays small and explainable
- it does not modify any project artifacts
- it helps the operator avoid stale-state mistakes

---

## Failure criteria

M21 is failing if:
- it becomes a giant file linter
- it invents fuzzy “health scores”
- it crashes when some optional artifacts are missing
- it creates noisy warnings that do not help decisions
- it drifts into monitoring/alerting/platform territory

---

## Constraints

- keep Python as the implementation language
- keep the module offline
- do not modify scorer, selector, candidateaudit, reviewfeedback, console, orchestrator, reviewexport, reviewloopmetrics, or operatorsnapshot unless strictly necessary
- keep code and docs in English
- prefer small explicit checks over generalized framework code

---

## Risks

### Risk: freshness thresholds become arbitrary
Mitigation:
- keep them minimal and clearly documented
- prefer relative ordering checks over strict wall-clock judgments where possible

### Risk: optional artifact absence is treated too harshly
Mitigation:
- separate required vs optional artifacts clearly

### Risk: operator over-trusts readiness_state
Mitigation:
- make the report descriptive and rule-based
- include warning reasons

### Risk: too many tracked files create noise
Mitigation:
- keep the tracked artifact set intentionally small

---

## Deliverables

M21 should produce:
- one pipeline health module
- one aggregate JSON health report
- one concise stdout summary
- updated manual verification steps

---

## Final rule

M21 must remain a thin readiness-check layer over existing artifacts.
It must not become a monitor, scheduler, or auto-recovery system.