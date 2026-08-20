## 1. Define Canonical Search Models

- [x] 1.1 Add immutable canonical goal and state models using exact goal/context/generation/registry fingerprints and multiset normalization.
- [x] 1.2 Add transition/result models for selected goal, verified candidate, substitutions, adapters, residual premises, costs, source anchors, bounds, omissions, and rejection.

## 2. Implement Bounded AND/OR Search

- [x] 2.1 Select one unresolved goal deterministically and obtain bounded SQLite shortlists through the type-search service.
- [x] 2.2 Batch Lean verification and create successors only from verified applications, replacing the selected goal with all residual proof premises.
- [x] 2.3 Implement best-first search using match class, unresolved count/size, adapters, instances, import/ownership, depth, and stable identity costs.
- [x] 2.4 Enforce caps for expanded states, candidates per goal, route depth, unresolved goals, Lean requests, routes, diagnostics, wall time, and output bytes.

## 3. Emit And Replay Routes

- [x] 3.1 Emit accepted/rejected route cards for complete, partial, exhausted, stale, and bounded searches with the omitted frontier.
- [x] 3.2 Add optional supervised scratch-example replay and permit `replayed` only after successful Lean execution.
- [x] 3.3 If enabled, store rejected-route memory only in `.ladon/index/proof-search-history.sqlite` using WAL and every required identity key.

## 4. Test Search Semantics

- [x] 4.1 Test direct close, two-premise AND, competing OR alternatives, cycles, duplicate states, adapters, stale candidates, no route, and each cap.
- [x] 4.2 Assert deterministic route ordering and that lexical/shape candidates never enter a route without verifier evidence.
- [x] 4.3 Test sidecar generation/context isolation, corruption/unavailability fallback, and published-index immutability.

## 5. Verify The Packet

- [x] 5.1 Run bounded-graph, verifier, type/difference/adapter, replay, installed output, process/resource, compile/quality, strict validation, and `git diff --check` gates.
