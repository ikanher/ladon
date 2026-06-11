## Context

The atlas workflow currently expects bridge reports shaped like
`ladon_proofir_bridge_report`, with top-level `joins`, `diagnostics`, and
`reviewerCards`. Quux's `ladon_proofir_bridge_snapshot` is a downstream
artifact with equivalent summary information nested under `bridgeReport` and
root identity under `sourceLadonReport`.

## Goals / Non-Goals

**Goals:**

- Normalize snapshot summaries before atlas workflow scoring.
- Keep the canonical machine-readable surface as atlas JSON.
- Preserve ProofIR diagnostic namespacing and trust-boundary notes.

**Non-Goals:**

- Do not feed snapshots back into the bridge join engine.
- Do not use snapshots as proof status authority.
- Do not require snapshots for atlas generation.

## Decisions

1. Normalize bridge report inputs at atlas workflow entry.

   A helper can convert snapshots into the existing bridge-report summary shape
   used by review-priority, low-confidence, and stale-evidence sections.

2. Use snapshot root metadata when reviewer cards are absent.

   `sourceLadonReport.analysisRootModule` provides the root needed for workflow
   grouping and scoring.

3. Convert diagnostic field names conservatively.

   `diagnosticId` maps to `ruleId`, `severity` maps to `level`, and message text
   is preserved when available.

## Risks / Trade-offs

- Snapshot drift -> Keep support limited to summary fields needed by atlas
  workflow.
- Status overclaim -> Trust notes must continue to state that statuses are
  quoted, not promoted by Ladon.
