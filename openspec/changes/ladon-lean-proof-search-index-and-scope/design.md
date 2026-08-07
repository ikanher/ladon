## Context

Report extraction is intentionally bounded and run-scoped. Proof search needs a
reusable local store spanning project-owned and external declarations, while scope
must still derive from the canonical Lake/module graph.

## Goals / Non-Goals

**Goals:** versioned persistent navigation, deterministic refresh, explicit
freshness, transitive and explicit-root scopes, omission reasons, and a small JSON
protocol. SQLite is the selected alpha backend rather than a public contract.

**Non-Goals:** no raw `Expr` cross-toolchain persistence, unsound incremental cache,
global package server, or implicit expansion beyond selected scope.

## Decisions

- Store declarations, binders, rendered/normalized type keys, source ranges,
  modules/packages, dependencies, aliases/exports, structures/fields/constructors,
  semantic tokens, and fingerprints in normalized SQLite tables.
- Create explicit SQLite indexes for fully qualified and segmented names,
  module/package ownership, source paths, semantic tokens, structure membership,
  and both source-to-target and target-to-source dependency traversal. Recursive
  SQL may serve bounded reachability queries, while existing Ladon graph code owns
  SCC, cycle, and other whole-graph algorithms.
- Default generated storage to `<repo>/.ladon/index/proof-search.sqlite`, beside the
  repository's existing Ladon policy directory but below a dedicated disposable
  subtree. `--index PATH` overrides the location for CI, read-only checkouts, and
  debugging. Ladon does not silently edit the repository's ignore files.
- Keep the persistent-index service and JSON protocol backend-neutral. SQLite table
  names, migrations, and SQL are implementation details and may change without a
  public compatibility promise.
- Index writes are transactional and schema-migrated; incompatible toolchain/helper
  fingerprints create a new generation rather than mutating evidence in place.
- Changed source or imported declaration fingerprints invalidate the owning module
  and recorded dependents. Missing dependency evidence downgrades freshness instead
  of guessing.
- Scope resolution is a query plan over canonical modules/packages: namespace,
  direct imports, transitive closure, project/external ownership, or explicit roots.
- Omitted declarations carry a stable reason such as outside roots, package filter,
  generated exclusion, missing elaborated row, or stale index generation.

## Risks / Trade-offs

- [SQLite growth] → Store compact normalized rows and expose vacuum/rebuild commands.
- [Missing SQL indexes turn bounded queries into table scans] → Assert required
  indexes and representative query plans in schema tests.
- [Invalidation fan-out is expensive] → Batch refresh by SCC/module order and report
  counts/timings.
- [External declarations lack source ranges] → Preserve owner/package and explicit
  unavailable-location status.

## Migration Plan

Create the default index under the repository-local disposable `.ladon/index/`
subtree. Index creation is an explicit write operation and never modifies Lean
sources or tracked policy files. Projects should ignore `.ladon/index/`; Ladon warns
when the generated subtree is visible to version control but does not edit ignore
files. Read-only repositories use an explicit external `--index` path. Schema
mismatch rebuilds or migrates transactionally, and removing the index is a safe
rollback. The acceptance run materializes disposable indexes for Ladon and the
Matrix-Factorization checkout and records generation identity, size, freshness, and
cold/warm timings without committing either database.
