# M10 Plan

## Milestone name
M10 - Review Feedback Loop

## Objective
Add a thin offline feedback layer that captures manual review outcomes for candidate records and summarizes how useful the current candidate-selection process is.

M10 is not a trading engine.
M10 is not a prediction layer.
M10 is not an execution system.

M10 should answer:
- how often `review_now` records are actually useful
- how often `review_if_time` records are noise
- whether labels and candidate classes align with real review outcomes
- where selector logic may be too strict or too loose

---

## Why M10 exists

The project already has:
- collection
- migration detection
- snapshots
- scorer v0 and v1
- screener
- reviewkit
- dataset audit
- candidate selection
- candidate audit and review queues

That means the project can already produce and inspect review candidates.

What it still lacks is a direct feedback loop from real manual review.

M10 exists to:
- capture human review outcomes explicitly
- measure selector usefulness
- create evidence for future selector/scorer changes
- reduce guesswork in future milestone planning

The goal is not more automation.
The goal is a real feedback loop.

---

## M10 scope

### In scope
- store manual review outcomes keyed by mint
- support simple outcome values
- generate a feedback report
- compare candidate_class against actual review outcome
- keep the system offline and deterministic
- document manual verification

### Out of scope
- execution logic
- trade entry logic
- profitability measurement
- real-time feedback
- databases
- external APIs
- machine learning
- automatic selector tuning
- market prediction

---

## Inputs and outputs

### Inputs
- `data/review_candidates.jsonl`
- optional: `data/labels/review_labels.jsonl`
- optional: existing review outcomes file

### Outputs
- `data/review_outcomes.jsonl`
- `data/reports/review_feedback_report.json`
- concise stdout summary

No mutation of source files.
Review outcomes are stored separately.

---

## Feedback philosophy

Review outcomes describe whether a candidate was worth human attention.

They do not describe:
- whether to buy
- whether the market moved up
- whether the token was profitable

This is a review-efficiency signal, not a trading signal.

---

## Allowed outcome values

Use exactly three outcome classes in v0:

### 1. useful
The candidate was worth the review time.

### 2. noise
The candidate was not worth the review time.

### 3. needs_more_context
The candidate could not be judged confidently from the available information.

These outcomes describe review usefulness, not market quality.

---

## Outcome storage rules

- one outcome record per mint
- outcomes stored separately from candidate records
- updates overwrite by mint
- optional note field allowed
- outcome records must remain easy to inspect manually

Suggested schema:
- mint
- candidate_class
- outcome
- note
- reviewed_at

---

## Feedback report requirements

The report should answer:

### 1. Totals
- total_reviewed_records
- total_useful
- total_noise
- total_needs_more_context

### 2. Candidate class × outcome
- review_now × useful/noise/needs_more_context
- review_if_time × useful/noise/needs_more_context
- ignore_for_now × useful/noise/needs_more_context

### 3. Label × outcome
If labels exist:
- interesting × useful/noise/needs_more_context
- suspect × useful/noise/needs_more_context
- review_later × useful/noise/needs_more_context
- incomplete × useful/noise/needs_more_context

### 4. Basic effectiveness indicators
Simple descriptive values such as:
- useful_rate_in_review_now
- noise_rate_in_review_if_time
- unlabeled_reviewed_count

No recommendations, only descriptive metrics.

---

## Workflow requirements

The layer should support a basic manual workflow:
1. select candidate from queue
2. review it manually
3. record outcome
4. re-run feedback report
5. inspect whether selector classes align with outcomes

This process should remain simple.

---

## Success criteria

M10 is successful if:
- outcomes can be recorded offline without error
- outcomes are stored separately and updated by mint
- feedback report is deterministic
- report makes selector usefulness easier to judge
- labels are handled gracefully when absent
- no source files are modified

---

## Failure criteria

M10 is failing if:
- outcomes become bloated or ambiguous
- the report acts like strategy advice
- source files are mutated
- missing labels break the feedback report
- the feedback loop remains too vague to guide later improvements

---

## Constraints

- keep Python as the implementation language
- keep the layer offline
- do not refactor selector, scorer, screener, reviewkit, audit, or candidateaudit unless strictly necessary
- keep code and docs in English
- prefer explicit counts over interpretation

---

## Risks

### Risk: outcomes are confused with trading success
Mitigation:
- document clearly that outcomes measure review usefulness only

### Risk: too few reviewed records make the report weak
Mitigation:
- report still runs and shows low sample size explicitly

### Risk: outcome notes become unstructured clutter
Mitigation:
- keep note optional and short in v0

### Risk: this becomes selector v2 by accident
Mitigation:
- no selector rule changes in M10

---

## Deliverables

M10 should produce:
- one outcome-recording entrypoint
- one feedback report entrypoint
- one feedback report file
- one concise stdout summary
- updated manual verification steps

---

## Final rule

M10 must remain a manual review feedback layer.
It must not become trading logic, selector v2, or execution.