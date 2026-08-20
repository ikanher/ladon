## Why

A capsule cannot be soundly assembled from a lexical name match or the bounded
dependency lists used in human-facing reports. Ladon needs a read-only planning phase
that asks the target Lean environment to resolve the exact theorem and records every
semantic and build input needed by later phases.

## What Changes

- Add a caller-neutral CLI operation that plans extraction for one fully qualified
  theorem name.
- Confirm declaration identity and kind with the repository's pinned Lean toolchain.
- Compute complete type/value dependency and repository module/import closures through
  a dedicated protocol that detects partial or truncated results.
- Record exact source-command boundaries, compiler-generated dependencies, trust
  facts, toolchain/configuration fingerprints, and unsupported build/runtime facets.
- Emit a deterministic plan that later materialization can reject when the repository
  has drifted.

## Capabilities

### New Capabilities

- `ladon-theorem-capsule-planning`: Resolve and plan a closure-complete,
  locked/rebuildable theorem capsule without changing the target repository.

### Modified Capabilities

- None.

## Impact

- Reuses Lean helper execution, declaration source evidence, the canonical module DAG,
  snapshot metadata, and existing process limits.
- Adds an exact dependency-stream protocol whose completeness is distinct from the
  capped declaration-surface report.
- Adds plan schemas, diagnostics, CLI coverage, and portable fixtures.
