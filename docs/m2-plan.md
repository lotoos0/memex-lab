# M2 Plan

## Milestone name
M2 - Migration Detection and First Feature Snapshot

## Objective
Extend the collector so it can detect token migration events and produce the first normalized feature snapshot that can later feed a scorer.

M2 is not about execution.
M2 is not about advanced scoring.
M2 is about improving lifecycle visibility and preparing usable structured inputs.

---

## Why M2 exists

M1 proves that the project can detect and log token creation events.

That is useful, but incomplete.

A token lifecycle collector becomes much more useful once it can also detect a meaningful later-stage event.
Migration is the next logical milestone because it represents a real lifecycle transition and gives the project a second anchor point beyond token birth.

M2 exists to:
- extend lifecycle coverage
- improve collector usefulness
- start defining scorer-ready normalized inputs
- keep progress practical and controlled

---

## M2 scope

### In scope
- detect migration-related events for pump.fun tokens
- define a normalized migration event record
- write migration events to structured local storage
- define the first simple feature snapshot structure
- produce feature snapshots from observed events using explicit rules
- document manual verification steps

### Out of scope
- auto-buy
- auto-sell
- order routing
- portfolio logic
- advanced scoring models
- dashboard UI
- database migration
- production deployment
- multi-platform support
- social sentiment ingestion
- machine learning
- backtesting engine

---

## Recommended implementation order

1. research and confirm the migration signal source
2. define the normalized migration event model
3. implement listen-only migration detection
4. append migration records to local storage
5. define a first feature snapshot structure
6. generate feature snapshots from collected event data
7. write manual verification steps

Do not start with feature engineering before migration detection works.

---

## Event targets for M2

### Primary target
Migration detection

### Secondary target
First feature snapshot generated from collected create and migration data

No additional lifecycle events are required for M2.

---

## First feature snapshot goals

The feature snapshot should be simple and explicit.

It should answer:
- when was the token first seen
- has a migration event been observed
- what token standard was observed at creation
- what known addresses or identifiers were captured
- what lifecycle timestamps are available

This is not a score yet.
This is a structured input layer for future scoring.

---

## Candidate feature fields

Possible initial fields:
- mint
- first_seen_at
- created_at
- migrated_at
- has_migrated
- token_standard
- creator
- bonding_curve
- migration_target
- source_count
- event_count

Only keep fields that can be directly justified by collected data.

Do not invent derived fields without clear value.

---

## Storage direction

Keep storage simple for M2.

Preferred approach:
- continue using JSONL
- either use separate files by event class
- or use one file with a clear event_type field

Do not introduce a database in M2 unless JSONL becomes a concrete blocker.

---

## Success criteria

M2 is successful if:
- the project can detect at least one real migration event
- migration records are stored in a normalized structure
- the first feature snapshot format is documented
- feature snapshots can be built from real collected data
- manual verification is practical and repeatable
- no execution logic is introduced

---

## Failure criteria

M2 is failing if:
- migration detection remains vague or undocumented
- the implementation mixes collector and scorer concerns carelessly
- features are invented without direct event support
- storage becomes overengineered
- scope expands into execution or UI work
- the project adds complexity without better observability

---

## Constraints

- keep Python as the implementation language
- preserve the existing collector-first architecture
- prefer small, testable changes
- do not refactor unrelated M1 code without a concrete reason
- keep code, comments, and docs in English
- avoid unnecessary abstractions

---

## Risks

### Risk: migration signal source is less straightforward than expected
Mitigation:
- verify the source before implementation
- prefer one confirmed source over broad speculative support

### Risk: feature snapshot scope grows too fast
Mitigation:
- keep the first snapshot minimal
- include only directly observable fields

### Risk: event storage becomes inconsistent
Mitigation:
- define normalized models before coding
- keep event_type explicit

### Risk: M2 drifts into scoring work
Mitigation:
- snapshots only, no ranking logic yet

---

## Deliverables

M2 should produce:
- migration event support in the collector
- normalized migration records
- first feature snapshot structure
- manual verification steps
- updated documentation for the new event path

---

## Final rule

M2 must improve lifecycle visibility without turning into a scoring or execution milestone.