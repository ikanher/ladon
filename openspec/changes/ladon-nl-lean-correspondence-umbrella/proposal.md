# Proposal

## Why

The latest paper audit produced a qualified, independently reviewed countercalculation, but its main finding remained outside Ladon's bound step-review workflow and only four comparisons reached reviewed status. Ladon needs to connect exact informal inferences to actual Lean applications and check the missing implications; additional inventories or schema-valid graphs alone do not supply that capability.

## What Changes

- Introduce source-bound, structured interpretations of prose claims with explicit binders, domains, quantifier scopes, permitted witness/constant dependencies, and unresolved alternatives.
- Extract bounded local Lean proof slices containing actual applications, instantiated arguments, local contexts, premise providers, and explicit omitted branches.
- Relate the informal and formal arguments through many-to-many correspondence links. Generate and check premise-supply and conclusion-transfer obligations against the original interpreted claim.
- Preserve separate outcomes for conditional-step validity, establishment of its premises, parent-claim support, interpretation fidelity, and method correspondence. Rejected proof attempts do not become refutations.
- Produce native ProofIR v3 evidence directly from the ordinary investigation workflow; reuse existing identity, derivation, source-goal, and checker contracts. Make independent reviews and counterexamples durable without duplicate manual transcription.
- Start with one working vertical: a checked local correspondence on an existing real proof passage, accompanied by portable positive, negative, and ambiguous controls. Expand extraction and challenge selection only after this gate works.
- Evaluate the resulting workflow on frozen held-out passages with actual Lean sources and a matched ordinary-tool baseline. Record negative or inconclusive results without claiming general detection or upgrading historical runs.

The bounded outcome is a public local-checkout command path that takes a quoted passage, an attributed interpretation, and selected formal support, then reports exact supported links, checked refutations, or remaining obligations. The first real-source case may remain interpretation-sensitive; preserving that distinction is part of success. The umbrella ends after the working vertical, bounded extensions, consumer checks, and one predeclared evaluation. Full-paper restarts require a separate evaluation decision.

Detailed requirements are in the four [capability specs](specs/), with staged acceptance in [work-packages.md](work-packages.md).

## Capabilities

### New Capabilities

- `ladon-prose-claim-interpretations`: Structured, source-bound interpretations and ambiguity, preserving binder scope and mathematical dependency permissions.
- `ladon-lean-proof-slices`: Bounded extraction of actual local Lean proof applications and their premise providers, with source and environment evidence.
- `ladon-proof-correspondence-checks`: Explicit object correspondence, generated implication obligations, scoped replay and refutation, and separate argument-validity judgments.
- `ladon-correspondence-review-workflow`: Ordinary CLI workflow, direct native evidence production, independent review, incremental results, and bounded comparative evaluation.

### Modified Capabilities

None at the existing core-contract level. The native v3 envelope, opaque Lean identity, observation-authority, and AND/OR derivation requirements are reused unchanged. Any added payload kind is explicitly registered and validated; no legacy converter or permissive payload path is introduced.

## Impact

Primary implementation owners are Ladon's investigation CLI/runtime, source-goal and semantic-check workers, Lean helpers, native ProofIR producers/validators/queries, and result rendering. Focused regressions may touch declaration compaction and entrypoint option routing where the recorded failures affect the consuming path. Tests, generic guides, and the packaged skill gain executable examples.

The change is additive and opt-in; current investigation v1/v2 files and existing CLI behavior remain supported. No mandatory model service or new solver dependency is assumed. Quux is an optional external experiment source, not a runtime dependency or a required checkout. No manuscript edits, historical-score rewrites, repository-wide formalization, or automatic unrestricted natural-language semantics are included.
