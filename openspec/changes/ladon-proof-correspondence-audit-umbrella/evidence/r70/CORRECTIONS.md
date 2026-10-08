# Original and proposed explanations

The immutable original is the [paper snapshot](sources/paper/NavierStokes_LostInTranslation_ArXiv.tex). These proposals are root-authored and **unadopted**. They correct or label the example arguments, not the paper's overall claim. No historical judgment is rebound to these new words.

## Polynomial: replace the erroneous argument, preserve the theorem

Original, `ex:example1`: the claimed multiplicities yield `(x-1)(x+1)^2`, and both factors are claimed nonnegative on `x ≥ -1`.

Proposed proof:

> Direct expansion gives `p(x)=(x+1)(x-1)^2`. For `x ≥ -1`, the first factor is nonnegative and the second is a square. Therefore `p(x)≥0`.

This corrects the root multiplicities and factorization, and removes the false sign inference. It changes the proof without adding assumptions or changing the final inequality. [Independent checking](cases/Polynomial.lean) supports the replacement. Final-theorem success does not retrospectively validate the original proof.

## Least element: preserve the unresolved presupposition

Original, `sec:why`: the displayed code uses `sInf {n | B_e n}` and proves the later rational identity, while the intended informal definition presupposes a least admissible index.

Proposed explanation:

> For this concrete polynomial, `(x₁,x₂)=(n,0)` is a root for every natural `n`. Hence no `n` satisfies `B_e(n)`, and there is no least admissible index in the informal definition. Lean's total `sInf` instead returns zero for the empty set, giving a well-defined formal value `r_e=1`; the algebraic identity for that value does not establish the intended existence. For a general nonempty subset `S` of the naturals, one may choose `n=sInf S`, prove membership and minimality, and then apply the rational identity.

The final sentence is an explicitly **conditional** variant. The nonemptiness hypothesis narrows that variant and is unavailable for the original concrete predicate. [Separate checks](cases/LeastElement.lean) support both the failure of concrete existence and the valid guarded choice. This is not a claim that Lean's total definitions are ill-defined.

## Matrix: keep the correct passage, label the alternative

The original diagonalization argument in `ex:example2` is retained unchanged as a faithful control. [Our spectral reconstruction](cases/Matrix.lean) checks its main mathematical steps, including existence of the eigenbasis through the spectral theorem. This is new code, not verification of the screenshot's exact bytes.

If an author prefers the shorter direct proof, label it as a replacement:

> Alternatively, expand `trace(A²)=∑ᵢⱼ aᵢⱼaⱼᵢ`. Symmetry makes each term `aᵢⱼ²`, so their sum is nonnegative.

This is valid and proves the same theorem. It does not assert that the change-of-basis argument was translated. No additional hypothesis is needed. The direct and faithful controls both pass; a method difference receives a correspondence finding, not a false-proof verdict.
