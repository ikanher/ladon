## 1. Type-Directed Search

- [ ] 1.1 Define a usable elaborated type-pattern syntax with holes, binder handling, namespace context, and deterministic validation errors.
- [ ] 1.2 Use the local index for bounded candidate prefiltering and Lean for authoritative unification, definitional equality, and application checks.
- [ ] 1.3 Implement ordered exact, reducible, coercion-assisted, and explicitly rejected match routes with limits and timeouts.
- [ ] 1.4 Return substitutions, match strength, scope, freshness, provenance, and rejection evidence in canonical results.

## 2. Semantic Search

- [ ] 2.1 Implement signature/name/token search with conjunction, negation, namespace filters, and deterministic ranking.
- [ ] 2.2 Group declaration families and surface nearby failed routes without claiming semantic equivalence from lexical similarity.
- [ ] 2.3 Expose type-directed and semantic search through the shared CLI contract.

## 3. Verification

- [ ] 3.1 Add portable fixtures for binder renaming, implicit arguments, reducible aliases, coercions, overloaded names, negation, caps, and no-match evidence.
- [ ] 3.2 Strictly validate this change and run focused search correctness, determinism, and latency gates.
