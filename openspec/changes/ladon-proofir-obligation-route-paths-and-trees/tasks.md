## 1. Freeze Endpoint And Path Oracles

- [x] 1.1 Add chain, unreachable, reverse, diamond, cycle-before-end, cycle-after-end, and over-cap fixtures to `tests/test_proofir_dag_query.py`.
- [x] 1.2 Encode exact expected node/edge sequences for every representative path, not just reachable node sets.
- [ ] 1.3 Add compact CDC external-premise and Lean-premise route oracles with exact status/authority transitions.
- [x] 1.4 Add failing assertions that an unrelated reachable node never appears as a route to the selected end.

## 2. Define Route Bounds And Results

- [x] 2.1 Add validated maximum depth, recursive states, nodes, edges, routes, and output bytes.
- [x] 2.2 Define `ladon-proofir-obligation-routes-v1` with selector, minimum depth, paths, selected subgraph, transitions, diagnostics, coverage, truncation, and nonclaims.
- [x] 2.3 Define stable path, edge-step, shared-node-reference, cycle-reference, and truncation identities.

## 3. Implement Endpoint-Correct Recursive SQL

- [x] 3.1 Write the forward recursive CTE carrying current node, depth, predecessor/path identity, edge identity, and visited state.
- [x] 3.2 Write the reverse CTE using the registered reverse index and identical result semantics.
- [x] 3.3 Compute endpoint minimum depth before representative path projection and distinguish unreachable from cap-truncated search.
- [x] 3.4 Select deterministic shortest paths ordered by depth, edge ordinal, and stable node identity under the route cap.
- [x] 3.5 Deduplicate the union of selected paths into a selected subgraph/tree with explicit shared references.

## 4. Preserve Status, Authority, And Cycles

- [x] 4.1 Join every route step to node kind/status and normalized authority rows without flattening authority classes.
- [ ] 4.2 Derive ordered authority/status boundary transitions and keep checker/Lean/ProofIR labels separate.
- [x] 4.3 Terminate repeated visited nodes, emit cycle references, and prove cyclic fixtures finish under every direction.
- [x] 4.4 Enforce every cap during traversal or projection and emit observed/allowed values.

## 5. Prove SQL Quality And Isolation

- [x] 5.1 Assert forward/reverse entry plans use `idx_proofir_dag_edge_forward` and `idx_proofir_dag_edge_reverse`.
- [x] 5.2 Prove route queries never read or write `lineage_edges` as ProofIR edge data.
- [ ] 5.3 Compare repeated and unchanged-rebuild route JSON byte-for-byte.

## 6. Verify The Packet Exit Class

- [x] 6.1 Run chain/diamond/unreachable/reverse/cycle/cap/CDC matrices plus DAG ingestion and checker-witness tests.
- [ ] 6.2 Run integrity, index registry, query-plan, output-byte, full Python, compile, strict quality, and `git diff --check` gates.
- [ ] 6.3 Audit for post-hoc end filtering, exhaustive enumeration, unbounded path strings, authority collapse, and Lean-lineage contamination.
