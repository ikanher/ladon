## Why

Elaborated proof-shape evidence can help reviewers inspect Lean proofs, but it
must not blur parser references with Lean-elaborated dependencies or theorem
truth.

## What Changes

- Add optional proof-xray witness ingestion.
- Require authority labels and backend metadata.
- Report proof-shape pressure such as automation hotspots and trust footprints.
- Keep the backend absent-safe.

## Capabilities

### New Capabilities

- `ladon-proof-xray-staging`: Optional authority-labeled proof-shape witness
  rows and reviewer summaries.

### Modified Capabilities

None.

## Impact

- Affected code: optional JSON input, pipeline, rendering, docs, and tests.
