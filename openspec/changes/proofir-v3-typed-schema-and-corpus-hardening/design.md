## Context

Expert review demonstrated self-hashed environment, claim, and source-map payloads with invalid nested values that passed the envelope validator. The shared corpus has too few cases to freeze a second implementation.

## Goals / Non-Goals

**Goals:** one authoritative typed construction path, closed nested schemas, stable Unicode diagnostics, independent input bounds, and executable coverage for every artifact kind and row family.

**Non-Goals:** legacy conversion, Rust implementation, Unicode normalization by accident, or accepting partially typed extension data as core semantics.

## Decisions

1. Kind dispatch selects an immutable payload model and serializes that model; it does not duplicate field validation.
2. The canonical profile explicitly rejects invalid Unicode scalar strings with ProofIR diagnostics and freezes normalization behavior in fixtures.
3. `maxArtifactBytes`, `maxBatchBytes`, and `maxArtifacts` are independent public limits.
4. Corpus cases name expected canonical bytes/IDs or exact stage/code/pointer/message diagnostics.

## Risks / Trade-offs

- [Stricter validation rejects alpha artifacts] → regenerate native-v3 fixtures and databases; do not add compatibility coercions.
- [Corpus growth obscures intent] → group cases by kind and contract seam and require unique descriptive IDs.

## Migration Plan

Land adversarial red fixtures, route every kind through its typed model, regenerate valid artifacts, and keep Rust held until the enlarged corpus is frozen.

## Open Questions

- Freeze the exact Lean environment Merkle inputs as an explicit typed-model decision.
