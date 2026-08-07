## Context

Packet evidence currently summarizes tracked artifacts but does not retain the full
declaration route from compiled endpoints to consumers, fields, and caller seams.
The theorem-surface changelog and new route cards provide the missing inputs.

## Goals / Non-Goals

**Goals:** compact declaration frontiers, accepted/rejected route history, freshness
and build evidence, source/audit ownership, revision diffs, and packet integration.

**Non-Goals:** no proof replay by packet normalization, theorem certification, or
replacement for source/Lean review.

## Decisions

- Define a canonical frontier schema referencing declaration/source fingerprints,
  not embedding the full index or duplicate report payloads.
- Join endpoints to confirmed consumers, constructor fields, residual assumptions,
  representation diagnostics, and route cards with per-row authority.
- Compare revisions by stable declaration identity plus type/value/source/dependency
  fingerprints from the existing changelog owner.
- Packet evidence quotes frontier status and freshness; it never upgrades it.
- Provide compact text for reviewers and full JSON for tooling, both deterministically
  ordered and bounded with truncation metadata.

## Risks / Trade-offs

- [Frontiers become huge] → Reference identities, cap secondary routes, and expose
  omitted counts.
- [Revision joins misidentify renames] → Separate exact identity from heuristic rename
  candidates.
- [Packet consumers overclaim] → Preserve nonclaims and authority on every row.

## Migration Plan

Add the frontier as an optional packet artifact and report phase. Existing packet
schemas remain valid when it is absent; rollback ignores the additive artifact.
