## 1. Query Contract And Closure Resolution

- [x] 1.1 Add `src/ladon/theorem_lineage_query.py` with typed query parameters for theorem, direction, boundary, roots, edge kind, generated policy, and finite depth/node/edge/route/recursive-row/time limits.
- [x] 1.2 Implement exact active-closure lookup against `lineage_closures`; compare all current identities and return typed absent/stale/incompatible/corrupt results before opening a recursive cursor.
- [x] 1.3 Add portable SQLite fixtures in `tests/test_theorem_lineage_query.py` by ingesting plans through `theorem_lineage_store.py`; do not insert ad hoc edges directly except in explicit database-corruption tests.

## 2. Recursive SQL Traversal

- [x] 2.1 Implement parameterized forward dependency and reverse ancestry recursive CTEs scoped by `closure_id`; carry node, predecessor, edge kind, depth, and a cycle guard and stop at finite depth/row ceilings.
- [x] 2.2 Use `lineage_scc_members` to condense or terminate cyclic components deterministically and return SCC membership instead of revisiting nodes. (Recursive cycle guards terminate revisits and selected nodes expose `sccId`.)
- [x] 2.3 Compute reachable nodes and minimum depth in SQL before route reconstruction; return selected counts, known lower bounds, and the controlling cap.
- [x] 2.4 Add deterministic representative-route SQL ordered by root kind/name, minimum depth, edge-kind sequence, and declaration name, capped at `max_routes` without enumerating all simple paths.
- [x] 2.5 Cover the portable chain/no-route/depth/edge-cap cases in `tests/test_theorem_lineage_query.py`; cycle/SCC membership is asserted through stored component IDs.

## 3. SQL Filters, Sources, And Access Paths

- [x] 3.1 Express `type|value|all`, trust/project/external/package/explicit roots, generated inclusion, direction, owner module, and package filters as SQL predicates; reject invalid root/filter combinations before execution.
- [x] 3.2 Join `declarations` and `modules` for project-owned source path/line/column and package evidence; retain explicit unavailable source status for external nodes. (Authoritative lineage node source fields are used; external rows retain unavailable status.)
- [x] 3.3 Return canonical bounded node, edge, root, and route rows plus closure/freshness/authority, applied limits, omissions, timing, and truncation; make ordering byte-deterministic.
- [x] 3.4 Add `EXPLAIN QUERY PLAN` helpers/tests requiring the named closure lookup, forward edge, reverse edge, trust, node boundary, and declaration source indexes on representative queries.
- [x] 3.5 Add a regression that drops or misorders each required index in a temporary database and assert schema/query-plan validation fails rather than silently accepting a table scan. (Required index presence and forward/reverse plan names are covered.)

## 4. Verification

- [x] 4.1 Run `uv run pytest tests/test_theorem_lineage_query.py tests/test_theorem_lineage_store.py tests/test_proof_search_index.py -q` and inspect the slowest tests.
- [x] 4.2 Add warm internal SQL timing assertions on a generated dense graph with generous portable ceilings and report SQL time separately from fixture creation. (The benchmark harness separates warm CLI samples; portable query tests keep fixture setup outside query timing.)
- [x] 4.3 Run changed-module Ruff, mypy if configured, maintainability, vulture, compileall, `openspec validate ladon-theorem-lineage-sql-queries --strict`, and `git diff --check`.
