## 1. Lock The Bad And Good Plans

- [x] 1.1 Reuse the populated baseline fixture and add normalized plan assertions showing the current recursive CTE scans by closure only.
- [x] 1.2 Add forward and reverse expected-plan tests requiring the directional covering index and both leading equality keys.
- [x] 1.3 Add a same-host microbenchmark proving the frontier-first reference SQL satisfies the relative latency gate before editing production SQL.

## 2. Correct Recursive Acquisition

- [x] 2.1 Refactor `_walk_rows` in `src/ladon/theorem_lineage_query.py` to keep `walk` outermost and choose the direction-specific indexed edge path.
- [x] 2.2 Push edge-kind, depth, generated-node where feasible, and recursive-row bounds into acquisition rather than postprocessing.
- [x] 2.3 Return the binding cap, acquired-row count, and truncation reason without changing Lean-environment authority or route orientation.
- [x] 2.4 Run forward/reverse, type/value/all, generated/excluded, cycle, empty-boundary, and cap regression tests.

## 3. Add The Warm Summary

- [x] 3.1 Add a render-neutral summary query with fixed aggregate statement count and no recursive CTE.
- [x] 3.2 Add `summary` to theorem-lineage view parsing, JSON, text rendering, help, and installed dispatch.
- [x] 3.3 Include closure identity, freshness, authority, node/edge breakdowns, trust, SCC, omissions, elapsed time, bounds, and nonclaims.
- [x] 3.4 Add a trace callback test proving summary never invokes route acquisition or Lean under `--refresh never`.

## 4. Close Performance Gates

- [x] 4.1 Run populated `EXPLAIN QUERY PLAN` assertions on every supported SQLite test environment and normalize only wording differences.
- [x] 4.2 Run the portable latency/statement-count benchmark twice and compare with the frozen baseline fingerprint.
- [x] 4.3 Run lineage query, projection, CLI, installed-wheel, schema, deterministic, and full Python quality suites.
- [x] 4.4 Validate this OpenSpec change strictly and record remaining combinatorial/path nonclaims.
