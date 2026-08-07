## Context

A theorem may match a goal conclusion while requiring premises unavailable in the
local context. Difference analysis must be Lean-backed, while higher-level mismatch
labels and adapter suggestions remain explainable routing metadata.

## Goals / Non-Goals

**Goals:** apply candidates against goals, map local hypotheses, classify remaining
premises, find discharge candidates, suggest bounded adapters, and persist routes.

**Non-Goals:** no automatic tactic execution in production files, invented premise
proofs, or silent acceptance of heuristic adapters.

## Decisions

- Ask Lean to instantiate candidate binders against the goal and return substitutions,
  synthesized implicits, matched local hypotheses, and residual metavariable goals.
- Normalize residuals conservatively and classify only when exact structural evidence
  supports a known category; otherwise use `unclassified-premise` with the type.
- Query the index/type-search service separately for each residual premise and retain
  scope/freshness on every possible discharger.
- Keep adapters in a versioned registry naming exact declarations, direction, input
  and output shapes, required side conditions, and supported toolchains.
- Route cards are immutable canonical JSON rows; a compiled probe can upgrade only
  its own stage to Lean-confirmed.

## Risks / Trade-offs

- [Typeclass search has side effects/cost] → Use the pinned environment, bounded
  heartbeat/deadline, and record synthesis failures.
- [Mismatch classifier overstates semantics] → Preserve exact residual types and
  distinguish structural labels from repo-policy labels.
- [Adapter catalog ages] → Version and test declarations per supported toolchain.

## Migration Plan

Land direct residual premise reporting first, then discharge search, then advisory
adapter routes. Existing search results remain valid without route cards.
