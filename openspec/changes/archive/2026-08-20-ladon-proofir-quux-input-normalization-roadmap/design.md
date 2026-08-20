## Context

Ladon already has an optional ProofIR bridge that consumes a compact
`proofir_bridge_index`, joins it to Ladon declaration/report evidence, and emits
review-routing diagnostics. Recent Quux work shows that the active ProofIR
surface is broader than that one shape:

- `proof_ir_lean_surface_bundle` rows carry declaration names, source paths,
  source ranges, content hashes, authority, proof trust, and replay boundaries.
- Some `proofir_bridge_index` rows use `sourceHash` where Ladon expects
  `contentHash`.
- Some bridge fixtures carry nested `sourceAnchor` rows with repository path,
  packet path, start line, and line hash.
- `ladon_proofir_bridge_snapshot` is already a downstream joined artifact with
  rendered bridge diagnostics.

The useful contract is not raw ProofIR. The useful contract is compact
source-anchored surface metadata that Ladon can attach to its own declaration
evidence while preserving the non-claim that theorem truth belongs to Lean or
explicitly named external artifacts.

## Goals / Non-Goals

**Goals:**

- Define a child-packet roadmap for Quux ProofIR input compatibility.
- Treat Quux surface bundles and bridge-index variants as normalized evidence
  inputs, not as new Ladon proof semantics.
- Preserve high-confidence source-hash joins when Quux supplies equivalent
  source evidence under a different field name.
- Represent line/source anchors conservatively instead of silently degrading or
  over-promoting them.
- Keep fixtures frozen and local to Ladon tests so CI does not depend on a dirty
  sibling checkout.

**Non-Goals:**

- Do not import Quux's full ProofIR v2/generated dialects into Ladon.
- Do not make Ladon replay Lean, recompute witnesses, or check proof truth.
- Do not make `../quux` a runtime or test dependency.
- Do not replace the existing compact `proofir_bridge_index` contract.
- Do not require ProofIR artifacts for normal atlas or Ladon report generation.

## Decisions

1. Normalize at the bridge boundary.

   Add a normalization layer before join logic rather than scattering
   artifact-kind branches through the bridge. The canonical internal shape
   remains close to the existing compact bridge index.

2. Treat `proof_ir_lean_surface_bundle` as the preferred Quux upstream seam.

   This bundle is source-first and already distinguishes extracted surface
   metadata from replay status. A child packet should either accept it directly
   or adapt it into the compact bridge-index shape with explicit diagnostics.

3. Treat `sourceHash` as a `contentHash` alias.

   If declaration name, source path, and hash match, Ladon should emit the same
   high-confidence attachment join it would have emitted for `contentHash`.
   This is field normalization only, not a change in proof authority.

4. Treat nested `sourceAnchor` rows as source-anchor evidence, not full content
   evidence.

   `repositoryPath`/`packetPath` plus `startLine`/`lineSha256` can improve
   reviewer routing, but they should not be promoted to `exact_source_hash_decl`
   unless the declaration row has a matching compatible content hash. A child
   packet should add a distinct match class or diagnostic for line-anchor joins.

5. Keep bridge snapshots optional and downstream.

   `ladon_proofir_bridge_snapshot` already contains joined rows and rendered
   diagnostics. The atlas may optionally import its root, join, and diagnostic
   summaries, but the bridge should not treat it as the primary source surface.

6. Freeze Quux-derived fixtures in Ladon.

   The active Quux checkout contains ongoing generated-artifact work. Ladon
   tests should copy small representative JSON excerpts into local fixtures and
   record their provenance, rather than reading live sibling files in CI.

## Child Packet Plan

1. `ladon-proofir-quux-surface-bundle-adapter-mini`

   Add a normalization path for `proof_ir_lean_surface_bundle`, including tests
   from frozen Quux surface-bundle excerpts.

2. `ladon-proofir-quux-source-anchor-normalization-mini`

   Add `sourceHash` alias handling and nested `sourceAnchor` support with
   conservative match kinds, trust rules, and regression tests.

3. `ladon-proofir-quux-bridge-snapshot-atlas-import-mini`

   Optionally let atlas/reviewer workflow consume
   `ladon_proofir_bridge_snapshot` summaries as already-rendered bridge evidence
   without making snapshots the canonical ProofIR bridge input.

## Risks / Trade-offs

- Schema drift -> Keep accepted shapes small, versioned by tests, and reject
  unsupported ProofIR artifact kinds with explicit diagnostics.
- Semantic overclaiming -> Keep trust rules in normalized bridge reports and
  atlas cards; attachment confidence remains separate from theorem truth.
- Fixture overfitting -> Use Quux excerpts only for compatibility coverage and
  keep synthetic adversarial tests for confidence downgrade behavior.
- Too much roadmap scope -> Stop this umbrella at packet sequencing; implement
  behavior in the child packets.
