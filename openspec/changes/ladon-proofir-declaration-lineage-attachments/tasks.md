## 1. Establish Preconditions And Failing Attachment Oracles

- [ ] 1.1 Verify the catalog, surface/replay, and DAG packet exit classes pass and all duplicated umbrella specs match standalone specs.
- [ ] 1.2 Add fixtures for exact file-hash/path/name, exact compatible range, mismatched hash subjects, stale file hash, basename-only, module-only, and several identical candidate names in different paths.
- [ ] 1.3 Add `tests/test_proofir_attachments.py` with failing strongest-unique selection, ambiguity, rejected-candidate, staleness, rebuild-recompute, and query-plan assertions.
- [ ] 1.4 Add `tests/test_proofir_lineage_overlay.py` with failing fresh, missing, and stale lineage overlay cases and graph-authority separation assertions.
- [ ] 1.5 Add the exact Quux CDC theorem negative oracle: current module witnesses/DAG context are visible but no theorem attachment is synthesized.

## 2. Add Attachment Schema And Indexes

- [ ] 2.1 Add artifact-generation-scoped candidate and selected-attachment tables referencing surface and declaration IDs with explicit method, confidence, freshness, and rejection reason.
- [ ] 2.2 Add uniqueness ensuring at most one selected current attachment per surface while allowing bounded competing candidate rows.
- [ ] 2.3 Add named indexes for surface-to-candidates, declaration-to-surfaces, candidate declaration name/path, selected attachment, and lineage-node overlay.
- [ ] 2.4 Extend foreign-key/index validation, counts, coverage, and omission reasons for exact, ambiguous, stale, unmatched, and context-only populations.

## 3. Implement Source-Compatible Resolution

- [ ] 3.1 Document hash subjects and compare surface whole-file hashes only with owning module source hashes; never equate file and declaration-block hashes.
- [ ] 3.2 Query candidates by exact declaration/candidate identity plus source path, then compute source-hash and compatible-range evidence with deterministic strongest-first ranking.
- [ ] 3.3 Select a declaration ID only when the strongest admissible rank contains exactly one candidate; otherwise store ambiguity or unmatched diagnostics and no selected row.
- [ ] 3.4 Preserve weaker candidates with method/confidence/rejection reasons, but cap and deterministically order their public projection.
- [ ] 3.5 Recompute all attachment rows during each unpublished base-index generation so obsolete lexical declaration IDs are never copied.

## 4. Implement Lineage Overlay Queries

- [ ] 4.1 Add SQL joins from selected declaration attachments to compatible active lineage nodes without modifying lineage tables or edges.
- [ ] 4.2 Compare base generation, repository, source, configuration, toolchain, helper, and lineage schema identities before declaring an overlay fresh.
- [ ] 4.3 Return declaration attachment even when lineage is missing/stale, with a separate explicit lineage availability/freshness result.
- [ ] 4.4 Add bounded theorem-first, declaration-first, surface-first, and artifact-first render-neutral query services with source anchors and coverage.
- [ ] 4.5 Keep ProofIR evidence, bridge attachment, and Lean lineage in separate result sections and label every authority/nonclaim.

## 5. Prove No Inferred Theorem Evidence

- [ ] 5.1 Reject selection from basename, module proximity, guarantee text, result text, descriptions, filenames, or related-artifact proximity alone.
- [ ] 5.2 Prove the CDC negative query returns no attached ProofIR evidence for `nonempty_indexedCycleDoubleCover` and explains which nearby artifacts lack explicit theorem identity.
- [ ] 5.3 Prove adding an explicit exact source-backed surface fixture changes only that theorem's attachment result.
- [ ] 5.4 Prove duplicate Matrix-Factorization-style candidate names remain ambiguous until path/hash evidence uniquely identifies one row.

## 6. Verify The Packet Exit Class

- [ ] 6.1 Run attachment and lineage-overlay suites, exact/ambiguous/stale/context matrices, CDC negative/positive pair, and rebuild-recompute tests.
- [ ] 6.2 Run foreign-key, constraint, required-index, `EXPLAIN QUERY PLAN`, cap, deterministic-order, and atomicity gates.
- [ ] 6.3 Run preceding ProofIR packets, theorem lineage, proof-search index, full Python, strict quality, compile, and `git diff --check` gates.
- [ ] 6.4 Audit for first-row selection, incompatible hash comparison, fuzzy theorem inference, copied stale declaration IDs, merged edge kinds, and authority promotion.
