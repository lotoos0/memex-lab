# M1 Collector Scope

## Objective
Deliver a listen-only collector foundation for low market cap Solana memecoin lifecycle data.

## M1 definition
M1 is complete when one real ingestion path works end-to-end and useful raw lifecycle data is logged in a structured format.

## In scope
- listen to one real event source
- detect at least one meaningful lifecycle event class
- parse event data into a normalized structure
- write raw and/or normalized output to local storage
- provide a runnable entrypoint
- document how to manually verify the result

## Out of scope
- auto-buy
- auto-sell
- strategy execution
- portfolio management
- advanced scoring
- dashboards
- multi-source ingestion
- heavy optimization

## Preferred first ingestion target
Choose one:
1. new token detection
2. bonding curve progress updates
3. migration detection

Only one target is required for M1.

## Recommended M1 target
Start with:
- new token detection
or
- migration detection

These are easier to verify than more complex derived signals.

## Required outputs
The collector must produce:
- timestamps
- source identifier
- event type
- token identifier or equivalent key
- raw payload or essential parsed fields
- error logs when parsing fails

## Storage for M1
Preferred storage order:
1. JSONL
2. SQLite
3. CSV

Default choice for M1:
- JSONL for raw event logging

Reason:
- easy to inspect
- append-friendly
- minimal setup
- good for early debugging

## Manual verification requirement
M1 is not done unless a human can:
- run the collector
- observe event output
- inspect logged records
- confirm that at least one real event path works

## Anti-goals
Avoid:
- abstract frameworks
- early plugin systems
- over-generalized event buses
- premature clean architecture
- fake completeness

## Design rule
Keep M1 simple, direct, and observable.