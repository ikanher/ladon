## Context

The measured database uses 197,419,008 bytes for `lineage_edges` plus its three indexes. The rowid table and autoindex duplicate storage, while separate forward ordering exists because the primary-key order puts `target` before `kind`. Full indexes also cover 148,695 `NULL` structure names and 150,743 empty semantic heads.

## Goals / Non-Goals

**Goals:** reduce bytes without losing accepted plans, eliminate redundant B-trees, make sparse indexes population-aware, and expose storage attribution.

**Non-Goals:** in-place migration, speculative compression, or removing access paths solely from intuition.

## Decisions

1. Benchmark `lineage_edges WITHOUT ROWID` with primary key `(closure_id, source, kind, target)` plus reverse `(closure_id, target, kind, source)`. Adopt only after forward/reverse and insert tests pass.
2. Remove `idx_import_source` and `idx_dependency_source` where primary-key prefixes satisfy all production plans.
3. Add an explicit exact declaration-name index; make head and structure indexes partial or generation-conditional so exact lookup never relies on skip-scan accidents.
4. Use `dbstat` when available and a documented fallback from page accounting; report capabilities when per-object bytes are unavailable.

## Risks / Trade-offs

- [WITHOUT ROWID changes insertion cost] → benchmark build and lineage publication as well as reads.
- [Partial index predicate misses a query] → populated plan inventory is a mandatory gate.

## Migration Plan

Create a new private schema generation in temporary databases, validate, and atomically rebuild. Never mutate schema-v4 in place.

## Open Questions

- Apply the same graph layout to ProofIR DAG edges only if its independent measurements justify it.
