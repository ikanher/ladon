## 1. Inventory And Version The Schema

- [x] 1.1 Map current declarations, binders, structures, fields, ProofIR, lineage, constraints, indexes, and schema identity before editing DDL.
- [x] 1.2 Bump private schema/generation identifiers to v4 and add deterministic rebuild-required status for older databases.

## 2. Add Semantic Relations

- [x] 2.1 Add bounded normalized declaration columns including folded/segmented names, ownership, rendered type/conclusion, fingerprints, heads, arity, proposition flag, semantic status, and helper/Lean identity.
- [x] 2.2 Add `symbols` with unique names, optional declaration owner, kind, ownership, and deliberate `ON DELETE SET NULL` behavior.
- [x] 2.3 Add `declaration_dependencies` as a constrained `WITHOUT ROWID` composite-key table with type/value kind and authority/status.
- [x] 2.4 Add `declaration_shapes` roles, key versions, symbol heads, arity, hash, coarse key, authority, and status.
- [x] 2.5 Extend binders, structures, and structure fields with the plan's complete semantic columns and foreign keys.
- [x] 2.6 Add `module_semantic_state` with source/compiled/import/surface/helper/Lean identities, status/reason, and terminal counts.

## 3. Add Every Required Access Path

- [x] 3.1 Add B-tree exact folded-name and all normalized FTS columns using the shared segmenter.
- [x] 3.2 Add both source-to-target and target-to-source covering dependency indexes.
- [x] 3.3 Add declaration-shape/head, binder-head, structure/field, module/status, source/scope, and join indexes required by public queries.
- [x] 3.4 Run `PRAGMA optimize` after population and benchmark `ANALYZE`, page size, and mmap without hard-coding unsupported settings.

## 4. Prove Integrity And Plans

- [x] 4.1 Add empty and populated v4 schema snapshots and enumerate all expected tables, columns, checks, primary keys, foreign keys, and indexes.
- [x] 4.2 Add negative insert/delete tests for every constraint and cascade/set-null policy.
- [x] 4.3 Add `EXPLAIN QUERY PLAN` gates for exact name, FTS, type shortlist, reverse consumers, fields, and module freshness.
- [x] 4.4 Measure fixture and reference-repository database bytes against the configured size cap.

## 5. Verify The Packet

- [x] 5.1 Run schema/catalog/ProofIR/lineage compatibility suites, FK/integrity checks, deterministic rebuilds, compile/quality gates, strict validation, and `git diff --check`.
