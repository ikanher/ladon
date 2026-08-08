## Context

The current database stores lexical and selected evidence relations but not a complete, constrained semantic declaration surface suitable for shortlisting and reverse-consumer claims.

## Goals / Non-Goals

**Goals:** disposable v4 generations, integer symbol dictionary, complete semantic relations, explicit coverage/status, required foreign keys/indexes, bounded display text, and validated query plans.

**Non-Goals:** in-place migration, storing Lean expressions as public authority, or broad integer-key conversion unrelated to high-cardinality edges.

## Decisions

1. Add normalized declaration columns plus `symbols`, `declaration_dependencies`, `declaration_shapes`, and `module_semantic_state`; extend binders/structures/fields.
2. Use `WITHOUT ROWID` for composite-key edge tables and bidirectional covering indexes for dependencies.
3. Every external dependency target receives a symbol row, preserving external-frontier evidence.
4. Fingerprints and coarse keys are shortlist evidence only. Current authoritative types are obtained from Lean during verification.
5. Validate DDL, foreign keys, integrity, indexes, plans, and `PRAGMA optimize` before publication.

## Risks / Trade-offs

- [Index growth] → integer symbols, bounded text, size measurements, and no duplicate imported declarations.
- [Schema drift] → single schema owner and rebuild-required status for incompatible generations.
