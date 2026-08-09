## Why

The build-time 512 MiB limit is stored as policy but later lineage writes can grow the same database beyond it without an explicit complete-database budget, refreshed statistics, or reliable terminal diagnostics.

## What Changes

- Separate base-build and complete-database budgets and report both explicitly.
- Estimate and enforce lineage growth inside the existing publication transaction while preserving the active closure on failure.
- Refresh planner statistics after publication and report marginal bytes and phase timing.
- Emit progress and exactly one terminal record; write requested files atomically.

## Capabilities

### New Capabilities

- `ladon-lineage-storage-budget-and-publication`: Complete-database budgets, transactional lineage publication, planner-statistics lifecycle, progress, and terminal output behavior.

### Modified Capabilities

## Impact

Changes lineage CLI options, metadata, ingestion, output writing, status/summary payloads, and failure-injection tests.
