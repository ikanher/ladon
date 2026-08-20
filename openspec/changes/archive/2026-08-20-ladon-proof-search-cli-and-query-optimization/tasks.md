## 1. Freeze Query Equivalence

- [x] 1.1 Import packet-1 fixtures for installed CLI, lineage routes, bottlenecks, boundary metadata, and ProofIR paths.
- [x] 1.2 Add trace assertions reproducing duplicate lineage traversal, boundary N+1, and per-node ProofIR materialization before refactoring.

## 2. Add Lightweight Dispatch

- [x] 2.1 Add `src/ladon/entrypoint.py` that dispatches proof-search before importing the general analyzer CLI.
- [x] 2.2 Point the installed console script at the lightweight entrypoint and keep `ladon.main` as a lazy compatibility wrapper.
- [x] 2.3 Move ProofIR imports inside evidence dispatch and verify help paths do not import optional heavy modules.

## 3. Remove Duplicate And N+1 Queries

- [x] 3.1 Refactor lineage route materialization to consume the one already-fetched bounded walk or adjacency result.
- [x] 3.2 Load all trust targets and boundary metadata for selected endpoints with one bounded set-oriented query.
- [x] 3.3 Collect distinct ProofIR path node IDs, fetch their rows once, and restore path order from an in-memory map.

## 4. Verify Performance And Contracts

- [x] 4.1 Assert lineage traversal acquisition count is one and SQL statement count remains constant as route count grows.
- [x] 4.2 Assert ProofIR route node acquisition count is one and endpoint/path semantics match baseline fixtures.
- [x] 4.3 Measure installed one-shot proof-search startup on the baseline host and require at least 50 percent overhead reduction.
- [x] 4.4 Run installed stream/signal/exit/help tests, focused query suites, full compile/quality gates, strict validation, and `git diff --check`.
