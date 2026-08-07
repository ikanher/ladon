## Why

Type-compatible candidates can still be mathematically wrong for a proof route when
they concern normalized rather than physical objects, or fixed indices rather than
uniform families. These project semantics must be explicit policy, not hard-coded
names guessed by Ladon.

## What Changes

- Define repository policy for semantic representation pairs and exact transport or
  conjugacy declarations between them.
- Classify results as fixed-index, finite-window uniform, or unbounded-family uniform.
- Track declared scale relations and warn when a candidate bounds a normalized object
  while the goal requests the physical object.
- Surface parameter-dependent growth that prevents a common uniform constant.
- Integrate representation/range facts into candidate differences and route cards
  without upgrading policy declarations to theorem truth.

## Capabilities

### New Capabilities

- `ladon-proof-representation-and-scale-awareness`: Policy-backed representation,
  scaling, transport, and parameter-range checks for proof candidates.

### Modified Capabilities

None.

## Impact

- Adds policy schema/validation, transport joins against the elaborated index,
  scale/range diagnostics, route-card fields, examples, and general synthetic
  fixtures without Matrix-Factorization-specific names.
