## 1. Operator Refinement

- [x] 1.1 Add the narrow convexification or biconjugate helper surface needed to
      define the full `C_p` transform in Lean.
- [x] 1.2 Rebind the public `TradeoffFunction.pSamplingOperator` surface to the
      full convexified operator while keeping the current outer API stable.

## 2. Structural Theorems

- [x] 2.1 Prove the public source-order and endpoint lemmas for the full `C_p`
      operator on the tradeoff surface.
- [x] 2.2 Re-export the refined operator and its structural lemmas on the
      privacy-object and GDP-facing subsampling surfaces.
- [x] 2.3 Add compatibility lemmas showing the refined operator stays below the
      raw symmetrized and weighted envelopes used by existing consumers.

## 3. Documentation And Verification

- [x] 3.1 Add or update a docs note explaining how the Lean encoding matches
      `paper/theory/mu-dp/subsample.tex` and its appendix properties.
- [x] 3.2 Compile the refined subsampling modules and verify existing downstream
      consumers still build against the stable public API.
