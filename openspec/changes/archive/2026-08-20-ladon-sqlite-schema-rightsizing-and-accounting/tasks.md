## 1. Measure Candidate Layouts

- [x] 1.1 Add a schema experiment fixture comparing current lineage edges with `WITHOUT ROWID` primary key `(closure_id, source, kind, target)` plus one reverse covering index.
- [x] 1.2 Measure insert, replace, forward/reverse all/type/value query latency, page count, and object bytes twice for both layouts.
- [x] 1.3 Record an accept/reject decision for lineage and independently for ProofIR DAG edges; do not generalize one result to the other.

## 2. Remove Proven Redundancy

- [x] 2.1 Add a validator that compares primary-key and index useful prefixes and reports undocumented duplicate access paths.
- [x] 2.2 Remove `idx_import_source` and `idx_dependency_source` only after populated plans prove primary keys cover every production query.
- [x] 2.3 Reorder/adopt the lineage edge primary key and remove the duplicate forward B-tree after both direction gates pass.
- [x] 2.4 Retain foreign-key integrity and cascade performance tests for every changed table.

## 3. Right-Size Sparse Declaration Indexes

- [x] 3.1 Add an explicit exact `declarations(name, ...)` access path and prove theorem dossier/disconnected triage no longer use skip-scan.
- [x] 3.2 Make structure-name indexing partial on non-null rows and measure the 150k-row lexical fixture size reduction.
- [x] 3.3 Make semantic head/shape/binder indexes partial or generation-conditional and test both lexical-empty and semantic-populated generations.
- [x] 3.4 Re-run module, namespace, package, path, kind, name, FTS, and semantic query plans after every removal.

## 4. Add Storage Accounting

- [x] 4.1 Implement deterministic per-object row/page/byte accounting via `dbstat` with an explicit unavailable fallback.
- [x] 4.2 Group accounting into base, FTS, semantic, lineage, ProofIR, SQLite internal, and free-page sections in build/status/summary payloads.
- [x] 4.3 Add before/after and marginal accounting tests that reconcile allocated database bytes within documented SQLite page overhead.

## 5. Publish A New Disposable Schema

- [x] 5.1 Bump schema version/generation/helper identity and update required index/constraint/access-path manifests.
- [x] 5.2 Prove old databases return incompatible-schema with rebuild guidance and are not mutated.
- [x] 5.3 Run atomic build, FK, integrity, query-plan, size, latency, deterministic, installed CLI, and full quality gates.
- [x] 5.4 Validate this OpenSpec change strictly and record measured bytes saved by each accepted physical change.
