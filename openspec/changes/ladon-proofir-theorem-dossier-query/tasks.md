## 1. Freeze The Dossier Contract With Failing Tests

- [x] 1.1 Copy one exact attached theorem, one explicit unattached surface, one duplicate-name ambiguity, and the Quux CDC negative case into compact fixtures.
- [x] 1.2 Add `tests/test_proofir_theorem_dossier.py` and assert the exact top-level v1 section names before implementing joins.
- [x] 1.3 Assert replay success and claim status remain separate in the fixture with a zero-return replay of a conditional claim.
- [x] 1.4 Assert the CDC fixture returns nearby artifacts under context-only evidence and no theorem attachment.
- [x] 1.5 Assert per-section ordering, caps, omitted counts, canonical JSON stability, and repeat-query byte equality.

## 2. Define The Versioned Result Model

- [x] 2.1 Add constants and typed construction helpers for `ladon-proofir-theorem-dossier-v1` in `proofir_queries.py`.
- [x] 2.2 Define declaration, attachment, surface, claim, replay, obligation-context, lineage, diagnostic, coverage, truncation, and nonclaim dictionaries.
- [x] 2.3 Add one bounds dataclass with validated positive caps for every one-to-many section and total serialized bytes.
- [x] 2.4 Add deterministic identity/deduplication helpers; never deduplicate solely by display name.

## 3. Implement Conservative SQL Projections

- [x] 3.1 Resolve the exact Lean declaration and selected attachment with parameterized queries; return ambiguity rather than the first row.
- [x] 3.2 Query explicit `declaration_name` surfaces separately and classify them as attached or unattached from stored attachment rows.
- [x] 3.3 Query claims through `proofir_surface_claims` and preserve claim-only rows without manufacturing a declaration attachment.
- [x] 3.4 Query replay runs/surfaces and artifact relationships only through exact stored bundle/artifact identities.
- [x] 3.5 Query DAG participation by exact stored surface/claim identities and keep it in `obligationContext`.
- [ ] 3.6 Overlay compatible active lineage identities; return declaration evidence even when lineage is missing or stale.
- [ ] 3.7 Query artifact/generation diagnostics and omissions relevant to every returned identity.

## 4. Enforce Authority, Freshness, And Bounds

- [x] 4.1 Preserve source status/authority fields verbatim and add mandatory per-section relation methods and nonclaims.
- [ ] 4.2 Compare repository, configuration, source, toolchain, helper, schema, and generation identities before marking lineage or attachments fresh.
- [x] 4.3 Apply SQL limits before materialization, disclose matched/returned counts, and enforce the final output-byte cap.
- [ ] 4.4 Add `EXPLAIN QUERY PLAN` assertions for theorem name, selected attachment, surface, replay, and lineage entry queries.

## 5. Integrate Without Breaking Existing Callers

- [x] 5.1 Add the dossier service alongside the thin theorem query and convert the thin query into a compatibility projection.
- [ ] 5.2 Update build/status metadata only where the dossier needs an already-stored generation identity; add no second cache or database.
- [x] 5.3 Add read-only connection tests proving the query performs no writes and invokes no subprocesses.

## 6. Verify The Packet Exit Class

- [x] 6.1 Run dossier exact/unattached/ambiguous/context-only/stale/cap matrices and existing attachment, lineage, replay, DAG, and bridge tests.
- [ ] 6.2 Run schema integrity, foreign keys, required indexes, query plans, deterministic output, compile, strict quality, and `git diff --check`.
- [ ] 6.3 Audit for filename/proximity inference, first-row selection, Cartesian double counting, authority promotion, and hidden external execution.
