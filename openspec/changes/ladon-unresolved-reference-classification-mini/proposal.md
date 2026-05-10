# Proposal

Unresolved declaration-reference rows currently mix several different things:
real missing local declarations, local binders or fields, anonymous parser terms,
and external Lean/library identifiers. This makes findings noisy, especially on
matrix-factorization owner files.

Classify unresolved reference candidates and split raw unresolved rows from
actionable unresolved rows.

# Scope

- Add deterministic candidate classification to declaration graph analysis.
- Preserve raw `top_unresolved_references`.
- Add `top_actionable_unresolved_references` for candidates that are worth a
  human review.
- Render candidate classifications in text reports.
- Use actionable unresolved rows for findings.

# Non-Goals

- No Lean elaboration.
- No hidden suppression of raw unresolved counts.
- No claim that ignored candidates are semantically irrelevant.
