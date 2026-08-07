## Why

Name search cannot find a theorem when users know the desired proposition but not
its identifier, while raw fuzzy text search produces unrelated collisions. Ladon
needs elaborated type matching and semantic ranking over the effective proof scope.

## What Changes

- Search elaborated declaration types using metavariables and partial patterns.
- Rank direct unification before symmetry, definitional unfolding, coercion, and
  explicitly bounded adapter-assisted matches.
- Return names, owner modules, types, source ranges, imports, substitutions, scope,
  match route, and authority/freshness labels.
- Combine tokenized Lean names, namespaces, docstrings, and signatures with AND/NOT
  filters, project-local ranking, and theorem-family grouping.
- Preserve failed-route evidence so unchanged rejected candidates are explained.

## Capabilities

### New Capabilities

- `ladon-type-and-semantic-declaration-search`: Type-directed and fuzzy semantic
  declaration discovery over the indexed, explicitly selected scope.

### Modified Capabilities

None.

## Impact

- Adds Lean-side query elaboration/unification, bounded match-route ranking, semantic
  token indexing, family integration, CLI/JSON results, and precision/latency gates.
