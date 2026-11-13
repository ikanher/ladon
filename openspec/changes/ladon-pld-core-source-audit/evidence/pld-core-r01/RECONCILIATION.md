# Reconciliation after the independent review

The first findings remain frozen at SHA-256 72f3579266002dea748dc14bc0b41761d2ab431caf4828597c8951c87ca22e3b (work/FINDINGS-FREEZE.json). This file records the adjudication; it does not rewrite that first report.

## Accepted reviewer corrections and refinements

1. **P2 is narrower than the source theorem block.** The checked event/profile equivalence and strictly positive shared-density identity substantiate local forward identities. They do not formalize the exponential-smoothing identity or the converse density recovery Y = δ'' − δ', X = e^t(δ'' − δ'). That converse is density-level and requires differentiability and tail/density regularity. The paper's broader discussion of discrete and mixed variables does not by itself supply those hypotheses for the displayed derivative formula. This is a formalization/scope gap, not a demonstrated false mathematical claim.
2. **P4 does not pass as a whole.** The exact finite product-density equality is formally checked under its stated shared-base, positivity, measurability, and finiteness conditions. It is not a direct formalization of the paper's Gaussian privacy-loss laws or general PRV/curve composition theorem. The first finding's “supported for that formal product-density instance” remains valid, but must not be read as support for the full source claim.
3. **The Gaussian control is partly resolved.** Lean checks the one-way scalar analytic-condition-to-all-measurable-events theorem for centered Gaussian pairs, with explicit premises. This justifies a control result for that implication. It does not establish the note's maximizing half-space characterization, equality/sharpness of the event supremum, or radial identity and envelope. The control is therefore accepted only for the one-way bridge, not the entire note.
4. **Gaussian PRV law mapping is outside the checked bridge.** The source calculation's signs and means are consistent, including the degenerate μ = 0 case as a point mass, but the frozen Lean owners reviewed here do not directly state those paired privacy-loss law equalities.

## Final dispositions

- **P1:** unresolved/not checked for arbitrary probability laws, singular or discrete components, and endpoint conventions.
- **P2:** local forward event/profile support; converse and generalized-law scope remain unsupported by the checked owners. No discrepancy established.
- **P3:** unresolved/not checked for exponential smoothing, differentiability/inversion, and uniqueness.
- **P4:** supported only for the checked finite shared-base product-density realization; the broader PRV/Gaussian-law and privacy-curve correspondence remains unresolved.
- **G1/G2:** one-way scalar-to-event Gaussian implication supported under exact Lean premises; maximizing event, sharpness, radial identity/envelope remain unverified. It is not a full-note pass.

No source fault was established. No missing operation was demonstrated: the remaining limitations are principally theorem coverage and scope mapping, and this bounded audit did not show that Ladon's current operations prevented resolution of the selected local questions.

## Reviewer independence and limitations

The reviewer reports using only the frozen manifest and copied source inputs, not the first findings, evidence narrative, or sibling checkout. No compilation was run by the reviewer. Their review took approximately four minutes. The independent assessment is preserved verbatim in review/REVIEW.md; this reconciliation is the author's response. The original first report and its hash remain intact.
