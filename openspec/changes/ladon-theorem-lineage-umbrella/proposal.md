## Why

Ladon already extracts a complete Lean-authoritative dependency DAG for a named
theorem, but users must inspect a large capsule-plan JSON document to understand
how trust axioms, external declarations, project lemmas, and the final theorem are
connected. A database-backed lineage workflow can turn that existing evidence into
fast, bounded, human-readable routes without inventing an alternative proof graph.

## What Changes

- Persist complete theorem-plan dependency closures in the repository-local proof
  search database with generation, authority, freshness, and trust metadata.
- Query reachability, shortest routes, branch counts, and boundary slices through
  indexed SQL and recursive CTEs.
- Add bounded lineage projections for trust roots, project boundaries, external
  packages, generated auxiliaries, representative spines, and bottlenecks.
- Add an ordinary `ladon theorem lineage` CLI that accepts a fully qualified theorem
  name and returns text or versioned JSON.
- Calibrate the complete workflow on portable fixtures, Quux, and
  Matrix-Factorization while keeping alternative-proof search an explicit nonclaim.

## Capabilities

### New Capabilities

- `ladon-theorem-lineage-db-schema-and-ingestion`: Transactional persistence of
  complete theorem-plan nodes, edges, frontiers, and identities in the local index.
- `ladon-theorem-lineage-sql-queries`: Indexed SQL traversal and bounded route
  selection over one fresh Lean-authoritative closure.
- `ladon-theorem-lineage-projections-and-bottlenecks`: Honest readable projections,
  representative spines, branch points, and mandatory bottlenecks.
- `ladon-theorem-lineage-cli-and-renderers`: Installed theorem-name command,
  stable result schema, compact text output, and operational behavior.
- `ladon-theorem-lineage-integration-and-calibration`: Cross-packet fixtures,
  large-repository measurements, docs, skills, and regression gates.

### Modified Capabilities

None.

## Impact

- Extends the private proof-search SQLite schema, migrations, integrity checks,
  lookup indexes, and status coverage.
- Reuses theorem-capsule planning as the only complete dependency authority and
  adds ingestion/query services without changing capsule guarantees.
- Extends the installed theorem CLI, JSON/text rendering, tests, documentation,
  and maintained Ladon skill.
- Adds bounded recursive-SQL and large-graph performance gates; no graph database
  or caller-specific interface is introduced.
