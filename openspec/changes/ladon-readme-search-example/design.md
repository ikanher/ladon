# Design

## Context

The [current README](../../../README.md) puts the RH archive lookup first. On the three pinned demo files, its exact `Real.sqrt |S.det|` query returns three declaration rows. A fixed-string `rg` search returns five lines, including all three matching declarations and two proof-body occurrences. This warrants an archive lookup recipe and an honest source-search baseline.

## Goals / Non-Goals

**Goals**

- Lead with a mathematical goal and show the difference between finding source declarations and checking an application in Lean.
- Use one pinned Mathlib checkout for all three examples and a single cached Mathlib module for the Lean check.

**Non-Goals**

- Search algorithm changes, benchmark claims, and edits to historical RH evidence fall outside the documentation update.

## Decisions

1. Pin Mathlib and Lean to v4.33.0. Build and reuse one repository-wide lexical index in a temporary directory.
2. Use `dist x y=0 ↔ x=y` to find `dist_eq_zero` with one normalized fragment. Combine `Injective f` and `f '' (s∩t)` to find `Set.image_inter`. The third example searches for Fubini using `Integrable`, `μ.prod ν`, and `∫ x,∫ y` in a declaration that spans two lines. It returns eight rows, including `MeasureTheory.integral_prod` and `MeasureTheory.integral_integral`.
3. Check those two Fubini candidates in `Mathlib.MeasureTheory.Integral.Prod` for a real-valued integral on the product of two s-finite measures, with the product integral on the left and the integral in `x` outermost on the right. `MeasureTheory.integral_prod` closes the goal. `MeasureTheory.integral_integral` states the equality in the reverse direction and its direct application is rejected.
4. Give the [RH walkthrough](../../../docs/RH_INDEX_EXAMPLE.md) a standalone setup using the three verified files and retain its detached-index instructions.

## Risks / Trade-offs

- Search results depend on the indexed files and toolchain. Pin the version, state the search scope, and describe the reported rows without claiming completeness.
- Record text-search comparisons in the implementation checks. Keep the published examples focused on type fragments and Lean application results.
- Link the cache setup for the Fubini check. The three lexical searches work before downloading compiled files.
