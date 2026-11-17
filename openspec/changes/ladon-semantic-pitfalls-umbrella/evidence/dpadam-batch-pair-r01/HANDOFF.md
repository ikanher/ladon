# DP-Adam batch pair: internal audit

This root session executes the user-selected follow-up; it is informed internal use, not a fresh independent auditor or a comparison arm. Prior reading is retained at `temp/dpadam-batch-scaling-audit-r01`. The primary source and exact selected range are in SCOPE.json/exposition.tex. The source excerpt does not itself state a general batch-comparison theorem: the paired consequence below is an attributed proposed consequence of its diffusion/calibration results, not a quotation.

## Reader question and original proposed goal

Fix the same nonempty dataset of size N, record gradients, clipping C>0, valid fixed beta pair, positive Adam stabilizer, public initial limit, and public objective bounds. Choose integer k>0 and q>0 with kq<=1. Compare two families at q and kq, with public denominators B=qN and B'=kB. At index j set T=k(j+1), T'=j+1, sharing gamma>0 and c>0; set s=sqrt(gamma T), eta=c/sqrt(T), sigma_DP=B s and likewise for the target. Their expected epoch counts Tq and T'q' agree. The epoch count grows along j; 'fixed epochs' here means matched between the two runs at each j.

Goal: determine whether the actual interpolated path laws converge to the SAME limiting law at H=c/sqrt(gamma), lambda=c sqrt(gamma), and whether both finite mechanisms eventually meet the same stated privacy target. Record separately the exact schedule identities eta'=sqrt(k) eta and sigma_DP'=sqrt(k) sigma_DP, the common sufficient utility bound, and any failure to construct the actual formal family data. Do not replace the goal by the scalar identities or assume the desired path-law equality.

## Checking recipe and invocation

From `/home/codex/projects/ladon`, use `PYTHONPATH=src .venv/bin/python -m ladon.entrypoint ...`; runtime resolution and version are recorded during the run. Pinned compiler and Lake: `/home/codex/.elan/toolchains/leanprover--lean4---v4.33.0/bin/{lean,lake}`. Donor is read-only; use existing compiled imports, no builds/index updates. Scratch proofs and all outputs live in Ladon. Execution bounds: SCOPE.json; count all attempts within the same session, retain all failures.

1. Read source assumptions and freeze the object map. Inspect actual family constructors, then the calibrated path-law and privacy consumers. Account for all extra fields; candidate names alone supply no proof.
2. Navigate with `proof-search search name --repo-root ../lean/matrix-factorization --text NAME --freshness stored --format json --output FILE`. A verified generation exists in the preliminary evidence; revalidate before a new batch. Stored lookup is lexical, not a mathematical check.
3. For an exact public source goal use `proof-search goal capture --repo-root ../lean/matrix-factorization --source OWNER.lean --module OWNER --line LINE --column COLUMN --lean-path PINNED_LEAN --lake-path PINNED_LAKE --format json --output CAPTURE.json`, then `proof-search goal complete --repo-root ../lean/matrix-factorization --capture-file CAPTURE.json --term "by ..." --lean-path PINNED_LEAN --lake-path PINNED_LAKE --format json --output RESULT.json`. The exercised position is `Mf/Optimization/SDE/DPAdamFixedBetaFastSlowHorizonTuning.lean:82:2`, module `Mf.Optimization.SDE.DPAdamFixedBetaFastSlowHorizonTuning`. Its full original-context goal is captured in `privacy-slope-capture.json.gz` (lossless gzip; expand to `privacy-slope-capture.json` before rerunning); the proposed proof is `privacy-slope.term`. Pass the file contents as the `--term` subprocess argument, not shell interpolation. This subordinate query checks actual privacy-coefficient cancellation; the full paired goal above remains separately assessed.
4. Scratch ordinary Lean compositions use `prepare_direct_lean_execution` and `run_bounded_target_process`; this is separate Lean evidence, not native completion. Record full closed target, axiom output, existing import identities, exit/status, elapsed time and peak sampled RSS.
5. Record claim interpretations and changes, exact checked propositions, residuals, unexamined coverage and reader consequences. An unresolved constructor or law-uniqueness obligation is an explicit gap, not a refutation. Match the empirical-objective and privacy conclusions separately.

Success: a complete bounded support/refutation/unresolved assessment with exact evidence and a consolidation/fix/pause decision. No requirement to find a bug, no automatic full-paper rerun, and no claim of improved detection.

## Retained result and reproduction

The informed exercise is recorded in REPORT.md and PREMISE-LEDGER.md. Native raw JSON is losslessly gzip-compressed; hashes of decompressed bytes are in NATIVE-SUMMARY.json. Decompress with Python `gzip.decompress` into fresh local files, then use those paths. The historical command receipt retains the original uncompressed paths. The raw files also remain locally under `temp/dpadam-batch-pair-r01/`. No transitive compiled dependency closure is packaged.

From the Ladon root, check either retained ordinary proof using `PYTHONPATH=src .venv/bin/python openspec/changes/ladon-semantic-pitfalls-umbrella/evidence/dpadam-batch-pair-r01/lean/check.py NEW_RECEIPT_NAME SampledFamily.lean` (or `BatchPair.lean`). Choose a new receipt name to preserve final observations. The runner uses the read-only donor and existing pinned imports with the declared bounds.
