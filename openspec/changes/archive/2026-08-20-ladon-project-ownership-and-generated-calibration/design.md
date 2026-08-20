## Context

Large owner reports mix authored target declarations, imported identities,
compiler-generated helpers, project-generated source families, and unresolved
rows. This child gives each population explicit evidence and prevents
generated/imported volume from dominating authored review.

## Decisions

### Classification is evidence-backed and fail-closed

Rows are classified as `target_owned`, `imported`, `compiler_generated`, or
`project_generated`; contradictory or insufficient evidence remains
`unclassified`. Target source roots, explicit generated-family policy, and
Lean compiler evidence have documented precedence.

### Project-generated families are configuration

A versioned repository-relative policy names stable families and path/module
patterns plus optional generator/manifest provenance. Overlapping rules are
rejected. Generated-looking names alone never change ownership.

### Metrics name their population

Population-sensitive rows record numerator, denominator, and exclusions.
Owner-focused defaults use `target_owned`; raw and other populations remain
inspectable. Family aggregates retain raw member references and make no
generator-correctness claim.

## Existing Owners And Exclusions

Text and elaborated declaration authority remain with their existing owners;
benchmark and finding vocabularies are reused. This child does not replay a
generator, assert freshness, infer theorem truth, or hard-code repository
family names.

## Risks

Misclassification can suppress authored work. Unclassified rows, explicit
provenance, negative fixtures, and raw views keep the decision auditable.
