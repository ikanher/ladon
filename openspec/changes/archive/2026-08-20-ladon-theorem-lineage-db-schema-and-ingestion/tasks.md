## 1. Schema Generation And Tables

- [x] 1.1 In `src/ladon/proof_search_schema.py`, bump the private schema version/generation and add `lineage_closures`, `lineage_nodes`, `lineage_edges`, `lineage_trust`, `lineage_scc_members`, and `lineage_omissions` exactly as listed in `design.md`.
- [x] 1.2 Add composite foreign keys so every lineage child belongs to one closure and every edge/trust endpoint belongs to a node in that same closure; add all boolean, enum, nonnegative-count, and uniqueness checks.
- [x] 1.3 Add named indexes for theorem/active-closure lookup, node boundary/owner/kind lookup, forward edges, reverse edges, trust roots, and SCC membership; extend `REQUIRED_LOOKUP_INDEX_COLUMNS` with their exact ordered columns.
- [x] 1.4 Extend `schema_foreign_keys`, table inventories, integrity inspection, database counts, and status output so missing lineage constraints or access paths fail validation.
- [x] 1.5 Update the explicit index build path in `src/ladon/proof_search_index.py` for the new generation and assert a rebuilt empty index reports lineage coverage `unavailable:not_ingested`.

## 2. Validated Plan Adapter

- [x] 2.1 Add `src/ladon/theorem_lineage_store.py` with a typed adapter that accepts a validated `TheoremPlan` payload and returns normalized immutable closure/node/edge/trust/SCC/omission rows.
- [x] 2.2 In the adapter, require `semanticGraph.status == complete`, `authority == lean_environment`, compatible helper protocol, exact node/edge counts, valid completion checksum, and a recomputed closure fingerprint before producing rows.
- [x] 2.3 Materialize every local node from `semanticGraph.nodes` and synthesize one typed external-frontier node for every otherwise missing edge endpoint; preserve owner, kind, generated, axiom, unsafe, fingerprint, and location-availability fields without name heuristics.
- [x] 2.4 Normalize `type` and `value` edges, trust rows, SCC membership, unsupported semantic facets, and target/source identity; reject duplicate rows whose metadata disagree.
- [x] 2.5 Add unit fixtures in `tests/test_theorem_lineage_store.py` for a local chain, external axiom target, compiler-generated node, SCC, checksum mismatch, dangling edge, conflicting duplicate, partial graph, and incompatible authority.

## 3. Transactional Ingestion And Freshness

- [x] 3.1 Implement `ingest_theorem_lineage(connection, plan, identities, limits)` in `theorem_lineage_store.py` using one immediate transaction and parameterized batched inserts.
- [x] 3.2 Insert the candidate closure and all children, verify counts/fingerprint/foreign keys/size inside the transaction, activate it, and delete the superseded theorem closure only after every check passes.
- [x] 3.3 On validation, constraint, integrity, size, interruption, or commit failure, roll back and prove the prior active closure identity and query rows remain unchanged.
- [x] 3.4 Add closure-status lookup that compares repository, schema, source inventory, configuration, toolchain, helper, and base-index identities and returns absent, fresh, stale-source, stale-configuration, stale-toolchain, incompatible-schema, or corrupt.
- [x] 3.5 Extend proof-search status JSON/text with lineage closure counts, active theorem count, storage bytes where available, coverage, and stale-reason summaries without implying zero dependencies when no closure was ingested.

## 4. Focused Verification

- [x] 4.1 In `tests/test_proof_search_index.py`, assert every new index's ordered columns, every new foreign key, integrity check, empty coverage row, schema identity, and deterministic rebuild output.
- [x] 4.2 In `tests/test_theorem_lineage_store.py`, test two theorem closures coexisting and one theorem being atomically replaced without disturbing the other.
- [x] 4.3 Add a size-cap regression using a dense synthetic plan and assert the prior SQLite file hash and active closure survive the rejected ingestion.
- [x] 4.4 Run `uv run pytest tests/test_proof_search_index.py tests/test_theorem_lineage_store.py -q`, then run the existing theorem-capsule planning/model tests and fix every regression before checking tasks complete.
- [x] 4.5 Run changed-module Ruff, mypy if configured, maintainability, vulture, `python -m compileall src/ladon`, `openspec validate ladon-theorem-lineage-db-schema-and-ingestion --strict`, and `git diff --check`; targeted checks pass, while the pre-existing repository-wide C-grade theorem-capsule maintainability failure remains separately recorded.
