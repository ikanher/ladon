## Context

Names and local IDs are display/navigation data, not global semantic identities.

## Goals / Non-Goals

**Goals:** detached content IDs, exact environment manifests, typed artifact-scoped subjects, and opaque Lean fingerprints.

**Non-Goals:** parsing Lean expressions in Python or treating database generations as canonical identity.

## Decisions

1. Content IDs hash detached canonical envelopes.
2. External references close over an explicit validated batch.
3. Exact statement comparison requires matching environment, scheme, and fingerprint.

## Risks / Trade-offs

- [Opaque fingerprints cannot be interpreted by core readers] → retain scheme metadata and report unsupported comparison explicitly.

## Migration Plan

Regenerate native-v3 artifacts and rebuild disposable databases; do not migrate legacy identities.

## Open Questions

- Minimum Lean environment Merkle inputs remain an integration-level question.
