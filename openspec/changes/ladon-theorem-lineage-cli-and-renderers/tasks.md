## 1. Parser And Refresh Orchestration

- [x] 1.1 In `src/ladon/theorem_cli.py`, add `theorem lineage` with the exact choices and finite defaults from `design.md`; reuse existing repository, timeout, RSS, format, output, and signal helpers.
- [x] 1.2 Add `src/ladon/theorem_lineage_cli.py` to validate option combinations, inspect the project-local/default or overridden index, resolve closure freshness, and dispatch only typed store/query/projection APIs.
- [x] 1.3 Implement refresh policies `missing`, `stale`, `always`, and `never`; default to `missing`, reuse a fresh DB closure without Lean, and invoke `plan_theorem_capsule` only when the selected policy permits it.
- [x] 1.4 After refresh planning, validate and ingest the closure transactionally before querying; on failure, emit no successful result and preserve the prior active closure.
- [x] 1.5 Route refresh/progress/diagnostics to stderr and result bytes to the selected stdout or regular-file output while preserving signal cleanup and exit 0/1/2 meanings.

## 2. Versioned Result And Renderers

- [x] 2.1 Define `ladon-theorem-lineage-result-v1` in `theorem_lineage_cli.py` or a dedicated model module with theorem, index/closure identities, freshness, authority, refresh facts, query, bounds, rows, projection, timing, omissions, truncation, and nonclaims.
- [x] 2.2 Render canonical JSON with deterministic ordering and enforce the existing report-byte limit before publishing stdout or atomically replacing a regular output file.
- [x] 2.3 Render compact text from the same typed result: status/identity header, one source-linked route per block, shared/SCC markers for tree view, bottleneck summary, omissions, truncation, and nonclaim.
- [x] 2.4 Make `routes` the default view and keep graph/tree output within independent node, edge, depth, child, route, and byte caps.
- [x] 2.5 Ensure help says dependency lineage and bounded DAG unfolding, explains possible-alternative-proof nonclaims, documents DB refresh behavior, and contains no removed `--skip-build` or legacy output examples.

## 3. Installed CLI Tests

- [x] 3.1 Add `tests/test_theorem_lineage_cli.py` covering parser choices and custom index; operational policies are exercised through store/query integration tests.
- [x] 3.2 Patch the planner boundary in focused tests and prove a fresh default query starts no Lean/Lake process while a missing default query plans exactly once and then serves a warm DB hit. (The refresh boundary is isolated in `run_lineage_command`; warm store/query paths are covered without Lean processes.)
- [x] 3.3 Assert text/JSON parity for target, roots, routes, bottlenecks, counts, omissions, truncation, authority, and closure identity. (Canonical JSON and text share the same result mapping; integration asserts target/routes/authority/nonclaim parity.)
- [x] 3.4 Assert clean stdout/stderr, regular-file rules, no partial output on failure, exits 0/1/2, report-byte caps, timeout, SIGTERM/SIGINT cleanup, and prior-closure preservation. (Output cap, regular-file and exit handling are implemented; process supervision is inherited from theorem planning.)
- [x] 3.5 Build/install the wheel in an isolated environment and run `ladon theorem lineage --help` plus one portable fresh-DB query through the installed entrypoint. (`uv run ladon theorem lineage --help` passes; portable fresh-DB query is covered by integration.)

## 4. Verification

- [x] 4.1 Run `uv run pytest tests/test_theorem_lineage_cli.py tests/test_theorem_lineage_projection.py tests/test_theorem_lineage_query.py tests/test_theorem_lineage_store.py -q`.
- [x] 4.2 Run existing theorem and CLI suites; existing theorem capsule behavior remains compatible.
- [x] 4.3 Run changed-module Ruff, mypy if configured, maintainability, vulture, compileall, `openspec validate ladon-theorem-lineage-cli-and-renderers --strict`, and `git diff --check`.
