## Context

`proof_ir_lean_surface_bundle` is a source-first artifact produced by Quux. Its
surfaces include declaration identity, source path/range/hash, authority, proof
trust, replay boundary, and extractor guarantee. That is enough for Ladon to
route review and join to declaration source evidence, but it is not a complete
ProofIR dialect.

## Goals / Non-Goals

**Goals:**

- Normalize surface bundles before join logic.
- Preserve source and authority metadata needed by reviewer cards.
- Avoid mutating input payloads.
- Keep bridge reports using the same `ladon_proofir_bridge_report` output shape.

**Non-Goals:**

- Do not replay Lean.
- Do not validate ProofIR claim semantics.
- Do not parse raw ProofIR v2 generated packets.

## Decisions

1. Add a pure `normalize_proofir_index` helper.

   It receives the optional input payload and returns a compact bridge index
   plus any normalization diagnostics. Existing join logic then consumes the
   compact shape.

2. Synthesize claims from surfaces when the bundle has no separate claim table.

   The bridge only needs claim status/authority/scope for cards. Surface bundle
   rows can provide warning-level quoted metadata without becoming proof truth.

3. Keep unsupported kinds malformed.

   Only the existing compact index and the Quux surface bundle are accepted in
   this child.

## Risks / Trade-offs

- Missing claim details -> Cards quote only the metadata present on the surface.
- Schema drift -> Freeze representative bundle fixtures in Ladon tests.
- Overclaiming -> Trust rules continue to say statuses are quoted, not promoted.
