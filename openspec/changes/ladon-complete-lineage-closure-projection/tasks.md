# Tasks

Planning, field reproduction, implementation, and focused regressions are in
progress. The specification owns acceptance; the design owns algorithms and
metrics. Final repository-wide verification remains open.

## 1. Reproduce the failure and freeze coverage oracles

- [x] 1.1 Add independent finite-graph fixtures and red tests for a shared 20-layer diamond, single-node closure, typed parallel edges and a cyclic component; verify expected node/edge sets are computed from fixture input rather than the query under test.
- [x] 1.2 Add failing metrics for false completeness, payload/count mismatch, dangling endpoints and graph dependence on route limits; verify exact-cap and cap-plus-one cases fail for the intended reason.
- [x] 1.3 Preserve a small regression of the field discrepancy (stored closure versus route graph), document its scope in test comments, and verify the packet evidence with `python openspec/changes/ladon-complete-lineage-closure-projection/evidence/verify.py`.

## 2. Retrieve complete stored closures within finite budgets

- [x] 2.1 Implement the closure-scoped read query using existing identity/freshness checks and one coherent read transaction; verify full expected node and typed-edge equality on the fixtures and rejection of stale/missing/ambiguous closures.
- [x] 2.2 Implement deterministic target-inclusive node selection, endpoint-closed typed edges and exact cap/filter omissions; verify generated-node, edge-kind, exact-cap, byte-limit and SCC tests.
- [x] 2.3 Add separate source/selected-graph/route/external coverage fields and exact payload counts; verify complete graph coverage never upgrades theorem-check, external-expansion or historical authority.
- [x] 2.4 Document closure-selection semantics and the finite limits next to the query API; run the focused new closure-query tests and existing store/query tests before moving on.

## 3. Make representative-route acquisition scale with unique graph work

- [x] 3.1 Replace path-expanded reachability with indexed distinct-node/minimum-depth acquisition and a finite typed-adjacency work cap; verify each node expands once on layered diamonds and both traversal directions terminate on SCCs.
- [x] 3.2 Build deterministic bounded representative routes after acquisition, retaining typed predecessor information; verify shortest-path tie handling and route-limit changes do not alter already acquired graph coverage.
- [x] 3.3 Split depth-exhaustion tests from actual depth truncation, add the public traversal-work limit and version its work-unit reporting; verify cap-plus-one behavior and document the change from path-row to distinct-node budgets.
- [x] 3.4 Run existing route, tree, bottleneck and query-plan tests; resolve intentional semantic changes explicitly and verify the existing forward/reverse closure indexes remain used.

## 4. Expose the new view through live and historical interfaces

- [x] 4.1 Add `--view closure` and handle inapplicable route-only options explicitly; verify parser/help tests and a CLI fixture returning the complete typed graph while existing `graph` retains representative-route semantics.
- [x] 4.2 Wire live and historical projections through the same coverage logic; verify `--refresh never` triggers no Lean/Lake process, evidence mutation, or historical-to-current authority upgrade.
- [x] 4.3 Retain atomic bounded output and deterministic fingerprints; verify prior output survives byte-limit/rendering failures and insertion order does not change canonical output.
- [x] 4.4 Update `docs/CLI.md`, relevant README guidance and the maintained Ladon skill's lineage instructions; verify documented commands and explain library-frontier versus axiom-complete scope.

## 5. Validate the integrated field result and release boundary

- [ ] 5.1 Run the focused lineage store/query/projection/CLI/history/hardening suites and the repository Python-quality gate; retain commands, exit statuses and source identities in an implementation receipt.
- [x] 5.2 Replay the retained gradient field case under the recorded resource ceilings, using stored-only queries after acquisition; verify exact selected node/typed-edge equality and zero false-complete/count/dangling-endpoint metrics, with bounded wall-time/RSS observations.
- [x] 5.3 Compare before/after graph work on the synthetic sharing fixture and field case; reject a repair that depends on increasing the old path-recursion ceiling or enumerating all simple paths.
- [x] 5.4 Verify stored closures remain usable by pre-existing views and rollback requires no data deletion/migration; run strict OpenSpec validation and obtain a source/behavior review of the final implementation before marking this change complete.
