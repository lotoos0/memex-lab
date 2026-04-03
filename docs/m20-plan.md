# M20 Plan

## Milestone name
M20 - Operator Snapshot

## Objective
Add a thin aggregate snapshot layer that reads the most relevant existing report artifacts and produces one compact operator-facing summary of the current system state.

M20 is not a dashboard.
M20 is not a new metrics engine.
M20 is not a historical analytics layer.

M20 should answer:
- what the current candidate state looks like
- what the current review loop state looks like
- what the latest alignment/funnel health looks like
- whether the operator can quickly understand the system without opening 4 separate reports

---

## Why M20 exists

The system already produces several useful reports:
- candidate audit
- review feedback report
- selector–scorer alignment report
- review loop metrics

Each is useful on its own.

The problem is operational fragmentation:
- too many artifacts
- too many places to look
- too much context switching

M20 exists to:
- consolidate top-line information
- reduce operator overhead
- provide one small “state of the system” report
- keep deeper reports available but not mandatory for every check

The goal is not more detail.
The goal is less friction in understanding the current state.

---

## M20 scope

### In scope
- read existing report artifacts
- extract a small set of top-line metrics
- write one snapshot report
- print one concise stdout summary
- degrade gracefully when some source reports are missing

### Out of scope
- recomputing the underlying reports
- historical trend tracking
- charts
- dashboards
- databases
- alerting systems
- changes to selector/scorer/review logic
- orchestrator changes

---

## Snapshot philosophy

M20 must remain a consolidation layer, not a second analytics engine.

It should:
- read already-produced report artifacts
- extract the most useful top-line fields
- present them in one place

It must not:
- reinterpret the data aggressively
- create new pseudo-scores
- try to replace the source reports

The source reports remain the source of truth.
The snapshot is only a concise operator summary.

---

## Required source reports

M20 may read these when present:

- `data/reports/candidate_audit_v2.json`
- `data/reports/review_feedback_report.json`
- `data/reports/selector_scorer_alignment_v2.json`
- `data/reports/review_loop_metrics.json`

The module must still run if one or more are missing.

When a source is missing:
- the snapshot should still be written
- missing sections should become sparse / null / omitted in a consistent way
- no crash

---

## Required snapshot sections

### 1. Candidate state
Top-line fields such as:
- total candidates
- review_now
- review_if_time
- ignore_for_now
- labeled count

Primary source:
- `candidate_audit_v2.json`
Fallback:
- sparse/null if unavailable

### 2. Review loop state
Top-line fields such as:
- total reviewed
- useful count
- noise count
- needs_more_context count
- useful rate
- sample size note

Primary source:
- `review_loop_metrics.json`

### 3. Alignment state
Top-line fields such as:
- scorer weak/partial/strong distribution
- selector class distribution
- key redundancy signal

Primary source:
- `selector_scorer_alignment_v2.json`

### 4. Feedback state
Top-line fields such as:
- reviewed labeled count
- reviewed unlabeled count
- outcome by class high-level counts if useful

Primary source:
- `review_feedback_report.json`
Only include the smallest useful subset.

### 5. Snapshot completeness
A small section that tells the operator which source reports were present or missing.

Example:
- candidate_audit_present
- feedback_report_present
- alignment_report_present
- review_loop_metrics_present

---

## Required output file

Write one report:
- `data/reports/operator_snapshot.json`

No extra artifacts in v0.

---

## Required stdout summary

Print a concise summary such as:
- candidates / review_now / review_if_time / ignore
- reviewed / useful / noise
- weak / partial / strong
- snapshot completeness note

It should help an operator answer:
- “Is the system healthy enough to continue review?”
- “Do I need to inspect deeper reports now?”

Without pretending to make decisions automatically.

---

## Success criteria

M20 is successful if:
- it produces one compact operator snapshot
- it works even when some source reports are missing
- it reduces the need to open several reports for routine checks
- it stays aggregate-only
- it does not duplicate full source report contents

---

## Failure criteria

M20 is failing if:
- it becomes a giant merged report
- it duplicates whole sections from all sources
- it invents new scoring or interpretation logic
- it crashes when one optional report is missing
- it is harder to understand than opening the original reports directly

---

## Constraints

- keep Python as the implementation language
- keep the module offline
- do not modify scorer, selector, candidateaudit, reviewfeedback, console, orchestrator, reviewexport, or reviewloopmetrics unless strictly necessary
- keep code and docs in English
- prefer sparse/null fields over brittle assumptions

---

## Risks

### Risk: snapshot duplicates too much data
Mitigation:
- include only top-line metrics
- avoid dumping nested full sections

### Risk: conflicting numbers between reports
Mitigation:
- clearly document source precedence per section
- keep the snapshot descriptive, not authoritative over source reports

### Risk: missing reports create confusing emptiness
Mitigation:
- add an explicit snapshot completeness section

### Risk: snapshot becomes stale if source reports are stale
Mitigation:
- do not hide that reality
- optionally include source file paths and/or presence flags, but not recomputation

---

## Deliverables

M20 should produce:
- one operator snapshot module
- one aggregate JSON snapshot report
- one concise stdout summary
- updated manual verification steps

---

## Final rule

M20 must remain a thin consolidation layer over existing reports.
It must not become a second analytics system or a replacement for the source reports.