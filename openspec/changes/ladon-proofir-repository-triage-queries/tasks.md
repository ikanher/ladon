## 1. Preregister Triage Families And Fixtures

- [x] 1.1 Define stable rule IDs and exact predicates for every initial triage family in a fixture manifest.
- [x] 1.2 Build one portable mixed-evidence repository with one positive member and one near-miss negative oracle per family.
- [x] 1.3 Add `tests/test_proofir_triage.py` with exact finding keys, reasons, owners, authorities, counts, ordering, and coverage.
- [ ] 1.4 Add duplicate-symptom fixtures proving stable deduplication and cross-references.

## 2. Define Triage Results And Bounds

- [x] 2.1 Define `ladon-proofir-repository-triage-v1` with generation, summary, families, findings, coverage, truncation, and nonclaims.
- [x] 2.2 Define deterministic finding IDs from rule plus semantic subject identity, never display text.
- [x] 2.3 Add per-family/global row and output-byte caps with validated defaults.
- [ ] 2.4 Store priority inputs explicitly and keep presentation ordering deterministic and non-ML.

## 3. Implement Explicit SQL Predicates

- [x] 3.1 Query surfaces with no selected attachment and surfaces with multiple strongest candidates as separate families.
- [x] 3.2 Query stale attachments and exact-source mismatches without comparing declaration-block hashes to whole-file hashes.
- [x] 3.3 Query replay-not-observed, stale-target, foreign-surface, and nonzero-return runs separately.
- [ ] 3.4 Query conditional conclusion nodes and authority-boundary routes using the route child service.
- [x] 3.5 Query stale/unmatched DAG witnesses and unsupported/malformed catalog artifacts.
- [ ] 3.6 Query evidence disconnected from current declarations while preserving explicit context-only identities.

## 4. Add Ownership, Grouping, And Query Plans

- [ ] 4.1 Attach exact source path/declaration owners only; preserve basename/module proximity as rejected context.
- [ ] 4.2 Group findings by family, owner, artifact, and theorem identity without changing raw finding facts.
- [ ] 4.3 Add named indexes only where `EXPLAIN QUERY PLAN` proves an uncovered routine predicate.
- [ ] 4.4 Assert per-family matched/returned/truncated counts agree with negative-evidence coverage.

## 5. Verify The Packet Exit Class

- [x] 5.1 Run every family and near-miss oracle, deduplication, ownership, grouping, caps, and deterministic rebuild tests.
- [ ] 5.2 Run dossier, negative-evidence, routes, catalog, attachment, replay, DAG, and lineage suites.
- [ ] 5.3 Run integrity, foreign keys, required indexes, query plans, full Python, compile, strict quality, and `git diff --check`.
- [ ] 5.4 Audit for fuzzy ownership, conditional-equals-defect language, duplicate findings, opaque ranking, and unbounded scans.
