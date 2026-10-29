# Source-only audit: Lemma 8.6, equation (8.19)

**Scope and freeze.** This is an independent reading of the supplied original-paper inputs only, before reading any peer post or formal mapping. The claim is about the selected equation (8.19), not blind discovery. No formal source, runtime, prior report, or outside material was consulted.

## Source identities

SHA-256 identities of the exact supplied files:

- `navier-stokes.pdf`: `0e779481c4da40bd28d1e642e1d8ca57447d129610df28dfa5a11e9af8ae228f`
- `full-paper.txt`: `168ebbc105b9685ee7310341a7cc227eab9dd59ec255c9ac77ce98c47d2839b6`
- `page-63.txt`: `ac601f02c4a52ed4a41c20eeb878cfd29d5b541bf6bad457d09200c83cb75308`
- `pages-95-96.txt`: `06c6f53efae976434009ba37786d7e79ef583f0058aba5c990576be656a9fa00`

## Precise source reading

On the unit auxiliary torus \(\mathbb T^2=\mathbb R^2/\mathbb Z^2\), let \(v_t=(b_g,1)\) be the fixed vector from (6.2), and let \(N=v_t\cdot\partial_y\). For each smooth scalar periodic \(F(y)\) whose normalized Haar integral is zero, there is a unique smooth periodic \(\phi(y)\) with zero Haar integral satisfying \(N\phi=F\). Its nonzero Fourier coefficients are \(\widehat\phi(k)=\widehat F(k)/(2\pi i v_t\cdot k)\), and the zero coefficient is set to zero. The small-divisor estimate (6.7) ensures no denominator vanishes and bounds its reciprocal by a constant times \(1+|k|\).

The bound is asserted for **each** integer \(m\ge0\): \(\|N^{-1}F\|_{C_y^m}\le C_m\|F\|_{C_y^{m+4}}\). The natural conventional interpretation is a torus \(C^m\) norm controlling all partial derivatives in \(y\) of total order at most \(m\), with \(m=0\) the supremum norm. The four-derivative loss is enough in dimension two: after the one divisor loss and Fourier coefficient estimates, the remaining lattice series has decay \((1+|k|)^{-3}\), as the proof states. Constants may depend on the fixed vector and derivative index, but the lemma states no uniformity over a varying direction.

By (3.7) and (3.9), Haar measure is normalized to total mass one and the zero-mean projection is taken in the independent auxiliary coordinate at fixed physical/slow coordinates. Thus in the subsequent application, “zero auxiliary mean at each slow and radial point” is pointwise in those parameters; one inverts only in (y), holding them fixed. The adjacent prose explicitly distinguishes the slow time derivative from this fast auxiliary derivative (page 95 / (6.6), (8.20)).

This lemma establishes only the scalar torus inversion and its regularity estimate. It does not itself assert existence or uniqueness for the Navier–Stokes correction, divergence-free realization, overlap compatibility, or the later velocity/chart properties; those are separately stated after (8.19), notably (8.20)–(8.22).

## Source references

- Original-paper page 63, equations (6.2), (6.4), (6.7): fixed direction and Diophantine divisor bound.
- Full-paper text lines 863–877, equations (3.7)–(3.9): normalized Haar average and pointwise auxiliary zero-mean part.
- Original-paper pages 95–96, Lemma 8.6, equation (8.19), and proof; full-paper text lines 4977–5005.
- Full-paper text lines 4970–4975 and page 63 equation (6.6): fast versus slow time derivative.

## Ambiguities / materially different readings to preserve

1. **Norm convention is not explicitly defined for (C_y^m) in the located source.** Section 4.5 defines (C^k) on the interval ([-1,1]), not this torus norm. A standard all-partial-derivatives torus norm is the evident reading, and equivalent max/sum conventions only alter constants. Reading (C_y^m) as controlling only derivatives along (v_t) would be materially weaker and is not supported by the notation or the proof's two-dimensional lattice summation; it should not be silently substituted.
2. **The quantified estimate concerns a fixed (v_t).** The paper does not state a constant uniform over a family of directions or torus metrics. Such uniformity would need a uniform version of (6.7), not just the displayed lemma.
3. **The zero mean is an essential solvability condition.** Without it, the zero Fourier mode cannot be inverted; the formula intentionally omits (k=0). “Unique” is only after imposing zero mean on the solution; otherwise constants can be added.
4. **The lemma's inputs are scalar functions.** Pair-valued use later is componentwise. Any stronger vector/tensor norm claim is a conventionally componentwise extension, not an additional lemma hypothesis.
5. **No finite-regularity version is stated.** The theorem assumes smoothness and gives every fixed (m) bound with four extra derivatives; it does not promise a single uniform constant over all (m), or an analytic/Gevrey estimate.

