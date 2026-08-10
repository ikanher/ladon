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

- [x] 4.1 Apply the alpha `proofir-v3-native-schema-and-canonicalization` architecture: canonical v3 vectors, kind dispatch, diagnostics, and immutable artifact behavior. Semantic freeze is reopened by Wave 4 review findings.
- [x] 4.2 Apply `proofir-derivation-hypergraph-semantics` and verify AND/OR semantics, cycle handling, and distinct bounded query contracts.

## 5. Wave 3: project and consume

- [x] 5.1 Apply `proofir-v3-sqlite-projection`, including all constraints, foreign keys, production-query indexes, plan gates, integrity checks, and accounting.
- [x] 5.2 Apply `proofir-v3-ladon-integration-and-release` and complete installed-CLI, matrix-factorization, resource, clean-break, and documentation gates.

## 6. Wave 4: expert-review hardening before semantic freeze

- [x] 6.1 Apply `proofir-v3-typed-schema-and-corpus-hardening`: first freeze adversarial red cases, then make typed models authoritative for every kind, Unicode case, and independent artifact/batch bound.
- [x] 6.2 Apply `proofir-v3-declaration-and-application-identity`: split declaration/type/value identities, repair exact attachment, and keep residual goals unchecked.
- [x] 6.3 Apply `proofir-v3-cross-artifact-resolution-and-query-contracts`: resolve against database union incoming batch and freeze truthful bounded graph/dossier results.
- [ ] 6.4 Apply `proofir-v3-lean-worker-framed-protocol`: add adversarial transport tests, nonce-bound NDJSON frames, and direct MetaM elaboration without a generated `sorry` theorem.
- [x] 6.5 Apply `proofir-v3-publication-bounds-and-portability`: reuse Ladon locks and durable publication, separate database/query bounds, and feature-detect optional SQLite introspection.
- [ ] 6.6 Apply `proofir-v3-freeze-evidence-and-review-packet`: package the complete review boundary with content and execution provenance and obtain a blocker-by-blocker disposition.

## 7. Wave 6: independent Rust reference

- [ ] 7.1 Lift the Rust hold only when all six Wave 4 child exit classes are green and the semantic-freeze packet records no open blocker.
- [ ] 7.2 Apply `proofir-v3-rust-reference-core` and require cross-language canonicalization, diagnostics, SQLite rows, and query parity without reproducing Lean semantics or depending on Quux.

## 7a. Wave 5: close the r03 review blockers before freeze

- [x] 7a.1 Reopen `proofir-v3-typed-schema-and-corpus-hardening`: import the 25 adversarial mutations as executable vectors, reject the 19 unambiguously malformed core values, decide the three source-coordinate policies, and freeze exact diagnostics.
- [x] 7a.2 Reopen `proofir-v3-declaration-and-application-identity`: serialize Lean local context and include environment, rule, conclusion, ordered substitutions, residuals, and context in application/step identities.
- [x] 7a.3 Reopen `proofir-v3-cross-artifact-resolution-and-query-contracts`: close bare artifact inputs, centralize fingerprint schemes, repair parent-truncation accounting, use portable large-set joins, and stabilize ordered aggregates.
- [ ] 7a.4 Finish `proofir-v3-lean-worker-framed-protocol`: preserve introduced locals, parse names with Lean, freeze universe closure, and isolate target initializers from protocol ownership. Local-context serialization and semantic application identity are closed; initializer isolation remains open.
- [ ] 7a.5 Reopen `proofir-v3-publication-bounds-and-portability`: add nonce/file-identity ownership, compare-and-delete cleanup, atomic stale claims, and the concurrent/crash/PID-reuse matrix.
- [ ] 7a.6 Finish `proofir-v3-freeze-evidence-and-review-packet`: reject old/vacuous manifests, inventory every archive file, capture command/log evidence, include replay closure, and clean-replay the extracted archive.
- [ ] 7a.7 Obtain a new expert disposition against every r03 P0/P1 finding; keep semantic freeze and Rust blocked until all required findings are green or explicitly accepted as nonblocking.

## 8. Umbrella closure

- [x] 8.1 Run the pre-review strict OpenSpec validation for the original umbrella and children, byte-compare copied specs, parse governance JSON, and run `git diff --check`.
- [x] 8.2 Run the pre-review non-Rust child commands, full Python suite, strict quality checks, and repository-owned separated-project dependency scans. Treat this as historical alpha evidence, not semantic-freeze evidence.
- [ ] 8.3 Re-run strict OpenSpec, spec-copy, governance, full-suite, quality, resource, and separated-project gates after Wave 4 is green.
- [ ] 8.4 After the Rust hold is lifted, run the Rust child conformance, quality, dependency, and isolated-build commands before claiming full-program closure.
- [ ] 8.5 Replace the stale alpha release-evidence statuses with current green evidence only after every affected exit class has a passing test, measurement, diagnostic, and documentation link.
