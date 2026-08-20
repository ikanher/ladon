## 1. Populate Complete Dependency Evidence

- [x] 1.1 Map semantic extraction dependency frames into symbols and constrained type/value dependency rows without report-oriented truncation.
- [x] 1.2 Insert external targets as symbol-frontier rows and reconcile per-module dependency counts and completeness.

## 2. Implement Reverse Consumer Queries

- [x] 2.1 Add exact declaration/symbol resolution with ambiguity, missing, stale, external, and ownership diagnostics.
- [x] 2.2 Add `proof_search_consumers.py` using the target-symbol covering index and bounded joins to source declarations/modules/locations.
- [x] 2.3 Add `proof-search consumers` parsing for declaration, dependency kind, ownership, scope, limit, freshness, and output bounds.
- [x] 2.4 Emit `ladon-proof-consumers-result-v1` with separate type/value results, coverage, omissions, bounds, and nonclaims.

## 3. Test Completeness And Plans

- [x] 3.1 Add direct type user, value/proof-body user, generated consumer, dependency consumer, and external target fixtures.
- [x] 3.2 Test confirmed empty only under complete current coverage and partial/unavailable results otherwise.
- [x] 3.3 Assert one indexed reverse lookup plus bounded set-oriented joins and constant statement count as consumers grow.

## 4. Verify The Packet

- [x] 4.1 Run schema/extraction/consumer, installed text/JSON, query-plan/count, deterministic/bounds, compile/quality, strict validation, and `git diff --check` gates.
