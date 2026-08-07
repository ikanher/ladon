# `ladon-theorem-lineage-db-schema-and-ingestion`

Persists the existing complete theorem-plan semantic graph in the shared
repository-local proof-search SQLite database.

- Dependencies: theorem-capsule planning and proof-search index lifecycle.
- Enables: indexed SQL traversal over fresh exact closures.
- Excludes: lexical dependency promotion, raw Lean `Expr` storage, and public SQL.
- Exit: constraints, indexes, exact adapter, atomic replacement, freshness, size,
  integrity, and prior-generation preservation gates pass.
