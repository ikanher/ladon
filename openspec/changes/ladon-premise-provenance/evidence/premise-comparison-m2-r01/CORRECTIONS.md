# Navigation and evidence clarification — addendum to the frozen first report

The original FINDINGS.md and FINDINGS.sha256 are preserved. This addendum corrects navigation and clarifies evidence authority; M.3's independent review owns the final case judgments.

- Case A's historical evidence directory is `openspec/changes/ladon-pitfall-baselines/evidence/qualification-runs/premise-provenance-v3-family-20261112b/slot-4c19e2/proof-slice.json`. The first report incorrectly uses an underscore in `premise_provenance-v3-family-20261112b`.
- In `openspec/changes/ladon-semantic-pitfalls-umbrella/evidence/dpsgd-gdp-r01/sources/Mf/Optimization/PoissonClippedSGD/GaussianStep.lean`, `hmean` and `henergy` are derived at lines 58–59. The selected `expected_aligned_step_bound` application starts at 63; its mean argument occurs at 66, and the energy goal is discharged at 68. The first report's 51–54 and 64–65 references did not identify these steps.
- For D, the authoritative argument observations are `observation.applications[0].arguments[35]` and `[36]` in the retained slice. Their scoped locals are in `observation.applications[0].localContext`, not just the outer theorem context. Traversing the root-reachable expression DAGs reaches `Lean.Name.mkNum \`_uniq 36487` and `Lean.Name.mkNum \`_uniq 36511`, respectively. The matching locals contain the mean and energy theorem applications as let values. Argument 36 retains its wrapper.
- Historical successful source compilation and roundtrip observation are not independent exported-provider replay. The latter remains unresolved for D. `complete` describes the selected observation, not all mathematical obligations or the whole theorem.
- M.2 did not collect phase-level elapsed-time/token measurements. None are reconstructed here. Historical extraction costs remain in their original reports; a current read of a stored observation is not a free end-to-end extraction.

These corrections were checked against the frozen source and retained slice. No Lean compilation, new proof extraction or benchmark run was needed.
