## 1. Define Difference And Route Models

- [x] 1.1 Add `ladon-proof-difference-result-v1` models for goal, candidate, attempts, substitutions, discharged binders, residuals, unresolved goals, mismatches, suggestions, coverage, and nonclaims.
- [x] 1.2 Add `ladon-proof-route-card-v1` with goal/context/index/worker/registry identities, route evidence, source anchors, bounds, omissions, accepted/rejected reason, and replay state.
- [x] 1.3 Add `proof-search explain` parsing for module, goal, candidate, assumptions, suggestion cap, match passes, freshness, and output bounds.

## 2. Implement Candidate Difference Analysis

- [x] 2.1 Reuse the semantic verifier to return successful conclusion application even when proof premises remain.
- [x] 2.2 Build bounded structural difference trees for each failed normalization pass.
- [x] 2.3 Implement generic classifications for head/arity, orientation, unfolding, coercion, projection, instance, parameter, missing-premise, and unclassified differences.
- [x] 2.4 Use precise applicable/stronger-premise/stronger-conclusion/index-boundary/representation-boundary/not-applicable labels.

## 3. Suggest One-Level Dischargers

- [x] 3.1 Derive one shape query per residual proof premise and retrieve bounded SQL shortlists in set-oriented batches.
- [x] 3.2 Verify all premise/candidate pairs in at most one additional Lean request.
- [x] 3.3 Rank and attach verified suggestions per premise with their own substitutions, residuals, authority, bounds, and omissions.

## 4. Render And Test Evidence

- [x] 4.1 Add deterministic text/JSON rendering that never collapses unmatched, unresolved, or unclassified states.
- [x] 4.2 Test direct close, one premise, incompatible conclusion, Eq/Iff orientation, reducible alias, projection, coercion, unresolved instance/term, and no-suggestion cases.
- [x] 4.3 Assert route-card identity changes when goal, context, generation, passes, or policy changes.

## 5. Verify The Packet

- [x] 5.1 Run semantic-helper, type-search, installed CLI, deterministic/bounds, compile/quality, strict validation, and `git diff --check` gates.
