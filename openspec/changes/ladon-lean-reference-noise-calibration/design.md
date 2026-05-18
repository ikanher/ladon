# Design

The classifier remains deterministic and string-based.

Add `local_type_parameter_candidate` for a small allowlist of common generic
type-parameter spellings seen in Lean proof-owner signatures, starting with the
observed Quux case (`Edge`, `State`) and similarly common graph vocabulary.

Add `WellFounded` to the external Lean/library root list. This matches how
`Nat`, `Fin`, `List`, and other Lean/library names are already classified.

Actionable unresolved rows still include only `actionable_unknown`. Raw
unresolved rows continue to show every candidate and its classification.
