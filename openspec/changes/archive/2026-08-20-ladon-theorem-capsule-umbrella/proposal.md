## Why

Ladon can identify declarations, source ranges, module imports, and direct elaborated
dependencies, but it cannot yet turn a named theorem into a portable artifact that
another caller can rebuild and check away from the original checkout. A theorem
extractor must coordinate semantic closure, build closure, source context, package
metadata, and independent Lean replay without claiming that a dependency DAG has one
unique path or that the result is globally minimal.

## What Changes

- Introduce a theorem-capsule workflow for ordinary CLI callers, split into planning,
  deterministic materialization, and clean-room replay packets.
- Resolve fully qualified theorem names with the pinned Lean environment and compute
  an exact, non-report-capped semantic and module/build closure.
- Package the owning file through the end of the theorem command together with the
  repository-owned import closure, toolchain and locked package metadata.
- Verify the capsule with Lean while the original checkout is unavailable and emit
  machine-readable evidence about the replay, inclusion reasons, trust frontier, and
  unsupported facets.
- Define the first product boundary as a closure-complete, locked/rebuildable capsule.
  Declaration-minimal slicing, global minimization, offline dependency vendoring, and
  system-hermetic packaging remain explicit future work.

## Capabilities

### New Capabilities

- `ladon-theorem-capsule-planning`: Resolve a theorem exactly and produce a
  drift-detecting plan containing separate semantic and build closures.
- `ladon-theorem-capsule-materialization`: Turn a valid plan into a deterministic,
  path-safe capsule without modifying or relying on writes to the target repository.
- `ladon-theorem-capsule-replay`: Rebuild and verify a capsule in isolation and emit
  a structured replay receipt.

### Modified Capabilities

- None.

## Impact

- Adds three coordinated implementation packets plus umbrella governance.
- Extends the installed `ladon` CLI with caller-neutral theorem-capsule operations.
- Reuses the canonical source layout and lexical scanner, module DAG algorithms,
  elaborated declaration evidence, snapshot registry, process supervisor, and CLI
  output contract rather than creating parallel authorities.
- Requires a dedicated exact dependency protocol because report-oriented declaration
  rows are intentionally bounded and cannot justify capsule completeness.
- Adds portable fixtures and negative gates for stale plans, missing files, toolchain
  drift, unsafe paths, undeclared reads, and replay failures.
