# Tech Decision

## Decision
Use Python as the primary language for M1.

## Decision date
2026-03-28

## Context
memex-lab starts with a collector-first milestone.
The immediate goal is not a production trading engine.
The immediate goal is to build and verify a reliable first ingestion path for low market cap Solana memecoin lifecycle data.

## Why Python
Python was chosen because it provides the fastest path to:
- rapid collector prototyping
- event parsing
- structured logging
- JSONL / CSV / SQLite storage
- quick manual verification
- easy iteration during the early research phase

Python also keeps the first milestone simple and lowers friction while the project is still defining its event model and collector boundaries.

## Why not TypeScript for M1
TypeScript may become useful later, especially if:
- the project grows into a service-oriented backend
- Solana-specific JS tooling becomes a stronger requirement
- a richer API or UI layer is introduced

However, TypeScript is not the best choice for the first milestone because M1 prioritizes speed of iteration and collector observability over long-term production structure.

## Trade-offs
Python advantages:
- fast setup
- low friction for experimentation
- strong fit for ingestion and data shaping

Python disadvantages:
- less strict typing by default
- may need later refactoring if the system grows significantly
- may not align with every Solana tooling example

These trade-offs are acceptable for M1.

## Revisit point
Re-evaluate the language decision after:
- M1 collector is working end-to-end
- the normalized event model is stable
- M2 scoring requirements are clearer

## Final rule
Do not reopen this decision during M1 unless Python creates a concrete blocker.