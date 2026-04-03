# M17 Plan

## Milestone name
M17 - Review Queue UX

## Objective
Improve the manual review loop by making review queue records easier to inspect and action from the local console, without changing scoring, selection, or workflow logic.

M17 is not a new selector.
M17 is not a dashboard rewrite.
M17 is not an execution layer.

M17 should reduce manual friction in the final review step.

---

## Why M17 exists

The project already has:
- review queues
- label and review outcome tools
- a local ops console
- orchestrated workflows

That means the system can already produce review candidates and run the review pipeline end to end.

What still creates friction is the manual review step itself:
- finding the next record to inspect
- copying mint values
- applying labels and outcomes
- moving through the queue efficiently

M17 exists to:
- make queue records visible in the console
- reduce mint copy/paste friction
- make label/outcome actions faster
- improve the review loop for the human operator

The goal is not new analysis.
The goal is faster manual review.

---

## M17 scope

### In scope
- load review queue records into the console
- show a simple list of queue items
- allow selecting one queue item
- populate label/outcome forms from the selected record
- optionally support moving to the next item after action submission

### Out of scope
- editing queue files directly
- reordering queue files
- changing selector logic
- changing scorer logic
- charts
- dashboards
- live updates
- search across all data files
- new workflow definitions

---

## Review UX philosophy

The queue viewer must remain thin.

It should:
- read existing queue files
- show enough context to act
- help the user submit existing actions faster

It must not:
- reimplement selector reasoning
- maintain a second queue state
- write queue files directly

The queue files remain the source of truth.

---

## Required features

### 1. Queue source toggle
Support loading one of:
- `data/review_queue_now_v2.jsonl`
- `data/review_queue_if_time_v2.jsonl`

Simple toggle or dropdown is enough.

### 2. Queue list
Show a simple list of queue records in the console.

Each item should show compact identifying info, for example:
- mint
- candidate_class
- quality_band
- score_total
- optional label if present

No table/grid library. Keep it simple.

### 3. Record detail preview
When a record is selected, show a small read-only detail area with:
- mint
- candidate_class
- quality_band
- score_total
- score_flags
- candidate_reasons
- label if present

No JSON editor. Read-only only.

### 4. Form autofill
When a queue item is selected:
- label form mint field is auto-filled
- outcome form mint field is auto-filled

Optional:
- if label exists, preselect it in the label dropdown

### 5. Optional next-item helper
After a successful label or outcome submission:
- optionally move selection to the next queue item

This should be small and explicit, not smart.

---

## UI constraints

Keep the current console layout intact as much as possible.

Allowed additions:
- one queue section
- one detail preview section
- minimal controls for queue source and refresh

Do not add:
- tabs
- multiple windows
- drag-and-drop
- inline editing of queue files
- complex queue filters

---

## Success criteria

M17 is successful if:
- queue items can be loaded and selected in the console
- record details are visible without opening files manually
- selecting a record reduces label/outcome entry friction
- existing tools are still used for label/outcome submission
- no queue logic is duplicated

---

## Failure criteria

M17 is failing if:
- console starts maintaining its own queue state beyond simple selection
- queue rendering becomes a mini-dashboard
- forms bypass existing reviewkit/reviewfeedback tools
- scope drifts into selection logic or record editing

---

## Constraints

- keep Python as the implementation language
- keep Tkinter as the GUI technology
- do not modify selector, scorer, candidateaudit, reviewfeedback, or orchestrator unless strictly necessary
- keep code and docs in English
- prefer simple list/detail UI over complex widgets

---

## Risks

### Risk: queue display becomes cluttered
Mitigation:
- show only the most useful fields
- keep preview read-only

### Risk: queue selection gets out of sync with file contents
Mitigation:
- provide manual refresh
- no live polling in v0

### Risk: form autofill feels like hidden state
Mitigation:
- keep selected mint visible and explicit in the UI

### Risk: too much convenience invites logic creep
Mitigation:
- only support viewing, selecting, and form prefill

---

## Deliverables

M17 should produce:
- console support for loading review queue records
- simple queue list + detail preview
- mint autofill into label/outcome forms
- updated manual verification steps

---

## Final rule

M17 must remain a thin review UX improvement layer over existing queue files and existing tools.
It must not become a second queue engine or a dashboard.