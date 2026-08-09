## Context

Status, authority, trust, freshness, replay, confidence, and guarantees currently overlap. Coverage counts are often database-wide rather than subject/population-scoped.

## Goals / Non-Goals

**Goals:** represent evidence as typed observations with explicit subject, environment, producer, guarantee, result, limitations, and coverage.

**Non-Goals:** computing Lean truth in Python/Rust or collapsing dimensions into a trust score.

## Decisions

1. One observation envelope covers checker results, attachments, replay relationships, assertions, and external attestations through typed payloads.
2. Assertion, validation, freshness, attachment, replay, authority basis, and guarantee scope remain independent enums/records.
3. Accepted checker results require exact checker identity, environment, inputs, subject results, operation, output digests, and bounds.
4. Coverage names a population kind and selector plus universe-known, expected, observed, projected, matched, omissions, and bounds.
5. Query coverage is derived from contributing artifact coverage and the requested subject; whole-table population is never sufficient.
6. Human nonclaims are paired with stable limitation IDs.

## Risks / Trade-offs

- [Verbose records] → content-address shared checker/environment records and keep projections compact.
- [Producer terminology differs] → map producer fields into namespaced extensions until a typed mapping is justified.

## Migration Plan

Freeze native observation vectors, update queries to consume them directly, and delete retired observation adapters. No legacy field projection is retained.

## Open Questions

- Which guarantee scopes require Lean-worker confirmation rather than producer assertion?
