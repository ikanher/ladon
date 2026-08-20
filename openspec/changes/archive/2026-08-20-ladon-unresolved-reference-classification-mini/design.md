# Design

Classification is intentionally conservative and string-based:

- `[anonymous]` and bracketed terms become `parser_noise`;
- short lowercase names, Greek names, underscore-prefixed names, dotted names
  with lowercase roots, and lowercase/camelCase bare identifiers become
  `local_or_field_candidate`;
- common Lean/library roots such as `Fin`, `Nat`, `Real`, `List`, `Set`, `Type`,
  `Finset`, and related roots become `external_candidate`;
- everything else becomes `actionable_unknown`.

Raw unresolved rows stay visible. Findings and the actionable table use only
`actionable_unknown` rows so the headline report is not dominated by binder and
field names.
