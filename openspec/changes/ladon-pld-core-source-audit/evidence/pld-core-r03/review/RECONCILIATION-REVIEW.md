# Reconciliation review (r03)

Reviewer attribution: root's invocation receipt explicitly identifies `gpt-6-luna`, medium effort; my earlier self-reported generic model label is not authoritative. No new Lean run was performed.

I compared the frozen first review with `EVIDENCE-v2.md`, `FINDINGS-v2.md`, and `PRE-REVIEW-MANIFEST.json`, and independently checked the source definitions needed for the law map and the later Gaussian note sections. The frozen first review remains unchanged.

## Corrections to the first assessment

### P2/P3.a/P4: exact law map and formal scope

The initial review was incomplete because it did not state the exact source-to-Lean law map. In the paper notation, take Lean's density arguments as `f=qQ`, `g=pP`. The definitions in `PLDRandomAllocation.lean` give:

- `forwardLossValue f g = log(f/g)`, sampled under density `f`; therefore `concretePLDPair μ qQ pP .forward` is law `Y = log(qQ/pP)` under Q.
- `reverseLossLaw` is `log(g/f)` sampled under `g`; therefore `.reverse` is law `−X`, where paper `X=log(qQ/pP)` is sampled under P. Law(X) is the pushforward of `.reverse` by negation; it is not `.reverse` itself.

Strict positivity justifies the log-ratio identities. This is a mathematical definition substitution, not a newly kernel-checked negation/pushforward theorem. `PLDPair` still stores real measures without the PRV tilt, probability normalization, or extended-line endpoint axioms.

Accordingly, revise the initial P2 description from merely “generic positive-density bridge” to **partial support**: the positive shared-density construction supports forward Y and reverse −X; arbitrary support/singular conventions and the full source theorem remain unresolved. P3.a is likewise **partial forward support**, not a formal proof of the full source PRV tail equality: the generic positive-region integral/event-bound theorem and forward-loss profile integral identity provide local backing, but the law map and arbitrary source generality are not kernel-certified. No evidence here establishes a missing theorem by lexical absence alone.

For P4, the product source convention independently samples the X-side and Y-side; the Lean product theorem encodes independent product laws within each side. With `f_i=qQ_i,g_i=pP_i`, forward composition is the law of `sum Y_i`, while reverse composition is the law of `sum (−X_i)`; negation recovers `sum X_i`. This is a positive-density independent-product specialization, not by itself source privacy-curve preservation or the general PRV composition theorem. Normalization belongs to the paper specialization, since the Lean product theorem admits finite nonnormalized measures.

### G2.b: later source proof

The first review was deliberately scoped to the inventory's cited spans and said the cited early passage left monotonicity as the remaining fact. That statement must not be read as a conclusion about the whole note. The later sections, beyond the selected 212-line audit cutoff, give a direct density-symmetry derivative proof of strict increase for every real ε and σ>0, continuity at zero with limit `(1−exp ε)_+`, the envelope corollary, and the endpoint-transfer proof. I checked those sections in reconciliation. The calculus is internally consistent: `e^ε φ(v)=φ(u)`, hence `F'(a)=2φ(u)>0`; the three ε-sign cases give the stated zero limit. Thus the note does provide mathematical source support for G2.b, including the separate Δ=0 envelope value. This does **not** enlarge the historical Lean query coverage; the formal theorem-level equivalence remains unverified by that query. `H` itself remains defined only for Δ>0, as inventory says.

The source note also states/proves the radial identity and the bridge equivalence, so G1.a/b and G2.a/b have mathematical source derivations in the note. The frozen findings' “unresolved formal/source correspondence” is acceptable if “formal” means checked Lean correspondence; it would be too broad if read as saying the note contains no proof. My initial G1/G2 comments similarly described mathematical support from the text and separately noted the missing Lean coverage.

### P3.d

The smooth normalized witness and sign discrepancy stand. With `δ(s)=∫_s∞q−e^s∫_s∞p`, for `p=N(−1/2,1)`, `q=N(1/2,1)`, and `q/p=e^t`, differentiation yields `δ''−δ'=e^s p(s)=q(s)`. Therefore the printed `x(s)=e^s(δ''−δ')` is false (for example at s=1); paired relation instead gives `x(s)=e^(−s)(δ''−δ')` under the smooth reconstruction assumptions. This does not refute a Lean theorem or establish reconstruction/uniqueness for mixed or endpoint-mass laws.

## Dispositions after reconciliation

| ID | Reconciled assessment |
|---|---|
| P1 | Unresolved: definition context is clear; existence/uniqueness for arbitrary curves and extended endpoints are not supplied by the queried real-measure structures. |
| P2 | Partial mathematical/formal support under strictly positive shared densities with exact Y/−X map; general representation unresolved. |
| P3.a | Mathematical source identity supported under the source PRV tilt; local positive-region/profile formal support only. General source construction remains unresolved. |
| P3.b | Source smoothing calculation supports independent rate-1 exponential Z; no queried formal support. |
| P3.c | Y reconstruction calculation supported under smooth-density/differentiability conditions; unrestricted classical formula unresolved. |
| P3.d | Discrepancy established by smooth normalized witness; correction is a distinct regularity-qualified formula. |
| P3.e | Unresolved: neither correction nor local pair definitions establish representation independence/uniqueness including endpoint masses. |
| P4 | Positive-density independent-product paired-law specialization supported with reverse `−X` and explicit negation; full curve preservation/general PRV claim unresolved. |
| G1.a | Mathematical source derivation supports the positive-part supremum and likelihood halfspace; no checked Lean theorem for this equality. Degenerate d=0 allows nonunique maximizers. |
| G1.b | Positive-r CDF reduction is algebraically and probabilistically supported in the note; r=0 is separate; no checked Lean projection/equality theorem. |
| G2.a | Mathematical source derivation supports radial profile including declared zero value; queried Lean theorem does not prove this equality. |
| G2.b | Later source sections prove strict monotonicity, envelope and endpoint transfer, with Δ=0 treated separately; queried Lean coverage does not certify the bridge. |
| S1 | Restricted one-way finite-Gaussian analytic-condition-to-event implication, with ε≥0, δ<1 and listed distance/domain premises only. |

All inventory IDs are reconciled; none are missing. The PRE-REVIEW manifest provides freeze hashes and inherited input/raw-evidence paths; it does not change the historical queried theorem scope or establish source-to-kernel correspondence beyond the signatures in the raw log.
