## 1. Inventory Production SQL

- [x] 1.1 Enumerate every SQL statement in ProofIR dossier, route, triage, coverage, ingestion replacement, and foreign-key cascade code with predicate, join, ordering, and cardinality expectations.
- [x] 1.2 Encode the inventory as a test-visible query-to-access-path registry; fail when production SQL lacks a registered populated-plan probe.
- [ ] 1.3 Add skewed populated fixtures for selected/unselected attachments, diagnostics, DAG obligations, replay failures, stale evidence, unsupported artifacts, and disconnected declarations.

## 2. Add Direct Lookup Paths

- [x] 2.1 Add and test selected attachment lookup by `declaration_id` and any required covering output columns.
- [x] 2.2 Add and test diagnostics lookup by `artifact_id` with deterministic reason/subject ordering.
- [x] 2.3 Add and test DAG obligation lookup plus forward/reverse route paths and node identity lookup.
- [x] 2.4 Verify exact declaration name uses the rightsizing packet's direct name index rather than skip-scan.

## 3. Optimize Negative-Evidence Triage

- [x] 3.1 Add measured partial indexes for stale attachments and stale/foreign replay surfaces.
- [x] 3.2 Add measured partial indexes for failed replay runs, unmatched witnesses, and unsupported/malformed artifact states where selective.
- [x] 3.3 Rewrite OR queries into bounded indexed unions when one unindexed OR branch forces a scan; preserve deterministic deduplication.
- [x] 3.4 Assert each triage family uses a selective path and fixed statement count on populated fixtures.

## 4. Audit Foreign-Key Child Paths

- [x] 4.1 Derive every child-key prefix from `PRAGMA foreign_key_list` and compare it with primary/explicit index prefixes.
- [x] 4.2 Add missing child indexes only for measured replacement/cascade paths and record byte cost.
- [ ] 4.3 Run generation replacement and deletion benchmarks with foreign keys enabled and failure injection.

## 5. Close Access-Path Gates

- [x] 5.1 Run all ProofIR dossier, route, triage, attachment, ingestion, coverage, schema, FK, integrity, and deterministic tests.
- [ ] 5.2 Run populated plan/latency gates twice and compare index-byte growth against the storage budget.
- [x] 5.3 Validate this OpenSpec change strictly and ensure no query result promotes ProofIR evidence into Lean truth.
