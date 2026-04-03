# M16 Plan

## Milestone name
M16 - Console + Orchestrator Integration

## Objective
Integrate the existing orchestrator workflows into the local ops console so the user can launch predefined workflows from the GUI without manually switching back to the CLI.

M16 is not a new workflow system.
M16 is not a scheduler.
M16 is not a dashboard rewrite.

M16 should connect the existing console to the existing orchestrator in a thin, explicit way.

---

## Why M16 exists

The project already has:
- a Tkinter ops console
- a CLI orchestrator with predefined workflows

Both are useful, but they are split:
- console is convenient for individual actions
- orchestrator is convenient for ordered multi-step flows

This creates avoidable friction:
- the user must choose between GUI and CLI
- workflows are not visible in the console
- the console cannot currently launch the most useful multi-step paths

M16 exists to:
- reduce tool-switching
- expose orchestrator workflows in the GUI
- keep operational control in one place
- avoid duplicating workflow logic in the console

The goal is not new workflow behavior.
The goal is one control surface.

---

## M16 scope

### In scope
- add orchestrator workflow controls to the console
- show workflow run status in the existing output/log panel
- refresh file status after workflow completion
- keep single-run safety (no overlapping command/workflow starts)

### Out of scope
- editing workflow definitions from the GUI
- background scheduling
- live progress bars
- parallel workflow runs
- workflow history database
- dashboard redesign
- new scoring or selector logic

---

## Integration philosophy

The console must not reimplement workflow sequences.

It should:
- invoke the orchestrator module as a subprocess
- use the same worker-thread subprocess mechanism already used for console commands
- reuse the existing output panel and status refresh behavior

The orchestrator remains the source of truth for workflow definitions.

---

## Required integration features

### 1. Workflow buttons in the console
Expose exactly the existing orchestrator workflows:

- `full_v2_review_flow`
- `refresh_candidates_only`
- `feedback_report_only`

No extra console-only workflows in v0.

### 2. Shared command execution model
Workflow buttons should:
- disable all action buttons during execution
- run through the same background-thread subprocess path as current console commands
- write results to the same output/log panel
- re-enable controls after completion

### 3. Clear output labeling
The output panel should clearly show:
- that a workflow was run
- which workflow name was invoked
- exit code
- orchestrator stdout/stderr

The console should not parse workflow output into custom UI widgets in v0.

### 4. File status refresh
After a workflow completes:
- refresh the existing file status panel
- do not add live polling

### 5. Single active run rule
If a workflow is running:
- no other workflow can start
- no single command can start
- label/outcome submissions are also blocked until completion

This keeps the console behavior consistent and predictable.

---

## UI constraints

Keep the existing console layout structure.
Do not redesign the whole window.

Allowed UI change:
- add a small `WORKFLOWS` section with buttons
or
- extend the existing actions section with a workflow subsection

Do not add:
- tabs
- split windows
- complex workflow panels
- progress bars
- run history lists

---

## Success criteria

M16 is successful if:
- all orchestrator workflows can be launched from the console
- workflows run through the existing subprocess/thread flow
- controls are blocked during execution
- output appears in the same log/output panel
- status refreshes after workflow completion
- no workflow logic is duplicated in the console

---

## Failure criteria

M16 is failing if:
- the console redefines workflow steps instead of calling the orchestrator
- commands and workflows can overlap
- the console grows into a second orchestration system
- the GUI is significantly redesigned just to support workflows
- scope drifts into scheduler or run-history features

---

## Constraints

- keep Python as the implementation language
- keep Tkinter as the GUI technology
- keep orchestrator as the source of truth for workflow definitions
- do not modify scorer, selector, candidateaudit, reviewfeedback, or other pipeline modules unless strictly necessary
- keep code and docs in English
- prefer small UI additions over redesign

---

## Risks

### Risk: console starts duplicating orchestrator logic
Mitigation:
- workflow buttons must call `python -m orchestrator --workflow ...`
- no inline workflow step lists in console code

### Risk: workflow output is verbose in the log panel
Mitigation:
- accept this in v0
- use the existing output panel rather than inventing special rendering

### Risk: blocked UI feels restrictive
Mitigation:
- keep behavior consistent with current “one active run at a time” model

### Risk: workflow names drift between console and orchestrator
Mitigation:
- import or share workflow names from a thin source of truth if possible
- if not, keep the mapping minimal and explicit

---

## Deliverables

M16 should produce:
- console support for launching orchestrator workflows
- updated manual verification steps
- no new pipeline logic
- no new workflow definitions

---

## Final rule

M16 must remain a thin integration layer.
The console may launch workflows, but the orchestrator remains the only place where workflow steps are defined.