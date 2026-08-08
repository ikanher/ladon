## Context

The query pipeline must preserve the distinction between SQL candidate evidence and verified Lean matches while remaining interactive on large repositories.

## Goals / Non-Goals

**Goals:** scoped SQL shortlist buckets, batched verification, deterministic ranking, complete public v1 contract, and diagnostic rejection mode.

**Non-Goals:** returning structural shortlist hits as semantic results or searching unbounded repositories.

## Decisions

1. Resolve module/import scope and semantic freshness before elaboration; fail closed on stale data unless stored-only candidates are explicitly requested.
2. Union exact fingerprint, head/arity, shape, constant-overlap, and FTS buckets, filtering scope/ownership in SQL before the cap.
3. Return verified applications by default and rank lexicographically by match class, residuals, unresolved goals, adapters, import/ownership/namespace/name costs, then FQN.

## Risks / Trade-offs

- [Shortlist misses useful candidates] → recall fixtures and bucket diagnostics; semantic FTS is a bounded final fallback.
- [Ranking appears opaque] → expose vector and human-readable explanation.
