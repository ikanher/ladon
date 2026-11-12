# Design

## Context

proof_slice already extracts selected scoped applications. proof_contract_provider_expansion.py revalidates owner-bound demand and observes one provider while leaving its obligation unresolved. Extend this evidence rather than infer origins from an axiom list or lexical dependency names.

## Goals / Non-Goals

**Goals:** show how a selected proof receives a conclusion through an actual hypothesis, structure field or instance, and identify missing source justification.
**Non-goals:** prove hypothesis necessity, decide arbitrary logical equivalence, expand the whole imported library, or infer circularity from a graph cycle alone.

## Decisions

### Bounded provider provenance

Use existing owner/local IDs, application occurrence, branch scope, proof argument and provider closures. A node records origin category (boundary hypothesis, local definition, field projection, instance argument, theorem application or unresolved provider). Edges record actual term dependencies and exact scope. Shared nodes are deduplicated by scoped identity while occurrence edges remain distinct.

Initial scope handles direct hypothesis use, local aliases, structure projection and instantiated type-class projection. Recursive/opaque providers and unsupported dependent projections retain named frontiers. Bounds start at 4096 nodes, 16384 edges and depth 64 within existing 8 MiB stage output; lowering limits is supported. Do not increase slice traversal defaults.

### What conclusion-supplied means

For the admitted profile, Lean must confirm that the observed projection has the exact target type under the original context. Use definitional equality in Lean for aliases; arbitrary logical equivalence requires an explicit separately checked bridge. The observation establishes use of that provider in this proof, not that every proof needs it.

Annotate source justification separately: explicit original premise, reviewed earlier derivation, disputed added premise or unresolved. A declaration of P → P is a valid conditional theorem. A source that claims P without establishing its HasConclusion P premise has a missing source obligation; report that only with the source mapping and reviewed scope. A synthetic generated-goal self-reference remains rejected by existing completion guards, independently of this diagnostic.

### Consumer interface

Expose a source-bound provenance plan/result that the umbrella can attach to observations and render as a short path ending at a premise or frontier. Reuse provider worker supervision and source identity checks. Accepted projection receipts carry exact hypothesis/context, target, term, environment and replay/trust evidence. Rendered names aid navigation but never join scopes.

## Risks / Trade-offs

- [Projection looks circular but the instance was independently constructed] → retain constructor/provider expansion and valid control; do not stop at class field type.
- [Proof irrelevance or normalization obscures origin] → preserve the observed raw term path and normalized typed comparison separately; unavailable origin is unresolved.
- [Expansion explodes] → first qualify direct/class/alias/independent-provider fixtures under 600 seconds total and 12 GiB; enforce graph caps, record frontiers and stop rather than recursively traverse the whole theorem closure.

## Migration Plan

The new provenance record is additive to existing provider-validity results. Old selected slices remain inspectable; no retroactive assertion of complete provenance. Coordinate registered payload/reader changes through the umbrella before native emission.

