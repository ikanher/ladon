## 1. Define Pure Graph Contracts

- [x] 1.1 Add bounded graph request/result dataclasses for stable node IDs, adjacency, caps, omissions, shared references, and cycle references.
- [x] 1.2 Add compact stable integer mapping and deterministic forward/reverse adjacency construction with malformed-edge diagnostics.

## 2. Implement Traversal Primitives

- [x] 2.1 Implement bounded BFS/frontier expansion and endpoint-aware reverse traversal.
- [x] 2.2 Implement cycle-safe bounded path enumeration with stable ordering and explicit depth/path/output omissions.
- [x] 2.3 Implement SCC calculation and DAG unfolding that preserves shared nodes and cycles as references.

## 3. Implement Dominators

- [x] 3.1 Add a near-linear dominator implementation with declared multiple-root, disconnected, and unreachable semantics.
- [x] 3.2 Add brute-force dominator and bounded traversal oracles used only by deterministic small-graph tests.

## 4. Adapt Existing Queries

- [x] 4.1 Change theorem-lineage traversal/tree/bottleneck code to acquire bounded SQL rows once and call pure graph functions.
- [x] 4.2 Change ProofIR route/tree code to the same pure graph boundary without changing public result schemas.

## 5. Verify The Packet

- [x] 5.1 Test chains, diamonds, cycles, SCCs, multiple roots, disconnected nodes, shared DAGs, malformed edges, and every cap.
- [x] 5.2 Differential-test deterministic generated graphs against brute-force oracles.
- [x] 5.3 Run existing lineage/ProofIR contracts, SQL-count tests, compile/quality gates, strict validation, and `git diff --check`.
