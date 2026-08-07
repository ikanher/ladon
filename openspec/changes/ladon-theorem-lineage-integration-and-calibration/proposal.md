## Why

Small graph fixtures cannot establish that lineage remains useful and bounded on
real Lean repositories. The integrated workflow needs reproducible correctness,
quality, database-access-path, and scale gates plus maintained user guidance.

## What Changes

- Add portable end-to-end fixtures for multiple axioms, type/value distinctions,
  external frontiers, shared dependencies, cycles, stale generations, and caps.
- Measure ingestion, warm SQL query, projection, and CLI latency separately on the
  existing Quux theorem and selected Matrix-Factorization theorems.
- Add result-quality checks for representative routes and bottlenecks without using
  sibling repositories as correctness oracles.
- Update CLI docs and the maintained Ladon skill with the database-first lineage
  workflow and the actual-proof-versus-alternative-proof distinction.

## Capabilities

### New Capabilities

- `ladon-theorem-lineage-integration-and-calibration`: End-to-end acceptance,
  large-project calibration, and maintained documentation for theorem lineage.

### Modified Capabilities

None.

## Impact

- Adds integration fixtures, benchmark records, documentation, and skill updates.
- Depends on all four implementation packets and preserves generated DBs as ignored,
  disposable project-local state.
