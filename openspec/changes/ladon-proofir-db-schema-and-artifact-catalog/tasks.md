## 1. Freeze The Catalog Contract With Failing Tests

- [x] 1.1 Add `tests/test_proofir_catalog_schema.py` with an in-memory schema fixture and failing assertions for the new tables, primary keys, checks, foreign keys, and exact required index columns.
- [x] 1.2 Add `tests/test_proofir_catalog.py` fixtures for one supported artifact, one unsupported kind, malformed JSON, a duplicate path/hash, an escaping path, and changed bytes at the same path.
- [x] 1.3 Add failing tests that unsupported input is catalog-only, malformed input creates no semantic rows, and no configured input reports `not-configured` rather than complete-empty coverage.
- [x] 1.4 Add failing atomicity tests that constraint, file-count, per-file-byte, total-byte, and metadata limits leave the prior canonical database readable.
- [x] 1.5 Add a failing two-build integration test proving unchanged configured artifacts are present after the second atomic base-index replacement.

## 2. Capture Configured Artifact Inputs

- [x] 2.1 Inspect existing repository-owned configuration conventions and choose one documented ProofIR input field/file; add parser tests before implementing it.
- [x] 2.2 Implement repository-relative explicit paths and bounded globs, canonicalize every match, reject repository escapes, sort deterministically, and deduplicate identical paths.
- [x] 2.3 Capture artifact size and SHA-256 once during repository snapshot construction and include configuration plus artifact identities in the generation fingerprint.
- [x] 2.4 Add configured file-count, per-file-byte, total-byte, and stored-metadata limits with observed/allowed values in errors.

## 3. Add The Constrained SQLite Schema

- [x] 3.1 Bump the private proof-search schema generation/helper identity and add normalized generation, artifact, relationship, and diagnostic tables to `proof_search_schema.py`.
- [x] 3.2 Add checks for allowed catalog/normalization states, nonnegative sizes, repository-relative paths, and supported relationship direction.
- [x] 3.3 Add cascading foreign keys from artifacts to their generation and from relationships/diagnostics to artifact endpoints.
- [x] 3.4 Add named indexes for active generation, kind/schema, path/hash, relation source, relation target, and diagnostic reason with exact ordered-column registry entries.
- [x] 3.5 Extend schema counts, evidence coverage, required foreign-key validation, integrity checks, and `PRAGMA user_version` expectations.

## 4. Implement Catalog Ingestion

- [x] 4.1 Add `src/ladon/proofir_catalog.py` with bounded JSON-object inspection and deterministic artifact IDs; store selected top-level identity metadata but not raw JSON payloads.
- [x] 4.2 Classify admitted-kind candidates as pending semantic normalization, unknown kinds as catalog-only, and malformed inputs according to the tested generation policy.
- [x] 4.3 Make insertion idempotent for identical bytes and reject conflicting duplicate identities before any semantic adapter runs.
- [x] 4.4 Insert artifact relationships only after both endpoints exist and add compact diagnostics for unsupported, malformed, truncated, stale, and unavailable evidence.

## 5. Integrate Atomic Index Generation

- [x] 5.1 Invoke configured catalog ingestion while building the unpublished temporary database, before commit and full validation.
- [x] 5.2 Add ProofIR catalog counts, configured-input coverage, limits, and fingerprints to internal status/build metadata without exposing private table names as public API.
- [x] 5.3 Prove failed catalog ingestion cannot replace the canonical database and lock cleanup follows existing PID-scoped behavior.
- [x] 5.4 Prove removing configuration and rebuilding yields `not-configured` coverage with no copied stale artifact rows.

## 6. Verify The Packet Exit Class

- [x] 6.1 Run the new catalog/schema/configuration tests and existing proof-search index, status, locking, lineage, and corruption tests.
- [x] 6.2 Run `PRAGMA integrity_check`, `foreign_key_check`, required-index comparison, and `EXPLAIN QUERY PLAN` assertions for path/hash and relationship lookups.
- [x] 6.3 Run the two-build fixture, size/cap failure matrix, deterministic-repeat test, full Python suite, strict quality checks, compile checks, and `git diff --check`.
- [x] 6.4 Verify no second SQLite file, tracked database, raw JSON blob store, recursive unconfigured artifact scan, or semantic rows from unsupported kinds were introduced.
