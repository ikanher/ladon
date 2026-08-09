## Why

Conceptual `any` searches are dominated by generic theorem tokens, and tiny owner analyses can render tens of thousands of repository-global candidates. Default results should prioritize concentrated local evidence and remain bounded in volume.

## What Changes

- Add stopword-aware, multi-segment concentration ranking with deterministic contribution evidence.
- Add a minimum matched-token control for `any` mode.
- Make owner reports selected/co-reachable by default and summarize global integrity inventory compactly.
- Preserve explicit opt-in projections for repository-global samples.

## Capabilities

### New Capabilities

- `ladon-proof-search-ranking-and-owner-projection`: Multi-segment conceptual ranking and owner-focused report projection.

### Modified Capabilities

## Impact

Changes name-search ranking metadata, CLI options, architecture report projection/rendering, fixtures, and regression snapshots.
