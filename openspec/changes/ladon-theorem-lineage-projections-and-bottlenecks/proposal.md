## Why

A complete theorem dependency DAG can contain thousands of declarations and tens of
thousands of edges, so returning the raw closure is technically correct but not
useful. Users need bounded views that show representative proof ancestry without
mislabeling repeated DAG paths as different proofs.

## What Changes

- Define trust, project, external, package, generated, type-only, value-only, and
  combined boundary projections over SQL-selected subgraphs.
- Produce representative shortest spines, branch summaries, repeated-node markers,
  and source-linked route rows.
- Compute mandatory bottlenecks with a deterministic dominator algorithm only after
  SQL has selected and bounded the relevant subgraph.
- Unfold optional tree views with cycle guards, shared-node references, and explicit
  caps rather than duplicating the whole DAG.

## Capabilities

### New Capabilities

- `ladon-theorem-lineage-projections-and-bottlenecks`: Bounded, source-linked views
  over exact lineage evidence, including representative routes and bottlenecks.

### Modified Capabilities

None.

## Impact

- Adds projection models/render-neutral rows and one narrowly scoped pure graph
  algorithm module for dominators and tree unfolding.
- Depends on bounded SQL query results and never reparses Lean or bypasses the DB.
