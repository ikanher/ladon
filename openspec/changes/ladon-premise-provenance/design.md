# Design

## Context

proof_slice already extracts selected scoped applications. proof_contract_provider_expansion.py revalidates owner-bound demand and observes one provider while leaving its obligation unresolved. Extend this evidence rather than infer origins from an axiom list or lexical dependency names.

## Goals / Non-Goals

**Goals:** show how a selected proof receives a conclusion through an actual hypothesis, structure field or instance, and identify missing source justification.
**Non-goals:** prove hypothesis necessity, decide arbitrary logical equivalence, expand the whole imported library, or infer circularity from a graph cycle alone.

## Decisions

### Bounded provider provenance

Use existing owner/local IDs, application occurrence, branch scope, proof argument and provider closures. A node records origin category (boundary hypothesis, local definition, field projection, instance argument, theorem application or unresolved provider). Edges record actual term dependencies and exact scope. Shared nodes are deduplicated by scoped identity while occurrence edges remain distinct.

Initial scope handles direct hypothesis use, local aliases, structure projection and instantiated type-class projection. Recursive/opaque providers and unsupported dependent projections retain named frontiers. The deferred provenance graph initially proposes 4096 nodes, 16384 edges and graph depth 64; those are graph limits, not proof-expression traversal limits. Existing slice traversal now defaults to 128 with a CLI override. Its 8 MiB output allowance did not fit the measured real-source observation. Keep future graph-output policy deferred until a selected mathematical obligation requires graph implementation; do not equate these separate limits.

### Mathematical comparison before extraction usability work

The revised [PLD bounded audit](../ladon-pld-core-source-audit/evidence/pld-core-r03/REPORT-v2.md) is complete. Its [child task ledger](../ladon-pld-core-source-audit/tasks.md) owns current status and its adjudication owns the upheld source formula finding, independent all-ID review, mathematical control support and incomplete formal correspondence. No production extension or comparative benefit follows from this exposed development result.

The subsequent matched pilot did not exercise native provenance. Its negative discovery gate does not settle the value of scoped proof-route evidence. The [umbrella's current decision](../ladon-semantic-pitfalls-umbrella/design.md#current-decision-after-the-matched-pilot) owns the next workflow qualification; the graph and resource/API changes here remain conditional on a concrete unresolved source obligation.

For each case retain the source claim, exact premise, observed original-proof route, available checked projection and reviewed source justification. The same formal projection can accompany either a faithful conditional passage or an omitted source obligation. The source mapping decides that distinction; do not infer an exposition fault from the formal route alone. A new proof of a projection does not establish that the original proof used it. Authored passages and mutations remain constructed development material, and exposed cases cannot establish blind discovery.

Use existing local-checkout Ladon, ordinary Lean and the retained experimental observation. If a new extraction needs the working experimental runtime, record its exact identity and bounds; preserve historical and fresh evidence separately. No production re-extraction is required solely for this report. Independent provider replay remains unresolved unless actually performed.

### Deferred resource configuration

Q.1–Q.3 are activated only by a documented blocker on a selected mathematical obligation. The report owns the successful experimental settings; they are not production defaults. If configuration becomes necessary, define finite units/ranges, bind effective settings to identity, preserve legacy inspection and carry settings through all affected re-extraction consumers. Producer, supervisor, parser and validator byte bounds must agree. Distinguish printer, elaboration, frame/output, timeout and memory failures without automatic escalation. Keep correctness/compatibility review before any production change; avoid new canonical fields without their required version/reader review.

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

