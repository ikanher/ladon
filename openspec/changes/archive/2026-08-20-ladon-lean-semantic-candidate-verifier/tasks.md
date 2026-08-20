## 1. Extend The Semantic Protocol

- [x] 1.1 Define `elaborate-pattern` request/result models for module context, pattern or pattern file, assumptions, wildcards, identities, fingerprints, shapes, diagnostics, and bounds.
- [x] 1.2 Define `check-candidates` batch models for candidate names, passes, limits, substitutions, residual proof goals, unresolved instances/terms, adapters, and failures.

## 2. Implement Lean Pattern Elaboration

- [x] 2.1 Elaborate the pattern once in the requested module namespace/import environment and create fresh metavariables for `_`.
- [x] 2.2 Elaborate repeatable assumptions into the local context and return stable rendered and structural query evidence.
- [x] 2.3 Return precise syntax, unknown-name, type, timeout, and environment-identity failures.

## 3. Implement Batched Candidate Checks

- [x] 3.1 Resolve current `ConstantInfo`, open candidate binders with fresh metavariables, and attempt syntactic then reducible matching.
- [x] 3.2 Add Eq/Iff symmetry and optional separately labelled bounded semi-reducible passes.
- [x] 3.3 Synthesize instances under finite limits, instantiate assignments, and separate proof residuals, instance residuals, and non-proof term metavariables.
- [x] 3.4 Return stale/missing candidates as explicit rows and never silently drop requested names.

## 4. Test Semantic Cases And Limits

- [x] 4.1 Add exact, wildcard, binder-renaming, reducible alias, equality/Iff symmetry, coercion, instance success/failure, missing premise, and stale-candidate fixtures.
- [x] 4.2 Assert one pattern elaboration and one helper candidate batch per request.
- [x] 4.3 Test heartbeat, recursion, deadline, candidate, diagnostics, cancellation, and output-byte limits with process cleanup.

## 5. Verify The Packet

- [x] 5.1 Run fake-protocol and pinned Lean integration suites, deterministic JSON tests, supervisor/resource gates, compile/quality gates, strict validation, and `git diff --check`.
