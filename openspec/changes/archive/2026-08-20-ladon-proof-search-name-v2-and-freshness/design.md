## Context

Index and query tokenization currently diverge at mixed-case boundaries, and stored generations do not by themselves prove current source freshness.

## Goals / Non-Goals

**Goals:** one normalization implementation, exact-name monotonicity, explicit query modes, verified/stored freshness, and honest source-only omissions.

**Non-Goals:** Lean semantic matching or removal of the compatibility alias in this packet.

## Decisions

1. Persist `name_casefold` and `name_segments` produced by `semantic_name_segments_v1`; query code calls the same function.
2. Execute exact folded-name lookup through a B-tree and union it before FTS ranking.
3. `--freshness verify` hashes current supported inputs; `stored` reports unchecked. A requested on-disk source root that cannot be indexed yields an omission or error.
4. New output uses `results`; `index query` may mirror `rows` with deprecation metadata for one transition.

## Risks / Trade-offs

- [Normalization changes ranking] → golden mixed-case/segmentation fixtures and deterministic tie breaks.
- [Verification costs more] → retain explicit cheap stored mode without calling it fresh.
