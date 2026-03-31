# M11 Plan

## Milestone name
M11 - Ops Console v0

## Objective
Add a small local operations console that makes the existing pipeline easier to run and inspect without replacing the command-line tools.

M11 is not a new scoring engine.
M11 is not a dashboard product.
M11 is not a trading terminal.

M11 should provide a thin GUI wrapper around the current offline workflow.

---

## Why M11 exists

The project already has multiple offline tools:
- scorer
- screener
- reviewkit
- audit
- selector
- candidateaudit
- reviewfeedback

That is good for architecture, but it creates operational friction.

M11 exists to:
- reduce command-line repetition
- make the current workflow easier to run
- give a simple status view of input/output files
- support basic manual labeling and review outcome recording

The goal is not a full interface.
The goal is lower operational friction.

---

## M11 scope

### In scope
- launch existing pipeline commands from a local GUI
- show simple file/status information
- show the latest stdout output of executed actions
- provide a small form for label and review outcome actions
- keep the GUI thin and operational

### Out of scope
- reimplementing scoring logic in GUI
- reimplementing selector logic in GUI
- charts
- dashboards
- live updates
- networking
- web app deployment
- authentication
- database integration
- execution logic
- trading signals

---

## GUI philosophy

The GUI must call the existing tools.
It must not become a second implementation of the pipeline.

The GUI should:
- execute commands
- show status
- show paths
- allow a few common manual actions

The CLI remains the source of truth.

---

## Technology choice

Use:
- Python
- Tkinter

Why:
- standard library
- low setup cost
- enough for buttons, status text, and small forms
- no need for heavier GUI frameworks

Do not use:
- PyQt / PySide
- Electron
- web frameworks

---

## Required features

### 1. Run actions
Buttons for the most common commands:
- scorer v0
- scorer v1
- screener v1 input flow
- selector
- candidateaudit
- reviewfeedback report

Optional if simple:
- reviewkit report

### 2. File status panel
Display for key files:
- whether the file exists
- last modified timestamp
- maybe file size
- maybe line count if cheap

Target files:
- data/scored_snapshots.jsonl
- data/scored_snapshots_v1.jsonl
- data/filtered_snapshots_v1.jsonl
- data/review_candidates.jsonl
- data/reports/candidate_audit.json
- data/reports/review_feedback_report.json

### 3. Output panel
A text box showing:
- last command run
- exit status
- stdout/stderr summary

No full logging system required.

### 4. Label form
Minimal form:
- mint
- label
- note
- submit button

This should call the existing label command, not write files directly.

### 5. Review outcome form
Minimal form:
- mint
- outcome
- note
- submit button

This should call the existing reviewfeedback record command, not write files directly.

---

## User flow

A typical use case should be:

1. run scorer v1
2. run screener on v1
3. run selector
4. inspect file statuses
5. add label or review outcome
6. run candidateaudit or reviewfeedback report
7. inspect latest output summary

That is enough for v0.

---

## Success criteria

M11 is successful if:
- the GUI launches locally without error
- key pipeline commands can be triggered from the GUI
- file status is visible and useful
- label and review outcome actions work through the GUI
- the GUI remains thin and does not duplicate business logic
- no source pipeline behavior is changed

---

## Failure criteria

M11 is failing if:
- the GUI duplicates pipeline logic
- the GUI becomes large and fragile
- command execution is opaque
- manual actions bypass the existing tools
- scope drifts into dashboard or trading UI work

---

## Constraints

- keep Python as the implementation language
- use Tkinter only
- do not refactor scorer, screener, selector, reviewkit, candidateaudit, or reviewfeedback unless strictly necessary
- keep code and docs in English
- prefer a simple single-window layout

---

## Risks

### Risk: GUI becomes a second source of truth
Mitigation:
- all actions must call existing CLI tools

### Risk: status becomes stale
Mitigation:
- add a manual refresh button
- do not promise live updates in v0

### Risk: output panel becomes noisy
Mitigation:
- show only the latest run result in v0

### Risk: too many buttons make it messy
Mitigation:
- only expose the most common actions

---

## Deliverables

M11 should produce:
- one local GUI entrypoint
- one simple single-window Tkinter interface
- one minimal operations flow for the current pipeline
- updated manual verification steps

---

## Final rule

M11 must remain a thin local operations console.
It must not become a new implementation of pipeline logic, a dashboard, or a trading interface.