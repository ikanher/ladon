## Why

The alpha SQLite publisher has a same-directory temporary file and atomic replace, but it does not yet share Ladon's proven build-lock/page-limit/durable-publication boundary and assumes optional SQLite introspection behavior.

## What Changes

- Reuse Ladon's project-local PID-owning build lock and durable database replacement.
- Enforce independent database and query resource bounds before publication.
- Feature-detect `dbstat` and assert plan semantics without freezing platform-specific `EXPLAIN QUERY PLAN` prose.

## Capabilities

### New Capabilities
- `proofir-v3-publication-bounds-and-portability`

### Modified Capabilities

## Impact

Changes the v3 SQLite publisher, storage accounting, query-plan gates, lock/status CLI output, crash tests, and database-size policy.
