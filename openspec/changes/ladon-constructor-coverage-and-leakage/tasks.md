## 1. Extend Structure Inspection

- [x] 1.1 Add `inspect-structure` and `instantiate-constructor` protocol models with module, parameters, assumptions, fields, projections, inheritance, source, identities, and bounds.
- [x] 1.2 Implement Lean helper operations that instantiate parameters and emit every unresolved field goal in declaration order.

## 2. Build The Coverage Engine

- [x] 2.1 Add `proof_search_constructor.py` and `proof-search constructor coverage` request validation for module, structure, arguments, assumptions, scope, caps, and freshness.
- [x] 2.2 Batch field shape shortlists in SQL and all field/candidate verification work in bounded Lean requests.
- [x] 2.3 Classify supplied-in-scope, residual-premise, stronger-hypothesis, restricted-boundary, unmatched, and unavailable rows with route cards.
- [x] 2.4 Add registry-backed quantitative/adapter classification and visibly labelled conservative heuristic fallback.

## 3. Detect Certificate Leakage

- [x] 3.1 Compare helper/constructor binders with target field types through Lean definitional equality and emit `equivalent_field_input` evidence.
- [x] 3.2 Query direct value dependencies on field projections and emit `direct_projection_dependency` evidence.
- [x] 3.3 Apply only registered/reducible aliases before emitting separately labelled `alias_projection_dependency` evidence.

## 4. Define And Test Output

- [x] 4.1 Add `ladon-constructor-coverage-result-v1` with one row per field, summaries, candidates, residuals, classifications, leakage, route cards, freshness, coverage, bounds, omissions, and nonclaims.
- [x] 4.2 Test parameterized/dependent/inherited fields, direct/premised/restricted/unmatched/unavailable states, and all three leakage classes.
- [x] 4.3 Assert text/JSON parity, deterministic field order, batching/query counts, and output caps.

## 5. Verify The Packet

- [x] 5.1 Run structure helper, type/difference/consumer integration, installed CLI, resource, compile/quality, strict validation, and `git diff --check` gates.
