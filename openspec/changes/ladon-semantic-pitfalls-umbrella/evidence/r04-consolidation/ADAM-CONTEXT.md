# Adam common-law attribution: contextual clarification

This is an append-only clarification of the exposed native MF example. Frozen
interpretation, proof, receipt and source bytes are unchanged. Exact selected
passages and whole-file SHA-256 identities are in [ADAM-CONTEXT.json](ADAM-CONTEXT.json).
Selections and the explanation here are attributed review, not Lean-certified
translation or a new source-only audit.

The old anchor at `adam-source.tex:425–465` covers calibration and most of the
explicit schedule, ending mid-sentence. That passage alone does not state the
two-family common-law consequence. Read it through line 467 and connect it to:

- Fixed momentum, stabilizer and Adam recursion (50–73).
- Positive diverging clock and common public initialization (99–108).
- Fixed record queries, reference-data Lipschitz bounds and measurable kernels
  (174–185).
- Weak convergence of interpolated path laws and uniqueness of the additive
  limiting equation (194–205).

In the preserved `AdamCase.lean`, `Primitives` supplies the reference dataset,
positive dimension/clipping/stabilizer/sampling, separated momentum parameters,
fixed queries, their Lipschitz bounds and clipped-query measurability. `Inputs`
adds positive schedule coefficients, two positive diverging step sequences, a
common converging initial sequence, and an admissible replacement sampling
probability. These are substantial hypotheses even though `selected` takes
only one non-Prop argument and yields zero direct premise-supply obligations.

`resample` changes sampling probability and its validity proofs; the other
primitive data remain fixed. `sourceMap_resample` uses uniqueness, and
`sourceLaw_resample` identifies the resulting law. `paired_source_convergence`
combines the original convergence theorem for the two families. `bridge`
projects the required hypotheses out of `Inputs` and applies that theorem.
Thus the quantifiers mean **for each admitted input, there exists a law shared
by its two families**. The law need not be the same for different inputs.

The source connection is an attributed derived consequence of these combined
passages: the explicit schedule sets the same limiting clock/noise coefficients,
and the same fixed queries, initialization and momentum determine the limiting
equation. The narrow quote alone did not establish that connection. A user of
the result must supply the input hypotheses and check that their processes are
the formal constructed families. The stronger gradient-specific source reading
and measurable-kernel-to-clipped-query bridge also require their separate
interpretation/constructor evidence; this note does not declare every field
literally present in the quote or logically necessary.

This does not assert equality of finite-run distributions or finite privacy
accountants, uniform convergence rates in sampling probability, applicability
to changing momentum, or completion of the whole source-method audit. It adds
readable context to existing support, not new mathematical coverage.
