## 1. Add Explicit Build Requests

- [x] 1.1 Add `--mode lexical|semantic|hybrid`, `--lean-timeout`, semantic completeness policy, and validation with omitted mode remaining lexical.
- [x] 1.2 Add installed help/text/JSON fields for execution warning, mode, helper/toolchain identity, coverage, cache, bounds, omissions, and publication state.

## 2. Build Sound Module Artifacts

- [x] 2.1 Discover imported and configured source-only modules and assign lexical/semantic status before extraction.
- [x] 2.2 Compute conservative module cache keys over source, transitive local imports, Lake/compiled state, toolchain, Lean, helper, and protocol.
- [x] 2.3 Reuse only exact cache hits and invoke semantic extraction for misses with finite per-module and whole-build limits.

## 3. Assemble And Publish A Generation

- [x] 3.1 Create a PID/randomized temporary database inside the repository-local `.ladon/index` directory and populate v4 in dependency order.
- [x] 3.2 Insert module coverage and reconcile every helper terminal count with stored rows.
- [x] 3.3 Run schema, FK, integrity, coverage, query-plan, size, and `PRAGMA optimize` gates.
- [x] 3.4 Recheck source/build identities and atomically replace the published database only after every gate passes.

## 4. Exercise Failure And Incremental Paths

- [x] 4.1 Test unchanged cache hits and source, import, helper, toolchain, and compiled-state invalidation.
- [x] 4.2 Inject helper failure, source change during build, size overflow, validation failure, active lock, stale lock, cancellation, and publication interruption.
- [x] 4.3 Assert the prior generation survives every failed build and temporary/lock cleanup is explicit.

## 5. Verify The Packet

- [x] 5.1 Run lexical no-Lean regression tests, semantic/hybrid fixtures, deterministic rebuilds, installed CLI contracts, resource gates, compile/quality gates, strict validation, and `git diff --check`.
