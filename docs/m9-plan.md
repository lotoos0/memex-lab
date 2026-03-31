# M9 Plan

## Milestone name
M9 - Candidate Audit and Review Workflow

## Objective
Add a thin offline layer that audits candidate-selection output and prepares simple review queues for manual inspection.

M9 is not a trading engine.
M9 is not a prediction layer.
M9 is not automated decision-making.

M9 should answer:
- how candidate classes are distributed
- how they relate to labels and data quality
- whether `review_now` and `review_if_time` look operationally useful
- how to turn candidate output into a practical manual review flow

---

## Why M9 exists

The project already has:
- collection
- migration detection
- snapshots
- scorer v0 and v1
- screener
- reviewkit
- dataset audit
- candidate selection

That means the project can already produce a shortlist of records for manual review.

What it still lacks is a validation and workflow layer for that shortlist.

M9 exists to:
- audit candidate-class usefulness
- create review queues from candidate output
- check whether labels and candidate classes align in a meaningful way
- support a better human review loop

The goal is not more automation.
The goal is to validate and operationalize the review shortlist.

---

## M9 scope

### In scope
- read candidate output records
- optionally read labels
- produce a candidate audit summary
- produce explicit review queue outputs
- keep the logic descriptive and deterministic
- document manual verification

### Out of scope
- execution logic
- trade signals
- automatic trade entry
- real-time notifications
- external APIs
- databases
- machine learning
- ranking formulas
- backtesting

---

## Inputs and outputs

### Inputs
- `data/review_candidates.jsonl`
- optional: `data/labels/review_labels.jsonl`

### Outputs
- `data/reports/candidate_audit.json`
- `data/review_queue_now.jsonl`
- `data/review_queue_if_time.jsonl`
- concise stdout summary

No mutation of source files.

---

## Candidate audit philosophy

This layer should not reinterpret market behavior.

It should only describe:
- how candidate classes are distributed
- how labels align with classes
- how many records are structurally stronger or weaker within each class
- whether review queues are small enough to be useful

No score changes.
No selector changes.
No prediction.

---

## Required audit sections

### 1. Candidate totals
- total_records
- total_review_now
- total_review_if_time
- total_ignore_for_now
- total_labeled_records

### 2. Candidate class distribution
- count by candidate_class
- percentage by candidate_class

### 3. Class × label alignment
If labels exist:
- count of labels within each candidate_class
- count of `interesting` in `review_now`
- count of `suspect` in `ignore_for_now`
- count of unlabeled records in `review_now`

### 4. Class × quality context
- candidate_class × quality_band
- candidate_class × has_blocking_flags
- candidate_class × has_migrated

### 5. Queue sizes
- record count in `review_queue_now.jsonl`
- record count in `review_queue_if_time.jsonl`

### 6. Optional queue usefulness notes
Simple descriptive notes such as:
- review_now queue is empty
- review_now queue is very large
- review_if_time queue dominates the dataset

These must remain descriptive, not advisory.

---

## Review queue rules

### review_queue_now.jsonl
Contains all records where:
- `candidate_class = review_now`

### review_queue_if_time.jsonl
Contains all records where:
- `candidate_class = review_if_time`

No extra filtering.
No sorting logic beyond stable input order unless clearly justified.

---

## Output requirements

### Human-readable stdout
Keep it short and operational.

Should include:
- total records
- class counts
- label alignment highlights
- queue sizes
- report path

### JSON report
Must contain the full structured candidate audit summary.

---

## Success criteria

M9 is successful if:
- candidate audit runs offline without error
- review queues are written correctly
- output is deterministic
- labels are handled gracefully when absent
- the audit makes candidate usefulness easier to judge
- no source files are modified

---

## Failure criteria

M9 is failing if:
- the audit output is vague or bloated
- the layer starts acting like a strategy engine
- queue outputs mutate source records
- labels absence breaks execution
- candidate usefulness remains unclear after reading the report

---

## Constraints

- keep Python as the implementation language
- keep the layer offline
- do not refactor selector, scorer, screener, reviewkit, or audit unless strictly necessary
- keep code and docs in English
- prefer counters and simple queue extraction over analytics complexity

---

## Risks

### Risk: queues are too large to be useful
Mitigation:
- report queue sizes explicitly

### Risk: labels are too sparse to validate much
Mitigation:
- audit must still run and report useful structural summaries without labels

### Risk: this becomes selector v2 by accident
Mitigation:
- do not change classification rules in M9

### Risk: stdout becomes noisy
Mitigation:
- keep stdout concise and push full detail into JSON report

---

## Deliverables

M9 should produce:
- one offline candidate-audit entrypoint
- one candidate audit report file
- two queue output files
- one concise stdout summary
- updated manual verification steps

---

## Final rule

M9 must remain a descriptive candidate-audit and queue-preparation layer.
It must not become selector v2, trading logic, or execution.