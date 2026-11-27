# Proposal

## Why

The RH archive searches found a Gaussian integral by its formula after a three-term name query returned no results. A formatting change alone took a separate type query from nine results to zero, and comparing the roughly 3.9 GiB archive with pinned Mathlib and Mf required separate calls and manual comparison.

## What Changes

1. Add normalized type-fragment search with conjunction, ranking by independently recorded conclusion matches, and per-fragment match evidence. Keep the existing literal search available for exact replays.
2. Add explicit stored mode to batch search so an agent can run several queries against one pinned index generation without walking the source tree. Keep the existing verified mode as the batch default.
3. Run one batch over a caller-supplied set of named indexes. Return results grouped by library, with each library's scope, source locations, generation, freshness and omissions.

The RH Gaussian integral, finite-product integral and dyadic tail-sum examples supply acceptance cases. Success includes finding those declarations through their types and comparing the RH and local results without rebuilding the archive. Normalized search and stored batching can ship separately. Named-index search composes the per-index batch reader and uses both increments for the full replay.

## Capabilities

### New Capabilities

- `ladon-normalized-type-fragment-search` — Conjunctive lexical matching over indexed types with inspectable conclusion ranking.
- `ladon-stored-search-batch` — Source-independent batches with per-index snapshot identity and bounded output.
- `ladon-named-index-search-batch` — One request over independent named indexes with per-library results and evidence.

### Modified Capabilities

None. The existing CLI, scope and verification contracts are the baseline for these additions.

## Impact

Extends the Python proof-search CLI, type shortlist and batch paths, output schemas, tests, CLI reference and coding-agent instructions. The existing [Lean proof discovery umbrella](../../ladon-lean-proof-discovery-umbrella/proposal.md) retains its broader elaborated matching and adapter work. Its type-search change may consume the normalized lexical shortlist. The [active project index umbrella](../../ladon-active-project-index-umbrella/proposal.md) owns the existing freshness and publication machinery. The [ranking and owner projection change](../../ladon-proof-search-ranking-and-owner-projection/proposal.md) owns name-search ranking.
