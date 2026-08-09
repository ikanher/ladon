## Why

The first-hand report contains high-value observations, but implementation needs portable failing fixtures and fingerprinted measurements so later optimizations cannot change answers or erase evidence.

## What Changes

- Capture current result contracts and the known `consumers`, `constructor`, and `explain` failures.
- Add realistic populated SQLite fixtures for lineage and ProofIR plan inspection.
- Record query plans, statement counts, database/index bytes, latency, ranking, and owner-report volume twice before production changes.

## Capabilities

### New Capabilities

- `ladon-first-hand-proof-search-baselines`: Reproducible first-hand fixtures and pre-change contract, plan, latency, size, status, ranking, and report-volume baselines.

### Modified Capabilities

## Impact

Adds tests, fixtures, benchmark helpers, and recorded evidence only; production behavior is unchanged.
