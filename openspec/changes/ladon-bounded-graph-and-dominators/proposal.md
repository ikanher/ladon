## Why

SQL should retrieve bounded graph rows, while reusable traversal and bottleneck algorithms need deterministic, cycle-safe implementations that can be tested independently.

## What Changes

- Add compact forward/reverse adjacency, bounded expansion, path enumeration, SCC, and DAG unfolding primitives.
- Replace repeated-set-intersection dominators with a tested near-linear algorithm.
- Adapt lineage and ProofIR queries without changing their public results.

## Capabilities

### New Capabilities

- `ladon-bounded-graph-and-dominators`: Pure bounded graph traversal and deterministic dominator computation.

### Modified Capabilities

## Impact

Adds `bounded_graph.py`, `dominators.py`, algorithm oracles, and adapters in theorem-lineage and ProofIR query code.
