# M19 Plan

## Milestone name
M19 - Review Loop Metrics

## Objective
Add a thin metrics/reporting layer that summarizes how the review loop is performing using existing artifacts:
- selector outputs
- candidate audit outputs
- review outcomes
- feedback reports

M19 is not a new selector.
M19 is not a new scorer.
M19 is not a dashboard rewrite.
M19 is not machine learning.

M19 should answer whether the current review system is actually useful over time.

---

## Why M19 exists

The system already has:
- scoring
- selection
- review queues
- review UX
- feedback capture
- export
- orchestration

That means the system can already generate candidates, review them, and store outcomes.

What it still lacks is a compact answer to:
- how much is being reviewed
- how much is useful vs noise
- how strong the current shortlist quality is
- whether the pipeline is improving or just changing

M19 exists to:
- measure review loop performance
- create a stable operational summary
- make the system easier to evaluate over time
- support future refinement decisions with data instead of intuition

The goal is not analysis theater.
The goal is a small set of metrics that actually help decide what to improve next.

---

## M19 scope

### In scope
- read existing review artifacts
- compute a compact set of review loop metrics
- write one report file
- print a concise human-readable summary
- remain aggregate-only

### Out of scope
- changing scoring logic
- changing selector logic
- time-series dashboards
- historical diff engine
- background monitoring
- external analytics integrations
- databases
- prediction or recommendation logic

---

## Metrics philosophy

M19 must stay small and useful.

It should report:
- what entered review
- what was actually reviewed
- what the outcomes were
- how the reviewed subset maps back to candidate classes and labels

It must not:
- invent “smart scores”
- infer profitability
- give market advice
- overfit tiny samples into fake certainty

The report should help future tuning, not pretend to be final truth.

---

## Required inputs

M19 may use:
- `data/review_candidates_v2.jsonl`
- `data/reports/candidate_audit_v2.json`
- `data/review_outcomes.jsonl`
- `data/reports/review_feedback_report.json`

The module should still run if:
- outcomes are missing
- feedback report is missing

In those cases it should produce a valid sparse report, not crash.

---

## Required report outputs

### 1. Candidate funnel metrics
Examples:
- total candidate records
- total review_now
- total review_if_time
- total ignore_for_now

### 2. Review coverage metrics
Examples:
- total reviewed records
- reviewed share of all candidates
- reviewed share of review_now candidates
- reviewed share of review_if_time candidates

### 3. Outcome distribution
Examples:
- useful count
- noise count
- needs_more_context count
- useful rate
- noise rate

### 4. Outcome by candidate class
Examples:
- reviewed review_now → useful/noise/needs_more_context
- reviewed review_if_time → useful/noise/needs_more_context

### 5. Label interaction summary
Examples:
- reviewed labeled count
- reviewed unlabeled count
- reviewed outcomes by label when labels exist

### 6. Sample-size note
A small, explicit signal such as:
- `low`
- `moderate`
- `sufficient`

This should be simple and rule-based, not interpretive.

---

## Required behavior

### Output file
Write one report:
- `data/reports/review_loop_metrics.json`

### Stdout summary
Print a concise summary with the most useful top-line metrics:
- candidates
- review_now / review_if_time / ignore
- reviewed
- useful / noise / needs_more_context
- useful rate
- sample size note

### Aggregate-only
No per-mint dumps in the report.

---

## Success criteria

M19 is successful if:
- it runs against existing artifacts without changing them
- it produces a compact and useful report
- it handles missing outcomes cleanly
- it stays aggregate-only
- the summary helps judge review-loop quality at a glance

---

## Failure criteria

M19 is failing if:
- it becomes a dashboard disguised as JSON
- it introduces derived pseudo-scores
- it crashes on missing optional inputs
- it reports numbers that are hard to interpret
- it tries to do historical analysis without enough data

---

## Constraints

- keep Python as the implementation language
- keep the module offline
- do not modify scorer, selector, candidateaudit, reviewfeedback, console, orchestrator, or reviewexport unless strictly necessary
- keep code and docs in English
- prefer a single compact report over multiple artifacts

---

## Risks

### Risk: sample size too small to mean much
Mitigation:
- include explicit sample-size note
- avoid strong conclusions in the report

### Risk: duplicate information from review_feedback_report
Mitigation:
- focus M19 on top-level loop metrics, not reprinting every existing section

### Risk: report becomes bloated
Mitigation:
- keep sections minimal and clearly named

### Risk: missing optional files create fragile behavior
Mitigation:
- treat outcomes and feedback artifacts as optional and degrade gracefully

---

## Deliverables

M19 should produce:
- one review-loop metrics module
- one aggregate JSON report
- one stdout summary
- updated manual verification steps

---

## Final rule

M19 must remain a thin aggregate metrics layer over the existing review loop.
It must not become a dashboard, predictor, or second feedback engine.