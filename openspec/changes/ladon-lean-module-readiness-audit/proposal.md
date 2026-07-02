## Why

Lean's module-system direction makes public/private boundaries, facade shape,
and namespace/module organization important review surfaces. Ladon should expose
that pressure from existing graph evidence and optional Lean-owned witnesses
without claiming module-system authority.

## What Changes

- Add module-readiness report rows for public facade pressure, implementation
  modules acting like public API, generated aggregation modules, and
  namespace/module drift.
- Accept optional module-system witness JSON with backend, version, command,
  source hash, visibility, and confidence metadata.
- Render module-readiness summaries in JSON/text output and benchmark fixtures.
- Keep all rows as review-routing evidence only.

## Capabilities

### New Capabilities

- `ladon-lean-module-readiness-audit`: Module boundary readiness rows and
  optional module-system witness ingestion.

### Modified Capabilities

None.

## Impact

- Affected code: module DAG reporting, declaration evidence joins, pipeline,
  rendering, CLI optional witness input, docs, and benchmarks.
