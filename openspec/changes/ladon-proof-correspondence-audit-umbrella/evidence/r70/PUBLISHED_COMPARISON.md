# One pinned inverse-estimate comparison

**Finding:** the inspected declaration requests five additional torus-coordinate derivatives, while the paper's equation (8.19) states four. This is a source-local coverage gap for that declaration, not a counterexample to (8.19), a renewed compiler result, or a judgment on the full Navier–Stokes argument.

The comparison is root-authored. It begins from the critique's reported example rather than independent discovery. Sources are frozen in [inventory](sources/navier/inventory.json): the [original PDF](sources/navier/navier-stokes.pdf), [pages 95–96 extraction](sources/navier/pages-95-96.txt), and GitHub commit `f9e8bc5b38b6e212696e8a30e3e91517af887bbd`. The supplied critique's `ex:Navier_strong` is in the [unchanged TeX](sources/paper/NavierStokes_LostInTranslation_ArXiv.tex). PDF extraction is a navigation aid; the original page governs notation.

## Exact comparison obligation

Fix the temporal direction `d=.temporal`, a smooth zero-mean periodic function, a fixed parameter `p`, and nonnegative integer `m`. Can the cited result, with appropriate definition identifications, establish a uniform estimate

`‖N⁻¹F‖_(C_y^m) ≤ C_m ‖F‖_(C_y^(m+4))`

with `C_m` independent of `F` and `p`? A bound using a source-dependent fifth-derivative constant would not answer that obligation. The critique interprets the `C_y^r` norm as the maximum over the suprema of all torus-coordinate derivatives of total order at most `r`. This convention is explicit in its notation section; the original estimate uses standard `C_y^r` notation without defining a Lean norm object here.

| Item | Inspected source / interpretation |
|---|---|
| Domain and variables | [TorusInverse](sources/navier/TorusInverse.lean), lines 21–25: universal cover `Plane = ℝ×ℝ`, integer-pair frequencies; [SmoothFamilyTorusInverse](sources/navier/SmoothFamilyTorusInverse.lean), lines 21–29: `f : P×Plane → ℂ`, periodic in the two torus coordinates, with `p` held fixed. The paper's domain is `ℝ²/ℤ²`. |
| Direction | [PDF page 63](sources/navier/page-63.txt), equation (6.2), and [TorusInverse](sources/navier/TorusInverse.lean), lines 190–200, agree on `(sqrt 2 - 1, 1)` for `.temporal`. |
| Inverse and mean | [SmoothFamilyTorusInverse](sources/navier/SmoothFamilyTorusInverse.lean), lines 31–37, defines integral Fourier coefficients and the multiplier inverse. The norm estimate itself has no zero-mean premise. Its separate `inverse_solves` theorem, lines 606–618, requires `ZeroMean f` to establish the equation. No existence/uniqueness claim is inferred from the bound alone. |
| Output derivative | [TorusInverse](sources/navier/TorusInverse.lean), lines 448–457: `derivativeWord` recursively uses actual coordinate `fderiv`; false selects `(1,0)`, true `(0,1)`. It does not differentiate `p`. Identifying arbitrary words with the conventional multi-indices uses smooth mixed-derivative commutation. |
| Input bounds | [Selected declaration](sources/navier/SmoothFamilyTorusInverse.lean), lines 1059–1080, requires the function and both pure coordinate derivatives of order `w.length+5` on the unit square to be bounded by the **same** `C`. `xJet` is iteration of the first derivative, [SmoothFourierData](sources/navier/SmoothFourierData.lean), lines 65–68; swapping the function supplies the other coordinate. |
| Constant | [ParametricTorusInverse](sources/navier/ParametricTorusInverse.lean), lines 643–649, defines `mixedLossConstant r` from `r`, fixed `omega`, and a lattice sum. It is nonnegative and contains no `f` or `p`. It bounds a single word; taking all lengths through `m` additionally requires a finite maximum of these constants. |
| Proof mechanism | [SmoothFourierData](sources/navier/SmoothFourierData.lean), lines 343–387, proves summability of a fourth-power weight majorant and bounds coefficient seminorm order `p` using `p+4` derivatives. The selected theorem instantiates `p=w.length+1`, giving `w.length+5`. This matches the displayed source, not merely red highlighting in the critique. |

Under these identifications, a `C_y^(m+5)` bound supplies the pointwise input hypotheses for every word of length at most `m`; a finite maximum yields the critique's conventional five-loss summary. The necessary norm/word identifications and finite-maximum passage are **source-based mathematical interpretations, not a Lean-checked adapter in this audit**.

A `C_y^(m+4)` bound does not supply the displayed `m+5` hypotheses merely because the source is smooth. Smoothness gives finiteness for each individual function, not a function-independent estimate of the higher norm by the lower. No such control or replacement coefficient estimate is supplied by the inspected proof path. A global search for every possible alternative theorem was outside this one-passage audit.

The paper's proof uses a third-power summable lattice majorant after four extra derivatives. The inspected implementation uses a fourth-power majorant and one additional derivative. The source confirms that difference. It does **not** show that the paper's third-power estimate is invalid; proving it or providing a corresponding formal bridge is a distinct mathematical task.

## Proposed coverage clarification

Original subject: the four-loss assertion in equation (8.19), retained unchanged in the PDF. The following is a proposed **coverage note**, not a replacement of that assertion:

> The cited Lean declaration bounds each torus derivative word using bounds on the source and its two pure derivatives five orders higher. With the usual norm identifications and a finite maximum over derivative words, this supports a five-loss estimate. A formal connection establishing the four-loss bound in (8.19) is not supplied by this cited declaration. The difference does not refute the four-loss bound or certify the rest of the paper.

Adoption is pending; no source document was edited or contacted. Adding a fifth-derivative premise would narrow the desired guarantee and would not complete the original four-loss obligation.

## Checking boundary and unresolved obligation

This investigation did not compile the downloaded Navier–Stokes files. Their [toolchain](sources/navier/lean-toolchain) is `v4.34.0-rc2`; their [manifest](sources/navier/lake-manifest.json) pins Mathlib `85e3a25e006c35636f0e53b0e9296caca2685bc0`, unlike the elementary fixture. The selected files omit the full import closure, including `DiophantineGraph` and `TransportPrimitive`, and no corresponding compiled population is retained. A fresh replay needs that actual pinned repository and its complete imports. The publicly pinned files permit source inspection now; stubbing their imports or porting only the statement would not renew their proof.

The open obligation is a function-independent four-loss estimate for the actual inverse, together with its exact conventional-norm and derivative identifications. There is **no freshly checked Navier–Stokes counterexample, residual goal, or implication adapter** in this package. Source-only closure of this bounded comparison leaves that mathematical obligation open. Pressure flux, later uses of this estimate, and the full paper were not audited.
