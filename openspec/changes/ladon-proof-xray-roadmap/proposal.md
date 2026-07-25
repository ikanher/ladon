## Why

Maintainers may eventually need proof-shape evidence such as tactic skeletons
and InfoTree-derived inspection rows, but Ladon must not blur parser references,
quoted witness rows, or direct Lean declaration facts with that future lane.

## What Changes

- Define a future contract for tactic-skeleton and InfoTree/proof-shape rows.
- Require explicit backend/version/source authority and inspection-only
  nonclaims.
- Consume quoted trust rows from `ladon-proof-xray-staging` and direct
  statement, dependency, axiom, sorry, and unsafe facts from
  `ladon-elaborated-declaration-surface` rather than duplicating them.

## Capabilities

### New Capabilities

- `ladon-proof-xray-roadmap`: Future elaborated-backend tactic-skeleton and
  InfoTree/proof-shape evidence contract.

### Modified Capabilities

None.

## Impact

- Affected future code: optional proof-shape extraction and consumers after the
  alpha declaration surface is stable.
