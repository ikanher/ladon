## Context

The previous umbrella added the right bridge-boundary normalization seam, but
the external review found concrete places where the evidence contract was not
fully inspectable from the packet or from reviewer cards. These are not theorem
failures. They are source-evidence and governance hardening issues.

## Goals / Non-Goals

**Goals:**

- Preserve quoted surface metadata through reviewer-facing claims.
- Detect stale hashes whenever a joined surface and declaration carry
  comparable source hashes, regardless of fallback join kind.
- Keep source-anchor and name-only snapshot joins warning-oriented.
- Make optional input malformed handling defensive for non-dict JSON values.
- Regenerate a complete review packet with changed transitive dependencies.

**Non-Goals:**

- Do not add new ProofIR input dialects.
- Do not replay Lean or validate theorem truth.
- Do not turn source anchors into proof evidence.
- Do not make review packets self-contained Lean replay bundles.

## Decisions

1. Preserve metadata as quoted metadata.

   Reviewer cards will include `proofTrust`, `replayBoundary`,
   `extractorGuarantee`, `quotedOnly`, and selected source metadata when present.
   These fields remain quoted external context.

2. Compare stale hashes from joined rows.

   Join rows already retain declaration content hashes. Add the surface hash and
   source path needed to decide stale-source drift independent of match kind.

3. Backfill bundle source metadata before normalizing surfaces.

   Top-level bundle source fields are file-level defaults. They should only fill
   missing surface fields and should never overwrite surface-specific evidence.

4. Treat unsupported and non-object ProofIR inputs as malformed optional input.

   This preserves the optional bridge boundary: malformed input yields a
   diagnostic report instead of an exception.

5. Packet completeness is part of evidence quality.

   The regenerated pro review bundle must include source files needed by the
   included tests, especially `src/ladon/atlas.py`.

## Risks / Trade-offs

- More metadata in cards -> Keep field names explicitly quoted and non-authority.
- Broader stale-source warnings -> Require same declaration/path context before
  comparing hashes.
- Defensive malformed handling -> Keep unsupported kinds rejected, not adapted.
