# Internal consumer exercise findings: Ladon 0.4.2 / actual update energy

## Result

**Status: supported at the terminal `2.9` ceiling in an actual captured Lean source context.** Ladon's source-goal completion accepted the full application proving the captured goal `expectedUpdateEnergy ... ≤ 29/10`, with independent compiler replay, complete trust coverage, and only `propext`, `Classical.choice`, and `Quot.sound`. This is evidence for this specific application and target context; it is not a general evaluation of Ladon's accuracy.

The prose claim itself is `J_T ≤ 63 K²/T + 1011(26/T + 1/999) ≤ 2.9`. The captured goal was the final consequence `J_T ≤ 2.9`. The stronger displayed intermediate bound is provided by existing formal ingredients inspected in source: `model_expected_update_energy_le` gives energy ≤ `logEnergyBound`, and `logEnergyBound_envelope` gives that bound ≤ the exact displayed RHS. The checked completion instead uses `model_expected_update_energy_le` followed by `logEnergyBound_safe` to reach `2.9`; I did not run a second high-memory completion for the intermediate RHS. Thus the final ceiling is directly completed evidence, while the displayed first inequality is an inspected compositional route, not a completed source-goal term in this exercise.

## Application evidence

- Captured source goal: `Mf.Optimization.FiniteMemoryAdam.Cumulative.Energy.physical_window_expected_energy_le`, at its actual `by` position in `Mf/Optimization/FiniteMemoryAdam/CumulativeEnergyUsefulUtility.lean:32`. The capture includes the theorem's real local context; no prose assumptions were reconstructed as Lean hypotheses.
- Captured target: `expectedUpdateEnergy F data η (1/100000000) x0 q hq σ ≤ 29/10`, with `T ≥ 16384`, `θ ∈ [0,0.38]`, `ρ ∈ [0,0.005]`, `q ∈ [1/4,1]`, `σ ∈ [0,1.9*physicalNoise]`, and `η ≠ 0`.
- Completed term applies `model_expected_update_energy_le` to the actual finite initialized model, obtains the generated release variance facts, and composes with `logEnergyBound_safe`. Both source-goal application and independent replay were accepted. Trust report: `lean-standard-no-placeholders-v1`, coverage `complete`; no `sorryAx`.
- Formal `expectedUpdateEnergy` is the integral of normalized `pathUpdateEnergy`; `pathUpdateEnergy_eq_mean` rewrites vector squared norm to coordinate squares, matching the prose's time/coordinate expectation defining `J_T`.
- The formal model uses the same β values, clipping, shared record mask, fresh Gaussian release (including empty mask through the history law), both corrected memories, initialized run, and outside-root stabilizer. The source-to-formal scaling uses `dimensionScale d = sqrt(d)`, with `modelDirection_eq_scalar_scaled`; the actual release is scaled by `dimensionScale` in `modelScaledRelease`.
- Assumptions align for this lemma: source global gradient coordinate bound is `SmoothObjective.scaled_gradient`; the centered amplitudes/deviations are `CenteredRecordFamily`; C¹ regularity provides the represented differentiability/continuity. The objective lower bound and descent regularity classes are stronger formal packaging than the energy estimate needs. The source's positive scaled step `γ` maps to `η=γ/sqrt(d)>0`, which satisfies captured `η≠0`; the energy theorem imposes no smaller-step restriction.
- Stabilizer correction: the source has `ζ=10^-8`, so `epsilon=sqrt(d)*ζ` and `epsilon²=10^-11`. My frozen note accidentally wrote `epsilon=10^-11`; root reviewer identified it. See the separately attributed [correction](INTERPRETATION-CORRECTION.md). Formal `fixed_scaled_stabilizer_sq` confirms `(sqrt(100000)*10^-8)^2=10^-11`.
- Formal `physicalNoise` equals the source `σ₀`: both are `1061065371702927 / 31250000000000000000`; the source interval therefore maps exactly to the captured formal interval.

## Limitations and classification

- The captured target is an existing formal energy specialization, not the TeX theorem encoded from scratch. Its class/record inputs are the formal representation of the stated source assumptions. The actual source-context goal avoids adding a new assumed energy bound.
- The stronger displayed intermediate RHS was not directly completed against a captured goal. Its producer/envelope declarations and parameter bounds are present in the imported owners, and the exact composition is straightforward, but the direct Ladon evidence here certifies the final `2.9` ceiling.
- No mathematical fault or missing assumption was found in this bounded exercise. No evidence was collected for the rest of the paper or theorem.
- One initial capture invocation failed before Lean execution with `invalid-source-digest` because my optional shell-computed digest argument was malformed for this CLI contract. I removed that optional argument and the actual capture succeeded. This is an invocation/workflow error, not a mathematical rejection.
- No index update, package synchronization, Lake build, target source edit, commit, or push was performed. Discovery used `rg` and direct Lean owner inspection; no full index status was run.

## Resource and usability feedback

- First substantive query time is retained in `first-substantive-query-time.txt`.
- Capture limits: timeout 180 s, output 8 MiB, process-tree RSS 12,288 MiB. Actual complete capture operation took 30.86 s; helper Lean processes used 8,761,586,156 and 9,002,942,464 bytes peak RSS; neither timed out or hit a limit.
- Completion limits were the same. Full original-goal completion took 54.31 s; peak supervised Lean process-tree RSS was 9,136,914,432 bytes. All four helper runs returned 0 and stayed under limits.
- Both operations loaded the large existing compiled context and consumed about 8–8.5 GiB. The interface reported helpful exact limits and retained complete source context/canonical replay evidence, but the 12 GiB cap had only a few GiB of headroom. We stopped after the useful application; no profiler rerun was needed.
- Ladon version output identifies package content and installed content identities, and explicitly warns that observed source revision is not installed-byte equality. Captured source context, accepted application, replay, and trust report were all available in the output artifacts.

## Identity and integrity

- Ladon checkout: `4218abbfc9fbab4af91edcf0406f73c4e3d9f941`, dirty; Ladon 0.4.2 invoked with `/home/codex/projects/ladon/.venv/bin/python -m ladon.entrypoint`.
- Target HEAD at start and end: `50810c904d0cfe31d4b397e688418040f71f2785`. The target working tree was already heavily modified/untracked at the start; this exercise wrote only to its exclusive output directory under the Ladon repo.
- Selected source SHA-256 at input and end: `775ef38b3ab68a5b1ff662bc8cf53b067866bca16b5cd5d1f648bcd002a38327` (matches `INPUT.json`).
- Exact commands, help/version output, command results and process receipts are retained in [COMMANDS.json](COMMANDS.json), `energy-goal-capture.json`, `energy-goal-completion.json`, and `completion-command.json`.
