## Why

SQLite is valuable for bounded queries, but current tables mix canonical evidence with adapter compatibility state and implicit relationships.

## What Changes

- Project validated v3 artifacts into normalized identity, subject, claim, step, observation, attachment, coverage, omission, and extension tables.
- Keep canonical artifacts authoritative and make database generations disposable.
- Derive every index from registered production SQL and foreign-key child paths.
- Add per-family coverage, provenance, storage accounting, and deterministic rebuilds.
- Preserve unknown namespaced extensions without allowing them to affect core decisions.

## Capabilities

### New Capabilities
- `proofir-v3-sqlite-projection`: Rebuildable, query-aligned storage for canonical v3 evidence.

### Modified Capabilities

## Impact

Introduces a new private schema generation, ingestion projection, query registry, migration rejection, storage accounting, and plan/latency tests.
