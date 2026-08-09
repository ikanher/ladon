## Why

Warm lineage currently exceeds thirty seconds even under tiny output caps because SQLite scans the entire stored closure during recursive steps. Output bounds must bound acquisition work, not merely trim results after an expensive traversal.

## What Changes

- Force direction-correct frontier-first recursive joins through the forward or reverse covering index.
- Validate populated `EXPLAIN QUERY PLAN` output and finite work bounds.
- Add a cheap closure-summary view that does not enumerate routes.

## Capabilities

### New Capabilities

- `ladon-lineage-query-plan-and-warm-summary`: Direction-correct indexed lineage traversal and a bounded constant-shape warm closure summary.

### Modified Capabilities

## Impact

Changes theorem-lineage SQL, projections, CLI view selection, tests, and performance fixtures without changing dependency authority.
