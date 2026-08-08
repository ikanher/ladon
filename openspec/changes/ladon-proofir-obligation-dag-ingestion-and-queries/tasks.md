## 1. Establish Preconditions And TDD Graph Oracles

- [ ] 1.1 Verify catalog and surface/replay packet exit classes pass and duplicated umbrella specs remain byte-for-byte equal.
- [ ] 1.2 Freeze small chain, diamond, cycle, missing-endpoint, conflicting-node, stale-witness, and mixed-authority DAG fixtures plus a compact CDC-derived fixture.
- [ ] 1.3 Add `tests/test_proofir_dag_store.py` with failing normalization, uniqueness, endpoint, authority/status, checker-relation, atomicity, and idempotence assertions.
- [ ] 1.4 Add `tests/test_proofir_dag_query.py` with failing exact forward/reverse, minimum-depth, mixed-authority, deterministic-route, cap, cycle, and query-plan assertions.
- [ ] 1.5 Encode exact CDC route oracles from the paper-backed input and the oriented integer-flow hypothesis to the conditional global conclusion.

## 2. Add Normalized DAG Schema

- [x] 2.1 Add artifact-owned DAG, node, edge, node-authority, checker-witness relation, and omission tables with deterministic composite keys.
- [x] 2.2 Add foreign keys guaranteeing every edge endpoint belongs to the same DAG and every checker relation names cataloged artifacts.
- [ ] 2.3 Add checks for node/edge kinds, bounded status/authority values, nonnegative ordinals/counts, and structured omission reasons.
- [x] 2.4 Add required forward `(dag, source, kind, target)`, reverse `(dag, target, kind, source)`, node status/identity, generation, and checker-target indexes.
- [ ] 2.5 Extend counts, evidence coverage, schema integrity validation, and exact index-column registries.

## 3. Implement DAG And Witness Adapters

- [x] 3.1 Add an explicit adapter for versioned `proof_ir_v2_obligation_dag` and reject generic objects that merely contain `uses`/`produces`.
- [x] 3.2 Normalize imported facts, obligations, and produced facts into typed nodes; normalize use and produce relationships into directed edges carrying obligation identity.
- [x] 3.3 Validate node uniqueness, endpoint closure, supported values, deterministic input order, row/byte caps, and conflicting duplicate content before insertion.
- [ ] 3.4 Preserve descriptions and caveats under bounded quoted fields and record truncation/unknown-value diagnostics without remapping authority.
- [ ] 3.5 Add the explicit DAG check-witness adapter and link it only by exact DAG/source artifact identity; keep reported validation separate from DAG and theorem status.

## 4. Implement SQL-First Route Queries

- [x] 4.1 Add parameterized recursive CTEs for forward/reverse reachability, minimum depth, start/end filters, and selected subgraph rows.
- [ ] 4.2 Carry obligation status and authorities through every returned route step and compute explicit boundary-transition summaries.
- [ ] 4.3 Add deterministic representative shortest routes with maximum depth, nodes, edges, routes, and output-byte controls plus truncation metadata.
- [x] 4.4 Terminate cyclic traversals with visited state/references and return cycle diagnostics rather than unbounded expansion.
- [ ] 4.5 Add render-neutral versioned route results whose nonclaim states that ProofIR routes are not Lean dependencies or proof-term verification.

## 5. Prove Graph Isolation And Query Quality

- [ ] 5.1 Assert no DAG adapter inserts into `lineage_nodes`, `lineage_edges`, or declaration dependencies.
- [ ] 5.2 Prove the external CDC input route stays conditional and the Lean-premise route preserves established steps followed by the conditional conclusion.
- [ ] 5.3 Prove stale or mismatched checker witnesses validate no active DAG even though they remain cataloged.
- [ ] 5.4 Prove `EXPLAIN QUERY PLAN` uses the named forward/reverse indexes for routine traversal entry steps.

## 6. Verify The Packet Exit Class

- [ ] 6.1 Run DAG store/query fixtures, cycle/cap/malformed/conflict matrices, CDC route oracles, and checker relation tests.
- [ ] 6.2 Run schema integrity, foreign-key, required-index, query-plan, deterministic-order, atomic failure, and size-limit gates.
- [ ] 6.3 Run catalog, surface/replay, lineage, full Python, strict quality, compile, and `git diff --check` gates.
- [ ] 6.4 Audit for exhaustive path enumeration, pure-Python repository traversal, authority flattening, generic dialect inference, checker promotion, and lineage-table contamination.
