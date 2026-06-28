## Why

Different Lean projects have different stale terms, trust words, TODO classes,
and local banned prose. Ladon needs reusable policy packs without embedding
those project terms in analyzer code.

## What Changes

- Build reusable policy-pack fixtures on top of source-pattern policies.
- Validate zero-match, capped-match, generated-filtered, and invalid-pattern
  behavior.
- Document that project terms live in policies or packs, not Ladon code.

## Capabilities

### New Capabilities

- `ladon-configurable-lexical-audit-packs`: Reusable source-pattern policy packs
  for project-owned lexical checks.

### Modified Capabilities

None.

## Impact

- Affected code: source-pattern policy tests, docs, optional fixtures.
