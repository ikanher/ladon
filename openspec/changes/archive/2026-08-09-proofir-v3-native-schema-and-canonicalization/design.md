## Context

V3 is a clean break. The product needs one semantic contract, not a compatibility container around several historical dictionaries.

## Goals / Non-Goals

**Goals:** deterministic bytes and digests, closed schemas, bounded validation, exact reference closure, immutable validated values, stable diagnostics, and explicit legacy rejection.

**Non-Goals:** legacy conversion, embedding old fields in extensions, a universal proof-term AST, or using SQLite as canonical serialization.

## Decisions

1. Canonical hashing excludes the detached `artifactId`; validators recompute and compare it.
2. Envelope fields are exactly version, kind, ID, producer, environment reference, subject references, coverage, payload, limitations, and extensions.
3. Each supported artifact kind has an explicit version-locked payload validator. Unknown kinds and legacy kinds fail with stable distinct diagnostics.
4. Unknown namespaced extensions round-trip byte-stably but cannot influence core semantic decisions.
5. Validated artifacts own deeply immutable data; caller mutation cannot invalidate a previously checked content ID.
6. CLI operations are `validate`, `canonicalize`, and `inspect`. There is no converter operation.
7. The canonical numeric profile accepts only integers in the inclusive range `[-9007199254740991, 9007199254740991]`. Non-integral quantities use explicitly typed canonical decimal strings.
8. Validation is bounded by input bytes, output bytes, nesting, collections, strings, and reference work, and emits deterministic code/pointer/stage records.

## Risks / Trade-offs

- [Existing local artifacts stop loading] → fail with an actionable legacy-unsupported diagnostic and require regeneration from the producer.
- [Useful historical examples disappear] → rewrite the semantic scenario as native-v3 fixture data without retaining legacy names or shapes.
- [Canonicalization differs across languages] → use shared golden bytes, Unicode cases, integer boundaries, and invalid-number fixtures.

## Migration Plan

Delete converter and direct legacy ingestion. Replace test artifacts with native-v3 fixtures, rebuild every local SQLite projection, and only then route consumers to the native model.

## Open Questions

- None. Widening the canonical numeric profile or kind set requires a versioned schema change and new cross-language vectors.
