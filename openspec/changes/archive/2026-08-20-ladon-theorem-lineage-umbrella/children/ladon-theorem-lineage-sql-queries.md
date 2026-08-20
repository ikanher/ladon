# `ladon-theorem-lineage-sql-queries`

Answers bounded reachability and representative-route questions with indexed,
parameterized SQLite recursive CTEs.

- Dependencies: completed lineage schema and ingestion exit class.
- Enables: bounded render-neutral projections.
- Excludes: exhaustive simple-path enumeration and routine Python graph traversal.
- Exit: closure/freshness, recursion, filters, bounds, determinism, sources, and
  `EXPLAIN QUERY PLAN` gates pass.
