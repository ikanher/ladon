## 1. Establish Packet Preconditions And Failing Fixtures

- [ ] 1.1 Verify the catalog packet exit class passes and its standalone capability spec matches the umbrella copy byte-for-byte.
- [ ] 1.2 Freeze minimal Quux-derived fixtures for one surface bundle, its exact replay provenance, a stale bundle hash, a foreign surface ID, a failed replay, and a downstream aggregate copy.
- [ ] 1.3 Add `tests/test_proofir_surface_store.py` with failing assertions for artifact-owned surfaces, claims, claim-only rows, ownership constraints, conflicts, and idempotent ingestion.
- [ ] 1.4 Add `tests/test_proofir_replay_store.py` with failing assertions that extractor boundary and replay run remain separate facts.
- [ ] 1.5 Add the 63/52/11 coverage oracle as a compact generated fixture or parameterized synthetic test without reading live Quux.

## 2. Extend Schema And Integrity Rules

- [x] 2.1 Add surface, claim, surface-claim, replay-run, and replay-surface tables under catalog artifact ownership.
- [x] 2.2 Add composite uniqueness, cascading artifact/bundle/surface foreign keys, valid return-code/status checks, nonnegative counts, and bounded-field diagnostics.
- [x] 2.3 Add named indexes for surface ID, claim ID, declaration name, source path/hash, replay bundle, and replay surface; register exact ordered columns in schema validation.
- [x] 2.4 Extend database counts and semantic coverage so cataloged, normalized, replay-related, replay-not-observed, stale, and failed-run populations are distinct.

## 3. Normalize Surfaces And Claims

- [x] 3.1 Reuse `normalize_proofir_index` for admitted compact indexes and Lean-surface bundles; add storage validation without duplicating bridge authority normalization.
- [x] 3.2 Preserve source path/range/hash subject, declaration name, authority, proof trust, extractor guarantee, replay boundary, claimed status, nonclaims, and bounded quoted metadata.
- [ ] 3.3 Store valid compact claims that have no surface and prove they cannot receive a declaration attachment implicitly.
- [ ] 3.4 Reject conflicting duplicate surface/claim identities transactionally and keep unsupported surface-like artifacts catalog-only.

## 4. Normalize Replay Provenance

- [x] 4.1 Add an explicit versioned adapter for `proof_ir_lean_replay_provenance`; reject structural lookalikes under other kinds.
- [x] 4.2 Preserve command, return code, module, repository commit/dirty scope, source identity, toolchain versions, guarantee, authority interpretation, and nonclaims as quoted replay evidence.
- [x] 4.3 Resolve the referenced bundle by repository-relative path plus full content hash and create the artifact relationship only on an exact match.
- [x] 4.4 Resolve each listed surface ID only inside that exact bundle; diagnose foreign IDs and stale bundle targets without borrowing same-named rows elsewhere.
- [ ] 4.5 Classify absent provenance as `not_observed`, nonzero return code as failed replay evidence, and return code zero as successful repository-local build evidence without changing surface/theorem status.

## 5. Add Stored Queries And Bridge Compatibility

- [ ] 5.1 Add bounded query services for surface identity, claim identity, declaration name, artifact membership, replay runs, and replay coverage.
- [ ] 5.2 Return surface boundary and replay provenance in separate result sections with explicit relation evidence and nonclaims.
- [ ] 5.3 Keep downstream snapshots/architecture indexes catalog-only and add a regression proving configured aggregate copies do not double-count primary surfaces.
- [ ] 5.4 Run existing in-memory ProofIR bridge tests unchanged and add parity assertions for normalized fields shared with the database adapter.

## 6. Verify The Packet Exit Class

- [ ] 6.1 Run surface/replay/catalog tests, exact stale/missing/failed/conflict matrices, and the 63/52/11 coverage oracle.
- [ ] 6.2 Run integrity, foreign-key, index-column, query-plan, size-cap, deterministic-order, and prior-generation preservation gates.
- [ ] 6.3 Run existing ProofIR bridge/CLI/atlas suites, full Python suite, strict quality, compile, and `git diff --check`.
- [ ] 6.4 Audit that no status collapse, theorem promotion, generic dialect guessing, aggregate double count, or full raw artifact payload storage was introduced.
