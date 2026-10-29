# Coordinate norm bridge feasibility

Parent: ladon-proof-contract-analysis-umbrella Task 2.1 (remains open).
Target: kernel-check generic finite-coordinate multilinear norm comparison and
specialize to Plane R x R, preserving derivative order. For n slots, d unit
coordinate vectors, coordinate functionals bounded by the norm, and exact
coordinate expansion, component bounds C>=0 imply operator norm <= d^n*C.
Reverse implication has factor 1. Prefix bounds use 2^n on Plane.
Acceptance: actual Lean proof, zero-order covered, constants independent of the
function, a checked negative control rejecting factor-one reverse comparison,
and independent review. Transport the existing five-order inverse if feasible.
No four-order estimate, new axiom, sorry, modified primary source, native runtime
support, blind-discovery credit, or identification of unspecified prose norms.
Change surface: root-owned isolated Lean/evidence and OpenSpec progress only.
No runtime edits, dependencies or builds. Rollback: additive evidence only.
Resource contract: new norm-bridge objective; one 600-second absolute execution
clock beginning at first Lean launch, all retries share deadline; 12 GiB RSS,
8 MiB output per process. Stop expansion upon cap/deadline; preserve failures.
Baseline: previous source-pair frozen evidence and current runtime/source hashes
will be reverified. No primary files may change. No push.
