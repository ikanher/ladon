# Child 1: Golden Predicate Regressions

Turn the Quux/MF observations into stable predicates over report JSON:

- Quux project: `Quux.Basic` top fan-in; broad `Quux.Problems` fan-out.
- Quux Propagation: small declaration graph; `PropagationAlgebra` fan-in; no
  proof-family candidates.
- Matrix-factorization project: `Mf.DP.Sensitivity` top fan-in; `Mf.NTK` top
  fan-out.
- BIFR owner: broad import closure; packed-profile declaration families;
  proof-family candidates.
- r37 packet: partial evidence, not complete.

Do not snapshot timing fields or full JSON payloads.
