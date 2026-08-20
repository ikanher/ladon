## 1. Protocol And Lifecycle Fixtures

- [x] 1.1 Define a versioned batch request, per-module result/diagnostic, and terminal-summary fixture contract.
- [x] 1.2 Add fake-helper tests for ordered batches, malformed frames, mixed success/failure, and protocol-version mismatch.
- [x] 1.3 Add process-supervisor tests for deadline, cancellation, escalation, pipe draining, and descendant cleanup.
- [x] 1.4 Add cache cases for source, transitive import, helper, options, toolchain, Lake manifest, and compiled-state changes.
- [x] 1.5 Add portable Lake fixtures for multiple libraries, non-root `srcDir`, generated roots, and conventional fallback.

## 2. Batched Lean Helper

- [x] 2.1 Extend the Lean helper to accept an ordered module batch and emit framed per-module records.
- [x] 2.2 Emit module-scoped parse/load failures without aborting serialization of already completed modules.
- [x] 2.3 Emit a terminal summary with protocol/helper/Lean versions and requested/completed/failed counts.
- [x] 2.4 Bound helper-retained state between modules or batches, require configured inventory batch size at least two, and document the chosen batch-size trade-off.

## 3. Python Runner And Cleanup

- [x] 3.1 Implement batch planning that uses at most `ceil(n / b)` helper invocations for `n` uncached modules and configured batch size `b >= 2`; only multi-module inventories are required to use fewer helpers than modules.
- [x] 3.2 Implement framed-stream validation and deterministic partial result assembly.
- [x] 3.3 Configure the CLI-owned target-process supervisor with conservative finite defaults for each Lean helper batch.
- [x] 3.4 Extend supervisor handling for helper-protocol failure while terminating and reaping the full group on timeout, cancellation, malformed protocol, or parent error.
- [x] 3.5 Add strict-mode handling without discarding successful rows or diagnostics.

## 4. Cache And Discovery

- [x] 4.1 Introduce a versioned cache namespace and fingerprint manifest for every required validity input.
- [x] 4.2 Hash/reuse the resolved local import closure and bypass or label cache use when relevant state is unavailable.
- [x] 4.3 Record cache hit, miss, invalidation reason, and fingerprint version in phase provenance.
- [x] 4.4 Implement Lake-declared library/source-root discovery before conventional path fallback.
- [x] 4.5 Emit actionable unsupported/fallback layout diagnostics instead of silently inventing module names.

## 5. Integration And Gates

- [x] 5.1 Expose helper command shape, versions, counts, timing, cache state, timeout state, and execution-safety warning through report v2.
- [x] 5.2 Assert text-only mode starts no target process and Lean mode never builds unless the shared CLI requested it.
- [x] 5.3 Run fake-process lifecycle tests and verify no helper descendant remains.
- [x] 5.4 Add and run `scripts/lean_runtime_gate.py --required`; it provisions the tracked fixture's pinned reference toolchain, runs non-skippable real-Lean root and multi-module batch integration, and treats unavailable Lean as failure.
- [x] 5.5 Run synthetic cold/warm/cache-invalidation benchmarks and record optional Quux timing separately.
- [x] 5.6 Run `uv run --locked pytest -q tests/test_lean_extraction.py tests/test_pipeline.py tests/test_extraction.py tests/test_root_matrix.py`.
- [x] 5.7 Run `uv run --locked python scripts/python_quality.py --strict`.
- [x] 5.8 Run `openspec validate ladon-lean-extraction-runtime-hardening --strict`.
