## Why

The proof-search database has indexed declaration-edge access paths, while theorem
capsule planning already produces complete Lean-authoritative closures. Those
surfaces are not yet joined, so every lineage question would otherwise reparse a
large JSON plan or rebuild an in-memory graph.

## What Changes

- Migrate the private local index to a generation that stores theorem-lineage
  closures, normalized endpoint nodes, typed edges, trust roots, and frontiers.
- Ingest only complete compatible theorem plans and preserve their plan, closure,
  source, configuration, toolchain, helper, and index generation identities.
- Enforce endpoint foreign keys, uniqueness, status checks, and indexed forward and
  reverse traversal paths.
- Replace one theorem closure transactionally and reject partial, stale,
  incompatible, or malformed evidence without damaging a prior valid closure.

## Capabilities

### New Capabilities

- `ladon-theorem-lineage-db-schema-and-ingestion`: Validated transactional storage
  of complete theorem dependency evidence in the repository-local SQLite index.

### Modified Capabilities

None.

## Impact

- Changes `proof_search_schema.py`, proof-search migrations/status, theorem-plan
  adapters, and focused schema/ingestion tests.
- Adds private tables and required indexes but no public SQL compatibility promise.
- Depends on existing theorem-capsule planning and proof-search index authorities.
