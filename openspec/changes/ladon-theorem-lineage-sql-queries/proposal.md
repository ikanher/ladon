## Why

Once exact theorem closures are stored, ordinary lineage questions should use the
database's indexed graph operations rather than duplicating graph traversal in
Python. The query contract must also bound recursive work and distinguish an empty
answer from missing or stale evidence.

## What Changes

- Resolve a fully qualified theorem to one fresh stored closure.
- Use parameterized recursive CTEs for forward/reverse reachability, shortest-depth
  discovery, trust-to-theorem routes, edge-kind filters, and boundary filters.
- Add deterministic limits for depth, nodes, edges, and routes with explicit
  truncation and omission reasons.
- Assert query plans use the required lineage indexes and reject unbounded or
  cycle-unsafe traversal.

## Capabilities

### New Capabilities

- `ladon-theorem-lineage-sql-queries`: Bounded indexed SQL queries over one exact,
  fresh theorem-lineage closure.

### Modified Capabilities

None.

## Impact

- Adds a private SQL query service and portable graph fixtures.
- Uses SQLite recursive CTEs and existing process/resource contracts; Python graph
  traversal is not the default implementation path.
- Depends on the lineage schema and ingestion packet.
