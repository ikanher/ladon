## Why

Ladon's bounded reports can hide upstream omissions, erase whole evidence
classes through first-N projection, and let partial atlas inputs appear
exhaustive. Separate format runs can also observe different source states, so
coverage and snapshot integrity must become an early shared foundation for the
remaining detection work.

## What Changes

- Introduce one compositional coverage model for canonical collections,
  projections, renderers, findings, review regions, and atlas consumers,
  including honest unknown-total and observed-lower-bound states.
- Make full and review projections disclose upstream and intentional omissions,
  with deterministic evidence-class stratification.
- Add severity-aware compact-text accounting that reconciles every selected
  finding with structured output.
- Prevent incomplete or fingerprint-incompatible atlas inputs from supporting
  false exhaustive queries.
- Render multiple requested formats from one immutable analysis result and
  verify source state after the last source-reading phase.
- Route integrity evidence through bounded, coverage-aware review regions.
- Keep producer exits limited to canonical registration rows and ordinary
  inspection actions; synthesize complete review-region objects only in the
  report packet's later integration milestone.
- Add tracked portable, installed-candidate, determinism, drift-injection, and
  large-inventory acceptance gates.
- Deliver the packet in two internal milestones: `coverage-foundation` lands
  first and enables the producer children; `snapshot-and-region-integration`
  finishes producer-aware stratification, inspection actions, multi-rendering,
  drift handling, and review routing after those children expose their rows.

## Capabilities

### New Capabilities

- `ladon-report-coverage-and-snapshot-integrity`: Compositional evidence
  coverage, source-stable multi-format rendering, atlas completeness, and
  integrity review routing.

### Modified Capabilities

None.

## Impact

This packet integrates with the existing owners
`ladon-large-inventory-scale-contract`, `ladon-report-contract-v2`,
`ladon-cli-execution-contract`, `ladon-installed-reportset-workflow`, and
`ladon-review-regions`; it does not introduce a parallel report schema, CLI
execution path, atlas engine, or review-region engine. It affects canonical
collection envelopes, v2/v3 projection metadata, text rendering, atlas
ingestion/query metadata, multi-output CLI options, source fingerprint
verification, and installed/scale gates. Per the umbrella dependency ledger it
starts with `coverage-foundation`, which supplies the shared coverage and
snapshot-identity contract used by the four producer children.
`snapshot-and-region-integration` then starts after scope/join,
declaration/audit, generated-family, and inspection surfaces are available, so
their strata and inspection actions can be integrated without a dependency
cycle. Those producer packets do not depend on the resulting complete region
objects.
