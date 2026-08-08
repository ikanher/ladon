## Why

Current name lookup can miss mixed-case exact declarations and can report freshness without verifying the current repository and supported source population.

## What Changes

- Normalize names identically at index and query time and union exact folded-name matches before FTS ranking.
- Make `all`, `any`, and `phrase` query modes and repeatable exclusions explicit.
- Introduce the `results` collection and a one-transition compatibility adapter for `index query`.
- Verify current supported inputs on demand and report source-only/untracked omissions honestly.

## Capabilities

### New Capabilities

- `ladon-proof-search-name-v2-and-freshness`: Monotone exact-name refinement, explicit query semantics, and identity-bearing freshness.

### Modified Capabilities

## Impact

Changes declaration normalization, FTS/B-tree population, name-query code, public result schema, compatibility rendering, docs, and tests.
