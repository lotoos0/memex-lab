# M12 Plan

## Milestone name
M12 - Selector v2

## Objective
Build a small evidence-informed refinement of the current candidate selection layer using observed review outcomes, candidate audit patterns, and existing labels.

M12 is not a trading engine.
M12 is not a prediction model.
M12 is not machine learning.

M12 should improve manual-review prioritization while staying:
- offline
- deterministic
- explicit
- explainable

---

## Why M12 exists

M8 introduced candidate selection.
M9 added candidate audit and review queues.
M10 added review feedback outcomes.
M11 improved operations through a local console.

That means the project now has enough feedback to refine selection logic based on real observed workflow, not just structural assumptions.

M12 exists to:
- reduce selector noise
- improve review-now precision
- improve usefulness of review-if-time
- make candidate selection better aligned with manual feedback

The goal is not smarter-looking logic.
The goal is fewer wasted reviews.

---

## M12 scope

### In scope
- define a selector v2 rule set
- preserve explainability
- write selector v2 output to separate files
- compare selector v1 vs selector v2 output
- keep all logic explicit and file-based

### Out of scope
- execution logic
- trade signals
- market prediction
- machine learning
- external APIs
- databases
- dashboards
- real-time selection
- automatic tuning
- backtesting

---

## Inputs and outputs

### Inputs
Primary input:
- `data/filtered_snapshots_v1.jsonl`

Optional context:
- `data/labels/review_labels.jsonl`
- `data/reports/candidate_audit.json`
- `data/reports/review_feedback_report.json`

### Outputs
- `data/review_candidates_v2.jsonl`
- `data/reports/selector_v1_vs_v2.json`

Do not overwrite selector v1 output.

---

## Selector philosophy

Selector v2 must remain a review-priority classifier.

It should not decide:
- what to buy
- what will pump
- what is profitable

It should only improve:
- who gets reviewed now
- who gets reviewed later
- who gets ignored for now

This is still manual-review support, not market intelligence.

---

## Guardrails for v2

- change at most 2 to 4 selection rules total
- preserve the three candidate classes:
  - review_now
  - review_if_time
  - ignore_for_now
- keep labels as weak explicit modifiers only
- document every change from v1 clearly
- keep the output schema stable unless there is a strong reason to extend it

---

## Candidate improvement directions

Possible directions for v2:

### 1. Better handling of migration-only records
These are already excluded, but v2 may make their reasoning clearer or more consistent with feedback reporting.

### 2. Better handling of partial records
Some `partial` records may be too noisy for `review_if_time` if they repeatedly end up as `noise` in M10.

### 3. Better use of labels as explicit overrides
Keep label effects narrow, but make sure:
- `interesting` helps only when structure is already acceptable
- `suspect` remains a hard stop

### 4. Better distinction between structurally OK and review-worthy
Two records can both be `partial`, but not equally worth attention. v2 may split them more cleanly using explicit rules.

---

## Allowed change types

Allowed examples:
- stricter rule for `review_now`
- stricter rule for `review_if_time`
- new descriptive candidate reason
- removal of noisy candidate reasons
- small label-override refinement

Not allowed:
- weighted scoring formulas
- hidden heuristics
- probabilistic ranking
- inferred market quality

---

## Required comparison

M12 must include a file-based comparison between selector v1 and selector v2.

The comparison should answer:
- how many records changed class
- class delta distribution
- how many moved:
  - review_now → review_if_time
  - review_if_time → ignore_for_now
  - ignore_for_now → review_if_time
  - etc.
- how many label-influenced records changed class
- whether queue sizes got smaller or larger

Comparison must remain aggregate-only.

---

## Success criteria

M12 is successful if:
- selector v2 runs offline without error
- selector v2 output is deterministic
- rule differences from v1 are documented clearly
- comparison output is useful and concise
- no execution logic is introduced

---

## Failure criteria

M12 is failing if:
- selector v2 becomes harder to understand than v1
- too many rules are added
- labels overpower structural data
- changes are not supported by observed workflow evidence
- output changes with no usable comparison

---

## Constraints

- keep Python as the implementation language
- keep selector self-contained
- do not refactor scorer, screener, reviewkit, candidateaudit, reviewfeedback, audit, or console unless strictly necessary
- keep code and docs in English
- prefer explicit class changes over complex logic

---

## Risks

### Risk: selector v2 becomes arbitrary
Mitigation:
- tie each rule change to a clearly observed workflow issue

### Risk: labels become pseudo-ground-truth
Mitigation:
- labels may only influence selection in narrow, documented ways

### Risk: comparison output becomes noisy
Mitigation:
- keep comparison aggregate-only

### Risk: M12 turns into prediction logic
Mitigation:
- forbid any market outcome or performance-based heuristics

---

## Deliverables

M12 should produce:
- selector v2 implementation
- selector v2 output file
- selector v1 vs v2 comparison report
- updated manual verification steps
- clear documentation of rule changes

---

## Final rule

M12 must remain a small, explainable selector refinement step based on review workflow evidence.
It must not become trading logic or execution.