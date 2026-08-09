## Context

The current function accepts arbitrary goal and candidate strings and implements only exact/casefold comparison. Semantic schema v4 already stores binders and conclusion text, allowing a conservative structured lexical explanation without implementing Lean in Python.

## Goals / Non-Goals

**Goals:** resolve candidate evidence, peel stored binders, normalize supported representation boundaries, return residual hypotheses, and avoid false negatives.

**Non-Goals:** unification, definitional equality, type-class synthesis, or verified theorem application without Lean.

## Decisions

1. Prefer a unique indexed declaration identity and its stored binders/conclusion. Keep explicit raw-signature input as lower-authority fallback.
2. Reuse one versioned lexical normalization module with type search; retain original and normalized forms.
3. Classify exact peeled conclusion as `lexically-applicable-with-residuals`; reserve `applicable` for Lean-backed evidence and `not-applicable` for proven contradiction.
4. Keep premise suggestions one level deep and read-only.

## Risks / Trade-offs

- [Lexical peeling mishandles complex dependent syntax] → return `indeterminate-lexical` at unsupported boundaries.
- [Public classification changes] → version the result schema and document compatibility.

## Migration Plan

Add failing theorem-with-binders fixtures, implement stored resolution and normalization, then switch CLI dispatch to the database-aware path.

## Open Questions

- Exact name of the intermediate positive classification is finalized with existing consumers during implementation.
