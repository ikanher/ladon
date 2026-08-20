## Context

One selected owner currently triggers broad top-namespace inventory work and
mixes global context into owner review. This child separates requested roots
from analysis populations and makes the selection previewable before any Lake
or Lean execution.

## Decisions

### Scope plans are explicit data

Supported scope kinds are `owner`, `closure`, `namespace`, `multi-root`,
`changed-set`, and `inventory`. A plan records requested/resolved roots,
primary/context populations, boundary modules, truncation, expected helper
batches, cache expectations, and a deterministic fingerprint.

### Preview performs discovery only

Preview may inspect caller-owned layout, source paths, manifests, indexes, and
policies. It never runs Lake, Lean helpers, target initializers, analysis
passes, or VCS commands.

### Changed sets are caller-supplied

The command accepts repository-relative paths or a versioned manifest. Git-ref
orchestration remains outside this capability. Ambiguous or unmapped paths are
diagnostics, never guessed module names.

### Scope does not claim mathematical correctness

Owner and closure evidence is primary for owner review; optional inventory
context is labeled separately. A suggested root is heuristic routing evidence,
not a claim about the mathematically correct proof root.

## Existing Owners And Exclusions

The source index comes from `ladon-large-inventory-scale-contract`; CLI and
report envelopes retain their existing owners. This child does not infer roots
from theorem semantics, run VCS, or redefine extraction authority.

## Risks

Narrow scopes may hide global pressure. Reports therefore record omitted
populations and permit explicit inventory context. Layout ambiguities fail
closed and participate in scope fingerprints.
