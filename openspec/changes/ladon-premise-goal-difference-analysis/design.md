## Context

Candidate applicability is richer than closes/does-not-close: assigned binders, discharged hypotheses, residual premises, unresolved instances, and structural mismatches guide the next proof step.

## Goals / Non-Goals

**Goals:** conservative mismatch evidence, one-level verified discharger suggestions, precise strength/boundary labels, and reusable route cards.

**Non-Goals:** inventing semantic explanations from structural differences or multi-step search.

## Decisions

1. Always return application evidence even when residual premises remain.
2. Produce bounded expression-difference trees for failed conclusion passes and retain `unclassified_expression_difference` when no registered rule applies.
3. Batch all residual-premise suggestions into one additional Lean request.
4. Key route cards by goal/context/index/worker/policy identities and preserve accepted/rejected and not-replayed states.

## Risks / Trade-offs

- [Misleading classifications] → rule IDs, authority fields, exact structural evidence, and conservative fallback.
- [Suggestion fan-out] → one level in P0 with per-premise and total caps.
