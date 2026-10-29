# Proposed bounded profile for real derivative-bound predicates

Status: reviewable design, not an implemented capability or an amendment to the
current runtime freeze. Parent task 2.1 remains open. The proposal responds to the
current real-source limitation; it does not promise discovery of an unfamiliar
exposition error.

## Concrete target

Add a separately versioned profile, provisionally `real-jet-bound-v1`, for
estimates of this shape, preserving the full typed context:

```text
∀ parameter-space / instances / fixed operator parameters / n,
  ∃ K : ℝ, 0 ≤ K ∧
    ∀ f S C,
      smooth f → periodic f → 0 ≤ C →
      J f S (n + δ) C → J (A f) S n (K * C)
```

Here `J f S r C` must be admitted as the actual predicate that bounds every joint
Fréchet derivative through order `r`, at every parameter in `S` and every torus
cover point. The initial production path supports a fixed natural literal `δ`.
K is selected after the fixed parameters and n, before f/S/C. Exact dependency
positions and source predicates remain part of the contract.

The real source positives are `inverse_finiteJets` (δ=5) and
`nonbarPart_finiteJets` (δ=4). They have different operator endpoints. The generic
`applyMultiplier_finiteJets` has symbolic `n+l+4`; its complete generic contract
remains unsupported in this first slice. Its existing source-bound applications
with l=1 or l=0 remain available as independent proof observations.

## Meaning and admission

Keep `norm-scale-v1` and its existing digest/semantics unchanged. Merely accepting
Real binders or renaming the old profile would reuse unproved natural-scalar laws
and would not preserve the function/set/predicate structure.

A new profile must retain typed references for the parameter context, predicate,
operator, input function, parameter set, scale index, bound, sign guards and
constant. Admission cannot be based only on a declaration name or a substring
such as `JetBound`:

1. Bind the predicate to its actual definition, source, compiled environment and
   exact application. Verify its equality with the supported derivative-prefix
   predicate through Lean, or retain a named unchecked admission obligation.
2. Preserve all j≤r / p∈S / Y quantifiers and the norm/carrier in that predicate.
3. Require checked laws for order-prefix weakening, increasing the real bound,
   and any multiplication/composition rule actually enabled. A syntax match or
   a natural-scalar fixture does not supply a Real-valued proof.
4. Track the position of K and all guards. A source-dependent constant is a
   different guarantee from a constant uniform over f/S/C.
5. Limit the first implementation to the supported literal shift and exact
   function/set matching. Leave symbolic offsets, other norms and unhandled
   guards opaque with named residuals.

A concrete registered bridge to the existing `JetBound` is acceptable; a special
case that trusts the Navier–Stokes declaration name is not. Its metadata must
bind the checked definition and laws, and invalidate after relevant source,
compiled import, helper, profile or toolchain changes.

## Consumer behavior

- Formal production emits only source-derived features and origins. Preserve
  unsupported statement snapshots and existing public CLI behavior.
- Validation dispatches explicitly on profile ID/digest. Old records retain
  their exact validation and comparison meaning. Unknown profiles reject.
- Comparison first checks endpoint, typed predicate/domain, representation,
  function/set correspondence and constant scope. It may then compare supported
  derivative requirements. Different operators cannot be silently identified.
- Propagation enables only the new profile's proved rules. Unsupported consumers
  reject or retain explicit unknowns; they cannot fall back to the Nat profile.
- The source-map and interpretation references, admissions and check evidence
  must survive native validation, storage, inspection and report projection.
  Use versioned payload variants if the current closed payload cannot express
  those references; do not add unchecked semantic fields to extension objects.
- A formal profile does not define the paper's conventional C_y^m norm.
  `paper-norm-bridge-unproved` remains until an exact source interpretation and
  checked adapter exist. A four-versus-five observation is a route comparison;
  it is not a theorem refutation.

## Test-first acceptance and measures

Freeze source cases and run the same current-checkout public operations before
and after implementation. Current baseline: both fixed-loss positives are
observed but unsupported (0/2 formal contracts); the symbolic case is observed
but unsupported (0/1). The next implementation target is 2/2 fixed-loss contracts
with exact origins and unchanged symbolic unsupported behavior. That is a
capability metric on informed source cases, not a discovery metric.

| Case | Required behavior |
|---|---|
| Existing inverse theorem | Extract δ=5, exact operator/predicate/set and quantifier dependencies, retaining nonnegativity and regularity assumptions. |
| Existing mean-removal theorem | Extract δ=4 with its own endpoint; never equate it with inversion. |
| Symbolic `n+l+4` theorem | Keep unsupported with exact source observation; never invent a fixed loss. |
| A genuine separately observed four-loss inverse statement | Preserve its actual δ=4 if admitted. The producer must not hardcode five or reject a statement merely because the known control uses five. |
| Alter five to four inside a frozen observation | Reject stale/tampered evidence. Direct application of the existing five-order theorem to that altered goal remains rejected, without declaring the altered proposition false. |
| Move K after f/S/C | Record the changed dependency guarantee, or return unsupported with that reason; never label it uniform. |
| Change f, A, S or a parameter instance on one side | Keep their exact identities; reject an unjustified same-endpoint comparison or unsupported production. |
| Drop a sign guard / put the estimate under negation or a disjunction | Preserve logical polarity and guards, or return unsupported. Never extract an unconditional estimate from a branch. |
| A same-named fake predicate with different definition | Fail profile admission even if its source text contains similar order arithmetic. |
| Substitute coordinate-only bounds or a paper norm | Leave a bridge residual until the exact interpretation is checked. |
| Unsupported mathematical profile in an old consumer | Explicit rejection/unknown, with historical profile behavior unchanged. |

Use false-positive controls as a separate count; require zero promotions of
unadmitted predicates, lost guards, mismatched endpoints or widened permissions.
Retain command cost, peak RSS, observations, extracted contract count and residuals
per case. Do not replace negative/unsupported cases with easier examples after
freezing them.

## Implementation and completion boundary

A bounded implementation would cover profile/record dispatch, a typed producer,
checked admission/laws, direct comparison, actual public CLI/report consumers and
historical-profile regression. Broader generic norm inference, a new paper proof,
beam search, caching and another blind paper run are outside this proposal.

Acceptance needs fresh original-source application checks, independent review of
profile meaning and trust boundaries, affected tests and native consumer checks,
and strict quality/OpenSpec validation. Keep full-suite qualification and
held-out benefit gates open until their own requirements are satisfied. Use the
existing 12 GiB cap and serialized Lean checks. Do not push.

The scope decision is whether to reopen the current mathematical-profile freeze
for this concrete capability. The producer and its consumers require a real
extension; the existing domain does not already supply it.
