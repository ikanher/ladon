## Context

Evidence records need exact subjects, environments, producers, guarantees, and completeness boundaries.

## Goals / Non-Goals

**Goals:** typed observations, exact check results, orthogonal evidence dimensions, selector-scoped coverage, and stable limitations.

**Non-Goals:** a scalar trust score or unqualified theorem-truth classification.

## Decisions

1. Process success without a subject guarantee remains a process observation.
2. Accepted checker results name exact inputs, subject, environment, checker, bounds, and guarantee scope.
3. Coverage reports each ingestion stage and query-matched population separately.

## Risks / Trade-offs

- [Detailed evidence is verbose] → normalize it in SQLite and expose bounded projections.

## Migration Plan

Emit native-v3 observations and rebuild projections; do not translate producer trust strings.

## Open Questions

- None.
