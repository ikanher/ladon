## Why

Lean diffs can be noisy when the review question is whether theorem statements
changed. The future semantic changelog should consume the bounded,
Lean-elaborated declaration rows produced by
`ladon-elaborated-declaration-surface`, not create a second extractor.

## What Changes

- Own the concrete `ladon-semantic-theorem-changelog` requirements moved out of
  the Review Radar planning umbrella.
- Compare before/after declaration rows for additions, removals, rename
  candidates, theorem-type drift, assumptions, conclusions, and proof-only
  changes.
- Preserve the declaration surface's backend, source evidence, confidence, and
  nonclaims.

## Capabilities

### New Capabilities

- `ladon-semantic-theorem-changelog`: Before/after semantic changelog rows
  derived from the alpha declaration surface.

### Modified Capabilities

None.

## Impact

- Dependency: `ladon-elaborated-declaration-surface` and report-contract-v2
  rows must be stable before implementation.
- Affected future code: a pure before/after comparator and atlas/diff
  consumers; no additional Lean helper or declaration extractor.
