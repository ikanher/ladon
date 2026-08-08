## Why

Lean-verified proof engineering needs complete binders, dependencies, shapes, structures, fields, and module coverage in SQLite, with constraints and access paths that make false completeness difficult.

## What Changes

- Bump disposable proof-search storage to schema v4 and report old generations as rebuild-required.
- Add normalized declaration metadata, a symbol dictionary, complete dependency/shape/binder/structure relations, and module semantic state.
- Add required foreign keys, checks, uniqueness constraints, exact-name/FTS/reverse-edge indexes, integrity tests, and query-plan gates.

## Capabilities

### New Capabilities

- `ladon-semantic-index-schema-v4`: Constrained, indexed semantic relations with explicit coverage and disposable rebuild semantics.

### Modified Capabilities

## Impact

Changes SQLite DDL, generation identity, validation, population adapters, status output, and schema/query-plan tests while retaining existing ProofIR and lineage relations.
