## 1. Lean-Aware Local Index

- [x] 1.1 Define the backend-neutral persistent-index contract and the alpha SQLite schema for declarations, elaborated signatures, modules, imports, source spans, consumers, theorem dependencies, and policy metadata.
- [ ] 1.2 Populate the index from existing authoritative lexical, module-DAG, and Lean-helper evidence without making the storage backend an elaboration authority.
- [x] 1.3 Build and replace index snapshots transactionally with deterministic identity and bounded memory use.
- [x] 1.4 Default to `<repo>/.ladon/index/proof-search.sqlite`, support an explicit external `--index` path, and warn without editing ignore files when generated state is version-control-visible.
- [x] 1.5 Create and test lookup indexes for names, modules/packages, source paths, semantic tokens, structure membership, and both directions of dependency edges.

## 2. Freshness And Scope

- [x] 2.1 Implement file-, configuration-, toolchain-, and schema-aware invalidation with explicit fresh, stale, partial, and unavailable states.
- [x] 2.2 Support repository, module, import-closure, namespace, file, and declaration-neighborhood scopes through one normalized scope model.
- [x] 2.3 Report exclusions, unavailable evidence, and incomplete indexing so an empty result cannot imply repository-wide absence.

## 3. Interfaces And Verification

- [x] 3.1 Add bounded canonical JSON and compact text inspection for index status, coverage, scope, and rebuild actions.
- [ ] 3.2 Add portable incremental-update, stale-index, partial-index, scope, determinism, and latency fixtures.
- [x] 3.3 Materialize disposable repository-local indexes for Ladon and Matrix-Factorization and record identity, size, freshness, and cold/warm query timings.
- [x] 3.4 Strictly validate this change and run focused index correctness, query-plan, and resource gates.
