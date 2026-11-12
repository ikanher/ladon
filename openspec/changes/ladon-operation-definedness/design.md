# Design

## Context

Typed lowering already binds operators to authored types, and typed prose observation retains actual elaborated expressions without granting truth or fidelity. docs/PROOF_CORRESPONDENCE_AUDIT.md records the empty-natural-set infimum example. This child makes such selected property checks reusable without reimplementing mathematical semantics.

## Goals / Non-Goals

**Goals:** expose exact typed operation meanings and demand evidence for properties actually presumed by the source.
**Non-goals:** prohibit total operations, automatically infer every informal presupposition, equate type checking with existence, or build a universal default-value detector.

## Decisions

### Expectations precede checking

A request binds an attributed source quote, interpretation and exact operation occurrence to an expected property: operation transport, existence, selected-value membership or a guard. The original source reviewer supplies this expectation before inspecting the counterpart's result. If the text does not select one interpretation, retain alternatives or unknown. Nothing may silently add nonemptiness, nonzero or order premises.

A property is not automatically required just because an operation is total. For an intentionally defaulting function the source may require no membership guarantee at all. Nat subtraction is always a defined operation; a mismatch arises only for the selected transport/algebraic property.

### Small typed adapter registry

Reuse current typed observation/lowering and Lean declaration fingerprints. Each adapter has versioned applicability, exact type/instance requirements, generated property goals and unsupported reasons.
- Nat/Int subtraction: compare an explicitly mapped expression/property, with and without the original order guard. Numerals and casts are elaborated at their intended types.
- Natural-set infimum: preserve exact set and instantiation; expose the source's existence/membership claim, checking nonemptiness or the direct selected-value property using pinned mathlib.
- A source-authored fallback selector can use the generic exact-property path with an explicit typed selection predicate. It receives no automatic library theorem recognition.

Do not name-match arbitrary minimum functions, treat Set Nat as an untyped set universe, or choose defaults in Python. Other operations (division, choice, extrema over reals) remain unsupported until separately qualified.

### Evidence and context

Generate separate original property and proposed guard/repair goals. Existing Lean capture/completion, independent replay and axiom policy establish property support or checked negation. Failed elaboration is a type/attempt outcome, not falsity. An explicit counterexample is tied to its assignment and actual operation identity.

Construct the complete original proposition before selecting its polarity. For `P := ∀ x, H x → Q x`, a refutation checks `¬ P` in an independent closed query, or checks an assignment with `H a ∧ ¬ Q a`. A local negative completion closed as `∀ x, H x → ¬ Q x` is only a conditional negative fact; it does not refute P. In particular, contradictory H permits both conditional polarities. Inspect the actual replayed closed target and its remaining assumptions before granting refutation authority. Controls must cover ambient `h : False`, aliases derived from hypotheses, contradictory branches and a genuine premise-satisfying counterexample.

Feasibility is a separate consumer dimension. Checks under H remain conditional even when the feasibility child is not run. A contradictory H cannot become unconditional existence evidence. Source interpretation review and exact bytes remain separately visible.

## Risks / Trade-offs

- [Pinned mathlib infimum interface differs] → qualify the actual elaborated constant/instance and a nonempty/empty pair in the fixture toolchain; do not assume identifiers across versions.
- [Automatic expectation invents the bug] → independent source review and controls where the same total operation is intentional.
- [Adapter broadens without evidence] → first run subtraction and Nat-infimum positive/negative probes under 600 seconds total, 12 GiB, existing output caps. Stop with an explicit unsupported receipt if exact operation identity cannot be retained; no whole-library scan.

## Migration Plan

New adapter/profile versions and receipts remain opt-in. Existing typed interpretation semantics and frozen readings stay unchanged. The umbrella owns public report projection and backward compatibility tests.

