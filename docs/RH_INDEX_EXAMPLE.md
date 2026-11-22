# Find a Gaussian integral in the RH archive

Suppose a proof needs the expectation of `exp(Zᵀ H Z / 2 + Zᵀ b)` for a standard Gaussian vector. The matrix can have off-diagonal entries. How would an agent find something useful in a million declarations without knowing a theorem name?

## Get a searchable index

From the Ladon checkout, complete the [setup](../README.md#setup). The following Bash commands download the 14 parts linked in Levent Alpöge’s announcement, join them in order, verify the snapshot used here, and build the index. Allow about 8 GiB of free disk for the archive, extracted sources, and index. [Author’s announcement](https://alpo.ge/remark.pdf)

```bash
RH_WORK=$(mktemp -d "$HOME/ladon-rh.XXXXXXXX")
(
  set -e
  cd "$RH_WORK"
  for part in {01..14}; do
    curl --fail --location --retry 3 --output "part$part" "https://alpo.ge/lean.tar.gz.part$part"
  done
  cat part{01..14} > lean.tar.gz
  echo '9631b4f020199e580ba86178cb56c6e9b09f690c2369a80dc4334aa93f49c7fc  lean.tar.gz' | sha256sum --check
  tar -xzf lean.tar.gz
) && RH_SRC="$RH_WORK/lean/src" &&
  uv run --locked ladon proof-search index build --repo-root "$RH_SRC" --max-index-mib 5120 &&
  RH_INDEX="$RH_SRC/.ladon/index/proof-search.sqlite"
```

If you already have the extracted archive, start with `RH_SRC=/absolute/path/to/lean/src` and run the index build and `RH_INDEX` assignment above. Putting the root at `lean/src` preserves Lean’s module names. Ladon 0.4.4 took 10 min 34 s on our machine and produced a 3.83 GiB SQLite file without invoking Lake.

If you have an existing index, set `RH_INDEX` to its absolute path. Both searches below work with the SQLite file alone. They use `--freshness stored` to query the recorded snapshot. Open the returned source paths relative to the matching archive’s `lean/src` to inspect the proofs.

## 1. Search by the mathematics

> Find an integral over real vectors involving the square root of a matrix determinant. Include Fourier transform results. Check whether evaluating at zero frequency gives a real Gaussian integral, and list the matrix hypotheses that survive.

```bash
uv run --locked ladon proof-search search type-text \
  --repo-root . --index "$RH_INDEX" --freshness stored \
  --pattern 'Real.sqrt |S.det|' --limit 10
```

The index returns three hits. Open `CompanionTheory/SpectralGeometry/LocalGlobalProofs/AdelicAnalysis/RealGaussianFourierTransform.lean` at line 122. In `fourier_gaussian_real_place`, set both matrix arguments to the real positive-definite matrix `A`, the complex parameter to `i`, and the frequency to zero. The hypothesis `A A⁻¹ A = A` follows from invertibility. The Fourier phase vanishes and the remaining scalar has modulus one. Taking absolute values gives

$$
\int_{\mathbb R^n} e^{-\pi x^\top A x}\,dx = \frac{1}{\sqrt{\det A}}.
$$

## 2. Find the missing algebra

> The exponent also contains a linear term. Find a real symmetric quadratic-form identity for translation by a vector. Explain how the identity fixes the factor of two in the cross term.

```bash
uv run --locked ladon proof-search search name \
  --repo-root . --index "$RH_INDEX" --freshness stored --text qf_add \
  --scope module --root GroundTheory.HeightsAndTheta.Heights.HeightKernels.PThetaSummandNorm \
  --limit 1
```

This targeted lookup reproduces the selected hit, `KThetaSummandNorm.qf_add`, at line 24 of `GroundTheory/HeightsAndTheta/Heights/HeightKernels/PThetaSummandNorm.lean`. For symmetric $A$ it expands $(z+v)^\top A(z+v)$ with cross term $2z^\top Av$. Writing $A=I-H$ and shifting by $v=A^{-1}b$ completes the square in the Gaussian **density**. For $A$ positive definite the resulting expectation is

$$
\mathbb E\exp\!\left(\tfrac12 Z^\top HZ + Z^\top b\right)
= \frac{\exp\!\left(\tfrac12 b^\top A^{-1}b\right)}{\sqrt{\det A}}.
$$

Ladon located the source declarations. In a separate Lean 4.33.0 replay we compiled the Fourier theorem and its two archive imports, used the consuming project's product Gaussian density, and checked integrability and the expectation formula. That replay covered this application. The search index itself contains declaration text and locations.
