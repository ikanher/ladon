## Context

Lineage, ProofIR, constructor coverage, and planning need common traversal primitives, while SQLite-specific traversal currently complicates testing.

## Goals / Non-Goals

**Goals:** compact deterministic adjacency, bounded/cycle-safe traversal, SCC/DAG unfolding, explicit omissions, and near-linear dominators.

**Non-Goals:** database acquisition, semantic edge inference, or unbounded enumeration.

## Decisions

1. Map external node identities to stable compact integers at the adapter boundary.
2. Return bounds and omission records from every traversal; shared and cycle references are explicit in unfolded DAGs.
3. Implement Lengauer-Tarjan or an equivalently tested near-linear dominator algorithm and compare generated small graphs with a brute-force oracle.

## Risks / Trade-offs

- [Algorithm bugs on cycles/multiple roots] → differential, malformed-edge, and deterministic generated tests.
- [Adapters change public ordering] → preserve contract-defined stable external identities.
