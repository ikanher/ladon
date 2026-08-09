## Why

Ordinary path traversal through the current obligation DAG can visually imply that one premise establishes a conclusion even when a step requires several conjunctive premises.

## What Changes

- Represent derivation steps as directed hyperedges with ordered premises, one conclusion, rule, substitutions, local context, and checker observations.
- Separate accepted derivations, advisory plans, and failed attempt logs.
- Represent alternative steps for one conclusion as explicit OR choices.
- Validate reference closure and either acyclicity or explicit SCC recursion policy.
- Add navigation-path, complete-slice, satisfaction, alternative, and SCC queries with distinct nonclaims.

## Capabilities

### New Capabilities
- `proofir-derivation-hypergraph-semantics`: Prover-neutral AND/OR derivation structure and bounded queries.

### Modified Capabilities

## Impact

Replaces obligation-DAG semantic ownership while retaining a compatibility projection. Touches DAG normalization, route rendering, theorem dossiers, proof planning, and checker witnesses.
