# M13 Plan

## Milestone name
M13 - Scorer v2

## Objective
Build a small feedback-informed refinement of the scorer that improves structural signal quality and aligns better with the current selector and review workflow.

M13 is not a trading engine.
M13 is not a prediction model.
M13 is not machine learning.

M13 should improve the usefulness of scoring while staying:
- offline
- deterministic
- explicit
- explainable

---

## Why M13 exists

The project already has:
- collection
- migration detection
- snapshots
- scorer v0 and v1
- screener
- reviewkit
- dataset audit
- selector v1 and v2
- candidate audit
- review feedback
- ops console

That means the project can already score, screen, shortlist, audit, and review records.

What still needs improvement is the alignment between:
- score quality
- selector behavior
- review outcomes

M13 exists to:
- reduce remaining scorer noise
- tighten structural scoring where current evidence supports it
- better separate review-worthy structure from broad data completeness
- make selector v2 depend less on aggressive cleanup

The goal is not a “smarter” score.
The goal is a cleaner and more useful score.

---

## M13 scope

### In scope
- define scorer v2 rule changes
- preserve scorer explainability
- write scorer v2 output to separate files
- compare scorer v1 vs scorer v2
- optionally re-screen scorer v2 output for analysis

### Out of scope
- execution logic
- trade signals
- profitability scoring
- market prediction
- machine learning
- external APIs
- databases
- dashboards
- real-time scoring
- automatic tuning

---

## Inputs and outputs

### Inputs
Primary input:
- `data/snapshots.jsonl`

Optional context:
- `data/reports/review_feedback_report.json`
- `data/reports/candidate_audit.json`
- `data/labels/review_labels.jsonl`

### Outputs
- `data/scored_snapshots_v2.jsonl`
- `data/reports/scorer_v1_vs_v2.json`

Optional downstream analysis:
- `data/filtered_snapshots_v2.jsonl`

Do not overwrite scorer v1 output.

---

## Scorer philosophy

Scorer v2 must remain a structural and data-quality score.

It should not attempt to answer:
- whether the token is good
- whether the market will move
- whether a trade should be taken

It should only improve:
- quality of structural classification
- usefulness of reasons and flags
- alignment with actual downstream review workflow

This remains an infrastructure score, not a market score.

---

## Guardrails for v2

- change at most 2 to 4 scoring rules total
- prefer modifying existing rules over adding many new ones
- preserve explicit reasons and flags
- keep point values simple integers
- document every change from v1 clearly
- keep the output schema stable unless strongly justified

---

## Candidate improvement directions

Possible improvement directions for scorer v2:

### 1. Better treatment of non-migrated partial structure
If selector v2 has to aggressively demote a broad category, scorer v2 may need to represent that structural weakness more clearly earlier.

### 2. Better separation of completeness and actionability
Some records may be structurally complete enough to score decently, while still being poor candidates for review priority.
Scorer should support this distinction more cleanly.

### 3. Flag cleanup
If some remaining flags are noisy or redundant in current workflow, prune or rename them.

### 4. Better alignment with review feedback
If reviewed records consistently show that certain score patterns lead to `noise`, scorer v2 may reflect that pattern more directly — but only through explicit structural rules, not outcome-driven heuristics.

---

## Allowed change types

Allowed examples:
- remove or tighten a v1 bonus
- add a new descriptive flag
- add a small penalty for a clearly weak structural condition
- rename a reason string for clarity
- prune a flag that adds no review value

Not allowed:
- hidden weighting
- probabilistic scoring
- market-outcome logic
- label-driven scoring
- using `useful` / `noise` directly as score targets

---

## Required comparison

M13 must include a file-based comparison between scorer v1 and scorer v2.

The comparison should answer:
- how many records changed score
- how many records changed flags
- score delta distribution
- which reasons/flags were added or removed most often
- optionally, how screener output would shift after rescoring v2

Comparison must remain aggregate-only.

---

## Success criteria

M13 is successful if:
- scorer v2 runs offline without error
- scorer v2 output is deterministic
- differences from v1 are clearly documented
- comparison output is useful and concise
- no execution logic is introduced

---

## Failure criteria

M13 is failing if:
- scorer v2 is harder to understand than v1
- too many rules are changed at once
- score changes are not justified by current workflow evidence
- output changes but no usable comparison exists
- scope drifts into trading or prediction logic

---

## Constraints

- keep Python as the implementation language
- keep scorer self-contained
- do not refactor selector, screener, reviewkit, candidateaudit, reviewfeedback, audit, or console unless strictly necessary
- keep code and docs in English
- prefer explicit score changes over interpretive commentary

---

## Risks

### Risk: scorer v2 becomes arbitrary
Mitigation:
- tie each change to an observed workflow or audit problem

### Risk: feedback is overused as pseudo-ground-truth
Mitigation:
- feedback may inform rule changes, but not define score labels directly

### Risk: selector and scorer become too tightly coupled
Mitigation:
- scorer changes must stand on structural logic, not selector outcomes alone

### Risk: comparison output becomes noisy
Mitigation:
- keep it aggregate-only and focused on deltas

---

## Deliverables

M13 should produce:
- scorer v2 implementation
- scorer v2 output file
- scorer v1 vs scorer v2 comparison report
- updated manual verification steps
- clear documentation of rule changes

---

## Final rule

M13 must remain a small, explainable scorer refinement step grounded in current review workflow evidence.
It must not become trading logic or prediction.