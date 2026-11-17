# DP-Adam square-root batch scaling: bounded source/owner assessment

## Conclusion

The local sources support distinguishing three claims. Scalar invariants have an explicit Lean owner and a narrow faithful exposition. The newer fixed-beta, privacy-calibrated diffusion exposition has a substantive tuned learning-rate limit, with matching formal-owner statements. A complete formal comparison of two batch-scaled actual optimizer families was not established in this inspection. No mathematical fault was established.

This is informed root review using the current Ladon checkout, not independent review, a scored pilot, or an exhaustive paper audit. The user's exact MF report passage remains unidentified. Searching Malladi identifies the newer diffusion exposition as the primary relevant natural-language manuscript; the scalar scaling note contains the earlier algebraic extension. The local Malladi scaling section was read directly, without web search.

## Sources and claims

1. `latex/natural-language/dp_adam_batch_size_scaling_rule_natural_language.tex` explicitly proves scalar identities and excludes SDE approximation, exact privacy accounting and hyperparameter transfer. `Mf/Optimization/AdamScalingInvariants.lean` matches that boundary. Its noise-update product is before the adaptive denominator, which is explicitly external to the identity.
2. `paper/sgd/adaptive-gradient-sde-scaling-rules/sqrt_scaling.tex` states the non-DP rule with simultaneous learning-rate, beta and numerical-epsilon changes, under weak-approximation assumptions and an Adam warm-start condition. A learning-rate factor alone is not the whole rule.
3. `latex/natural-language/dpadam_privacy_calibrated_diffusion.tex`, lines 128–145, explicitly distinguishes fixed-beta high-noise averaging from Malladi's beta-to-one regime. Lines 572–705 give calibration, the explicit run-length schedule and bound-minimizing coefficient. The clock assumptions are in lines 245–274.
4. `DPAdamFixedBetaFastSlowTunedFiniteRate.tuned_family_learningRate_limit` (line 221) states eta_n sqrt(mesh_n+1) -> sqrt(2 G/(L d scalarVariance(beta))). It consumes GrowingClockData, a calibrated step/noise limit and a tuned-horizon equality. Reading its statement is not replay of the family constructor or the stochastic theorem.
5. `DPAdamFixedBetaFastSlowHorizonTuning.privacySlope_eq_card_formula` cancels q from the leading privacy slope under B=q|D|. `BatchTransferExponent.clockLawLearningRate_ideal_fixed_epoch_eq_of_pos` proves the deterministic fixed-epoch clock bridge.

## Mathematical inference from these sources

For fixed dataset size N and the same epoch budget E, T_B=EN/B gives eta_B=c/sqrt(T_B)=c sqrt(B/(EN)). Thus eta_(kappa B)/eta_B=sqrt(kappa) if c is shared. The explicit schedule has s_B=sqrt(gamma T_B) and sigma_DP,B=B s_B; with the same gamma it yields sigma_DP,kappaB=sqrt(kappa) sigma_DP,B. This is exact schedule algebra for admissible counts. For general asymptotic families the corresponding claim concerns limits, not exact equality at finite run lengths.

The new tuned coefficient is c=sqrt(2 G/(L d sigma_beta^2)). Its batch independence requires the same public G,L,d and momentum-dependent variance. In the fixed-beta manuscript, beta stays fixed. Importing Malladi's beta'=1-kappa(1-beta) changes that premise and requires a new comparison of memory coefficients. The limiting drift also contains alpha_beta/C. A clock identity alone cannot establish equality of trajectory laws.

For a meaningful comparison, hold dataset/objective, clipping, momentum and initial law fixed; maintain B=qN and valid sampling rates; declare the same accountant convention, privacy target, slack and order; and handle integer counts. Changing C or the sampler may change the clipped drift or covariance. Exact finite privacy equality does not follow from equality of Tq^2/sigma^2. The newer result promises eventual privacy with slack and asymptotic utility, with no quantified full path approximation error in the inspected exposition. The learning-rate coefficient minimizes a sufficient bound, not actual training loss.

## Actual Ladon evidence

- `search-proxy-verified.json`: exact scalar-owner lookup; index generation verified fresh, no source/configuration difference reported. This is lexical navigation evidence.
- `search-tuned.json`: exact tuned-owner lookup from the same stored generation; this individual lookup does not recheck freshness.
- `check-clock.json`: one live direct-Lean application, pinned Lean 4.33.0, accepted with no residual premises. The fully quantified goal states the deterministic clock identity with positive examples and source/target batch sizes. Authority is elaborator-check with exact environment and explicit pinned execution; source freshness is reported unknown. This is not source-goal completion with independent replay/trust and does not certify the stochastic proof.
- `lineage-tuned-stored.json`: unavailable, reason `not_ingested`; no refresh or fallback occurred. This is absence of stored evidence, not absence of a theorem or a mathematical failure.
- Initial broad name search and an empty scoped search are retained; exact-name follow-up found the intended owner. Their misses were not treated as theorem absence.

The local source checkout was invoked as `PYTHONPATH=src .venv/bin/python -m ladon.entrypoint`. No donor sources, index, dependencies or shared compiled artifacts were changed; no build or new lineage extraction ran. The checker used default finite bounds and existing compiled imports. Source identities are retained in SOURCE-IDENTITIES.json; this directory does not package the compiled dependency closure.

## Next consequential audit obligation

Select two actual fixed-beta DP-Adam families at q and kappa q, with the same original objective/clipping/memory/public bounds and an explicit count relation. Connect their primitive assumptions to the formal family data, derive their common calibrated limit or precisely stated utility comparison, and check conclusion transfer back to the source passage. Preserve finite versus asymptotic conclusions and report unconstructed family assumptions. This would test premise supply and source-to-formal object mapping with the newer machinery, rather than repeating scalar cancellation.

The existing exposition audit at `latex/lean/dpadam_privacy_calibrated_diffusion_proof_audit.md:135` records related primitive-family packaging boundaries. These are prior author/reviewer observations, not independently reproduced absence claims. A new audit should inspect current producers before treating those historical boundaries as unresolved today.
