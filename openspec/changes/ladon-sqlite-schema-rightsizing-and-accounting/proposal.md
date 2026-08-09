## Why

The live Matrix-Factorization database spends about 197 MB on one lineage edge table plus three B-trees, while other indexes duplicate primary keys or index almost entirely empty semantic columns. The disposable schema should be aligned with actual query shapes and account for its own storage.

## What Changes

- Redesign edge and graph tables with query-aligned `WITHOUT ROWID` primary keys where measured beneficial.
- Remove indexes duplicated by primary keys and convert sparse semantic indexes to partial indexes.
- Add deterministic per-table and per-index byte accounting and duplicate/unused-index checks.
- Bump the private schema generation and require atomic rebuild rather than in-place migration.

## Capabilities

### New Capabilities

- `ladon-sqlite-schema-rightsizing-and-accounting`: Query-aligned compact table/index layouts and per-table/per-index byte accounting.

### Modified Capabilities

## Impact

Changes private DDL, schema validation, build/status reporting, fixtures, and size regression gates.
