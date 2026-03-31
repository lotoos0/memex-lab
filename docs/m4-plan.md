# M4 Plan

## Milestone name
M4 - Filtering Layer and Score Interpretation

## Objective
Extend scorer v0 output with a simple filtering and interpretation layer that makes scored snapshots easier to use operationally.

M4 is not a trading engine.
M4 is not a prediction system.
M4 is not a real-time alerting layer.

M4 should make the current offline score output more useful, more readable, and easier to inspect in batches.

---

## Why M4 exists

M3 introduced a first explainable scorer.

That is useful, but still raw.

The project now needs a thin interpretation layer that can:
- group records by score quality
- filter records by simple explicit conditions
- produce outputs that are easier to inspect and compare
- preserve explainability

M4 exists to convert "a file full of scores" into "a usable offline filtering layer."

---

## M4 scope

### In scope
- read scored snapshot records from local JSONL
- assign simple score bands or quality classes
- produce filtered output records
- preserve score reasons and flags
- generate a small summary/report for the current run
- document manual verification

### Out of scope
- execution logic
- trade entries
- buy/sell signals
- real-time filtering
- external APIs
- machine learning
- databases
- dashboards
- alerting
- ranking by market opportunity
- portfolio logic

---

## Input and output

### Input
`data/scored_snapshots.jsonl`

### Outputs
- `data/filtered_snapshots.jsonl`
- optional lightweight summary printed to stdout

The filtering layer remains offline and repeatable.

---

## Filtering philosophy

Filtering should not pretend to know what is tradable.

Filtering should only classify records based on:
- score level
- data completeness
- presence of important flags
- basic lifecycle consistency

The purpose is to reduce noise and surface more complete records.

---

## Candidate score bands

Start with a very simple mapping.

Example:
- `weak` = score 0 to 3
- `partial` = score 4 to 6
- `strong` = score 7 to 9

These labels describe data completeness and lifecycle quality, not trade quality.

The final names may be adjusted, but they must remain operational and non-hyped.

---

## Candidate filtering fields

Each filtered record may include:
- all original scored snapshot fields
- quality_band
- is_complete_record
- has_blocking_flags
- filter_version
- filter_reasons

These should be derived explicitly from scored snapshot fields.

---

## Filtering rules direction

Examples:
- classify as `strong` only if score_total is high and blocking flags are absent
- classify as `partial` if useful lifecycle data exists but some fields are missing
- classify as `weak` if the record is sparse or heavily flagged
- mark `is_complete_record` true only when create-side and migration-side essentials exist together
- mark `has_blocking_flags` true when flags indicate lifecycle inconsistency or serious missing data

No hidden weighting.
No complex formula.
No prediction.

---

## Summary/report requirements

The M4 run should print a lightweight summary such as:
- number of records processed
- number of weak / partial / strong records
- number of records with blocking flags
- output path written

This is for observability only.

---

## Success criteria

M4 is successful if:
- scored records can be filtered offline without errors
- filtered output remains explainable
- quality bands are deterministic
- a human can inspect a record and understand why it was classified
- summary output is useful and concise
- no execution logic is introduced

---

## Failure criteria

M4 is failing if:
- quality bands become vague or hype-driven
- filtering starts pretending to be a trade signal
- too many derived assumptions are added
- output becomes harder to inspect
- scope drifts into execution or market prediction
- the implementation depends on external systems

---

## Constraints

- keep Python as the implementation language
- keep filtering offline
- do not refactor collector modules
- do not refactor scorer core unless strictly necessary
- keep storage as JSONL
- keep code and docs in English
- prefer simple classification over ambitious logic

---

## Risks

### Risk: quality band is mistaken for a trade rating
Mitigation:
- document clearly that bands describe record completeness and consistency, not market edge

### Risk: flags become overloaded
Mitigation:
- keep a small distinction between informational flags and blocking flags

### Risk: filter output duplicates too much data without added value
Mitigation:
- only add a few clearly justified derived fields

### Risk: M4 becomes an accidental strategy layer
Mitigation:
- classification must only reflect current scored data, not future expectations

---

## Deliverables

M4 should produce:
- offline filtering entrypoint
- filtered snapshot output file
- simple band/class logic
- concise run summary
- updated manual verification steps

---

## Final rule

M4 must remain a thin interpretation layer over scorer output.
It must not become an execution or prediction system.