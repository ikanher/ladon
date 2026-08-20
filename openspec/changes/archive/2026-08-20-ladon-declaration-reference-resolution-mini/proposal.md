## Why

The first declaration graph smoke run on Quux produced declaration nodes but no
resolved edges because helper reference candidates often use local or partially
qualified names. Ladon needs a conservative resolver before declaration graph
reports become useful.

## What Changes

- Resolve reference candidates by exact full name first.
- Resolve unique declaration basenames when unambiguous.
- Resolve module-local names such as `foo` to `Module.foo` when present.
- Keep ambiguous or unknown candidates unresolved.
- Add tests for unique basename, module-local, ambiguous, and unknown cases.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `ladon-declaration-graph`: Declaration graph analysis uses conservative
  reference resolution instead of exact-only matching.

## Impact

- Affected code: `src/ladon/analysis/declaration_graph.py`.
- Affected tests: declaration graph resolution cases.
- Report output may show more resolved edges and fewer unresolved references.
