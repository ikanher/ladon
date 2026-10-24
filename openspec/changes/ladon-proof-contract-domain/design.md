# Design

## Context

See proposal.md and the parent design. proofir_v3.py owns closed envelopes and bounds; proofir_v3_payloads.py owns kind dispatch. correspondence_interpretation.py already preserves scoped binders and explicit symbols. Core readers intentionally do not interpret Lean expressions. The new domain must add mathematical summaries without bypassing those boundaries.

## Goals / Non-Goals

**Goals:** provide one consumable contract model with a small denotation and sound supported operations. **Non-Goals:** normalize arbitrary Lean types in Python, infer necessary parameter dependence from proof-term occurrence, or impose a universal semiring on every proof.

## Decisions

### Full proposition plus abstract features

A contract binds a statement/interpretation reference, an ordered typed telescope, assumption/conclusion references, domain predicates, norm/regularity scale identity, and feature records with known/unknown/unsupported states. Regularity is indexed by a declared scale and an affine nonnegative integer offset in the first profile. Constant and witness dependence uses binder-scoped allowed-dependency sets tied to quantifier order. Unknown is not the empty dependency set. An allowed dependence is an upper bound on what a witness may use, not evidence that it must use every parameter.

Define the profile's denotation as an explicit quantified proposition. For estimates, preserve function/operator identities and norm indices rather than only a derivative-loss integer. Contract comparison is implication under an explicit shared context and object map. Only compare different scales, domains or representations with a checked bridge. Alpha-renaming can preserve semantics without requiring distinct source artifact IDs to coincide.

### Initial mathematical profile

Admit norm-scale estimates, nonnegative scalar bounds, logical conjunction/application, and restricted quantifiers. A supported composition rule takes estimates for two compatible operators and returns their composite estimate with summed offsets and valid nonnegative constant composition. Combining two requirements may use a maximum only with a declared, checked nesting/embedding relation. Dependencies combine conservatively under the exact scope. Generic domain inclusion and quantifier rewrites require specific checked rules.

Formalize a small contract interpreter and soundness of each admitted rule in a pinned Lean fixture. The Python evaluator implements the corresponding finite structural operations and is checked against Lean-produced examples and an independent small oracle. Those tests do not prove arbitrary extraction soundness. Every generated route remains a conditional analysis result until its exact applications and premise providers are checked.

### Dominance and rule registry

Define A dominates B only when, for the same endpoint and compatible context, A has no stronger requirements and no weaker guarantees under supported implication rules. Return dominates, equivalent, incomparable or unknown with evidence. Retain complete tuple correlations. Rule records identify version, premise arity/order, side conditions, substitutions, output construction, monotonicity evidence and Lean theorem/environment. Unsupported proposed rules remain advisory and cannot prune frontiers or discharge obligations.

### Native integration

Register proofir.contract and proofir.contract-analysis with dedicated closed payload validators. The latter has explicit stage variants; later children extend only their owned variant under the shared profile, with conformance updates. Preserve v3 canonicalization, exact references, source/environment identities and limits. Store profile/rule digests and authority/completeness dimensions. Update Python inspect/validation/storage dispatch and shared conformance declarations; Rust must either support the tested subset or reject it explicitly. No silent opaque-success projection.

## Risks / Trade-offs

- Numeric loss hides incompatible norms → scale/object identities are mandatory.
- Apparent dependency disappears through a lemma → dependence comparisons are conservative; elimination needs a checked implication.
- Proving the abstraction consumes the project → feasibility is one composed estimate, a two-premise maximum with embedding, and a two-route trade-off, bounded to 60 minutes of check execution and 12 GiB RSS. Stop with a named unsupported rule if these cannot be represented soundly.
- Shared schema becomes a monolith → dedicated contract validators and stage variants keep the native envelope unchanged.

## Migration Plan

Add kinds and profile version; existing bytes/IDs are unchanged. First publish domain fixtures and reader rejection tests, then allow children to consume the profile. Changing a rule's mathematical meaning creates a new profile/rule identity and invalidates dependent summaries. Rollback removes producer exposure without rewriting existing artifacts.

