# M3 Plan

## Milestone name
M3 - Scorer v0

## Objective
Build the first simple, explainable scorer on top of snapshot data.

The scorer must not predict market outcomes.
The scorer must not make execution decisions.
The scorer must only evaluate the quality and completeness of collected lifecycle data using explicit rules.

---

## Why M3 exists

M1 established create-event collection.
M2 established migration detection and feature snapshots.

That gives the project enough structure to build the first scoring layer.

M3 exists to:
- turn raw snapshots into structured evaluations
- define a first explicit scoring model
- create a base for future filtering and ranking
- keep scoring interpretable and easy to verify

The goal is not intelligence.
The goal is consistency.

---

## M3 scope

### In scope
- read snapshot records from local JSONL
- apply explicit scoring rules
- produce scored snapshot records
- include score reasons in output
- keep scoring deterministic and explainable
- document manual verification

### Out of scope
- execution logic
- trade entry rules
- order routing
- model training
- machine learning
- external APIs
- social sentiment scoring
- real-time scoring
- dashboards
- database storage
- backtesting
- portfolio logic

---

## Input and output

### Input
`data/snapshots.jsonl`

### Output
`data/scored_snapshots.jsonl`

The scorer is offline and repeatable.
It reads snapshots and overwrites the scored output file.

---

## Scoring philosophy

The scorer should reward:
- presence of expected lifecycle data
- internal consistency
- useful completeness of collected fields

The scorer should penalize:
- missing important fields
- inconsistent lifecycle structure
- suspicious duplication patterns
- incomplete snapshot information

This scorer is not a profitability score.
It is a data-quality and lifecycle-structure score.

---

## Candidate score fields

The scored record should include:
- all original snapshot fields
- score_version
- score_total
- score_reasons
- score_flags

### Example derived checks
- has_create_event
- has_migration_event
- creator_present
- token_standard_known
- bonding_curve_present
- migration_target_present
- create_event_count_ok
- migration_event_count_ok
- lifecycle_order_valid

Only include checks that are directly explainable from snapshot fields.

---

## Example scoring approach

Start with a small fixed-point system.

Example:
- +2 if create data exists
- +2 if creator is present
- +1 if token standard is known
- +1 if bonding curve is present
- +2 if migration exists
- +1 if migration target is present
- +1 if create event count looks normal
- +1 if migration event count looks normal
- -2 if lifecycle order is invalid

This is just an example shape.
The final rule set should remain simple and explicit.

---

## Scoring output requirements

Each scored record must show:
- final numeric score
- score version
- list of reasons
- list of flags or warnings

A human should be able to inspect one record and understand why it got its score.

No hidden weighting.
No black-box logic.

---

## Success criteria

M3 is successful if:
- snapshots can be scored offline without errors
- scored output is deterministic
- score rules are documented and understandable
- reasons and flags are visible in each record
- manual verification is practical
- no execution logic is introduced

---

## Failure criteria

M3 is failing if:
- score logic becomes opaque
- too many derived assumptions are introduced
- scoring turns into prediction
- output cannot explain why a record got its score
- project scope drifts into trading logic
- scoring depends on external or unstable data

---

## Constraints

- keep Python as the implementation language
- keep scorer offline
- do not refactor collector modules unless strictly necessary
- keep storage as JSONL
- keep code and docs in English
- prefer simple rules over ambitious ones

---

## Risks

### Risk: score is confused with trade quality
Mitigation:
- document clearly that this is a structural score, not a buy signal

### Risk: too many rules too early
Mitigation:
- keep v0 small and transparent

### Risk: poor explanation of score output
Mitigation:
- require score reasons and flags in every record

### Risk: scope drifts into ranking engine design
Mitigation:
- scorer only reads snapshots and writes scored snapshots

---

## Deliverables

M3 should produce:
- scorer input/output models if needed
- offline scorer entrypoint
- scored snapshot output file
- documented score rules
- manual verification steps

---

## Final rule

M3 must remain a simple, explainable offline scoring layer.
It is not a trading engine and not a prediction system.