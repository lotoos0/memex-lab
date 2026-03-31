# M8 Plan

## Milestone name
M8 - Candidate Selection Layer

## Objective
Add a thin offline candidate-selection layer that turns scored and screened records into a short list of human-review candidates.

M8 is not a trading engine.
M8 is not a buy/sell signal system.
M8 is not a prediction model.

M8 should answer:
- which records are worth further manual review
- which records are lower priority but still potentially useful
- which records should be ignored for now

---

## Why M8 exists

The project already has:
- collection
- migration detection
- snapshots
- scorer v0 and v1
- screener
- labeling and export tools
- audit

That means the project can already collect, summarize, score, classify, and audit records.

What it still lacks is a final human-facing shortlist layer.

M8 exists to:
- reduce review noise
- surface more relevant records
- create a small and explicit triage layer
- prepare a cleaner bridge toward later decision workflows

The goal is not automation.
The goal is better candidate selection for manual review.

---

## M8 scope

### In scope
- read scored and/or screened records
- assign a simple review priority class
- produce candidate output records
- keep the logic explicit and explainable
- support concise summary output
- document manual verification

### Out of scope
- execution logic
- buy/sell decisions
- market prediction
- external APIs
- databases
- real-time alerts
- automatic trade entry
- machine learning
- portfolio logic
- strategy backtesting

---

## Inputs and outputs

### Inputs
Primary input:
- `data/filtered_snapshots_v1.jsonl`

Optional context:
- `data/labels/review_labels.jsonl`
- `data/reports/dataset_audit.json`

M8 should work even if optional context files are absent.

### Outputs
- `data/review_candidates.jsonl`
- concise stdout summary

No mutation of source files.

---

## Selection philosophy

Candidate selection is not trade recommendation.

It should only classify records into review priority buckets based on:
- score quality
- blocking flags
- completeness
- migration-only status
- obvious data gaps
- optionally prior labels

No hidden weighting.
No fuzzy ranking.
No trade language.

---

## Candidate classes

Start with exactly three classes:

### 1. review_now
Use for records that look structurally strong and worth immediate human attention.

### 2. review_if_time
Use for records that are incomplete but still potentially worth a look.

### 3. ignore_for_now
Use for records with obvious data quality or lifecycle issues that do not justify current review time.

These are priority classes, not predictions.

---

## Candidate selection rules

The first rule set should remain simple and explicit.

Examples of acceptable direction:
- `review_now`
  - quality_band = strong
  - no blocking flags
  - not migration_only
- `review_if_time`
  - quality_band = partial
  - no blocking flags
  - or manually labeled as interesting
- `ignore_for_now`
  - blocking flags present
  - migration_only
  - severe missing lifecycle coverage
  - manually labeled as suspect

The exact rules should stay small and deterministic.

---

## Label interaction

Labels may influence priority, but only in a limited and explicit way.

Allowed examples:
- label `interesting` can raise a record from `review_if_time` to `review_now`
- label `suspect` can force `ignore_for_now`

Labels must not create complex weighting.
No multi-label reasoning.

---

## Output requirements

Each candidate record should include:
- all original filtered fields needed for review context
- candidate_class
- candidate_reasons
- selection_version

The output must remain inspectable and explainable.

---

## Summary/report requirements

Stdout should include:
- total records processed
- count by candidate_class
- count of label-influenced selections
- output path

Keep it concise.

---

## Success criteria

M8 is successful if:
- candidate selection runs offline without error
- output is deterministic
- classes are explainable
- the shortlist is narrower and more useful than raw filtered data
- optional labels are handled gracefully
- no source files are modified

---

## Failure criteria

M8 is failing if:
- classes start pretending to be trade signals
- logic becomes opaque
- too many rules are introduced
- labels become pseudo-ground-truth
- output is not meaningfully easier to review
- scope drifts into execution or prediction

---

## Constraints

- keep Python as the implementation language
- keep the layer offline
- do not refactor collector, scorer, screener, reviewkit, or audit unless strictly necessary
- keep code and docs in English
- prefer simple class assignment over ranking formulas

---

## Risks

### Risk: candidate classes are mistaken for trading signals
Mitigation:
- use review-oriented language only
- document clearly that this is manual-review prioritization

### Risk: labels overpower structural data
Mitigation:
- keep label effects small and explicit

### Risk: too many records still end up in review_now
Mitigation:
- keep review_now criteria strict

### Risk: candidate logic duplicates screener semantics without adding value
Mitigation:
- focus on review priority, not on repeating band names

---

## Deliverables

M8 should produce:
- one offline candidate-selection entrypoint
- one candidate output file
- one concise stdout summary
- updated manual verification steps

---

## Final rule

M8 must remain a human-review prioritization layer.
It must not become a trading signal or execution system.