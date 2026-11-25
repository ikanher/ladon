# Handle overlapping Lake source roots in proof search

## Why

Ladon 0.5.1 fails to build a lexical index for the OAI Lean checkout because source discovery assigns two module names to one physical file. The user sees an SQLite uniqueness error without the path, competing names, or a way to resolve ownership. The [bug report](bug-report.md) records the production failure and a two-file reproducer.

## What Changes

- Detect multiple discovered module names for one source path during source discovery.
- Use canonical ownership when the layout establishes it. Provide an explicit resolution path when static discovery cannot determine ownership.
- Report unresolved conflicts in terms of source paths and module names. Preserve the published index if a conflict prevents a build or update.
- Accept the fix when the reproducer produces searchable declarations under confirmed module names and a comparable unresolved fixture produces an actionable diagnostic.

## Capabilities

### New Capabilities

- `ladon-index-source-layout` governs source ownership and ownership diagnostics for lexical indexing.

### Modified Capabilities

None.

## Impact

The change affects Lake source discovery and the lexical index build, update, freshness, and query paths that use its source inventory. The reproduction requires only the Ladon CLI and Python.
