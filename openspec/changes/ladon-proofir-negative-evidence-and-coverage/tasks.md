## 1. Freeze The Coverage Vocabulary

- [x] 1.1 Add a table-driven fixture covering not-configured, unavailable, observed-absent, unsupported, malformed, stale, ambiguous, failed, unmatched, missing, and context-only states.
- [x] 1.2 Add `tests/test_proofir_negative_evidence.py` with exact coverage dictionaries for catalog, surface, claim, attachment, replay, DAG, witness, and lineage families.
- [ ] 1.3 Add combined-state oracles for stale-plus-failed replay and ambiguous-attachment-plus-context-only DAG evidence.
- [x] 1.4 Add assertions that unconfigured/unavailable never serialize as observed absence.

## 2. Add Shared Coverage Models

- [x] 2.1 Define one stable evidence-family enumeration and one coverage-state enumeration.
- [x] 2.2 Implement a constructor requiring configuration, availability, inspected population, matched population, state, reasons, and truncation.
- [x] 2.3 Add mandatory open-world nonclaims and compact human explanations for every state.
- [ ] 2.4 Reject inconsistent combinations such as unavailable with a positive inspected population.

## 3. Derive Generation-Scoped Coverage

- [x] 3.1 Derive catalog configured/supported/unsupported/malformed populations from active generation rows.
- [x] 3.2 Derive normalized surface/claim/attachment/replay/DAG/witness populations with separate stale/failure/ambiguity predicates.
- [ ] 3.3 Derive compatible/missing/stale lineage availability without interpreting missing lineage as no Lean dependencies.
- [x] 3.4 Add selector-specific observed-absence only after the relevant indexed population is queried.
- [ ] 3.5 Recompute stored coverage during atomic rebuild and prove no stale prior-generation counts survive.

## 4. Integrate Dossier And Artifact Queries

- [x] 4.1 Add coverage and negative-evidence sections to theorem dossiers without changing positive evidence rows.
- [x] 4.2 Add artifact coverage for unsupported, malformed, stale-target, and unmatched-relation states.
- [x] 4.3 Return context-only identities and exact rejection reasons for nearby but unattached evidence.
- [ ] 4.4 Derive counts and rows from the same SQL predicates and assert their equality under truncation.

## 5. Verify The Packet Exit Class

- [x] 5.1 Run the full state matrix, combined states, CDC context-only oracle, and no-config/malformed/unsupported catalog cases.
- [ ] 5.2 Run dossier, artifact, replay, attachment, DAG, lineage, rebuild, integrity, deterministic, and cap tests.
- [ ] 5.3 Run full Python, compile, strict quality, OpenSpec strict validation, and `git diff --check`.
- [ ] 5.4 Audit for closed-world language, absence/unavailability collapse, status promotion, count drift, and copied stale coverage.
