## Context

Portable benchmark-oracle infrastructure exists for selected signals, but the
current product also relies on fixed thresholds and live-repository
cardinalities that have already drifted. There is no unified measurement of
false positives, missing-import recall, declaration/dependency coverage, Lean
runtime, memory, cache invalidation, or report determinism.

The harness consumes the clean-checkout child's tracked-source baseline and the
shared CLI/report contracts. It closes only after corrected signals, Lean
runtime, and declaration surfaces have supplied their focused fixtures and
conservative provisional bounds.

## Goals / Non-Goals

**Goals:**

- Make portable labeled fixtures the authority for promoted behavior.
- Measure correctness, coverage, resource use, and output stability separately.
- Reuse the ordinary installed CLI for end-to-end measurements.
- Treat live repositories as non-blocking drift evidence.

**Non-Goals:**

- Score model performance or add a model-specific benchmark.
- Turn all heuristic observations into release-blocking findings.
- Require Quux, matrix-factorization, mathlib, or hard-coded local paths.
- Compare whole JSON snapshots when semantic predicates suffice.

## Decisions

1. **Use versioned benchmark manifests.** Each case names the fixture, command,
   report version, expected positive/negative/boundary labels, and applicable
   metrics. Expected truth is reviewed source data, not inferred from Ladon's
   current output.

2. **Separate metric families.**

   - Signal precision and false-positive counts by finding kind.
   - Recall for seeded missing imports and trust markers.
   - Declaration and direct-dependency extraction coverage against labeled Lean
     fixtures.
   - Cold/warm latency, cache hit/invalidation behavior, peak RSS where
     supported, timeout cleanup, and child-process count.
   - Report schema validity, normalized byte determinism, size, and text/JSON
     semantic parity.

   A composite quality score was rejected because it hides which contract
   regressed.

3. **Exercise the installed CLI end to end.** Pure-function oracle tests remain
   useful, but promotion requires subprocess evidence using the same command
   users run. No benchmark-only analyzer path may change selection or
   thresholds.

   Required runs consume the clean-checkout candidate resolver explicitly:
   `--candidate worktree` materializes current tracked files, while a treeish or
   directory selects that exact candidate. No implicit working directory or
   sibling checkout is accepted.

4. **Use robust performance gates.** Tiny synthetic cases get generous absolute
   ceilings and invariant checks such as bounded process count and warm-cache
   improvement. Large live runs record observations and trend deltas without
   failing on shared-runner variance.

5. **Version calibration with the signal contract.** Threshold/promotion policy
   and sample-size behavior are emitted in reports and tied to a manifest
   version. Moving repository module counts cannot serve as correctness
   assertions.

6. **Preserve raw results.** Machine JSON includes environment/toolchain
   identity and per-case measurements; the text summary highlights regressions
   without losing the underlying rows.

## Risks / Trade-offs

- **Fixture labels encode maintainer bias** → Require positive, intentional
  negative, and boundary cases with source rationale.
- **Performance gates are noisy** → Gate structural bounds and broad synthetic
  ceilings; trend real repositories separately.
- **Benchmark suite becomes a second implementation** → Invoke packaged CLI and
  restrict helpers to labels, normalization, and measurement.
- **Reports grow excessively** → Track size budgets and store summaries by
  default with opt-in raw samples for development runs.

## Migration Plan

Inventory and reuse existing oracle fixtures, add missing labeled defects, add
CLI correctness/coverage metrics, then runtime/report measurements. Replace
stale Quux cardinality assertions with drift records only after equivalent
portable predicates exist.

## Open Questions

- Exact numeric budgets will be baselined on CI hardware during implementation
  and committed with rationale.
