## 1. Program controls

- [x] 1.1 Verify every child capability spec is byte-identical to its umbrella copy and every ledger dependency names an existing change.
- [x] 1.2 Establish the shared native-v3 valid/invalid corpus, stable diagnostic vocabulary, release-evidence format, and TDD rule before child production edits.
- [x] 1.3 Add a dependency gate that rejects any Ladon runtime, build, packaged, test, inspection, execution, or calibration use of `../quux`.

## 2. Wave 0: make the clean break executable

- [x] 2.1 Remove the v2 converter, compatibility artifact kind, direct legacy ingestion/adapters, legacy fixtures, and legacy SQLite tables or projections.
- [x] 2.2 Freeze tests proving every legacy ProofIR kind fails with a stable diagnostic and never contributes a projected row.

## 3. Wave 1: establish semantic identity and evidence

- [x] 3.1 Apply `proofir-content-environment-and-subject-identity` against native-v3 fixtures.
- [x] 3.2 Apply `proofir-observation-authority-and-coverage-core` after typed subjects exist.
- [x] 3.3 Apply `proofir-attachment-and-link-observations` using the shared identity and observation models.

## 4. Wave 2: introduce v3 artifacts and derivations

- [x] 4.1 Apply `proofir-v3-native-schema-and-canonicalization` and freeze canonical v3 vectors, closed kind schemas, validation diagnostics, and immutable artifact behavior.
- [x] 4.2 Apply `proofir-derivation-hypergraph-semantics` and verify AND/OR semantics, cycle handling, and distinct bounded query contracts.

## 5. Wave 3: project and consume

- [x] 5.1 Apply `proofir-v3-sqlite-projection`, including all constraints, foreign keys, production-query indexes, plan gates, integrity checks, and accounting.
- [x] 5.2 Apply `proofir-v3-ladon-integration-and-release` and complete installed-CLI, matrix-factorization, resource, clean-break, and documentation gates.

## 6. Wave 4: independent Rust reference

- [ ] 6.1 Begin `proofir-v3-rust-reference-core` only after the canonical corpus and normalized projection contract are frozen.
- [ ] 6.2 Require cross-language canonicalization, diagnostics, and SQLite parity without reproducing Lean semantics or depending on Quux.

## 7. Umbrella closure

- [ ] 7.1 Run strict OpenSpec validation for the umbrella and every child, byte-compare copied specs, parse governance JSON, and run `git diff --check`.
- [ ] 7.2 Run all child test commands, the full project suite, strict quality checks, and dependency scans in an environment where Quux is absent.
- [ ] 7.3 Produce a release-evidence manifest mapping every umbrella requirement and child exit class to passing tests, measurements, diagnostics, and documentation.
