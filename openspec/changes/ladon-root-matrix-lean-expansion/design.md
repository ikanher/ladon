# Design

Root-matrix entries should use Lean extraction when the root is a concrete owner
whose declaration-level graph gives useful calibration evidence. Project
facades remain text-backed because their primary role is module-DAG inventory.

The selected roots were smoke-tested before this packet:

- `Quux/Problems/BIFRRMSESaturationMini.lean`
- `Mf/DP/GaussianCore.lean`
- `Mf/DP/BSRFactorCore.lean`
- `Mf/Optimization/FTRLAnalysis.lean`

All produced valid reports. GaussianCore required mathlib/local-variable
reference-noise calibration before becoming suitable as a default matrix entry.
