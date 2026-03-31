# M14 Plan

## Milestone name
M14 - Selector–Scorer Alignment

## Objective
Evaluate and refine the interaction between scorer v2 and selector v2 so that the two layers are aligned and not redundantly penalizing the same record types.

M14 is not a trading engine.
M14 is not a prediction layer.
M14 is not machine learning.

M14 should answer:
- whether selector v2 is still appropriately strict after scorer v2
- whether some selector v2 rules are now redundant
- whether queue size and composition remain useful after the scorer shift
- whether selector logic can be simplified or slightly relaxed without reintroducing noise

---

## Why M14 exists

M12 introduced selector v2 and made the shortlist precision-first.
M13 introduced scorer v2 and moved most non-migrated records from partial to weak.

That means both layers now penalize broad non-migrated structure:
- scorer v2 lowers their score and band
- selector v2 still explicitly demotes them

M14 exists to:
- check whether both layers are still needed as currently defined
- reduce redundant filtering if possible
- improve consistency between score bands and candidate classes
- preserve shortlist usefulness while simplifying logic where justified

The goal is not a more complicated selector.
The goal is cleaner alignment between upstream scoring and downstream selection.

---

## M14 scope

### In scope
- compare current selector v2 behavior against scorer v2 output
- define a small selector refinement if justified
- preserve explainability
- write selector v3 output to separate files if rule changes are introduced
- compare selector v2 vs selector v3 if a v3 is created

### Out of scope
- execution logic
- trade signals
- market prediction
- machine learning
- external APIs
- databases
- dashboards
- real-time operation
- backtesting

---

## Inputs and outputs

### Inputs
Primary input:
- `data/filtered_snapshots_v1.jsonl`
- optional additional downstream analysis:
  - `data/scored_snapshots_v2.jsonl`
  - `data/review_candidates_v2.jsonl`
  - `data/reports/scorer_v1_vs_v2.json`
  - `data/reports/selector_v1_vs_v2.json`
  - `data/reports/review_feedback_report.json`

### Outputs
If no selector change is justified:
- one alignment report only:
  - `data/reports/selector_scorer_alignment.json`

If a selector refinement is justified:
- `data/review_candidates_v3.jsonl`
- `data/reports/selector_v2_vs_v3.json`
- `data/reports/selector_scorer_alignment.json`

Do not overwrite selector v2 output.

---

## Alignment philosophy

M14 must not assume that more filtering is always better.

It should examine:
- whether weak-band records are already sufficiently deprioritized by scorer v2
- whether selector v2 is still doing necessary work
- whether a lighter or clearer rule set could preserve queue usefulness

The priority is:
- fewer redundant rules
- clearer semantics
- useful shortlist size

This remains manual-review support, not market intelligence.

---

## Decision gate

M14 must first answer a structural question:

### Gate A — keep selector v2 unchanged
If scorer v2 already provides enough separation and selector v2 still produces the most useful shortlist, M14 should stop at an alignment report and no new selector version should be created.

### Gate B — create selector v3
Only if the evidence shows a clear benefit:
- simplify selector rules
- or slightly relax/tighten them
- and produce a measurable improvement in queue composition or review usefulness

No selector v3 should be created just to have a new version number.

---

## Allowed change types

If Gate B is triggered, allowed examples:
- remove one redundant selector reason
- simplify one class-changing rule
- slightly relax one condition if scorer v2 already did part of the filtering
- add a clearer reason string tied to scorer v2 semantics

Not allowed:
- hidden weighting
- probabilistic ranking
- label-heavy selection logic
- market-outcome heuristics
- major rewrite of selector behavior

---

## Required alignment questions

M14 should explicitly answer:

1. After scorer v2, how many records are now weak / partial / strong?
2. How does selector v2 currently distribute those records into:
   - review_now
   - review_if_time
   - ignore_for_now
3. Are there record groups that scorer v2 already downgrades sufficiently, making selector v2 rules redundant?
4. Would changing selector rules improve shortlist usefulness without recreating noise?
5. If a selector v3 is proposed, what exact current-data problem does it solve?

---

## Success criteria

M14 is successful if:
- it produces a clear alignment conclusion
- selector changes are introduced only if justified
- any selector refinement stays small and explainable
- comparison output is useful if v3 is created
- no execution logic is introduced

---

## Failure criteria

M14 is failing if:
- a selector v3 is created without a real current-data justification
- rule changes are made just to look active
- alignment analysis is vague
- scope drifts into trading or prediction

---

## Constraints

- keep Python as the implementation language
- keep selector and scorer self-contained
- do not refactor screener, reviewkit, candidateaudit, reviewfeedback, audit, or console unless strictly necessary
- keep code and docs in English
- prefer explicit comparisons over interpretation-heavy commentary

---

## Risks

### Risk: M14 becomes version churn
Mitigation:
- no selector v3 unless evidence clearly supports it

### Risk: scorer and selector become too tightly coupled
Mitigation:
- alignment may inform simplification, but selector must remain independently explainable

### Risk: conclusions are based on too little reviewed data
Mitigation:
- report current sample size and keep conclusions modest

### Risk: selector relaxation reintroduces queue sprawl
Mitigation:
- require comparison output before accepting any new selector version

---

## Deliverables

M14 should produce either:
- an alignment report only

or, if justified:
- alignment report
- selector v3 implementation
- selector v2 vs v3 comparison
- updated manual verification steps

---

## Final rule

M14 must begin with alignment analysis first.
A new selector version is optional, not mandatory.
If the evidence does not justify change, the correct output of M14 is “keep selector v2 as-is.”