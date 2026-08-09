## Context

The consumer implementation returns `complete` whenever the target symbol exists. The constructor CLI passes an empty tuple to an analysis function that always returns `available`. Existing tests encode these placeholders rather than the intended coverage contract.

## Goals / Non-Goals

**Goals:** derive status from stored coverage, execute real constructor SQL, distinguish observed absence from unavailable evidence, and version changed semantics.

**Non-Goals:** synthesizing constructors, inferring dependencies lexically, or treating partial Lean extraction as complete.

## Decisions

1. Centralize semantic coverage evaluation from `evidence_coverage` and module semantic state before running result queries.
2. Query structures by exact identity/module and fields by ordered structure ID; known zero-field requires explicit complete coverage metadata, not merely zero rows.
3. Return v2 payloads with status, population, scope, authority, omissions, and bounds. Preserve a narrowly labeled compatibility adapter if required.
4. Replace placeholder tests with positive complete, unavailable, partial, missing, ambiguous, and known-empty cases.

## Risks / Trade-offs

- [More unavailable results initially] → this is honest until semantic extraction is populated; documentation explains how to build it.
- [Coverage metadata disagrees with rows] → treat disagreement as integrity failure, not empty evidence.

## Migration Plan

Introduce v2 result builders, wire read-only database handlers, retain explicit v1 compatibility only during the release window, then update docs/skill.

## Open Questions

- Whether module-scoped consumer completeness is exposed in the first v2 CLI or repository-wide only.
