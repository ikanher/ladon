## Context

The first-hand report and follow-up inspection identified functional, plan, storage, and presentation failures on a 150,743-declaration database. Existing unit fixtures are too small: they verify index names and payload shapes but do not expose planner choices, absent semantic populations, or report-volume pathologies.

## Goals / Non-Goals

**Goals:** create portable populated fixtures, freeze current behavior before edits, and separate authoritative regression predicates from host-specific calibration.

**Non-Goals:** production fixes, sibling-repository dependencies, or absolute cross-host performance promises.

## Decisions

1. Build fixtures deterministically through schema/store APIs, then assert their row-count and distribution fingerprints. Hand-written database blobs were rejected because they hide schema drift.
2. Capture both raw evidence and compact predicates. Snapshot-only testing was rejected because large JSON can match while plans or work bounds regress.
3. Use two consecutive same-host measurements and retain both. Averaging away disagreements was rejected because it masks cache and nondeterminism effects.
4. Scale the lineage fixture enough to force planner choice while keeping CI practical; record a separate read-only Matrix-Factorization calibration when present.

## Risks / Trade-offs

- [Large fixtures slow CI] → generate once per test session and use focused markers.
- [Timing is noisy] → gate deterministic plans/counts and same-host relative predicates; retain raw timings observationally.

## Migration Plan

Add fixtures and failing tests first. Do not edit production modules in this packet. Downstream packets turn named failures green one class at a time.

## Open Questions

- Final portable closure dimensions are selected from measured CI cost while preserving the bad planner choice.
