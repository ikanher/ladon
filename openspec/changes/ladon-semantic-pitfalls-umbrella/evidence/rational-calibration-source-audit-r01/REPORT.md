# Rational Poisson–Gaussian calibration: bounded source audit

## Reader question and outcome

Does the source theorem at [lines 85–105](SOURCE.tex) support both the adaptive-mechanism privacy conclusion when its rational check succeeds and eventual success when the real moment inequality is strict?

**Within the inspected canonical checker and mechanism, yes.** I found no mathematical fault in this passage. Lean has separate checked declarations for the real moment bound, eventual acceptance, optional-record transcript privacy, public initialization, and common randomized postprocessing. The proof obligation passes through the *same* `T`, `m`, rational `q`, `ε`, `δ`, and certified `σ`; the mechanism theorem additionally requires that its actual sampling rate equal `q` and its actual noise multiplier be at least `σ`. The source describes those parameters as fixed for the mechanism. This is a source-to-formal interpretation by the present auditor, not a machine-certified translation of the prose.

The complete source was frozen in [SOURCE.tex](SOURCE.tex) before the formal owners were inspected; [FIRST.md](FIRST.md) records the source-only interpretation. [INPUTS.json](INPUTS.json) and [FORMAL-INPUTS.json](FORMAL-INPUTS.json) bind the current local bytes. The sibling source and several Lean owner files are untracked, so a sibling Git commit alone would not identify this exercise. No prior `.audit.json` or `.result.json` was opened. This is an exposed, author-run audit, not an independent finding or a comparative Ladon result.

## Claim-to-proof map

| Source obligation | Exact formal support | Scope of the check |
| --- | --- | --- |
| Accepted rational test implies `A^T ≤ δ exp((m−1)ε)` | `Rational.check_power_sound` | The checker includes all stated parameter-domain tests, uses nonnegative binomial weights, and bounds `sampledGaussianRenyiMoment m q (1/σ²) ^ T`. Its moment definition is the source finite binomial sum. |
| Strict real inequality implies test success at every sufficiently large precision | `Rational.eventually_check_of_strict` | Lean proves `∀ᶠ n in atTop, check ... n = true`. Its interval uses Taylor order `n+1`; this corresponds to source precision `N ≥ 1`. |
| Accepted test certifies the adaptive optional-record transcript | `PoissonAdaptiveQuery.Data.optionalTranscript_approxDP_of_rationalCheck` | Requires equality of actual and certified sampling rates, actual multiplier at least certified noise, and measurable record queries. The conclusion is `ApproxDP OptionalRecordAdjacent` for the released sum transcript. |
| Independent public seed and common randomized postprocessing | `PoissonAdaptiveQuerySeed.Data.publicSeedTranscript_approxDP_of_rationalCheck` and `publicSeedPostprocess_approxDP_of_rationalCheck` | Requires a probability seed measure, joint query measurability, and a measurable probability kernel for postprocessing. The formal seed is included in the released joint law. |

The formal `optionalTranscriptLaw` maps optional record slots to zero for empty entries, uses the common clipped query, and releases the sum history; its privacy proof splits both directed cases of `OptionalRecordAdjacent`. That is the inspected mechanism map, rather than just a scalar moment proposition. The exact definitions and owners are retained in [formal](formal); this snapshot is selective and does not contain their complete import closure.

## Representation boundary

The prose's exponential lemma permits **any** fixed sufficient dyadic power for each nonnegative input. The executable `Rational.check` instead computes the least sufficient power with `expPower`; its stage `n` uses source Taylor order `N=n+1`. Thus the cited end-to-end privacy and eventual-acceptance theorems directly certify the canonical executable test. A separate formal `RationalExpInterval.interval_encloses` lemma accepts any sufficient power, and `tendsto_interval_width_cast` handles any fixed power, so the generic prose argument has relevant formal components. I did not assemble a separate end-to-end Lean theorem for every arbitrary power selection. This is an explicit coverage limit, not a counterexample to the source theorem.

The real-to-rational comparison is also a *sufficient* privacy certificate. Neither a failed check nor equality at the real threshold establishes nonprivacy, and the source does not claim that it does.

## Verification and limits

- In the sibling's pinned Lake environment, `lake env lean Mf/DP/PoissonMomentRationalCertificate.lean` and `lake env lean Mf/DP/PoissonMomentRationalPrivacy.lean` both exited 0 against the available compiled imports. Their selected `.olean` files were newer than the corresponding source files at the time of inspection; the complete dependency build was not rerun.
- [Check.lean](Check.lean) imported the privacy owner and printed the selected declaration types and axioms. Its [stdout](Check.stdout) shows only `propext`, `Classical.choice`, and `Quot.sound` for `check_power_sound`, `eventually_check_of_strict`, and the public-seed postprocessing theorem.
- The source/owner match is bounded to the selected theorem and the inspected mechanism/interval definitions. The companion note, every possible query interpretation, arbitrary-power end-to-end packaging, and whole-paper correctness remain outside this result.

This real passage gives a useful example of a successful multi-declaration application audit, including a concrete representation limit. It still does not show that Ladon's native interface finds or verifies more than a careful reader using ordinary Lean. The [preceding constructed comparison](../fresh-application-pilot-r01/REPORT.md) also found equal verdicts. The next investment should target source-to-formal object and assumption selection on independently chosen material; repeating a known theorem's replay would not test that bottleneck.
