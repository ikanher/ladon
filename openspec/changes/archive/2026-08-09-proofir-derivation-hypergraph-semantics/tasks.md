## 1. Define semantic counterexamples

- [x] 1.1 Add a failing fixture where a step requires both `A` and `B` for `C`, proving a navigation path through `A` alone is not a proof slice.
- [x] 1.2 Add fixtures for alternative steps deriving one conclusion, ordered premises, substitutions, contexts, recursion/SCCs, rejected candidates, and unresolved premises.
- [x] 1.3 Add property tests for deterministic traversal, bound enforcement, AND satisfaction, OR alternatives, and cycle classification.

## 2. Implement derivation artifacts

- [x] 2.1 Add typed derivation steps with rule, ordered premise references, conclusion reference, substitutions, local context, and exact check-run reference.
- [x] 2.2 Store accepted derivations, advisory plans, and failed attempt logs as separate artifact kinds with separate validation rules.
- [x] 2.3 Validate reference closure, step/result consistency, duplicate IDs, acyclicity where promised, and explicit SCC metadata where recursion is allowed.
- [x] 2.4 Implement bounded `navigation path`, `derivation slice`, `satisfaction analysis`, and `alternative analysis` queries with distinct result schemas and nonclaims.
- [x] 2.5 Reimplement any useful graph kernel behind Ladon-owned interfaces; do not import, invoke, vendor, or require Quux.

## 3. Adapt and verify

- [x] 3.1 Replace retired obligation-DAG fixtures with native derivation fixtures that preserve the useful ordering, identity, and ambiguity scenarios.
- [x] 3.2 Update path renderers so every partial route states that it does not establish conjunctive completeness.
- [x] 3.3 Run native derivation unit/property/query tests and strict quality checks with `../quux` unavailable.
