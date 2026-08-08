## Why

The current obligation query returns bounded reachability rows but does not prove that its rows form a route to the requested endpoint or expose representative path/tree structure. ProofIR DAG data becomes useful for proof planning only when start/end semantics, cycles, shortest paths, and authority transitions are exact.

## What Changes

- Implement endpoint-correct forward and reverse route queries with recursive SQL.
- Return representative shortest paths and a deduplicated selected subgraph/tree rather than an unstructured reachability list.
- Preserve node status, authority, obligation identity, and boundary transitions along every step.
- Add deterministic cycle handling and explicit depth/node/edge/path/output caps.

## Capabilities

### New Capabilities

- `ladon-proofir-obligation-route-paths-and-trees`: Bounded endpoint-correct paths and selected obligation trees over stored DAGs.

### Modified Capabilities

## Impact

Affects `proofir_dag_store.py`, public route result schemas, SQL indexes/query plans, and DAG route fixtures. It does not alter Lean lineage tables or run external checkers.
