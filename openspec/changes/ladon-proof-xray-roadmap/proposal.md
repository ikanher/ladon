## Why

Maintainers eventually need proof-shape evidence such as tactic skeletons and
trust footprint, but Ladon must not blur parser references with Lean-owned
elaborated proof artifacts.

## What Changes

- Define a roadmap for elaborated proof x-ray rows.
- Specify authority labels for tactic skeletons, axiom/sorry footprint, proof
  shape, and dependencies.
- Preserve parser-reference nonclaims.

## Capabilities

### New Capabilities

- `ladon-proof-xray-roadmap`: Future elaborated-backend proof-shape evidence
  contract.

### Modified Capabilities

None.

## Impact

- Affected future code: Lean helper/backend extraction, declaration reports,
  atlas/reviewer cards.
