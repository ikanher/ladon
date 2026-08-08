## Context

Normalized ProofIR DAG nodes and edges have forward/reverse indexes. The existing recursive CTE emits reachable nodes but does not retain predecessor/path identity sufficiently to prove endpoint-specific routes.

## Goals / Non-Goals

**Goals:** endpoint-correct shortest paths, representative alternative paths, selected subgraph/tree output, cycle safety, deterministic bounds, and authority-transition summaries.

**Non-Goals:** exhaustive path enumeration, mathematical DAG validation, Lean dependency inference, or checker execution.

## Decisions

1. Recursive SQL carries node, depth, predecessor/path identity, visited state, and edge ordinal. Endpoint filtering happens inside the route relation, not after reachability projection.
2. Minimum depth is computed first; representative paths are then ordered by depth and stable node/edge identity under a route cap.
3. The selected tree is the deduplicated union of returned routes with explicit shared-node references. It is not claimed to be the unique proof tree.
4. Each step returns node status/authorities and the traversed edge/obligation. Boundary transitions are derived without ranking authorities.
5. Cycles terminate through visited state and produce diagnostics. Caps cover depth, states, nodes, edges, routes, and serialized bytes.

## Risks / Trade-offs

- [Recursive path state can grow quickly] → hard expansion caps and diamond/cycle stress fixtures.
- [Representative routes omit alternatives] → explicit truncation metadata and no exhaustive-language claims.
- [SQLite planner changes] → assert named entry indexes while avoiding brittle full-plan snapshots.

## Migration Plan

Introduce `ladon-proofir-obligation-routes-v1`, retain the old function only as an internal compatibility shim, then update CLI and dossier callers.
