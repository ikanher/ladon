## Context

Validated artifacts need fast bounded queries, but database layout must follow stable semantics and measured SQL.

## Goals / Non-Goals

**Goals:** normalized disposable schema, deterministic projection, explicit provenance/coverage, query registry, FK/index gates, and storage accounting.

**Non-Goals:** canonical storage, in-place migration, graph-database dependency, or extension-driven semantic decisions.

## Decisions

1. Tables cover artifacts, observations, environments, subjects, claims, steps, premises, conclusions, substitutions, check runs/results, surfaces, attachments, coverage, omissions, and extensions.
2. Every row retains source content artifact and local pointer provenance.
3. Rebuilds are atomic and reject incompatible generations; no retired ProofIR semantic table exists.
4. Production SQL is registered with populated plan predicates and foreign-key child-prefix checks.
5. Storage accounting reports table/index bytes and marginal artifact projection cost.
6. Unknown extensions are stored as bounded canonical blobs and excluded from core indexes.

## Risks / Trade-offs

- [Normalized joins cost latency] → measure dossier/slice/triage plans before adding covering indexes.
- [Schema growth] → partial indexes and per-family byte budgets.

## Migration Plan

Build the native-v3 projection in disposable fixtures, bump the private schema, and require a clean rebuild. Retired schemas are deleted, not compared or migrated.

## Open Questions

- Whether statement and term opaque payloads live in SQLite or a content-addressed blob directory.
