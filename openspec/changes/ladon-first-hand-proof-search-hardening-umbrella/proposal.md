## Why

First-hand use on Matrix-Factorization exposed a gap between Ladon's declared SQLite contracts and its behavior at realistic scale: warm lineage can scan a 203,560-edge closure for more than thirty seconds, post-build writes bypass storage policy and planner statistics, empty semantic populations are reported too confidently, and several query paths are either unindexed or over-indexed. This umbrella converts that evidence into ordered, TDD-first packets that make proof search responsive, coverage-honest, and storage-accountable.

## What Changes

- Freeze reproducible correctness, query-plan, latency, storage, status, ranking, and report-volume baselines before changing behavior.
- Make bounded warm lineage use direction-correct indexed traversal and add a cheap closure-summary view.
- Enforce complete-database storage policy, transactional lineage publication, statistics refresh, progress/final diagnostics, and atomic output.
- Right-size the SQLite schema by removing redundant B-trees, using query-aligned `WITHOUT ROWID` layouts, and making sparse indexes partial.
- Add the missing core and ProofIR access paths, including foreign-key child and triage paths, with populated query-plan tests.
- Make `consumers` and `constructor` results reflect actual semantic coverage instead of treating empty populations as complete evidence.
- Peel theorem binders conservatively in `explain`, return residual premises, and use `indeterminate-lexical` when lexical evidence cannot decide applicability.
- Improve conceptual `any` ranking and keep owner reports focused by default while preserving opt-in repository-global inventory.
- Finish with installed CLI, documentation, maintained skill, Matrix-Factorization calibration, and full regression gates.

## Capabilities

### New Capabilities

- `ladon-first-hand-proof-search-baselines`: Reproducible first-hand fixtures and pre-change contract, plan, latency, size, status, ranking, and report-volume baselines.
- `ladon-lineage-query-plan-and-warm-summary`: Direction-correct indexed lineage traversal and a bounded constant-shape warm closure summary.
- `ladon-lineage-storage-budget-and-publication`: Complete-database budgets, transactional lineage publication, planner-statistics lifecycle, progress, and terminal output behavior.
- `ladon-sqlite-schema-rightsizing-and-accounting`: Query-aligned compact table/index layouts and per-table/per-index byte accounting.
- `ladon-proofir-query-access-paths`: Explicit core and ProofIR lookup, triage, graph, and foreign-key child access paths validated on populated data.
- `ladon-coverage-sensitive-consumers-and-constructors`: Coverage-honest reverse-consumer and structure-field results.
- `ladon-binder-aware-proof-difference`: Conservative binder peeling, normalized conclusion comparison, and residual-premise reporting.
- `ladon-proof-search-ranking-and-owner-projection`: Multi-segment conceptual ranking and owner-focused report projection.
- `ladon-proof-search-operational-release`: Integrated CLI, diagnostics, documentation, skill, calibration, and release acceptance.

### Modified Capabilities

## Impact

Touches the private SQLite schema generation, lineage ingestion and SQL, ProofIR dossier/triage queries, consumer and constructor handlers, proof-difference analysis, name ranking, architecture report projection, CLI output/progress contracts, tests, benchmarks, documentation, and the maintained Ladon skill. Disposable indexes require rebuild; Lean source repositories are not modified.
