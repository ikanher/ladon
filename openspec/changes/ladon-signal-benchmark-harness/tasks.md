## 1. Manifest And Fixture Inventory

- [x] 1.1 Inventory and reuse existing portable benchmark-oracle fixtures without duplicating their owners.
- [x] 1.2 Define a versioned manifest schema for fixture, CLI command, report version, labels, rationale, and metric families.
- [x] 1.3 Label positive, intentional-negative, and boundary cases for every promoted structural signal.
- [x] 1.4 Add labeled declaration-kind, statement-field, direct dependency, trust-footprint, cache, timeout, and report-contract fixtures.
- [x] 1.5 Reject required manifest commands containing sibling-repository or maintainer-local paths.

## 2. Correctness And Coverage Metrics

- [x] 2.1 Implement per-kind true-positive, false-positive, false-negative, precision, and recall calculations where labels apply.
- [x] 2.2 Add missing-internal-import recall and absent-external-import false-positive oracles.
- [x] 2.3 Add facade, namespace, generated, similarity, unresolved-reference, architecture, source-pattern, and claim-authority positive/intentional-negative boundary oracles.
- [x] 2.4 Add declaration-surface required-field and declaration-kind coverage.
- [x] 2.5 Add separate elaborated type/value dependency coverage without counting parser candidates as hits.

## 3. Runtime, Cache, And Process Metrics

- [x] 3.1 Add cold/warm wall-time, cache state, report-size, and peak-RSS measurement with platform capability metadata.
- [x] 3.2 Count helper launches and descendants for a synthetic inventory batch.
- [x] 3.3 Add controlled timeout/cancellation cases that assert bounded cleanup and no orphan process.
- [x] 3.4 Add cache hit/invalidation cases for every required fingerprint input.
- [x] 3.5 Baseline generous synthetic budgets on CI hardware and commit the values with rationale.

## 4. Report And CLI Stability

- [x] 4.1 Run all end-to-end product cases through an installed ordinary `ladon` command.
- [x] 4.2 Validate report schema, normalized byte determinism, text/JSON semantic parity, and size budgets.
- [x] 4.3 Emit machine-readable per-case results plus a compact summary with separate metric families.
- [x] 4.4 Assert benchmark commands contain no role-specific analysis option or alternate threshold path.

## 5. Required And Optional Runs

- [x] 5.1 Add portable correctness and broad synthetic resource checks to required CI.
- [x] 5.2 Remove hard-coded sibling paths from root-matrix/calibration defaults and convert fixed Quux module-count/top-node assertions to explicitly configured non-blocking live drift rows.
- [x] 5.3 Keep Quux, matrix-factorization, and mathlib runs opt-in with environment/toolchain provenance.
- [x] 5.4 Require positive, negative, and boundary evidence before a changed default behavior is marked ready.

## 6. Gates

- [x] 6.1 Add `scripts/ladon_benchmarks.py --candidate <treeish|directory|worktree> --required` for the installed-CLI portable suite; reject a missing candidate and use the clean-checkout materialization contract.
- [x] 6.2 Run `uv run --locked pytest -q tests/test_benchmark_oracles.py tests/test_calibration_regression.py tests/test_root_matrix.py tests/test_lean_extraction.py tests/test_render.py`.
- [x] 6.3 Run the required benchmark command from the clean-checkout tracked-source baseline.
- [x] 6.4 Update `automation.json` with the installed-CLI clean-candidate benchmark gate.
- [x] 6.5 Run `uv run --locked python scripts/python_quality.py --strict`.
- [x] 6.6 Run `openspec validate ladon-signal-benchmark-harness --strict`.
