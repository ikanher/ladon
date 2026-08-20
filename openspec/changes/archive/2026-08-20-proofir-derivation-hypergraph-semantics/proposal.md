## Why

Ordinary graph paths lose the conjunctive meaning of theorem premises and blur accepted derivations with plans and failed attempts.

## What Changes

- Represent applications as typed directed hyperedges with ordered premises and one conclusion.
- Separate derivations, plans, and attempt logs.
- Add explicit acyclic/SCC policy and distinct bounded graph-query contracts.

## Capabilities

### New Capabilities
- `proofir-derivation-hypergraph-semantics`

### Modified Capabilities

## Impact

Changes derivation validation, SQLite rows, dossier navigation, slices, satisfaction, alternatives, and SCC inspection.
