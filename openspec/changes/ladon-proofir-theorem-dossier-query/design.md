## Context

The v3 proof-search database stores catalog artifacts, surfaces, claims, replay runs, DAGs, declaration attachments, and lineage tables. The current theorem projection queries only exact `declaration_name` surfaces and a selected attachment, so callers still correlate evidence manually.

## Goals / Non-Goals

**Goals:**

- Produce one bounded theorem result with stable, separate evidence sections.
- Select theorem evidence only from explicit names or selected attachments.
- Surface generation/freshness, authority, relation methods, diagnostics, omissions, and nonclaims.
- Keep queries read-only and SQL-first.

**Non-Goals:**

- Proving theorem truth, replaying Lean, or running ProofIR generators.
- Treating ProofIR DAG edges as Lean declaration dependencies.
- Fuzzy attachment based on filenames, descriptions, or module proximity.

## Decisions

1. The result schema is `ladon-proofir-theorem-dossier-v1` with `declaration`, `attachments`, `surfaces`, `claims`, `replay`, `obligationContext`, `lineage`, `diagnostics`, `coverage`, and `nonclaims` sections. Separate sections prevent authority collapse; a flattened card was rejected.
2. The query starts from the exact declaration candidate and selected `proofir_attachments`, then admits explicit surface declaration-name matches as unattached quoted evidence. Proximity joins are excluded.
3. Each section has its own deterministic cap and truncation record; a single global SQL join was rejected because one-to-many products double-count rows.
4. Replay is related only through exact stored artifact/surface relations. Lineage is overlaid only when its generation identities are compatible.
5. Aggregate summary fields are derived from the returned normalized identities, never raw artifact payloads.

## Risks / Trade-offs

- [Several bounded queries can be slower than one join] → use named indexes and record query-plan tests.
- [Explicit identity can return less evidence] → return context-only and unmatched sections rather than guessing.
- [Schema evolution] → version the public dictionary independently of private SQLite tables.

## Migration Plan

Add the v1 dossier alongside the current thin query, switch the ordinary CLI after parity tests, then remove the private thin projection when no internal caller remains.

## Open Questions

- Whether theorem aliases should be accepted only through the existing declaration alias table or deferred to a later packet.
