# M7 Plan

## Milestone name
M7 - Scorer v1

## Objective
Build the first evidence-informed update to the scorer by refining the existing rule set using current dataset patterns, audit output, and manual labels.

M7 is not a trading engine.
M7 is not a prediction model.
M7 is not machine learning.

M7 should improve scorer usefulness while staying:
- offline
- deterministic
- explainable
- small in scope

---

## Why M7 exists

M3 delivered scorer v0.
M4 and M5 made the scored output easier to inspect, filter, and label.
M6 added dataset audit visibility.

That means the project now has enough feedback to improve the scorer based on observed data rather than assumptions alone.

M7 exists to:
- refine weak or overly generic score rules
- improve explanation quality
- make scorer output more aligned with real observed data conditions
- introduce a controlled comparison between scorer v0 and scorer v1

The goal is not complexity.
The goal is better signal hygiene.

---

## M7 scope

### In scope
- define a scorer v1 rule set
- keep scorer offline and deterministic
- compare v0 and v1 outputs on the same input snapshots
- preserve explainability
- write scored output for v1 to a separate file
- document rule differences and expected impact

### Out of scope
- execution logic
- trade signals
- market prediction
- machine learning
- external APIs
- database storage
- real-time scoring
- dashboard work
- automatic parameter tuning
- strategy backtesting

---

## Inputs and outputs

### Inputs
- `data/snapshots.jsonl`
- optional analysis context from:
  - `data/reports/dataset_audit.json`
  - `data/labels/review_labels.jsonl`

### Outputs
- `data/scored_snapshots_v1.jsonl`
- optional comparison output:
  - `data/reports/scorer_v0_vs_v1.json`

Do not overwrite v0 output.

---

## Scoring philosophy

Scorer v1 should remain a structural and data-quality score.

It may become more useful and more nuanced than v0, but it must still:
- use explicit rules
- expose reasons and flags
- remain human-auditable
- avoid pretending to measure profitability

This is still not a buy/sell score.

---

## Candidate improvement directions

Possible improvement directions for v1:

### 1. Better treatment of migration-only records
Current migration-only records can score partially but often represent incomplete lifecycle coverage.
v1 may make this more explicit through:
- a dedicated flag
- a dedicated penalty
- or clearer reasons

### 2. Better distinction between completeness and consistency
Some v0 rules may mix "data exists" and "data is coherent".
v1 should keep these concepts cleaner.

### 3. Better use of labels as evaluation context
Labels do not directly change score in v1, but they can inform which patterns deserve stronger or weaker handling.

### 4. Cleaner explanation output
Reasons and flags should remain concise and easier to interpret during manual review.

### 5. Rule pruning
If a v0 rule adds noise and little value, remove or simplify it instead of piling on more rules.

---

## Guardrails for v1

- add at most 2 to 5 rule changes total
- prefer modifying existing rules over adding many new ones
- do not introduce hidden weighting
- keep point values simple integers
- document exactly what changed from v0
- preserve `score_version`
- keep output schema stable unless there is a strong reason to extend it

---

## Required comparison

M7 must include a simple comparison between v0 and v1.

The comparison should answer:
- how many records changed score
- how many records changed flags
- how many records changed score band after re-screening
- what the most common score deltas are

If possible, comparison should remain file-based and offline.

---

## Success criteria

M7 is successful if:
- scorer v1 runs offline without error
- v1 is deterministic
- v1 differences from v0 are explicitly documented
- comparison output is usable
- reasons and flags remain explainable
- no execution logic is introduced

---

## Failure criteria

M7 is failing if:
- scorer v1 becomes harder to understand than v0
- too many new rules are added
- rule changes are not justified by observed data
- output changes but no comparison is provided
- scope drifts into prediction or trading logic

---

## Constraints

- keep Python as the implementation language
- keep scorer self-contained
- do not refactor collector, screener, reviewkit, or audit unless strictly necessary
- keep storage as JSONL and simple report files
- keep code and docs in English
- prefer explicit comparisons over interpretive commentary

---

## Risks

### Risk: v1 becomes arbitrary
Mitigation:
- tie every rule change to a documented observed issue from current data

### Risk: labels are overused as pseudo-ground-truth
Mitigation:
- labels may inform evaluation, not directly define score logic

### Risk: too many rule changes obscure causality
Mitigation:
- cap changes to a small number and document each one clearly

### Risk: comparison output becomes verbose
Mitigation:
- keep comparison focused on deltas and counts

---

## Deliverables

M7 should produce:
- scorer v1 implementation
- v1 output file
- v0 vs v1 comparison output
- updated manual verification steps
- clear documentation of rule changes

---

## Final rule

M7 must remain a small, explainable scorer refinement step based on evidence from the current dataset.
It must not become a prediction layer or trading engine.