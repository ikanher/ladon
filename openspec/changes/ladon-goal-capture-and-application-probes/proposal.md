## Why

Proof search is most useful when it can see the actual local goal and hypotheses.
Users also need a safe way to test a suggested application without modifying the
unfinished production module.

## What Changes

- Accept a Lean scratch file and line/column and capture the current goal, local
  hypotheses, namespace, open scopes, and imports through the pinned toolchain.
- Map local hypotheses to candidate binders and feed the exact goal/context into
  type search and premise-difference analysis.
- Parse relevant compiler type-mismatch diagnostics into an explicit query input.
- Emit a separate minimal scratch `example` that imports the candidate owner and
  checks a proposed application under supervised Lean execution.
- Keep scratch artifacts outside production source and label failed probes honestly.

## Capabilities

### New Capabilities

- `ladon-goal-capture-and-application-probes`: Goal/context extraction, local-binder
  matching, compiler-error queries, and isolated Lean application probes.

### Modified Capabilities

None.

## Impact

- Extends the Lean helper, process supervisor integration, scratch artifact handling,
  CLI location syntax, route cards, and fixtures for incomplete proof owners.
