## Why

Quux Lean-surface bundles and replay-provenance artifacts carry complementary
facts for the same surface, but the current one-input bridge cannot query them
together. Persisting both makes replay coverage inspectable only if their
statuses remain separate and externally quoted.

## What Changes

- Normalize supported compact bridge indexes and Lean-surface bundles into
  artifact-owned surfaces and claims.
- Add a narrow adapter for `proof_ir_lean_replay_provenance` and relate it to
  the exact hashed surface bundle and listed surface IDs.
- Preserve extractor replay boundaries, repository-local build outcomes,
  authority interpretations, dirty-worktree scope, and nonclaims as distinct
  evidence facts.
- Reject stale or mismatched artifact relationships and report surfaces with
  missing replay provenance without treating absence as failure.
- Keep unsupported raw ProofIR dialects catalog-only.

## Capabilities

### New Capabilities

- `ladon-proofir-surface-and-replay-ingestion`: Transactional normalization and
  querying of quoted surfaces, claims, replay provenance, and exact artifact
  relationships without authority promotion.

### Modified Capabilities

None.

## Impact

- Extends ProofIR input normalization, storage, evidence diagnostics, and
  coverage.
- Reuses current bridge trust rules and adds frozen adversarial fixtures from
  the Quux surface/replay seam.
