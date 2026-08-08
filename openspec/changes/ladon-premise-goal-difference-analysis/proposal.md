## Why

A theorem that does not close a goal can still be the right route, but Ladon must expose exactly what matched and what remains rather than reduce Lean evidence to a rejection.

## What Changes

- Add `proof-search explain` for conclusion attempts, binder substitutions, residual premises, unresolved metavariables, and conservative mismatch trees.
- Suggest verified declarations for each residual premise at one bounded level.
- Emit versioned proof-route cards with generations, context, source anchors, bounds, omissions, acceptance, and replay state.

## Capabilities

### New Capabilities

- `ladon-premise-goal-difference-analysis`: Lean-backed application differences, residual-premise suggestions, and route-card evidence.

### Modified Capabilities

## Impact

Adds difference, route-card, and semantic-registry core modules; semantic helper operations; CLI output; and positive/negative mismatch fixtures.
