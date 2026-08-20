## Why

Forward dependencies do not answer which declarations consume a theorem, and an empty reverse query is trustworthy only when dependency extraction is complete.

## What Changes

- Persist complete Lean-owned type and value dependency edges through symbol IDs.
- Add `proof-search consumers` with exact declaration resolution, ownership and dependency-kind filters, source locations, and bounded results.
- Report partial coverage and external frontiers instead of false absence.

## Capabilities

### New Capabilities

- `ladon-declaration-consumers-query`: Indexed reverse type/value consumers with ownership and completeness semantics.

### Modified Capabilities

## Impact

Adds reverse query code and CLI/renderers, uses schema-v4 dependency indexes, and adds completeness and constant-query-count tests.
