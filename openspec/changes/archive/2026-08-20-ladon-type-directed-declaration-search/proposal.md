## Why

Users who know a desired proposition but not its declaration name need fast type-directed discovery whose final matches are checked by Lean rather than inferred from stored text.

## What Changes

- Add `ladon proof-search search type` with module, pattern, assumptions, scope, package/namespace, candidate, match-pass, freshness, and output bounds.
- Shortlist in SQLite by exact fingerprint, head/arity, shape, constants, and semantic FTS before one batched Lean verification request.
- Rank verified results by an explicit deterministic vector and retain shortlist diagnostics as non-authoritative evidence.

## Capabilities

### New Capabilities

- `ladon-type-directed-declaration-search`: Bounded SQL shortlisting followed by deterministic Lean-verified type search.

### Modified Capabilities

## Impact

Adds type-query and ranking modules, CLI/parser/renderers, result schema v1, scope/freshness integration, and portable and large-repository tests.
