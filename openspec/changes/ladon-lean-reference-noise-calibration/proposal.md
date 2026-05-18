# Proposal

The refreshed post-calibration Quux Propagation owner run still promoted
`Edge` and `WellFounded.*` unresolved references as actionable. Manual
inspection shows these are not missing proof owners:

- `Edge` is a recurring generic type-parameter spelling in the owner.
- `WellFounded.*` is external Lean infrastructure.

Calibrate the unresolved-reference classifier so these cases remain visible in
raw unresolved rows but no longer drive actionable findings.

# Scope

- Add a narrow local-type-parameter classification bucket.
- Treat `WellFounded` as a known external Lean root.
- Update live calibration predicates so Quux Propagation expects no promoted
  unresolved-reference hotspot after this classifier pass.
- Preserve raw unresolved counts and rows.

# Non-Goals

- No Lean elaboration.
- No broad suppression of uppercase names.
- No claim that every generic-looking name is semantically irrelevant.
