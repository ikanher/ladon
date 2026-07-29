## Why

A copied source tree is not evidence that a theorem package is self-contained. Ladon
must ask Lean to rebuild the capsule in a clean environment where the original
checkout is unavailable, and must report exactly what was checked and what remains
outside the guarantee.

## What Changes

- Add explicit replay and extract-with-verification CLI flows for theorem capsules.
- Run the pinned Lean toolchain under Ladon's existing supervision limits from an
  isolated fresh directory with the original checkout unavailable.
- Verify that the fully qualified theorem exists and that its toolchain-scoped
  structural identity, dependency evidence, and trust frontier match the plan.
- Detect undeclared repository reads, missing dependencies, mutations, and toolchain
  or manifest mismatches.
- Emit a deterministic machine-readable replay receipt without treating Ladon itself
  as the proof authority.

## Capabilities

### New Capabilities

- `ladon-theorem-capsule-replay`: Independently rebuild and verify a theorem capsule
  with Lean and publish bounded, auditable replay evidence.

### Modified Capabilities

- None.

## Impact

- Reuses the process supervisor and clean CLI channel contract.
- Adds replay receipts, structural fingerprints, failure taxonomy, and portable
  positive/negative fixtures.
- Establishes locked/rebuildable verification as the first guarantee; offline
  vendoring and system-hermetic execution remain outside this packet.
