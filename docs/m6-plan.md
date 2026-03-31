# M6 Plan

## Milestone name
M6 - Dataset Audit Layer

## Objective
Add a thin offline audit layer that summarizes the current dataset and highlights data coverage, completeness, flag frequency, score distribution, and label distribution.

M6 is not a trading engine.
M6 is not a prediction layer.
M6 is not a real-time analytics system.

M6 should help answer:
- what data we actually have
- how complete it is
- where the biggest gaps are
- how labels are distributed across the current dataset

---

## Why M6 exists

The project already has:
- create-event collection
- migration detection
- snapshots
- scorer
- screener
- labeling and export tools

That is enough structure to start auditing the data itself.

M6 exists to:
- reveal data quality patterns
- identify the most common missing fields and flags
- quantify coverage of full lifecycle records
- support future scorer improvements with evidence instead of assumptions

The goal is not more code.
The goal is better visibility into the data.

---

## M6 scope

### In scope
- read current filtered records
- optionally read labels
- generate a deterministic dataset audit summary
- print a concise human-readable report
- write a machine-readable report file
- keep the audit logic simple and explicit

### Out of scope
- execution logic
- market prediction
- real-time dashboards
- external APIs
- databases
- charting libraries
- machine learning
- backtesting
- automatic scorer tuning
- online analytics

---

## Inputs and outputs

### Inputs
- `data/filtered_snapshots.jsonl`
- optional: `data/labels/review_labels.jsonl`

### Outputs
- `data/reports/dataset_audit.json`
- concise stdout summary

No mutation of source files.
No feedback into the pipeline.

---

## Audit philosophy

The audit layer should not interpret the market.
It should only describe the current dataset.

It should answer:
- how many records exist
- how many are weak / partial / strong
- how many have blocking flags
- how many are migrated
- how many appear complete
- what score totals occur most often
- which flags appear most often
- which labels appear most often

No hidden weighting.
No “intelligence”.
No strategy output.

---

## Required audit sections

### 1. Dataset totals
- total_records
- total_labeled_records
- total_migrated_records
- total_blocking_records
- total_complete_records

### 2. Quality distribution
- quality_band counts
- score_total counts

### 3. Lifecycle coverage
- has_migrated true/false counts
- created_at present/missing
- migrated_at present/missing
- full lifecycle count
- migration-only count
- create-only count

### 4. Flag distribution
- count by score_flag
- top most frequent flags

### 5. Missing field distribution
Count missing presence for important fields such as:
- created_at
- creator
- token_standard
- bonding_curve
- migration_target
- snapshot_built_at

### 6. Label distribution
If labels file exists:
- count by label
- count of labeled vs unlabeled records
- optional simple cross-tab:
  - label × quality_band
  - label × has_migrated

If labels file does not exist:
- audit should still run successfully

---

## Output requirements

### Human-readable stdout
Keep it short and operational.

Example sections:
- total records
- quality bands
- migration coverage
- top flags
- labels summary

### JSON report
The JSON report should contain the full structured audit summary.
It should be deterministic and easy to inspect.

---

## Success criteria

M6 is successful if:
- the audit runs offline without error
- the report is deterministic for the same input
- the stdout summary is concise and useful
- the JSON report captures the agreed sections
- labels are handled gracefully when absent
- no upstream files are modified

---

## Failure criteria

M6 is failing if:
- the audit output is vague or hard to inspect
- the module starts inferring market meaning from the data
- source files are mutated
- the report becomes bloated or unreadable
- scope drifts into scoring or execution logic

---

## Constraints

- keep Python as the implementation language
- keep the layer offline
- do not refactor collector, scorer, screener, or reviewkit unless strictly necessary
- prefer JSON output over introducing charts
- keep code and docs in English
- prefer simple counters and summaries over ambitious analytics

---

## Risks

### Risk: audit becomes pseudo-research instead of descriptive reporting
Mitigation:
- keep all outputs descriptive and count-based

### Risk: too many sections reduce readability
Mitigation:
- keep stdout short and JSON detailed

### Risk: labels file may be absent or sparse
Mitigation:
- audit must handle missing labels gracefully

### Risk: this becomes scorer v1 by accident
Mitigation:
- audit reports on existing fields only, no new scoring logic

---

## Deliverables

M6 should produce:
- one offline audit entrypoint
- one JSON report file
- one concise stdout summary
- updated manual verification steps

---

## Final rule

M6 must remain a descriptive dataset-audit layer.
It must not become scoring, filtering, execution, or market interpretation logic.