# Frozen interpretation

Reader question: Does the formal development support f-DP amplification for an arbitrary mechanism composed with hidden uniform fixed-size subsampling?

Source: paper/theory/mu-dp/subsample.tex, ranges 35–75 and 161–201; exact bytes/hash in INPUTS.json and SOURCE.tex.

Objects: n-slot dataset in X^n, 1 ≤ m ≤ n, uniform choice of exactly m individual slots, arbitrary randomized mechanism M on X^m, output only M(selected data). Repeated record values do not identify individual slots. Sampling identities are hidden.

Assumptions: M is f-DP for neighboring m-slot datasets; p=m/n. Quantification is over mechanisms and neighboring n-slot inputs, not just Gaussian mechanisms.

Conclusion: both neighboring directions have trade-off at least C_p(f), defined as the convex lower envelope of min(f_p,f_p inverse), f_p=p f+(1-p) Id.

Ambiguities: the selected excerpt does not itself define adjacency. Inspect surrounding definitions before selecting replacement versus add/remove. Symmetry of f and the smooth-proof extension require care. Bernoulli sampling extension and sharpness are excluded.

Prior exposure: informed root; prior reserve map and workflow known. This freeze precedes new candidate checks, and is not a blind interpretation.

## Revision after surrounding-source inspection

`fDP/fDP.tex:32` explicitly defines same-size replace-one adjacency, and `paper.tex:146` includes that file. This settles the earlier adjacency uncertainty for this manuscript. Sampling must preserve slot multiplicity and a fixed ordering into X^m; no permutation invariance is assumed. `fDP/tradeoff.tex` motivates symmetric trade-off functions; a full application must retain its validity/symmetrization obligations.
