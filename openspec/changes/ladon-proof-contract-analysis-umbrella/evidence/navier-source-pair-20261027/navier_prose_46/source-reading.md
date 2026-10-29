# Lemma 8.6 / equation (8.19): source-only reading

**Frozen before consulting peer posts or any formal mapping.** This is a reading of the paper's assertion, not a claim of blind discovery or a formal verification.

## Source identity and scope

The supplied source files have these SHA-256 hashes:

- `page-63.txt`: `ac601f02c4a52ed4a41c20eeb878cfd29d5b541bf6bad457d09200c83cb75308`
- `pages-95-96.txt`: `06c6f53efae976434009ba37786d7e79ef583f0058aba5c990576be656a9fa00`
- `full-paper.txt`: `168ebbc105b9685ee7310341a7cc227eab9dd59ec255c9ac77ce98c47d2839b6`
- `navier-stokes.pdf`: `0e779481c4da40bd28d1e642e1d8ca57447d129610df28dfa5a11e9af8ae228f`

Primary passage: paper p.95, §8.5, Lemma 8.6 and (8.19), continuing p.96 proof; supplied extraction `pages-95-96.txt`. Relevant setup: p.63, equations (6.2)–(6.6), supplied `page-63.txt`. Additional paper context: §8.5 proof following (8.19), equation (8.23), full-paper text lines 4977–5015. The paper's analogous torus norm estimate for a different directional operator is (8.10), full-paper lines 4773–4778.

## Proposed precise mathematical statement

Let \(\mathbb T^2=\mathbb R^2/\mathbb Z^2\) carry normalized Haar measure, and let \(v_t=(b_g,1)\) be the fixed vector from (6.2), where \(b_g=\sqrt2-1\). For a smooth scalar-valued function \(F\) on this torus with zero Haar average, define
\[
N=v_t\cdot\partial_y=b_g\partial_{y_1}+\partial_{y_2}.
\]
There is exactly one smooth scalar \(\phi\) with zero Haar average such that \(N\phi=F\). Its zero mode is set to zero and, for every nonzero \(k\in\mathbb Z^2\), its Fourier coefficient is \(\widehat F(k)/(2\pi i v_t\cdot k)\). Equivalently,
\[
\phi(y)=\sum_{k\ne0}\frac{\widehat F(k)}{2\pi i v_t\cdot k}e^{2\pi i k\cdot y}.
\]
For each integer \(m\ge0\), \(\|\phi\|_{C_y^m}\le C_m\|F\|_{C_y^{m+4}}\).

The natural conventional reading of \(C_y^m\) is the supremum norm over the torus of all y-partial derivatives up to order m (equivalent choices of finite-dimensional norm alter constants). The text does not define this norm on the cited page, so this is a conventional interpretation, not an explicit norm normalization. The constants may depend on m and the fixed vector/Diophantine bound; no uniformity in m is asserted.

## What the prose makes explicit

- Domain is the standard two-torus \(\mathbb T^2\); y denotes its coordinate.
- N is the constant-coefficient directional derivative along the fixed temporal eigenvector \(v_t\) from (6.2); it is not an arbitrary vector field.
- F is smooth and has zero Haar mean. The solution is required to be smooth and zero mean too.
- The claim includes every integer m including m=0; the loss is exactly four derivatives in the displayed estimate.
- The Fourier formula excludes k=0, with the zero-average condition fixing the additive constant.
- Invertibility relies on the paper's divisor estimate (6.7); the proof says four extra derivatives leave a summable \((1+|k|)^{-3}\) series in dimension two.
- In the application, the operator acts in the auxiliary torus at fixed slow/radial point. The proof says the multiplier commutes with slow coefficient derivatives, preserves reality, and preserves slow/radial support and smooth zero extensions; it need not preserve auxiliary-torus support (p.96, proof after (8.22)).
- The application to residuals is specifically the zero-auxiliary-mean component \(E_\theta^\circ,E_z^\circ\), after subtracting the auxiliary average at every slow point. The lemma alone does not assert the residuals have this property; that is imposed by the decomposition.

## Dependencies and non-claims

As a bare lemma, the bound's constant is indexed by m and implicitly depends on fixed \(v_t\) and its Diophantine constant. It does not quantify over changing directions or families of vectors. In the paper application, the slow variables are parameters and the inverse acts pointwise in them; the proof supplies commutation with slow coefficient derivatives. Equation (8.23) explains the corresponding chart scaling under finite coverings.

The statement does not assert an inverse on nonzero-mean functions, a solution for nonzero-mean F, compact support in y, preservation of y-support, or a bound uniform in m or in a varying direction. It does not by itself assert a Navier–Stokes solution, existence/uniqueness for the full correction problem, or chart/velocity claims. Those occur in the subsequent application: (8.20) gives chart representatives, (8.21) realizes a divergence-free velocity increment, and (8.22) describes cancellation with a flat reconstruction remainder. These are logically additional assertions, not part of (8.19).

## Materially different readings to keep distinct

1. **Norm convention:** \(C_y^m\) could mean the maximum of derivatives of exactly order m, rather than the standard norm including all orders \(\le m\). On a compact torus these conventions can be related when lower norms are included/controlled, but they are not literally the same definition; the excerpt leaves convention unstated.
2. **Parameter-dependent F:** One may read “a smooth function” as just a scalar function on \(\mathbb T^2\), or as a smooth family over slow variables. The literal lemma states only the former. The surrounding application supports the latter as a pointwise parameterized use, with commutation assertions in its proof; it does not change the lemma's stated domain.
3. **Real versus complex scalar:** The Fourier formula uses complex coefficients. The prose does not name the scalar field. Real-valued F yields real-valued phi by conjugate symmetry; allowing complex-valued F is also natural and the same estimate holds. No vector-valued generalization is stated.
4. **Coordinate convention:** The torus is identified with \(\mathbb R^2/\mathbb Z^2\), as indicated by \(k\in\mathbb Z^2\) and exponent \(2\pi i k\cdot y\). A different period convention would change Fourier factors; it is not the displayed convention.

