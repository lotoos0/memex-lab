# Project Brief

## Project name
memex-lab

## One-line summary
memex-lab is a staged research and execution framework for low market cap Solana memecoins, starting with a collector-first architecture.

---

## Why this project exists

Most low market cap memecoin trading systems fail for predictable reasons:
- poor visibility into token lifecycle
- weak data quality
- unreliable execution assumptions
- premature automation
- no structured scoring foundation

This project exists to build a cleaner path:
1. collect real-time lifecycle data
2. normalize and store it
3. score tokens in a structured way
4. only later consider execution

The goal is not hype.
The goal is controlled edge discovery.

---

## Primary objective

Build a reliable first-version collector for low market cap Solana memecoin lifecycle data.

The collector must help answer:
- when a token appears
- what lifecycle phase it is in
- what important events happened
- what raw signals are observable early
- what data can later support scoring

---

## Current phase

Phase: M1 - Collector Foundation

This phase focuses on:
- project setup
- repository control
- collector scope definition
- first data pipeline decisions
- first event logging milestone

This phase does not focus on:
- fully automated trading
- advanced strategy logic
- dashboard polish
- prediction models

---

## In scope for M1

- define collector responsibilities
- choose initial implementation language and structure
- define normalized event model
- decide first storage format
- support first real-time event ingestion path
- log basic lifecycle-relevant data
- document setup and manual verification flow

---

## Out of scope for M1

- auto-buy
- auto-sell
- portfolio logic
- position sizing engine
- advanced scoring logic
- production deployment
- multi-exchange support
- sentiment and social media analysis
- complex UI

---

## Success criteria for M1

M1 is successful if:
- the repository has clear project control documents
- collector scope is clearly defined
- one real event ingestion path works end-to-end
- the system can log useful raw lifecycle data
- manual verification steps are documented
- future scorer inputs become clearer after collected samples

---

## Failure criteria for M1

M1 is failing if:
- implementation starts before scope is clear
- collector mixes in execution logic
- raw data is hidden or poorly structured
- no reliable manual verification exists
- the system becomes overengineered before first working ingestion

---

## Project principles

- collector first
- structure before automation
- simple before clever
- observable before optimized
- explainable before powerful
- small steps over large rewrites

---

## Roles

### Human
Owns scope, priorities, and final decisions.

### Claude Code
Plans tasks, reviews changes, identifies risks, and produces test plans.

### Codex
Implements scoped changes, fixes issues, and executes coding tasks.

---

## Development rule

No tool should silently expand scope.

Every meaningful task should answer:
- what is changing
- why it is changing
- how it will be verified
- what remains out of scope

---

## First milestone target

Deliver a collector foundation that can ingest and log a first class of useful real-time Solana memecoin events.

Examples of acceptable early targets:
- new token detection
- lifecycle event logging
- bonding curve progress updates
- migration detection

Only one ingestion path is required for M1.
Depth can come later.

---

## Notes

This project should earn complexity.
It should not start by pretending to be a full trading engine.