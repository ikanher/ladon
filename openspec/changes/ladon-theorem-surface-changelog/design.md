## Context

This is future Lean-backed work. It should build on declaration source evidence
and not infer theorem truth from statement shape.

## Goals / Non-Goals

**Goals:**

- Classify theorem-surface changes.
- Separate proof-only changes from statement drift.
- Preserve backend and confidence labels.

**Non-Goals:**

- No theorem proving, proof search, or correctness validation.
- No claim that a strengthened/weakened theorem is desirable.

## Decisions

- Treat theorem type extraction as quoted Lean/backend evidence.
- Keep parser and elaborated authority labels distinct.

## Risks / Trade-offs

- Statement-drift classification can overclaim semantics -> Use conservative
  labels and source evidence.
