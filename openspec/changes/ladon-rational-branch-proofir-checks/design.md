# Design

## Context

See [proposal.md](proposal.md) for motivation and [the capability delta](specs/ladon-contract-probes/spec.md) for observable behavior. The accepted rational branch checker in `proof_contract_refinement.py` evaluates an exact assignment over a bounded AST, while `proof_contract_probes.py` regenerates source-derived goals and binds their ProofIR/Lean receipts. Existing probe templates lower into a closed Nat context and cannot be reused to claim rational semantics.

## Goals / Non-Goals

**Goals:** Add an isolated, versioned rational-branch checking route that regenerates its Lean goals from the validated rational branch and assignment, and binds those goals and receipts to the same semantic request.

**Non-Goals:** Do not translate manuscript prose, accept caller-authored Lean goals, alter ordinary source-pair probe templates, authenticate branch lineage, prove a theorem over all rationals, or lift a checked assignment into an analytic counterexample.

## Decisions

### Use a separate rational route and worker operation

Add a closed request schema for the branch, source root, base rational goal, assignment, deadline and resource limits. Recompute the existing checker result at planning and checking time. A dedicated producer converts each evaluated predicate's bounded AST into a Lean `Rat` proposition and creates only the obligations dictated by that result. It does not pass these values through the existing paired-template compiler, which assumes a Nat object context and two source readings. The ordinary probe request remains unchanged.

Alternative considered: add `branchId` as metadata to existing application probes. Rejected because current templates would still generate Nat-context goals and would not check any branch predicate.

The request keeps `sourceRoot` and `workspaceRoot` separate. `sourceRoot` validates branch citations and content digests; `workspaceRoot` selects the exact pinned Lean toolchain and prebuilt Mathlib libraries. The first artifact stage is a closed `proofir.contract-analysis` payload named `rational-branch`, with its own profile digest and native validator. It contains only regenerated planning data and no check-run references. The exact generated propositions are normalized in the bounded preflight before a plan is emitted. A failed or unavailable preflight returns a stopped result without an artifact.

### Check translation by differential obligations

Compile rational literals, variable substitutions, arithmetic, powers, absolute values and comparisons into closed Lean `Rat` expressions. Generate one goal per evaluated branch/base premise and conclusion that asserts the corresponding Lean comparison has the exact boolean value reported by the Python checker. Use the workspace's Mathlib tactics to normalize these closed rational goals, then replay the resulting terms through the existing bounded Lean proof checker. A bounded feasibility check found that Lean core alone could not reduce Rat comparisons/equality and did not provide the needed `abs`; the same signed, comparison, power and absolute-value cases compiled with `import Mathlib` and `norm_num`. Therefore this route is supported only when the exact Lean workspace can import the required Mathlib functionality; otherwise it reports unsupported before producing checked support. Python already rejects a division whose evaluated denominator is zero; the Lean route must reject the whole request before goal generation whenever the existing rational checker rejects it, so field division's totalized zero case cannot silently diverge.

Alternative considered: prove only a single derived proposition about the overall assignment status. Rejected because a mismatch could be hidden by aggregation; individual predicate obligations give a smaller differential trace and identify the exact disagreement.

### Bind regenerated semantics through plans and receipts; do not trust public caches

Include branch ID/kind, source-span content identities, base and derived rational-goal digests, exact assignment representation, checker version and generated Lean goal digests in the regenerated plan identity. Bind the same values plus the checked goal and proof-term digests into receipts. Bind the actual compiled import inventory into each check-run artifact and overall checked receipt, and reject a multi-goal result if that inventory changes during checking. Public cache data is unauthenticated and therefore cannot skip fresh Lean replay; cache acceleration stays disabled until Ladon can authenticate local provenance. Keep the artifact and result separately versioned so old source-pair plans remain compatible.

Alternative considered: rely on existing `planId` alone. It is sufficient only if the generated artifact already incorporates branch semantics; a dedicated route must make that dependency explicit in the plan preimage. A plan ID binds the selected Lean executable and compiled-library root paths, but not every `.olean` content digest; checked receipts bind the exact compiled inventory actually loaded for proof replay.

## Risks / Trade-offs

- Lean `Rat` elaboration or `norm_num` may differ from the Python evaluator on an AST operation or literal → Require Mathlib in the exact workspace and run a bounded differential gate covering signed literals, all comparison operators, arithmetic, powers, absolute value and nonzero division; compare every predicate result on a fixed edge-case matrix. Run under the existing bounded Lean worker limits, stop after 60 seconds, and keep the route unsupported if any disagreement or unsupported syntax remains.
- A checked rational assignment can be mistaken for a source-theorem result → Preserve source fidelity as unverified, keep repair branches separate, and describe the result only as checked finite rational obligations.
- Caller-made cache objects can forge public replay/trust labels → Never treat unauthenticated cached data as acceptance; require fresh worker replay and test a structurally matching forged cache.
- Adding a new artifact stage may exceed current ProofIR schema limits → Confirm exact envelope-stage support before producing artifacts; if stage expansion is incompatible, add a new envelope kind/version rather than weakening an existing closed schema.

## Migration Plan

Introduce the new request, artifact and receipt versions without changing existing source-pair requests. Expose the rational path as an explicit route with cache-based acceptance disabled. A future authenticated cache implementation may add acceleration; until then every supplied proof is replayed. Rollback consists of disabling the new route; previously emitted versioned artifacts remain inspectable and existing probe consumers are unaffected.
