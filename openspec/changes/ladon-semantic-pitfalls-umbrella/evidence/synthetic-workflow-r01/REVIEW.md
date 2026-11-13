# Independent source-only review

**Reviewer:** independent development-math and recipe review  
**Scope:** `DEVELOPMENT.md`, `Development.lean`, `RECIPE.md`, the supplied `original.tex`, and the five named original-capsule stochastic-approximation Lean files. No builds or evaluation cases were used.

## Verdict

The D0/D1/D2 development cases are mathematically sound as stated. D1 is a genuine counterexample to the altered finite account under the original finite-age assumptions, and its singleton realization satisfies the stochastic hypotheses (including the conditional row at every age). The scalar Lean certificates establish only their rational propositions; `DEVELOPMENT.md` appropriately calls out that the stochastic embedding requires separate justification. The generic recipe covers the key distinctions in the requested scope and is suitable as a bounded source-audit procedure. It does not itself establish that a particular natural-language interpretation is the uniquely correct one, nor that the procedure will discover a discrepancy.

## Mathematical checks

In the source corollary, `P_0=1` and `P_1=1+A_0`. With `X_0=1, X_1=2, A_0=1, B_0=C_0=0`, the source row at age zero is equality, `2=(1+1)1`, and the normalized terminal term is `E[X_1/P_1]=1=E[X_0]`. Thus D0 is faithful, including the finite account's `N=1` index convention.

For D1, take the one-point probability space with its trivial filtration and the sequences stated in `DEVELOPMENT.md`. They are adapted; all finite-age variables are integrable; `X,A,B` are nonnegative; and the conditional row is equality at age zero and at every later age. `A` has only one nonzero term, and `C` is identically zero, so the infinite summability assumptions also hold. At `N=1`, the altered account evaluates to `2+0 ≤ 1+0`, which is false. This proves an actual stochastic realization, rather than only a rational assignment. The formal `OriginalOneStep` models the age-zero row and the signs, while its `NormalizedAccount` and `MutatedAccount` are rational abstractions; it does not encode the process or conditional expectation. The written source realization supplies that missing bridge.

D2 is correctly inadmissible: `X_0=-1` violates the source's nonnegativity condition on `X_n`. The failed `OriginalOneStep` premise is the appropriate control; a conclusion comparison outside the assumptions cannot refute the source claim.

## Source attribution and recipe

The cited source passage is `original.tex`, lines 57–73: the finite normalized corollary and its explanation of the terminal quantity. Its displayed normalization is also reflected in `Mf.Optimization.StochasticApproximation.almost_supermartingale_finite` in `MultiplicativeDescent.lean`. That declaration's context includes adaptedness of `A`, finite-age integrability of `X,B,C`, almost-sure nonnegativity of `A`, and the conditional row. The finite theorem itself concludes the normalized finite expectation inequality and does not require the infinite summability hypotheses. Accordingly, D1 is properly described as a constructed alteration of the displayed finite account, not as a defect in the original note or formal theorem. The additional source realization satisfies even the stronger infinite assumptions.

The recipe explicitly separates a scalar abstraction from its realization in the source's probability setting (step 6); a fully closed refutation from an assignment satisfying the original premises (step 6); and source interpretation from Lean candidate checking (steps 2, 3, and 7). Step 5 also distinguishes declaration dependencies, inspected binder/use evidence, local-term observations, and independently checked provider terms, and says to follow actual proof/source uses when premise supply matters. That is adequate guidance to avoid treating a declaration graph alone as evidence that a premise is supplied. The recipe's wording could be read quickly as treating all retained dependency evidence as equally explanatory, but its explicit distinctions and source-use instruction correct that reading.

The workflow is general enough for unseen bounded claims: it starts from claims and interpretations rather than fixed diagnoses, preserves quantifiers/domains/normalization, permits checking context inhabitation or premise supply as well as entailment, keeps repairs separate, and recognizes abstention and unresolved outcomes. Its scope and authority limits are stated. It is a workflow specification, not evidence that the tool interface or any specific audit achieved those steps; the report must still give exact settings, residuals, failures, and unexamined claims.

## Limits

This review checks the supplied mathematics and source crosswalk only. It does not execute Lean, validate the supplied certificates against a compiled environment, inspect Ladon telemetry, establish source provenance beyond the supplied files, or evaluate the recipe on held-out cases. No claim about discovery benefit or balanced evaluation follows from these development examples.
