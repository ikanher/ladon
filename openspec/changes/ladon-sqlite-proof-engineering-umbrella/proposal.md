## Why

Ladon's SQLite index is fast enough for navigation, but proof engineering still lacks a complete semantic path from deterministic SQL shortlists to Lean-verified applications, residual premises, consumers, constructor coverage, and bounded routes. This umbrella turns `ladon_sqlite_proof_engineering_implementation_plan.md` into ordered, independently reviewable implementation packets while retaining SQLite as the canonical persistent store.

## What Changes

- Establish baseline contracts and measurements before changing public behavior.
- Correct name search, freshness, CLI startup, SQL query counts, graph traversal, and dominators.
- Add schema-v4 semantic storage, a framed Lean extraction protocol, and atomic semantic generations.
- Add Lean-verified type search, premise/goal explanation, reverse consumers, constructor coverage, adapters, and bounded AND/OR planning.
- Finish with installed-command, documentation, skill, fixture, performance, and six-scenario release gates.
- Reconcile the older Lean proof-discovery packets explicitly; this program refines their overlapping P0 concerns and does not create a second proof authority.

## Capabilities

### New Capabilities

- `ladon-proof-search-baselines-and-contracts`: Reproducible contract, SQL-count, latency, size, and regression baselines.
- `ladon-proof-search-name-v2-and-freshness`: Correct normalized name search and verified freshness semantics.
- `ladon-proof-search-cli-and-query-optimization`: Lightweight dispatch and set-oriented lineage/ProofIR queries.
- `ladon-bounded-graph-and-dominators`: Pure bounded traversal and independently tested dominators.
- `ladon-semantic-index-schema-v4`: Constrained and indexed semantic SQLite relations.
- `ladon-lean-semantic-extraction-protocol`: Versioned framed extraction with complete/partial evidence.
- `ladon-semantic-index-build-mode`: Cached semantic extraction and atomic generation publication.
- `ladon-lean-semantic-candidate-verifier`: Batched Lean pattern elaboration and candidate checking.
- `ladon-type-directed-declaration-search`: Deterministic SQL-shortlisted, Lean-verified type search.
- `ladon-premise-goal-difference-analysis`: Residual-premise, mismatch, suggestion, and route-card evidence.
- `ladon-declaration-consumers-query`: Complete reverse type/value consumer queries.
- `ladon-constructor-coverage-and-leakage`: Field coverage and certificate-leakage diagnostics.
- `ladon-semantic-adapter-registry`: Versioned built-in and repository adapter rules checked by Lean.
- `ladon-bounded-proof-route-planner`: Bounded AND/OR search over Lean-verified transitions.
- `ladon-proof-engineering-release-contract`: Installed CLI, docs, skill, acceptance, and release synchronization.

### Modified Capabilities

## Impact

Touches the proof-search SQLite schema and lifecycle, Lean helpers and protocols, installed CLI dispatch, query modules, graph algorithms, public JSON contracts, fixtures, benchmarks, documentation, and the maintained Ladon skill. It introduces no graph database and keeps lexical commands free of implicit Lean execution.
