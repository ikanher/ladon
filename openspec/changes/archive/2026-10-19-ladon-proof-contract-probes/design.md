# Design

## Context

See proposal.md. Existing Lean application checks and rational witnesses can test exact obligations. Quux ProbeSeparation proves a finite matrix example only; it does not provide a separating family for arbitrary mathematical statements.

## Goals / Non-Goals

**Goals:** turn contract differences into concrete downstream use questions with reproducible evidence. **Non-Goals:** interpret failure to find a term as a refutation, or infer general equivalence from a finite set of successful probes.

## Decisions

### Typed probe templates

Freeze five initial families: boundary regularity application; constant selection before a varying parameter; existential witness dependence; restricted-domain application; inequality-direction transfer. Each template carries exact source contract IDs, object map, desired application, scoped assumptions, expected observation kind and permitted checker. Templates use semantic feature identities, not paper names or equation numbers.

The first restricted-domain consumer is intentionally limited to `∀ x : Nat, P x` versus `∀ x : Nat, x ≤ 0 → P x`; its contract endpoint and conclusion must identify the exact AST predicate symbol. Broader subset/subtype and other guard profiles remain explicit unsupported cases.

The inequality-direction consumer is intentionally limited to the source-bound pair `∀ x : Nat, x ≤ 0` and `∀ x : Nat, 0 ≤ x`. It recognizes only a single Nat universal binder and the literal zero-bound operand reversal, requires exact shared native contract context (`object:nat-order`, `domain:Nat`, `scale:none`, `representation:original`) and `relation:Nat.le` endpoint/conclusion identities, and rejects assumptions or non-unknown out-of-scope metadata. The left-to-right implication is the valid Nat control; right-to-left counterexample evidence is checked separately. Other constants, types, relations, and order contexts remain unsupported.

A probe can yield checked application support, a checked counterexample to an implication, or an unresolved attempt. Comparing acceptance with failed elaboration can reveal a syntactic/application restriction, but alone does not prove semantic separation. Mark semantic distinguishing evidence only when the exact supported interpretation is checked on one side and an appropriate checked non-implication/counterexample is available on the other.

### Authority of agreement

Finite agreement reports survived-probe-family. It can become equivalence only with a replayed separating-family theorem for the exact object class, observation function and chosen family. The first delivery includes a tiny finite calibration with such a theorem and an unseparated pair that agrees on incomplete probes. This validates the boundary without claiming a separating basis for PDE estimates.

### Execution and findings

Reuse existing candidate workers, source-goal completion and rational_witness.py. No model API is required to run frozen probes; an LLM may propose additional terms as attributed attempts. The probe command emits the analysis probe variant and check-run/attempt-log references. Cache only exact subject/environment/template matches. At most 64 probes share the parent clock and 12 GiB worker cap; every attempt remains in the denominator.

An optional prior result on `check-probe` is only a receipt cache. Ladon regenerates the plan and source context under the same absolute deadline before reuse, binds it to the same plan ID and exact generated goal, reloads each content-addressed raw checker result, and checks its accepted trust state plus proof-term digest. Each accepted raw result also carries a Ladon-added binding to that plan, goal ID, goal digest/text and term digest; this prevents a receipt reference from being transplanted between generated goals. The repository-local `.ladon` store is trusted input: hashing detects later mutation but does not authenticate the original writer. Do not reuse data from an untrusted workspace; malicious same-user writers with access to that store are outside this mechanism's threat model. A changed plan identity is stale; unsupported, corrupt, incomplete and expired entries confer no authority. Goals with a different submitted term take the ordinary bounded checker route. The CLI reads this cache from `--reuse-result`; reused goals are marked explicitly.

Independent review receives original interpretation records and source-map anchors, exact generated goals, and every submitted checker attempt with its raw evidence. The review-export API accepts an explicit ordered list of complete result envelopes from separate invocations; it preserves order and duplicates because the runner itself has no cross-invocation attempt ledger. Each attempt is bound to the exact inspected native plan where possible; failures before preparation remain visible as unbound execution attempts. The exported reviewer input contains no proposed semantic outcome, authority/fidelity/falsity labels, or candidate-analysis wrapper. Low-level checker/execution outcomes remain visible as evidence. Existing content-addressed receipt loading detects changed evidence but, like reuse, trusts the local Ladon evidence store and does not authenticate its writer. Valid transport, stronger-than-needed hypotheses and harmless alternate proof routes are required controls.

## Risks / Trade-offs

- Easy probes produce reassuring but irrelevant success → bind each probe to a specific contract feature and report its distinguishing scope.
- Witness search failures inflate fault counts → keep unresolved distinct from checked refutation throughout report projection.
- Probe-family completeness becomes a research project → require only the tiny separating-family calibration; general completeness is explicitly unsupported.
- Templates fail to distinguish even a simple family → stop after a 30-minute check of five faults and five matching controls; record which template remains unsupported.

## Migration Plan

Extend only the domain-owned probe variant and opt-in CLI branch. Historical findings keep their labels and authority. New checker runs never overwrite old first attempts or reviewer responses.

