# Proposal

Lean-backed smoke runs on `Mf/DP/GaussianCore.lean` surfaced actionable
unresolved-reference findings for mathlib infrastructure and local theorem
variables:

- `Δ`, `X`, and `C` are local variable/type-parameter spellings.
- `MeasurableSet`, `ENNReal.*`, and `ProbabilityTheory.*` are external
  mathlib names.

Calibrate the unresolved-reference classifier so these remain visible in raw
rows but stop driving missing-reference findings.

# Scope

- Treat single uppercase identifiers, including uppercase Greek letters, as
  local type/value parameter candidates.
- Add common mathlib roots observed in GaussianCore to external roots.
- Smoke rerun GaussianCore and confirm actionable unresolved rows disappear or
  shrink to genuinely unknown candidates.

# Non-Goals

- No Lean elaboration.
- No hiding raw unresolved counts.
- No broad suppression of multi-character uppercase theorem-like names.
