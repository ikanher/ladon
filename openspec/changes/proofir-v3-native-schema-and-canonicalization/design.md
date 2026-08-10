## Context

Artifact-kind strings without complete schemas cannot safely define an interchange representation.

## Goals / Non-Goals

**Goals:** one envelope, closed schemas, deterministic IDs/bytes, stable staged diagnostics, and bounded ordinary CLI operations.

**Non-Goals:** legacy conversion, floating-point JSON, or partial output publication.

## Decisions

1. The canonical profile accepts bounded JSON-safe integers and rejects floats.
2. Every supported kind has a complete payload validator and reference-closure rules.
3. Validated artifacts are frozen independently of caller dictionaries.

## Risks / Trade-offs

- [Strict schemas reject experimental fields] → retain namespaced extensions behind explicit bounds.

## Migration Plan

Delete legacy paths, regenerate native-v3 artifacts, and rebuild disposable projections.

## Open Questions

- None.
