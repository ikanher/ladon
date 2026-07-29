## Why

An exact dependency plan is useful evidence but is not itself a portable proof
artifact. Ladon needs a deterministic and path-safe materializer that preserves the
source context Lean actually saw and creates a package boundary without mutating the
analyzed checkout.

## What Changes

- Consume only compatible, non-stale theorem-capsule plans.
- Copy the theorem's owning source file from byte zero through the exact end of its
  command, preserving namespace, section, notation, attribute, variable, and
  elaborator context.
- Copy the repository-owned import closure while preserving module paths and source
  roots, plus pinned toolchain and locked Lake package metadata.
- Emit a deterministic directory or archive with hashes and an inclusion reason for
  every file.
- Reject path traversal, collisions, unsafe links, changed inputs, and unsupported
  dynamic/native packaging facets instead of producing a capsule with overstated
  guarantees.

## Capabilities

### New Capabilities

- `ladon-theorem-capsule-materialization`: Materialize a validated theorem plan as a
  deterministic, locked/rebuildable capsule outside the target repository.

### Modified Capabilities

- None.

## Impact

- Adds capsule layout and manifest schemas, safe copy/archive code, and materialization
  CLI behavior.
- Reuses source/config fingerprints produced by planning.
- Adds portable fixtures for prefix extraction, multiple source roots, unsafe paths,
  input drift, and deterministic output.
