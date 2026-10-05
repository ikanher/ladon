import Mf.DP.PoissonFixedEpochEnergyThreshold

/-!
# Small-batch divergence on a fixed positive epoch budget

This module transfers the fixed-participation calibration theorem to the
discrete path `T = E + k`, `q = E / T`.  The result is eventual endpoint
dominance only; it does not assert adjacent or all-horizon monotonicity.

Boundary cases remain owned by
`sampledGaussianFeasibleStddevSet_zero_eq_empty` (`delta = 0`),
`sampledGaussianCalibratedStddev_zero_sensitivity`,
`fixedParticipationTargetProbability_critical_not_mem_Ioo`, and
`fixedParticipationCalibratedStddev_eventually_eq_zero_of_supercritical`.
They are deliberately not folded into the strict-interior theorem below.
-/

open Filter

namespace Mf.DP

noncomputable section

set_option autoImplicit false

/-- The discrete rate along `T = E + k` tends to zero. -/
theorem tendsto_poissonFixedEpoch_ofExtra_samplingRate_zero
    (epoch : Nat) (epoch_pos : 0 < epoch) :
    Tendsto
      (fun extra =>
        ((PoissonFixedEpochPoint.ofExtra epoch epoch_pos extra).samplingRate : Real))
      atTop (nhds 0) := by
  let schedule := cappedFixedParticipationSchedule (epoch : NNReal)
    (by exact_mod_cast epoch_pos)
  have hShift := schedule.tendsto_samplingRate_zero.comp
    (tendsto_add_atTop_nat epoch)
  apply hShift.congr'
  filter_upwards with extra
  simp only [Function.comp_apply, schedule, cappedFixedParticipationSchedule,
    PoissonFixedEpochPoint.ofExtra_samplingRate_eq_cappedParticipationRate,
    Nat.add_comm]

/-- Exact identification of the discrete calibrated privacy component with
the capped fixed-participation owner at horizon `E + k`. -/
theorem poissonFixedEpoch_ofExtra_privacyVariance_eq_capped
    (epoch : Nat) (epoch_pos : 0 < epoch) (extra : Nat)
    (sensitivity epsilon delta : Real) :
    poissonFixedEpochPrivacyVarianceOfStddev
        (PoissonFixedEpochPoint.ofExtra epoch epoch_pos extra)
        (poissonFixedEpochCalibratedStddev
          (PoissonFixedEpochPoint.ofExtra epoch epoch_pos extra)
          sensitivity epsilon delta : Real) =
      fixedParticipationPrivacyVarianceComponent ((epoch : NNReal) : Real)
        (cappedParticipationRate (epoch : NNReal) (epoch + extra) : Real)
        (fixedParticipationCalibratedStddev
          (cappedFixedParticipationSchedule (epoch : NNReal)
            (by exact_mod_cast epoch_pos))
          sensitivity epsilon delta (epoch + extra) : Real) := by
  rw [poissonFixedEpochPrivacyVarianceOfStddev_eq_fixedParticipation]
  simp only [poissonFixedEpochCalibratedStddev,
    fixedParticipationCalibratedStddev,
    cappedFixedParticipationSchedule,
    PoissonFixedEpochPoint.epoch_ofExtra,
    PoissonFixedEpochPoint.horizon_ofExtra,
    PoissonFixedEpochPoint.ofExtra_samplingRate_eq_cappedParticipationRate]
  norm_num

/-- The existing calibrated small-rate standard-deviation asymptotic transfers
verbatim to the discrete exact-epoch path. -/
theorem tendsto_poissonFixedEpochCalibratedStddev_smallRate_ratio_one
    (epoch : Nat) (epoch_pos : 0 < epoch)
    (sensitivity epsilon delta : Real)
    (sensitivity_pos : 0 < sensitivity) (epsilon_nonneg : 0 ≤ epsilon)
    (delta_pos : 0 < delta)
    (delta_lt_boundary : delta < 1 - Real.exp (-(epoch : Real))) :
    Tendsto
      (fun extra =>
        (poissonFixedEpochCalibratedStddev
            (PoissonFixedEpochPoint.ofExtra epoch epoch_pos extra)
            sensitivity epsilon delta : Real) *
          Real.sqrt (2 * Real.log
            (1 / ((PoissonFixedEpochPoint.ofExtra epoch epoch_pos extra).samplingRate :
              Real))) /
          sensitivity)
      atTop (nhds 1) := by
  have hCapped :=
    tendsto_cappedFixedParticipationCalibratedStddev_smallRate_ratio_one
      (epoch : NNReal) (by exact_mod_cast epoch_pos)
      sensitivity epsilon delta sensitivity_pos epsilon_nonneg delta_pos
      delta_lt_boundary
  have hShift := hCapped.comp (tendsto_add_atTop_nat epoch)
  apply hShift.congr'
  filter_upwards with extra
  simp only [Function.comp_apply, poissonFixedEpochCalibratedStddev,
    fixedParticipationCalibratedStddev, cappedFixedParticipationSchedule,
    PoissonFixedEpochPoint.horizon_ofExtra,
    PoissonFixedEpochPoint.ofExtra_samplingRate_eq_cappedParticipationRate,
    Nat.add_comm]

/-- Although its epoch-normalized privacy contribution diverges, the raw
calibrated Gaussian standard deviation itself tends to zero. -/
theorem tendsto_poissonFixedEpochCalibratedStddev_zero
    (epoch : Nat) (epoch_pos : 0 < epoch)
    (sensitivity epsilon delta : Real)
    (sensitivity_pos : 0 < sensitivity) (epsilon_nonneg : 0 ≤ epsilon)
    (delta_pos : 0 < delta)
    (delta_lt_boundary : delta < 1 - Real.exp (-(epoch : Real))) :
    Tendsto
      (fun extra =>
        (poissonFixedEpochCalibratedStddev
          (PoissonFixedEpochPoint.ofExtra epoch epoch_pos extra)
          sensitivity epsilon delta : Real))
      atTop (nhds 0) := by
  let rate : Nat → NNReal := fun extra =>
    (PoissonFixedEpochPoint.ofExtra epoch epoch_pos extra).samplingRate
  let noise : Nat → Real := fun extra =>
    (poissonFixedEpochCalibratedStddev
      (PoissonFixedEpochPoint.ofExtra epoch epoch_pos extra)
      sensitivity epsilon delta : Real)
  let scale : Nat → Real := fun extra =>
    Real.sqrt (2 * Real.log (1 / (rate extra : Real)))
  have hRateZero : Tendsto (fun extra => (rate extra : Real)) atTop (nhds 0) := by
    simpa [rate] using
      tendsto_poissonFixedEpoch_ofExtra_samplingRate_zero epoch epoch_pos
  have hRatePos : ∀ᶠ extra : Nat in atTop, 0 < rate extra :=
    Filter.Eventually.of_forall fun extra =>
      (PoissonFixedEpochPoint.ofExtra epoch epoch_pos extra).samplingRate_pos
  have hRateGT : Tendsto (fun extra => (rate extra : Real)) atTop
      (nhdsWithin 0 (Set.Ioi 0)) := by
    apply tendsto_nhdsWithin_iff.mpr
    refine ⟨hRateZero, ?_⟩
    filter_upwards [hRatePos] with extra hPositive
    exact_mod_cast hPositive
  have hInverse : Tendsto (fun extra => ((rate extra : Real))⁻¹) atTop atTop :=
    tendsto_inv_nhdsGT_zero.comp hRateGT
  have hLog : Tendsto
      (fun extra => Real.log (1 / (rate extra : Real))) atTop atTop := by
    have h := Real.tendsto_log_atTop.comp hInverse
    apply h.congr'
    filter_upwards with extra
    rw [one_div]
    rfl
  have hScaled : Tendsto
      (fun extra => 2 * Real.log (1 / (rate extra : Real))) atTop atTop :=
    hLog.const_mul_atTop (by norm_num)
  have hScale : Tendsto scale atTop atTop := by
    change Tendsto
      ((fun value : Real => Real.sqrt value) ∘
        fun extra => 2 * Real.log (1 / (rate extra : Real))) atTop atTop
    exact Real.tendsto_sqrt_atTop.comp hScaled
  have hRatio : Tendsto
      (fun extra => noise extra * scale extra / sensitivity)
      atTop (nhds 1) := by
    simpa [noise, scale, rate] using
      tendsto_poissonFixedEpochCalibratedStddev_smallRate_ratio_one epoch epoch_pos
        sensitivity epsilon delta sensitivity_pos epsilon_nonneg delta_pos
        delta_lt_boundary
  have hScaledRatio : Tendsto
      (fun extra => sensitivity *
        (noise extra * scale extra / sensitivity))
      atTop (nhds sensitivity) := by
    simpa using hRatio.const_mul sensitivity
  have hQuot := hScaledRatio.div_atTop hScale
  apply hQuot.congr'
  filter_upwards [hScale.eventually (eventually_gt_atTop 0)] with extra hScalePos
  dsimp [noise, scale]
  field_simp [sensitivity_pos.ne', hScalePos.ne']
  exact mul_div_cancel_right₀ _ hScalePos.ne'

/-- The calibrated privacy component diverges along the discrete fixed-epoch
small-batch path. -/
theorem tendsto_poissonFixedEpochPrivacyVariance_atTop
    (epoch : Nat) (epoch_pos : 0 < epoch)
    (sensitivity epsilon delta : Real)
    (sensitivity_pos : 0 < sensitivity) (epsilon_nonneg : 0 ≤ epsilon)
    (delta_pos : 0 < delta)
    (delta_lt_boundary : delta < 1 - Real.exp (-(epoch : Real))) :
    Tendsto
      (fun extra =>
        poissonFixedEpochPrivacyVarianceOfStddev
          (PoissonFixedEpochPoint.ofExtra epoch epoch_pos extra)
          (poissonFixedEpochCalibratedStddev
            (PoissonFixedEpochPoint.ofExtra epoch epoch_pos extra)
            sensitivity epsilon delta : Real))
      atTop atTop := by
  have hCapped :=
    tendsto_cappedFixedParticipationCalibratedPrivacyVariance_atTop
      (epoch : NNReal) (by exact_mod_cast epoch_pos)
      sensitivity epsilon delta sensitivity_pos epsilon_nonneg delta_pos
      delta_lt_boundary
  have hShift := hCapped.comp (tendsto_add_atTop_nat epoch)
  apply hShift.congr'
  filter_upwards with extra
  simpa only [Function.comp_apply, Nat.add_comm] using
    (poissonFixedEpoch_ofExtra_privacyVariance_eq_capped epoch epoch_pos
      extra sensitivity epsilon delta).symm

/-- The exact calibrated epoch-normalized privacy variance has the sharp
leading equivalent `Delta^2 / (2 E q log (1/q))`. -/
theorem tendsto_poissonFixedEpochPrivacyVariance_div_leadingTerm_one
    (epoch : Nat) (epoch_pos : 0 < epoch)
    (sensitivity epsilon delta : Real)
    (sensitivity_pos : 0 < sensitivity) (epsilon_nonneg : 0 ≤ epsilon)
    (delta_pos : 0 < delta)
    (delta_lt_boundary : delta < 1 - Real.exp (-(epoch : Real))) :
    Tendsto
      (fun extra =>
        poissonFixedEpochCalibratedPrivacyVariance
            (PoissonFixedEpochPoint.ofExtra epoch epoch_pos extra)
            sensitivity epsilon delta /
          fixedParticipationPrivacyVarianceLeadingTerm (epoch : Real)
            ((PoissonFixedEpochPoint.ofExtra epoch epoch_pos extra).samplingRate : Real)
            sensitivity)
      atTop (nhds 1) := by
  have hCapped :=
    tendsto_cappedFixedParticipationCalibratedPrivacyVariance_div_leadingTerm_one
      (epoch : NNReal) (by exact_mod_cast epoch_pos)
      sensitivity epsilon delta sensitivity_pos epsilon_nonneg delta_pos
      delta_lt_boundary
  have hShift := hCapped.comp (tendsto_add_atTop_nat epoch)
  apply hShift.congr'
  filter_upwards with extra
  simp only [Function.comp_apply, poissonFixedEpochCalibratedPrivacyVariance,
    poissonFixedEpoch_ofExtra_privacyVariance_eq_capped,
    PoissonFixedEpochPoint.ofExtra_samplingRate_eq_cappedParticipationRate,
    Nat.add_comm]
  norm_num

/-- Adding the nonnegative frozen-gradient sampling component preserves
divergence of the calibrated total horizon-average variance. -/
theorem tendsto_poissonFixedEpochTotalAverageVariance_atTop
    (epoch : Nat) (epoch_pos : 0 < epoch)
    (sensitivity epsilon delta energy : Real)
    (sensitivity_pos : 0 < sensitivity) (epsilon_nonneg : 0 ≤ epsilon)
    (delta_pos : 0 < delta)
    (delta_lt_boundary : delta < 1 - Real.exp (-(epoch : Real)))
    (energy_nonneg : 0 ≤ energy) :
    Tendsto
      (fun extra => poissonFixedEpochTotalAverageVariance
        (PoissonFixedEpochPoint.ofExtra epoch epoch_pos extra)
        sensitivity epsilon delta energy)
      atTop atTop := by
  have hPrivacy := tendsto_poissonFixedEpochPrivacyVariance_atTop epoch epoch_pos
    sensitivity epsilon delta sensitivity_pos epsilon_nonneg delta_pos
    delta_lt_boundary
  apply tendsto_atTop_mono' atTop ?_ hPrivacy
  filter_upwards with extra
  unfold poissonFixedEpochTotalAverageVariance
    poissonFixedEpochTotalAverageVarianceOfStddev
  exact le_add_of_nonneg_left
    (poissonFixedEpochSamplingVariance_nonneg
      (PoissonFixedEpochPoint.ofExtra epoch epoch_pos extra) energy energy_nonneg)

/-- For fixed coordinate energy, the bounded sampling term is negligible:
the complete frozen-gradient average variance has the same sharp leading
equivalent as its privacy component. -/
theorem tendsto_poissonFixedEpochTotalAverageVariance_div_leadingTerm_one
    (epoch : Nat) (epoch_pos : 0 < epoch)
    (sensitivity epsilon delta energy : Real)
    (sensitivity_pos : 0 < sensitivity) (epsilon_nonneg : 0 ≤ epsilon)
    (delta_pos : 0 < delta)
    (delta_lt_boundary : delta < 1 - Real.exp (-(epoch : Real))) :
    Tendsto
      (fun extra =>
        poissonFixedEpochTotalAverageVariance
            (PoissonFixedEpochPoint.ofExtra epoch epoch_pos extra)
            sensitivity epsilon delta energy /
          fixedParticipationPrivacyVarianceLeadingTerm (epoch : Real)
            ((PoissonFixedEpochPoint.ofExtra epoch epoch_pos extra).samplingRate : Real)
            sensitivity)
      atTop (nhds 1) := by
  let rate : Nat → NNReal := fun extra =>
    (PoissonFixedEpochPoint.ofExtra epoch epoch_pos extra).samplingRate
  have hRateZero : Tendsto (fun extra => (rate extra : Real)) atTop (nhds 0) := by
    simpa [rate] using
      tendsto_poissonFixedEpoch_ofExtra_samplingRate_zero epoch epoch_pos
  have hRatePos : ∀ᶠ extra : Nat in atTop, 0 < rate extra :=
    Filter.Eventually.of_forall fun extra =>
      (PoissonFixedEpochPoint.ofExtra epoch epoch_pos extra).samplingRate_pos
  have hLeading := tendsto_fixedParticipationPrivacyVarianceLeadingTerm_atTop
    rate (epoch : Real) sensitivity (by exact_mod_cast epoch_pos) sensitivity_pos
    hRateZero hRatePos
  have hSampling : Tendsto
      (fun extra => poissonFixedEpochSamplingVariance
        (PoissonFixedEpochPoint.ofExtra epoch epoch_pos extra) energy)
      atTop (nhds (energy / (epoch : Real))) := by
    have h := tendsto_fixedParticipation_samplingVarianceComponent
      (samplingRate := fun extra => (rate extra : Real))
      (participationBudget := (epoch : Real)) (energy := energy) hRateZero
    apply h.congr'
    filter_upwards with extra
    rw [poissonFixedEpochSamplingVariance_eq_rate]
    rfl
  have hSamplingRatio := hSampling.div_atTop hLeading
  have hPrivacyRatio :=
    tendsto_poissonFixedEpochPrivacyVariance_div_leadingTerm_one epoch epoch_pos
      sensitivity epsilon delta sensitivity_pos epsilon_nonneg delta_pos
      delta_lt_boundary
  have hSum := hSamplingRatio.add hPrivacyRatio
  have hEq :
      (fun extra =>
        poissonFixedEpochSamplingVariance
              (PoissonFixedEpochPoint.ofExtra epoch epoch_pos extra) energy /
            fixedParticipationPrivacyVarianceLeadingTerm (epoch : Real)
              (rate extra : Real) sensitivity +
          poissonFixedEpochCalibratedPrivacyVariance
              (PoissonFixedEpochPoint.ofExtra epoch epoch_pos extra)
              sensitivity epsilon delta /
            fixedParticipationPrivacyVarianceLeadingTerm (epoch : Real)
              ((PoissonFixedEpochPoint.ofExtra epoch epoch_pos extra).samplingRate : Real)
              sensitivity) =ᶠ[atTop]
        (fun extra =>
          poissonFixedEpochTotalAverageVariance
              (PoissonFixedEpochPoint.ofExtra epoch epoch_pos extra)
              sensitivity epsilon delta energy /
            fixedParticipationPrivacyVarianceLeadingTerm (epoch : Real)
              ((PoissonFixedEpochPoint.ofExtra epoch epoch_pos extra).samplingRate : Real)
              sensitivity) := by
    filter_upwards [hLeading.eventually (eventually_gt_atTop 0)]
      with extra hPositive
    unfold poissonFixedEpochTotalAverageVariance
      poissonFixedEpochTotalAverageVarianceOfStddev
      poissonFixedEpochCalibratedPrivacyVariance
    dsimp [rate]
    field_simp [hPositive.ne']
  simpa only [zero_add] using hSum.congr' hEq

/-- Every fixed real threshold is eventually strictly below the calibrated
fixed-epoch total variance. -/
theorem eventually_threshold_lt_poissonFixedEpochTotalAverageVariance
    (epoch : Nat) (epoch_pos : 0 < epoch)
    (sensitivity epsilon delta energy threshold : Real)
    (sensitivity_pos : 0 < sensitivity) (epsilon_nonneg : 0 ≤ epsilon)
    (delta_pos : 0 < delta)
    (delta_lt_boundary : delta < 1 - Real.exp (-(epoch : Real)))
    (energy_nonneg : 0 ≤ energy) :
    ∀ᶠ extra : Nat in atTop,
      threshold < poissonFixedEpochTotalAverageVariance
        (PoissonFixedEpochPoint.ofExtra epoch epoch_pos extra)
        sensitivity epsilon delta energy := by
  exact (tendsto_poissonFixedEpochTotalAverageVariance_atTop epoch epoch_pos
    sensitivity epsilon delta energy sensitivity_pos epsilon_nonneg delta_pos
    delta_lt_boundary energy_nonneg).eventually (eventually_gt_atTop threshold)

/-- For all sufficiently small batches on a fixed positive epoch budget, the
exact total variance is strictly larger than at full batch. -/
theorem eventually_poissonFixedEpoch_fullBatch_lt_totalAverageVariance
    (epoch : Nat) (epoch_pos : 0 < epoch)
    (sensitivity epsilon delta energy : Real)
    (sensitivity_pos : 0 < sensitivity) (epsilon_nonneg : 0 ≤ epsilon)
    (delta_pos : 0 < delta)
    (delta_lt_boundary : delta < 1 - Real.exp (-(epoch : Real)))
    (energy_nonneg : 0 ≤ energy) :
    ∀ᶠ extra : Nat in atTop,
      poissonFixedEpochTotalAverageVariance
          (PoissonFixedEpochPoint.fullBatch epoch epoch_pos)
          sensitivity epsilon delta energy <
        poissonFixedEpochTotalAverageVariance
          (PoissonFixedEpochPoint.ofExtra epoch epoch_pos extra)
          sensitivity epsilon delta energy := by
  exact eventually_threshold_lt_poissonFixedEpochTotalAverageVariance epoch epoch_pos
    sensitivity epsilon delta energy
    (poissonFixedEpochTotalAverageVariance
      (PoissonFixedEpochPoint.fullBatch epoch epoch_pos)
      sensitivity epsilon delta energy)
    sensitivity_pos epsilon_nonneg delta_pos delta_lt_boundary energy_nonneg

/-- One small-batch cutoff works for every nonnegative frozen-coordinate
energy.  The cutoff is uniform because the calibrated privacy component alone
eventually exceeds the finite full-batch baseline; the sampling contribution
is merely nonnegative. -/
theorem eventually_poissonFixedEpoch_fullBatch_lt_totalAverageVariance_uniform_energy
    (epoch : Nat) (epoch_pos : 0 < epoch)
    (sensitivity epsilon delta : Real)
    (sensitivity_pos : 0 < sensitivity) (epsilon_nonneg : 0 ≤ epsilon)
    (delta_pos : 0 < delta)
    (delta_lt_boundary : delta < 1 - Real.exp (-(epoch : Real))) :
    ∀ᶠ extra : Nat in atTop, ∀ energy : Real, 0 ≤ energy →
      poissonFixedEpochTotalAverageVariance
          (PoissonFixedEpochPoint.fullBatch epoch epoch_pos)
          sensitivity epsilon delta energy <
        poissonFixedEpochTotalAverageVariance
          (PoissonFixedEpochPoint.ofExtra epoch epoch_pos extra)
          sensitivity epsilon delta energy := by
  have delta_lt_one : delta < 1 :=
    lt_trans delta_lt_boundary
      (sub_lt_self 1 (Real.exp_pos (-(epoch : Real))))
  let fullBatchVariance :=
    (fullBatchGaussianBaseStddev sensitivity epsilon delta sensitivity_pos
      epsilon_nonneg delta_pos delta_lt_one) ^ 2
  have hPrivacy := tendsto_poissonFixedEpochPrivacyVariance_atTop epoch epoch_pos
    sensitivity epsilon delta sensitivity_pos epsilon_nonneg delta_pos
    delta_lt_boundary
  filter_upwards [hPrivacy.eventually (eventually_gt_atTop fullBatchVariance)]
    with extra hPrivacyDominance
  intro energy energy_nonneg
  rw [poissonFixedEpochTotalAverageVariance_fullBatch_eq_base_sq epoch epoch_pos
    sensitivity epsilon delta energy sensitivity_pos epsilon_nonneg delta_pos
    delta_lt_one]
  have hSampling := poissonFixedEpochSamplingVariance_nonneg
    (PoissonFixedEpochPoint.ofExtra epoch epoch_pos extra) energy energy_nonneg
  unfold poissonFixedEpochTotalAverageVariance
    poissonFixedEpochTotalAverageVarianceOfStddev
  dsimp [fullBatchVariance] at hPrivacyDominance ⊢
  linarith

/-- Weak endpoint dominance is an immediate corollary of the strict eventual
comparison. -/
theorem eventually_poissonFixedEpoch_fullBatch_le_totalAverageVariance
    (epoch : Nat) (epoch_pos : 0 < epoch)
    (sensitivity epsilon delta energy : Real)
    (sensitivity_pos : 0 < sensitivity) (epsilon_nonneg : 0 ≤ epsilon)
    (delta_pos : 0 < delta)
    (delta_lt_boundary : delta < 1 - Real.exp (-(epoch : Real)))
    (energy_nonneg : 0 ≤ energy) :
    ∀ᶠ extra : Nat in atTop,
      poissonFixedEpochTotalAverageVariance
          (PoissonFixedEpochPoint.fullBatch epoch epoch_pos)
          sensitivity epsilon delta energy ≤
        poissonFixedEpochTotalAverageVariance
          (PoissonFixedEpochPoint.ofExtra epoch epoch_pos extra)
          sensitivity epsilon delta energy :=
  (eventually_poissonFixedEpoch_fullBatch_lt_totalAverageVariance epoch epoch_pos
    sensitivity epsilon delta energy sensitivity_pos epsilon_nonneg delta_pos
    delta_lt_boundary energy_nonneg).mono fun _ => le_of_lt

/-- Along the small-batch tail, the exact calibrated energy threshold is
eventually zero: privacy variance alone already exceeds the full-batch
baseline. -/
theorem eventually_poissonFixedEpochCalibratedEnergyThreshold_eq_zero
    (epoch : Nat) (epoch_pos : 0 < epoch)
    (sensitivity epsilon delta : Real)
    (sensitivity_pos : 0 < sensitivity) (epsilon_nonneg : 0 ≤ epsilon)
    (delta_pos : 0 < delta)
    (delta_lt_boundary : delta < 1 - Real.exp (-(epoch : Real))) :
    ∀ᶠ extra : Nat in atTop,
      poissonFixedEpochCalibratedEnergyThreshold
        (PoissonFixedEpochPoint.ofExtra epoch epoch_pos extra)
        sensitivity epsilon delta sensitivity_pos epsilon_nonneg delta_pos
        (lt_trans delta_lt_boundary
          (sub_lt_self 1 (Real.exp_pos (-(epoch : Real))))) = 0 := by
  let fullBatchVariance :=
    (fullBatchGaussianBaseStddev sensitivity epsilon delta sensitivity_pos
      epsilon_nonneg delta_pos
      (lt_trans delta_lt_boundary
        (sub_lt_self 1 (Real.exp_pos (-(epoch : Real)))))) ^ 2
  have hPrivacy := tendsto_poissonFixedEpochPrivacyVariance_atTop epoch epoch_pos
    sensitivity epsilon delta sensitivity_pos epsilon_nonneg delta_pos
    delta_lt_boundary
  filter_upwards [hPrivacy.eventually (eventually_ge_atTop fullBatchVariance)]
    with extra hDominance
  exact poissonFixedEpochEnergyThreshold_eq_zero_of_fullBatch_le
    (PoissonFixedEpochPoint.ofExtra epoch epoch_pos extra)
    (poissonFixedEpochCalibratedPrivacyVariance
      (PoissonFixedEpochPoint.ofExtra epoch epoch_pos extra)
      sensitivity epsilon delta)
    fullBatchVariance hDominance

end

end Mf.DP
