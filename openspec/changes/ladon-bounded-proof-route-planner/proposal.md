## Why

Shortest proof routes are AND/OR searches over unresolved goals, not simple paths between declarations, and every transition must remain Lean-verified and bounded.

## What Changes

- Add a canonical multiset state model and deterministic bounded best-first search.
- Expand one goal through SQL-shortlisted, Lean-verified candidates and replace it with all residual premises.
- Record caps, omissions, accepted/rejected route cards, optional scratch replay, and generation/context identities.
- Keep any rejected-route memory in an optional generation-keyed sidecar, never the published index.

## Capabilities

### New Capabilities

- `ladon-bounded-proof-route-planner`: Deterministic bounded AND/OR planning over Lean-verified theorem applications.

### Modified Capabilities

## Impact

Adds planner state/search modules, verifier and route-card integration, optional history-sidecar support, replay hooks, and bounded-search fixtures.
