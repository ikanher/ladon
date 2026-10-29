# Informed derivative-loss diagnostic

**The current application checker exposes the missing fifth-derivative premises
on the actual cited declaration.** Its faithful five-derivative control closes;
the otherwise identical four-derivative probe leaves exactly two fifth-order
bounds unresolved. The specialized contract producer and scoped proof slice
both encounter explicit limits on this real theorem. No Ladon runtime was
changed for this diagnostic.

This is answer-informed development evidence. The passage and declaration were
selected from the existing [published comparison](../../../ladon-proof-correspondence-audit-umbrella/evidence/r70/PUBLISHED_COMPARISON.md).
The result does not establish independent discovery, a refutation of the paper's
estimate, or completion of the original prose-to-Lean correspondence.

## Original question and faithful control

Lemma 8.6, equation (8.19), states a bound of the form

`‖N⁻¹ F‖_(C_y^m) ≤ C_m ‖F‖_(C_y^(m+4))`.

The original [pages 95–96](../../../ladon-proof-correspondence-audit-umbrella/evidence/r70/sources/navier/pages-95-96.txt)
and [PDF](../../../ladon-proof-correspondence-audit-umbrella/evidence/r70/sources/navier/navier-stokes.pdf)
remain unchanged. Its claimed constant is independent of the source function.

The selected declaration is
`NavierStokes.SmoothFamilyTorusInverse.norm_derivativeWord_inverse_le` at the
pinned original commit `f9e8bc5b38b6e212696e8a30e3e91517af887bbd`.
It bounds one output derivative word using a common scalar bound on the source
and its two pure coordinate derivatives of order `w.length + 5`.

The [five-order control](goal-loss-5.txt) preserves this declaration's complete
interface: arbitrary parameter type and instances, direction, source function,
smoothness, periodicity, word, parameter, point, scalar bound and conclusion.
The [four-order probe](goal-loss-4.txt) changes only the two input derivative
orders from `w.length + 5` to `w.length + 4`. Their frozen authoring contract is
[APPLICATION-PROBES.json](APPLICATION-PROBES.json).

These goals are **authored application probes**, not an encoding of the complete
paper estimate. In particular they do not construct a conventional `C^m` norm,
take the finite maximum over output words, or prove the paper's existence and
uniqueness assertion. The faithful control is faithful to the cited formal
theorem; its fifth-order premises are stronger than the paper's stated input
regularity. No source passage was edited to obtain that control.

## Executed results

| Existing operation | Observed result | Evidence |
| --- | --- | --- |
| `investigation contract produce --channel formal` on the original theorem | Source statement observed; contract `unsupported`, with `telescope-limit`; no contract emitted | [Result](formal-production.json), [command](formal-producer-command.json) |
| `proof-search check candidate` with five-order premises | `accepted`, complete, five premises discharged, zero residuals | [Result](application-loss-5.json), [command](application-loss-5-command.json) |
| Same check with four-order premises | `applicable-with-residuals`, partial, three premises discharged, exactly two unresolved fifth-order bounds | [Result](application-loss-4.json), [command](application-loss-4-command.json) |
| Ordinary Lean check of the faithful control and printed axioms | Exit zero; both the control and original declaration use only `propext`, `Classical.choice`, `Quot.sound` | [Source](CheckControl.lean), [receipt](control-trust-command.json) |
| Scoped slice of the actual `coefficient_seminorm_bound` application | Original source compilation succeeds; generated helper fails with `expression node count exceeds 8192`; slice unavailable | [Result](scoped-slice.json), [command](scoped-slice-command.json) |

The two unresolved premises are the common-`C` bounds for
`xJet (w.length + 5) (slice f p)` and for the coordinate-swapped slice on the unit
square. The four-order assumptions remain in their local contexts; the checker
does not silently replace them with the missing fifth-order bounds.
[APPLICATION-SUMMARY.json](APPLICATION-SUMMARY.json) preserves the short result
projection. CLI exit zero alone is insufficient: the formal producer exits
successfully while its mathematical profile reports `unsupported`.

The initial application receipts use `ambient-selected-application-check` and
explicitly report source freshness as unknown. Their exact imported environment
is recorded, but they are not certificates of a freshly rebuilt entire import
closure. The separate control check uses copied compiled imports. The later
slice freshly compiles the selected original source before its traversal fails;
that failure supplies no completed slice or native correspondence certificate.
The control compile emits two unused-binder-name warnings for `hf` and `hp`;
both hypotheses remain in the theorem's quantified type.

## Where the automated routes stop

1. **Formal contract recognition.** The observed declaration has 14 binders;
   the producer admits at most eight. Independently, its current profile accepts
   Nat binder domains, Nat order and Nat multiplication. This theorem involves
   parameter types and instances, functions, propositions, lists, Real bounds
   and Complex norms. Increasing the binder limit alone cannot admit it.
   See `src/ladon/proof_contract_recognition.py` and the preserved observation.

2. **Selected proof extraction.** `scopedOccurrences` in
   `src/ladon/lean/ladon_scoped_slice_helper.lean` recursively walks the theorem
   expression and counts visits. The 8,192-visit guard fires during that walk,
   before the separate expression serialization and one-MiB guards. No evidence
   here identifies how many distinct shared expression nodes exist or whether
   the requested occurrence was reached before the limit. A larger budget,
   occurrence-directed traversal or sharing-aware traversal is a proposal, not
   an exercised fix.

3. **Prose interpretation and norm bridge.** The ordinary application checker
   accepts rich Lean propositions and already exposes the required local
   premises. An author still supplied the source reading and application goals.
   The full paper comparison needs conventional norm and derivative-word
   identifications, the finite maximum over output orders, and either a valid
   four-loss proof or another sufficient bridge. The existing application result
   does not construct those identifications automatically.

The source proof uses the coefficient estimate at order `w.length + 1`, whose
input requirement adds four further derivatives. Thus the visible source path
requests `w.length + 5`. This remains a source-inspected explanation: the scoped
slice that would expose that internal application did not complete.

## Why the missing premise matters

A failed application alone does not prove a mathematical gap. Here there is
also a simple ordinary mathematical check of the proposed direct premise
transfer. On the two-torus take

`F_n(x,y) = (2πn)^(-4) exp(2π i n x)`, for positive integers `n`.

These functions are smooth, periodic and have zero mean. Derivatives involving
`y` vanish. The magnitude of the pure `k`th `x` derivative is `(2πn)^(k-4)`.
Consequently the maximum of all coordinate derivatives through order four is
one, while the fifth derivative has magnitude `2πn`. This rules out deriving
the needed fifth-order bound from the fourth-order norm with the same bound,
or with any fixed function-independent multiplier.

This calculation was checked by the root and independent reviewer as ordinary
mathematics; it was **not Lean-formalized in this diagnostic**. It refutes that
particular input-premise transfer, not the four-loss inverse estimate. A sharper
Fourier argument can avoid the missing premise. The paper's estimate and its
other possible formal counterparts remain outside this local result.

## Independent review and resources

One fresh Luna-medium sidecar reviewed the original source comparison, frozen
goals and application results. Its [first audit](AUDIT.json) agrees with the
bounded result and identifies the remaining norm bridge. The
[addendum](AUDIT-ADDENDUM.json) reviews the control's trust receipt, the 14-binder
observation, the Nat-only recognition limits and the traversal failure. Both
are read-only source/evidence reviews; the reviewer did not run Lean. Root ran
the recorded commands and checked their outputs. Exact dispatch and result
identities are retained in [assignment](REVIEW-ASSIGNMENT.json) and
[verification](VERIFICATION.json).

All processes used the current local Ladon 0.4.0 checkout and the original
Lean 4.34.0-rc2 toolchain. Formal production took 13.27 seconds; the five- and
four-order application commands took 4.61 and 4.53 seconds; the ordinary control
check took 3.18 seconds; the failed slice took 7.57 seconds. The largest sampled
outer-process RSS was approximately 5.02 GiB, below the fixed 12 GiB cap.
No command timed out or exhausted memory or output. The slice failed at its
expression traversal bound. These are individual observations, not speedup or
detection-accuracy measurements.

Primary sources and runtime inputs were verified unchanged. The independent
retest-8 report remains frozen and separate; its Lemma 6.1 result contributes
no answer-informed case to a discovery evaluation. No package code or tests
were changed, no full suite was rerun, and nothing was pushed.

## Decision

This diagnostic demonstrates a useful existing capability: **once a faithful
local context is supplied, the application checker can retain the precise
missing hypotheses while accepting the faithful control**. It also gives a
concrete proof-extraction failure to reproduce on a real analytic declaration.

The smallest proposed engineering follow-up is to make bounded selected
application extraction usable on this exact theorem while preserving local
contexts, occurrence identity, resource stops and honest coverage. The retained
failure is an acceptance target; any change must retain the five-order success
and the two four-order residuals. This is a proposal, not an implemented fix or
authorization to broaden the runtime automatically.

The original contract producer requires a separately designed analytic profile;
a binder-cap increase is insufficient. Before another discovery trial, the
source reading and exact missing-premise comparison should be retained together
through existing evidence/report operations. General norm interpretation and
selection of useful passages remain unestablished. Parent gates 2.1, 3.3 and
3.4 stay open; this informed case does not satisfy the A/B/C promotion protocol.
