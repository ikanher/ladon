## Context

The forward covering index exists, but the recursive CTE currently lets SQLite choose the edge relation before the frontier. With no post-lineage statistics, the plan searches only by closure and repeatedly scans 203,560 edges. A frontier-first `CROSS JOIN` used `(closure_id, source)` and reduced the observed bounded traversal to 0.02 seconds.

## Goals / Non-Goals

**Goals:** make plan shape robust, bind acquisition work, and provide a nonrecursive warm summary.

**Non-Goals:** alternative-proof search, transitive-closure precomputation, or changing Lean-environment authority.

## Decisions

1. Encode join order intentionally at the recursive seam and select the forward/reverse index by direction. Planner hints alone were rejected because they do not force frontier-first loop order.
2. Treat populated `EXPLAIN QUERY PLAN` predicates as contract tests. Index-name inventory alone was demonstrated insufficient.
3. Implement summary with direct aggregate queries over closure metadata and indexed child tables; never call route projection internally.
4. Apply recursive row caps inside the CTE and report the first binding cap.

## Risks / Trade-offs

- [SQLite plan text varies by version] → assert normalized access-path predicates, not whole plan strings.
- [Path enumeration is still combinatorial] → finite recursive-row cap and summary default for overview work.

## Migration Plan

Preserve existing views, add `summary`, and replace only traversal SQL. Roll back by restoring the prior query module; stored closures remain compatible.

## Open Questions

- Whether `summary` should become the default view is deferred to the release packet after calibration.
