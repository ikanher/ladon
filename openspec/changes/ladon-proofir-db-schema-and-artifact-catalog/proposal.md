## Why

ProofIR evidence has no durable identity or coverage model in the project-local
index. Before semantic rows can be joined safely, Ladon needs a constrained
artifact catalog that survives the same transactional generation rules as the
rest of the proof-search database.

## What Changes

- Add normalized artifact-generation, artifact, relationship, diagnostic, and
  coverage tables to the existing proof-search SQLite schema.
- Identify artifacts by repository-relative path, content hash, artifact kind,
  schema version, and configured import identity.
- Catalog unsupported kinds without interpreting them and distinguish absent,
  unsupported, malformed, stale, and normalized evidence.
- Add foreign keys, checks, lookup indexes, size limits, atomic publication,
  and deterministic idempotent ingestion.
- Define rebuild behavior so configured imports are reproduced rather than
  silently lost when the base database is replaced.

## Capabilities

### New Capabilities

- `ladon-proofir-db-schema-and-artifact-catalog`: Transactional and indexed
  artifact identity, relationships, diagnostics, coverage, and generation
  lifecycle in the existing project-local database.

### Modified Capabilities

None.

## Impact

- Changes the private proof-search schema generation, validation, counts, and
  build inputs.
- Adds artifact configuration/fingerprinting and catalog ingestion services.
- Requires new schema, lifecycle, corruption, and rebuild regression tests.
