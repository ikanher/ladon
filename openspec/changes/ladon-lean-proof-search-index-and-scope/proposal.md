## Why

Interactive theorem discovery needs elaborated declaration data in seconds, not a
repository rebuild for every query. It also needs an explicit answer to what was in
scope and why declarations or modules were omitted.

## What Changes

- Materialize a versioned persistent local query index of elaborated declarations,
  binders, source ranges, dependencies, aliases, exports, structures, fields, and
  constructors. The alpha backend is SQLite, but its schema is not a public API.
- Fingerprint sources, imports, toolchain, helper protocol, and index schema; expose
  honest fresh, stale-indirect, partial, and lexical-fallback states.
- Incrementally refresh changed modules and invalidated dependents without claiming
  a sound incremental cache when evidence is incomplete.
- Define proof-work scopes for current namespace, direct imports, full transitive
  closure, project-owned declarations, external packages, and explicit root sets.
- Emit omission reasons and a small versioned JSON query protocol.

## Capabilities

### New Capabilities

- `ladon-lean-proof-search-index-and-scope`: Persistent Lean-aware declaration
  indexing, freshness evidence, scope selection, and omission diagnostics.

### Modified Capabilities

None.

## Impact

- Adds a repository-local `.ladon/index/` lifecycle, alpha SQLite
  schema/migrations, Lean extraction fields, cache invalidation,
  repository/toolchain fingerprints, scope resolvers, JSON protocol rows, and
  large-repository latency fixtures.
