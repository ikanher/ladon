## Context

This is post-alpha work. It consumes the typed output of
`ladon-elaborated-declaration-surface` and must not infer theorem truth from
statement shape.

## Goals / Non-Goals

**Goals:**

- Classify declaration and theorem-surface changes.
- Separate proof-only changes from statement drift.
- Preserve backend and confidence labels.
- Reuse the alpha declaration extractor and report model.

**Non-Goals:**

- No theorem proving, proof search, or correctness validation.
- No claim that a strengthened/weakened theorem is desirable.
- No parallel Lean helper, declaration inventory, or report schema.

## Decisions

- Treat theorem type extraction as consumed Lean/backend evidence.
- Keep parser and elaborated authority labels distinct.
- Implement comparison as a pure consumer of before/after declaration rows.
- Defer Review Radar cards and CLI orchestration to a later bounded MVP child.

## Risks / Trade-offs

- Statement-drift classification can overclaim semantics -> Use conservative
  labels and source evidence.
