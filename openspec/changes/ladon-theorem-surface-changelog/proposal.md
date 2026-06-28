## Why

Lean diffs can be noisy when the review question is whether theorem statements
changed. Ladon needs a future semantic changelog surface that describes theorem
type drift without claiming theorem truth.

## What Changes

- Define theorem-surface rows for changed type, added premise, conclusion
  drift, name/type drift, and proof-only changes.
- Require backend confidence, source evidence, and nonclaims.

## Capabilities

### New Capabilities

- `ladon-theorem-surface-changelog`: Lean-backed theorem statement changelog
  review rows.

### Modified Capabilities

None.

## Impact

- Affected future code: Lean helper extraction, declaration graph reports,
  atlas diffs.
