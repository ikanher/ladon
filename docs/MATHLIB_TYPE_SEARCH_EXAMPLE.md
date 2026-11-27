# Search Mathlib by theorem type

## Build the Mathlib index

From the Ladon checkout, follow the [Ladon setup](../README.md#setup) and run
these commands in Bash. They pin Mathlib to `v4.33.0` and put the source and
index in a scratch directory. This step only needs the Mathlib source.

```bash
MATHLIB_DEMO=$(mktemp -d)
MATHLIB="$MATHLIB_DEMO/mathlib"
MATHLIB_INDEX="$MATHLIB_DEMO/mathlib.sqlite"

git clone --depth 1 --branch v4.33.0 \
  https://github.com/leanprover-community/mathlib4.git "$MATHLIB" &&
  uv run --locked ladon proof-search index build \
    --repo-root "$MATHLIB" --index "$MATHLIB_INDEX"
```

Keep these variables in the same shell for the three
[README searches](../README.md#search-mathlib-by-theorem-type). The index
covers this Mathlib checkout. A hit is evidence that the indexed signature
contains the requested fragments, which can occur in its hypotheses or its
conclusion.

## Check the Fubini candidates

With [Elan](https://github.com/leanprover/elan) installed, download the cached
compiled files for the Fubini module and its imports. Mathlib's
`lean-toolchain` selects Lean 4.33.0.

```bash
(cd "$MATHLIB" && lake exe cache get Mathlib.MeasureTheory.Integral.Prod)
```

From the Ladon checkout, check both candidates against an equality for a
real-valued integrable function and two σ-finite measures on ℝ. The goal uses
fully qualified Lean names so it can be elaborated in the selected module.

```bash
LEAN_BIN=$(cd "$MATHLIB" && elan which lean)
LAKE_BIN=$(cd "$MATHLIB" && elan which lake)
GOAL='∀ (μ ν : MeasureTheory.Measure ℝ) [MeasureTheory.SFinite μ] [MeasureTheory.SFinite ν]'\
' (f : ℝ × ℝ → ℝ), MeasureTheory.Integrable f (μ.prod ν) →'\
' MeasureTheory.integral (μ.prod ν) f ='\
' MeasureTheory.integral μ (fun x => MeasureTheory.integral ν (fun y => f (x, y)))'

uv run --locked ladon proof-search discover --repo-root "$MATHLIB" \
  --module Mathlib.MeasureTheory.Integral.Prod --goal "$GOAL" \
  --candidate MeasureTheory.integral_prod \
  --candidate MeasureTheory.integral_integral \
  --toolchain-mode explicit --lean-path "$LEAN_BIN" --lake-path "$LAKE_BIN" \
  --evidence-store "$MATHLIB_DEMO/check-evidence.sqlite"
```

`MeasureTheory.integral_prod` is accepted with no remaining goals.
`MeasureTheory.integral_integral` is rejected for direct application. It
starts from the iterated integral and concludes with the product integral.
The rejection applies to this direct application. The reversed equality is
still available through symmetry.
[Mathlib source](https://github.com/leanprover-community/mathlib4/blob/v4.33.0/Mathlib/MeasureTheory/Integral/Prod.lean#L444)
