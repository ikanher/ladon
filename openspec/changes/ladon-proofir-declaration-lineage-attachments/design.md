## Context

The proof-search database contains stable declaration IDs, source paths, block
hashes, modules, and theorem-lineage nodes. Real Matrix-Factorization data has
many duplicate candidate names, including identical fully qualified candidates
in several source files. Current bridge matching stops at the first matching
row, which is unsuitable for persistent evidence.

## Goals / Non-Goals

**Goals:**

- Resolve supported surfaces to zero or one declaration ID conservatively.
- Preserve all candidate evidence and ambiguity/staleness diagnostics.
- Overlay exact attachments on fresh active theorem lineage.
- Support theorem-first and artifact-first stored queries.

**Non-Goals:**

- No fuzzy theorem attachment from prose, result labels, module proximity, or
  filename similarity.
- No insertion of ProofIR nodes or edges into lineage tables.
- No automatic theorem truth or replay promotion.

## Decisions

1. Add attachment-candidate and selected-attachment tables. Candidate rows keep
   match method, confidence, source comparison, and declaration ID. A selected
   attachment exists only when the strongest admissible evidence is unique.
2. Rank exact declaration name plus source path plus file hash first; then exact
   declaration/path/range; then weaker context-only candidates. Name-only and
   module-only evidence can support diagnostics but not selected attachment.
3. Compare surface file hashes with `modules.source_sha256`; compare ranges and
   block hashes only under compatible documented semantics. Never compare a
   file hash to a declaration block hash.
4. Join selected attachments to lineage nodes by exact declaration identity and
   active closure generation. If the lineage closure is missing or stale,
   return attachment evidence with explicit lineage unavailability.
5. Result projections keep `proofir` and `leanLineage` sections and label bridge
   relations. No combined edge list may obscure authority.
6. Use the CDC theorem as a negative oracle: its module-level witness and
   conditional DAG can be discoverable context, but no theorem attachment is
   emitted until an artifact explicitly names and source-anchors that theorem.

## Risks / Trade-offs

- [Lexical declaration IDs change across rebuild] → Recompute attachments in
  the unpublished generation; do not copy IDs blindly.
- [Hash semantics differ] → Store hash subject/kind and permit equality only
  for the same subject.
- [Weak evidence disappears from results] → Keep context candidates and reasons
  without selecting them as attachments.
- [Lineage freshness differs from artifact freshness] → Report both identities
  separately and require compatibility for overlay.

## Migration Plan

1. Add duplicate-name, exact-path/hash, stale, and negative-CDC tests.
2. Add attachment tables, indexes, and deterministic resolver.
3. Add declaration and lineage SQL joins.
4. Add stable result projections and bridge compatibility checks.

## Open Questions

- Whether future Lean extraction can supply a compiler-stable declaration key;
  v1 recomputes joins from current generation evidence.
