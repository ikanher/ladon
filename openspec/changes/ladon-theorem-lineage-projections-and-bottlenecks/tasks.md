## 1. Canonical Projection Model

- [x] 1.1 Add `src/ladon/theorem_lineage_projection.py` with immutable render-neutral models for projection identity, nodes, edges, roots, routes, collapses, repeated references, bottlenecks, bounds, omissions, and nonclaims.
- [x] 1.2 Build projection input exclusively from bounded rows returned by `theorem_lineage_query.py`; add a guard that rejects missing closure authority/freshness or inputs above configured node/edge caps.
- [x] 1.3 Implement SQL-backed trust, project, external, package, generated, type-only, value-only, and combined projection selectors and preserve every filter in the selected-subgraph fingerprint.
- [x] 1.4 Implement SQL aggregation for degrees, branch points, owner/package collapse rows, member counts, and representative shortest spines; keep trust roots individually visible under external collapse.

## 2. Narrow Pure Algorithms

- [x] 2.1 Add `src/ladon/theorem_lineage_algorithms.py` containing no filesystem, SQLite, subprocess, or repository imports; expose only deterministic functions over immutable bounded node/edge values.
- [x] 2.2 Implement SCC-condensed iterative dominators and return the target's immediate and complete mandatory-bottleneck chain for the exact selected roots/subgraph.
- [x] 2.3 Implement deterministic DAG tree unfolding with child/depth/node/byte caps, cycle/SCC references, and shared-node references on second and later visits.
- [x] 2.4 Add explicit precondition failures when pure-algorithm inputs exceed SQL-established caps; do not add a Python reachability or shortest-path fallback.

## 3. Projection Fixtures

- [x] 3.1 Add `tests/test_theorem_lineage_projection.py` using ingested/query-selected chain, diamond, multi-root, external-collapse, generated-node, and cyclic fixtures.
- [x] 3.2 Prove every representative spine starts at its selected root, ends at the exact theorem, and contains contiguous stored typed edges.
- [x] 3.3 Prove each reported bottleneck occurs on every route of exhaustive small fixtures and disappears when one bypass edge is added.
- [x] 3.4 Prove tree unfolding expands a shared node once, emits stable references afterward, terminates cycles, and reports each controlling cap and omitted lower bound.
- [x] 3.5 Assert every projection includes the actual-compiled-proof versus alternative-proof nonclaim and never labels a route as a possible proof.

## 4. Verification

- [x] 4.1 Run `uv run pytest tests/test_theorem_lineage_projection.py tests/test_theorem_lineage_query.py -q` and add property-style permutations proving stable output under input-row reordering.
- [x] 4.2 Profile dominators/tree unfolding on the portable maximum bounded subgraph and keep projection time/memory separate from SQL time.
- [x] 4.3 Run changed-module Ruff, mypy if configured, maintainability, vulture, compileall, `openspec validate ladon-theorem-lineage-projections-and-bottlenecks --strict`, and `git diff --check`.
