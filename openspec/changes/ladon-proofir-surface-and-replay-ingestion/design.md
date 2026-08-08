## Context

The current normalizer accepts `proofir_bridge_index` and
`proof_ir_lean_surface_bundle`. Quux additionally emits separate
`proof_ir_lean_replay_provenance` files. In the current corpus, 63 surface rows
all quote an extractor boundary of `not_replayed_by_extractor`, while 52 have a
separate successful repository-local replay artifact.

## Goals / Non-Goals

**Goals:**

- Persist artifact-owned surfaces and claims from the two existing input seams.
- Normalize replay provenance and exact bundle/surface relationships.
- Preserve quoted authority, replay boundary, source identity, and nonclaims.
- Make replay coverage and stale/missing relationships queryable.

**Non-Goals:**

- No theorem-truth validation or proof-term transport.
- No collapse of extractor and replay-provenance statuses.
- No ingestion of generic `proof_ir_surface_bundle` or replay-like dialects by
  structural guessing.

## Decisions

1. Add artifact-owned `proofir_surfaces`, `proofir_claims`,
   `proofir_surface_claims`, `proofir_replay_runs`, and
   `proofir_replay_surfaces` with composite uniqueness and cascading artifact
   foreign keys.
2. Reuse `normalize_proofir_index` for existing admitted inputs, then validate
   database-required identities and caps in a storage adapter. Do not fork the
   bridge's authority normalization.
3. Adapt replay provenance only when `artifactKind` and schema are explicitly
   supported. Preserve command, return code, toolchain versions, repository
   scope, dirty state, guarantee, authority interpretation, and nonclaims as
   quoted evidence.
4. Link replay to a surface bundle only when the referenced repository-relative
   path and full content hash match a cataloged artifact. Link listed surfaces
   only when IDs belong to that exact bundle.
5. A surface without provenance has coverage `not_observed`; it is not a failed
   replay. A nonzero return code is a recorded failed run, not theorem falsity.
6. Keep derived bridge/architecture snapshots catalog-only in v1 to avoid
   duplicate source surfaces.

## Risks / Trade-offs

- [A successful build is read as proof transport] → Render repository scope,
  dirty state, command, and explicit nonclaims beside return code.
- [Surface IDs collide across artifacts] → Scope identity by artifact and use
  relationship tables for logical correspondence.
- [Replay points at stale bundle bytes] → Retain the provenance artifact but
  emit a stale relationship diagnostic and no active replay-surface join.
- [Large prose fields bloat SQLite] → Bound quoted text and record truncation in
  diagnostics; retain source artifact identity for full inspection.

## Migration Plan

1. Add frozen bundle/provenance fixtures and failing storage tests.
2. Add tables and adapters under the catalog generation transaction.
3. Add queries and coverage counts.
4. Verify existing in-memory bridge behavior remains compatible.

## Open Questions

- Whether compact bridge claims with no surface ID need a dedicated claim-only
  query in v1; storage must preserve them even if the first CLI does not render
  them separately.
