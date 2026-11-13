import Mf.DP.Profile.SampledGaussianSequenceComparison

/-!
# Canonical fixed-sampling high-noise privacy limit

For independent Bernoulli-sampled unit shifts plus Gaussian noise, both directed
exact event profiles converge to the Gaussian profile when variance per update
has a positive limit. The concrete comparison uses the fourth-order chi-square
estimate and product laws; no privacy certificate or approximation hypothesis
is supplied by the caller. This formalizes the fixed-q high-noise consequence
of Räisä, Jälkö and Honkela, *Subsampling is not Magic* (ICML 2024), Theorem 5.2.
The theorem concerns canonical independent products, not adaptive transcripts.
-/
open Filter MeasureTheory
open scoped Topology ENNReal NNReal
namespace Mf.DP
noncomputable section

/-- Both canonical directed privacy profiles converge at every fixed budget. -/
theorem canonical_sampledGaussian_profiles_tendsto
    (q : ℝ≥0) (hq : q ≤ 1) (hqpos : 0 < q)
    (T : ℕ → ℕ) (sigma : ℕ → ℝ≥0) (kappa epsilon : ℝ)
    (hTpos : ∀ j, 0 < T j) (hsigma : ∀ j, 0 < sigma j)
    (hT : Tendsto T atTop atTop) (hkappa : 0 < kappa)
    (hscale : Tendsto (fun j => (sigma j : ℝ) ^ 2 / (T j : ℝ))
      atTop (𝓝 kappa)) (_hepsilon : 0 ≤ epsilon) :
    Tendsto (fun j => eventHockeyStickProfile
      (sampledGaussianSourceProductLaw (T j) q hq 1 (sigma j ^ 2) :
        Measure (Fin (T j) → ℝ))
      (sampledGaussianReferenceProductLaw (T j) (sigma j ^ 2) :
        Measure (Fin (T j) → ℝ)) epsilon)
      atTop (𝓝 (ENNReal.ofReal (gdpProfile ((q : ℝ) / Real.sqrt kappa) epsilon))) ∧
    Tendsto (fun j => eventHockeyStickProfile
      (sampledGaussianReferenceProductLaw (T j) (sigma j ^ 2) :
        Measure (Fin (T j) → ℝ))
      (sampledGaussianSourceProductLaw (T j) q hq 1 (sigma j ^ 2) :
        Measure (Fin (T j) → ℝ)) epsilon)
      atTop (𝓝 (ENNReal.ofReal (gdpProfile ((q : ℝ) / Real.sqrt kappa) epsilon))) := by
  let P (j : ℕ) := sampledGaussianReferenceProductLaw (T j) (sigma j ^ 2)
  let Q (j : ℕ) := sampledGaussianSourceProductLaw (T j) q hq 1 (sigma j ^ 2)
  let G (j : ℕ) := matchedGaussianSourceProductLaw (T j) q 1 (sigma j ^ 2)
  let mu : ℝ := (q : ℝ) / Real.sqrt kappa
  have hmu : 0 < mu := div_pos (by exact_mod_cast hqpos) (Real.sqrt_pos.mpr hkappa)
  have hparameter := tendsto_matchedGaussianSignalToNoise q T sigma kappa
    hTpos hsigma hkappa hscale
  have hcont := (Training.continuousOn_gdpProfile_pos epsilon).continuousAt
    (isOpen_Ioi.mem_nhds hmu)
  have hformula := ENNReal.tendsto_ofReal (hcont.tendsto.comp hparameter)
  have hf : Tendsto (fun j => eventHockeyStickProfile
      (G j : Measure (Fin (T j) → ℝ)) (P j : Measure (Fin (T j) → ℝ)) epsilon)
      atTop (𝓝 (ENNReal.ofReal (gdpProfile mu epsilon))) := by
    apply hformula.congr'
    exact Eventually.of_forall fun j =>
      (matchedGaussianProduct_eventProfiles_eq_gdp (T j) q (sigma j) epsilon
        (hTpos j) hqpos (hsigma j)).1.symm
  have hr : Tendsto (fun j => eventHockeyStickProfile
      (P j : Measure (Fin (T j) → ℝ)) (G j : Measure (Fin (T j) → ℝ)) epsilon)
      atTop (𝓝 (ENNReal.ofReal (gdpProfile mu epsilon))) := by
    apply hformula.congr'
    exact Eventually.of_forall fun j =>
      (matchedGaussianProduct_eventProfiles_eq_gdp (T j) q (sigma j) epsilon
        (hTpos j) hqpos (hsigma j)).2.symm
  obtain ⟨distance, hd, hclose⟩ := sampledGaussianSourceProduct_sequence_eventDistance
    q hq T sigma kappa hTpos hsigma hT hkappa hscale
  constructor
  · apply tendsto_of_eventually_profile_close _ _ distance _ hf hd
    filter_upwards [hclose] with j hj
    exact ⟨eventHockeyStickProfile_le_add_sourceDistance epsilon hj.symm,
      eventHockeyStickProfile_le_add_sourceDistance epsilon hj⟩
  · have herror : Tendsto (fun j => ENNReal.ofReal (Real.exp epsilon) * distance j)
        atTop (𝓝 0) := by
      simpa using ENNReal.Tendsto.const_mul hd (Or.inr ENNReal.ofReal_ne_top)
    apply tendsto_of_eventually_profile_close _ _ _ _ hr herror
    filter_upwards [hclose] with j hj
    exact ⟨eventHockeyStickProfile_le_add_referenceDistance epsilon hj.symm,
      eventHockeyStickProfile_le_add_referenceDistance epsilon hj⟩

end
end Mf.DP
