# Unscored development cases

These cases qualify a checking recipe. All obligations and witnesses are supplied.
They are excluded from evaluation mutation selection and scoring.

Original source: the retained `synthetic-challenge-r01/original.tex`, lines
57–73, with the standing assumptions at lines 24–49. The formal owner is
`Mf.Optimization.StochasticApproximation.almost_supermartingale_finite`, present
before the replayed terminal theorem in the local capsule.

**D0: faithful finite account.** At N=1, take a deterministic process with
X0=1, X1=2, A0=1, B0=C0=0. The normalized bound gives X1/(1+A0) ≤ X0,
which is equality. Development.lean checks the rational abstraction.

**D1: constructed normalization omission.** Change only the displayed finite
account to E[X_N] + sum E[B_n] ≤ E[X_0] + sum E[C_n]. Keep its original
finite-age assumptions. The same assignment gives 2 ≤ 1, which is false.
It is a synthetic operation/property discrepancy, not a flaw in the original note.

Source realization: use a singleton probability space and its trivial filtration.
Let X0=1 and Xn=2 for n≥1, A0=1 and An=0 for n≥1, and Bn=Cn=0 always.
Every process is adapted and finite-time integrable. X,A,B are nonnegative.
The conditional row holds with equality at every age. A has finite support and
C=0, so even the original infinite summability conditions hold. At N=1 the
normalized account is true and the altered account is false. The formal scalar
certificate does not itself prove this stochastic realization; independent
mathematical review must check the embedding.

**D2: inadmissible assignment control.** X0=-1, X1=-2, A0=1 violates X0≥0.
It must be rejected as a source counterexample even if some algebraic comparison
fails. Development.lean checks that its encoded premise is false.

No ambiguity case is claimed here. These are development checks, not a balanced
evaluation population or evidence of discovery benefit.
