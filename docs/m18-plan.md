# M18 Plan

## Milestone name
M18 - Review Export

## Objective
Add a thin export layer for review-ready records so the current shortlist can be extracted into a compact, research-friendly format without changing selector, candidateaudit, or queue logic.

M18 is not a new selector.
M18 is not a data warehouse.
M18 is not a dashboard.

M18 should make it easier to take the current review output and use it outside the console.

---

## Why M18 exists

The system already produces:
- candidate files
- review queues
- audits
- feedback
- console-based review UX

That is enough for operating inside the system.

What is still weak is handoff:
- getting a clean shortlist out
- sharing a review subset
- taking the most relevant fields into a separate research step

M18 exists to:
- export review-ready subsets cleanly
- reduce manual JSONL digging
- make shortlist handoff easier
- preserve the existing review workflow

The goal is not more analysis.
The goal is cleaner output for downstream human research.

---

## M18 scope

### In scope
- export current review queue records into compact files
- support at least one machine-friendly format
- support one human-review-friendly format if it is cheap and clearly useful
- keep exports deterministic
- keep export filters explicit and small

### Out of scope
- changing selector logic
- changing queue logic
- editing queue files
- live sync with external tools
- databases
- spreadsheets with formulas
- dashboarding
- remote sharing integrations

---

## Export philosophy

The export layer must not invent new scoring or ranking.

It should:
- read existing review queue files or candidate files
- extract a compact subset of fields
- optionally filter by an explicit queue or class
- write stable export files

It must not:
- reorder by hidden heuristics
- recompute selection
- transform data into opinionated derived metrics

The source data remains the source of truth.

---

## Required exports

### 1. review_now export
Export the current `review_queue_now_v2.jsonl` into a compact handoff format.

### 2. review_if_time export
Export the current `review_queue_if_time_v2.jsonl` into a compact handoff format.

### 3. optional candidate subset export
If cheap and useful, support exporting from `data/review_candidates_v2.jsonl` filtered by candidate class.

---

## Required formats

### Required
- **JSONL** compact export

### Optional, only if cheap and clearly useful
- **CSV** compact export

No Excel generation in M18.
No rich formatting in M18.

---

## Required output fields

Exports should include only the most useful review-facing fields, for example:
- mint
- candidate_class
- quality_band
- score_total
- score_flags
- candidate_reasons
- label
- has_migrated
- selected queue source (if relevant)

Do not dump every field by default.

---

## CLI requirements

The export tool should support:
- choosing the source
- choosing the output path
- choosing the format (`jsonl` required, `csv` optional)
- optional class filter when exporting from candidate files

Example use cases:
- export current review_now queue
- export current review_if_time queue
- export only `review_now` candidates from `review_candidates_v2.jsonl`

No interactive prompts in v0.

---

## Success criteria

M18 is successful if:
- review-ready records can be exported cleanly
- exported output is compact and useful
- the export is deterministic
- no queue or candidate logic is changed
- the handoff is easier than manually digging in JSONL files

---

## Failure criteria

M18 is failing if:
- the export layer starts recomputing selection logic
- output is bloated with irrelevant fields
- too many output formats are added
- scope drifts into spreadsheet/reporting product work
- the export is harder to use than the source files

---

## Constraints

- keep Python as the implementation language
- keep the export layer offline
- do not modify selector, candidateaudit, reviewfeedback, console, or orchestrator unless strictly necessary
- keep code and docs in English
- prefer explicit small export options over flexible but messy interfaces

---

## Risks

### Risk: export schema becomes too wide
Mitigation:
- keep a small fixed field set

### Risk: too many source modes complicate the tool
Mitigation:
- start with queue exports first
- make candidate export optional only if clearly cheap

### Risk: CSV introduces escaping/format edge cases
Mitigation:
- only add CSV if it is very small and clean to support

### Risk: exported files get mistaken for source-of-truth data
Mitigation:
- make the export clearly derivative and compact

---

## Deliverables

M18 should produce:
- one export module
- review queue export support
- compact export schema
- updated manual verification steps

---

## Final rule

M18 must remain a thin derivative export layer over existing review outputs.
It must not become a second analysis or reporting system.