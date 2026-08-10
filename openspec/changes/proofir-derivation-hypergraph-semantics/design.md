## Context

A path through one application node does not establish that all premises were supplied.

## Goals / Non-Goals

**Goals:** explicit AND/OR semantics, accepted/plan/attempt separation, cycle policy, and bounded query-specific nonclaims.

**Non-Goals:** universal proof-term syntax or treating a navigation route as a complete proof.

## Decisions

1. One step owns ordered premise, conclusion, rule, substitution, context, and supporting-observation references.
2. Premises are conjunctive; same-conclusion steps are alternatives.
3. Acyclic artifacts reject cycles; recursive artifacts declare SCC semantics.

## Risks / Trade-offs

- [Complete slices grow quickly] → every query has explicit node, edge, depth, alternative, and output caps.

## Migration Plan

Regenerate accepted derivations, plans, and attempt logs as distinct v3 artifacts.

## Open Questions

- None.
