# Tasks

The bounded domain is implemented and independently reviewed. Current result and scoped limitations: [acceptance](evidence/ACCEPTANCE.md). See [design.md](design.md) and [the capability contract](specs/proofir-mathematical-contracts/spec.md).

## 1. Demonstrate a sound bounded contract profile

- [x] 1.1 Define the initial contract denotation, norm-scale compatibility and dependency permission semantics in a small pinned Lean fixture; verify the fixture builds and document the exact supported fragment. See [Lean feasibility](evidence/LEAN-FEASIBILITY.json): natural-valued indexed scales and extensional dependency permissions.
- [x] 1.2 Prove the admitted composition, two-premise combination and monotone-dominance rules with explicit side conditions; run the 60-minute feasibility gate from design.md and preserve axiom/readiness evidence before expanding dependent work. Root supervised replay passed in 0.30 seconds, peak sampled RSS 768290816 bytes under 12 GiB; only standard propext in the listed axiom judgments. [Receipt](evidence/LEAN-FEASIBILITY.json).
- [x] 1.3 Implement the typed contract representation and comparator with known/unknown/unsupported states; verify scope, incompatible-scale, quantifier-order and correlated-tuple controls against the Lean fixture and an independent finite oracle. [Validation](evidence/VALIDATION.json), independent review includes 36,864 correlated comparisons before the explicit-anchor addition.

## 2. Publish consumable native artifacts

- [x] 2.1 Register the two closed native payload kinds, profile/rule identities and stage-variant schema owners; verify malformed fields, missing references, profile drift and byte/depth caps reject through ordinary native validation. [Validation](evidence/VALIDATION.json); comparison admitted, later child variants explicitly unsupported.
- [x] 2.2 Integrate inspection, reference closure and storage/projection dispatch; verify a portable round trip and unchanged canonical IDs for existing native fixtures, and document new kind/version behavior. [Validation](evidence/VALIDATION.json); schema 10 requires disposable rebuild and indexes/FKs are exercised.
- [x] 2.3 Update shared conformance declarations and test unsupported-reader behavior, including Rust's explicit rejection unless parity is implemented; record the supported consumer matrix without claiming untested parity. Profile document and two Rust boundary tests recorded in [validation](evidence/VALIDATION.json).

## 3. Deliver the domain acceptance boundary

- [x] 3.1 Add property/mutation coverage for dependency permissions, dominance side conditions and alpha-renaming; verify the documented examples with real Lean checks and preserve unknown rather than erasing unsupported features. [Validation](evidence/VALIDATION.json), including explicit choice-point and source-authority controls.
- [x] 3.2 Publish domain acceptance evidence, scoped test results, rule theorem/environment identities and child-consumable fixtures; verify no Quux import or mandatory model service is needed and run applicable focused quality checks. [Acceptance](evidence/ACCEPTANCE.md) and [independent review](evidence/INDEPENDENT-REVIEW.json).
