# M5 Plan

## Milestone name
M5 - Labeling and Export Layer

## Objective
Add a thin offline data-preparation layer that helps inspect, export, and manually label records produced by the current pipeline.

M5 is not a trading engine.
M5 is not a real-time system.
M5 is not a prediction layer.

M5 should make the existing data easier to review, segment, and reuse for later scorer improvements.

---

## Why M5 exists

The project already has:
- create-event collection
- migration detection
- snapshot building
- scorer v0
- screener v0

That is enough structure to start preparing data for better analysis.

M5 exists to:
- reduce review friction
- make it easier to inspect subsets of records
- support manual labeling
- prepare cleaner inputs for future scorer improvements

The goal is not more automation.
The goal is better data handling.

---

## M5 scope

### In scope
- export subsets of existing records using explicit offline filters
- support simple manual labeling
- generate small summary reports from current JSONL files
- optionally export to CSV when clearly useful
- keep the layer deterministic and explainable

### Out of scope
- execution logic
- real-time alerting
- trading signals
- machine learning
- external APIs
- databases
- dashboards
- online annotation tools
- backtesting
- portfolio logic

---

## Input and output

### Inputs
Possible inputs:
- `data/snapshots.jsonl`
- `data/scored_snapshots.jsonl`
- `data/filtered_snapshots.jsonl`

### Outputs
Possible outputs:
- `data/exports/*.jsonl`
- `data/exports/*.csv`
- `data/labels/*.jsonl`
- concise stdout summaries

The exact file set should remain minimal and justified.

---

## Layer philosophy

This layer should not change the upstream data.
It should:
- read existing files
- produce derived exports
- store labels separately
- keep manual work reversible and inspectable

No hidden mutation.
No implicit state.
No silent overwrites without being explicit.

---

## Candidate features

### 1. Export subsets
Examples:
- export only `quality_band=strong`
- export only `has_migrated=true`
- export only records with no blocking flags
- export only `partial` records for review

### 2. Manual labeling
Support simple labels such as:
- `interesting`
- `incomplete`
- `suspect`
- `review_later`

Labels should be stored separately from the main pipeline output.

### 3. Summary/report
Examples:
- counts by quality band
- counts by has_migrated
- counts by has_blocking_flags
- counts by label
- counts by score_total

### 4. Sample extraction
Examples:
- random sample of N records
- top N by score_total
- first N matching a simple filter

### 5. Optional CSV export
Only if it makes manual review easier.
Do not add CSV just because it looks useful in theory.

---

## Labeling rules

Labels are human annotations, not model output.

Requirements:
- one record can have zero or one label in v0
- labels are attached by `mint`
- labels must be easy to inspect and edit manually
- labeling must not modify source records
- labels must remain optional

No multi-label taxonomy yet.
No complex annotation schema.

---

## Export rules

Exports must be:
- deterministic
- explicit
- reproducible
- based only on current input data

No fuzzy logic.
No hidden filtering.

Every export should clearly state:
- input file
- filter used
- output file

---

## Success criteria

M5 is successful if:
- records can be exported by simple explicit conditions
- manual labels can be stored separately and reused
- summary output is useful and concise
- data remains easy to inspect
- no upstream files are mutated
- no execution logic is introduced

---

## Failure criteria

M5 is failing if:
- labeling becomes too complex
- exports are hard to reproduce
- the layer silently changes source data
- output sprawl grows without clear value
- scope drifts into strategy or execution logic
- manual review becomes harder, not easier

---

## Constraints

- keep Python as the implementation language
- keep the layer offline
- do not refactor collector, scorer, or screener unless strictly necessary
- prefer JSONL first
- only add CSV if there is a clear manual-review benefit
- keep code and docs in English
- prefer small tools over a large framework

---

## Risks

### Risk: label schema grows too early
Mitigation:
- keep labels single-value and optional in v0

### Risk: export layer duplicates screener/scorer semantics
Mitigation:
- exports should consume existing fields, not recreate scoring logic

### Risk: too many output files
Mitigation:
- keep output naming simple and constrained

### Risk: this becomes a strategy layer
Mitigation:
- labels and exports describe data, not trading decisions

---

## Deliverables

M5 should produce:
- one offline export entrypoint
- one simple labeling mechanism
- one concise reporting path
- updated manual verification steps

---

## Final rule

M5 must remain a data handling and review layer.
It must not become execution, prediction, or market analysis logic.