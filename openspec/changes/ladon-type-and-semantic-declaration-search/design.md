## Context

The index can cheaply prefilter names, tokens, and normalized type heads, but only
Lean can decide whether an elaborated query pattern unifies with a declaration type.

## Goals / Non-Goals

**Goals:** exact and partial type patterns, bounded match-route ranking, semantic
fuzzy search, family grouping, substitutions, and source/import evidence.

**Non-Goals:** no unrestricted proof synthesis, unbounded simplification search, or
claim that a fuzzy result applies.

## Decisions

- Elaborate a query in the selected module/namespace context with explicit wildcard
  holes, then prefilter by type heads/tokens before Lean checks candidate constants.
- Use ordered match classes: direct unification, equality symmetry, bounded
  definitional reduction, registered coercion, then explicitly named adapter route.
- Cap candidate count, reduction depth, and adapter steps; expose truncation.
- Tokenize Lean names by namespace, camel/snake segments, docstrings, and signature
  constants; AND terms are required and NOT terms filter before ranking.
- Reuse declaration-family groups and store failed-route identity/reason so unchanged
  rejections remain visible rather than silently resurfacing.

## Risks / Trade-offs

- [Wildcards make everything match] → Require structural anchors and rank specificity.
- [Definitional matching is expensive] → Prefilter, bound work, and expose timeouts.
- [Docstrings bias ranking] → Keep semantic and Lean match scores separate.

## Migration Plan

Add new query/result schemas without changing existing reports. Start with exact and
direct-unification routes, then enable bounded transformations behind explicit match
classes.
