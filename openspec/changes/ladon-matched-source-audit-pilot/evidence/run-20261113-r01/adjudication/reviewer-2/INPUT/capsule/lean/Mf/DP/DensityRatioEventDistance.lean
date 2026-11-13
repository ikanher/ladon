import Mf.DP.LawAccountingOracle
import Mf.DP.CenteredBernoulliGaussianProductChiSquare
import Mathlib.MeasureTheory.Integral.MeanInequalities

/-!
# Uniform event control from a squared density residual

A direct probability-space Cauchy--Schwarz estimate controls every measurable
event by the square root of the density-ratio residual's second moment.  This
is the event-level interface needed for exact accounting stability; no
total-variation metric or KL/Pinsker theorem is introduced.
-/

open MeasureTheory ProbabilityTheory

namespace Mf.DP

noncomputable section

/-- Probability-space Cauchy--Schwarz for a real scalar. -/
theorem integral_abs_le_secondMomentRoot
    {X : Type*} [MeasurableSpace X]
    (base : Measure X) [IsProbabilityMeasure base]
    (residual : X → Real)
    (hmeas : AEStronglyMeasurable residual base)
    (hsq : Integrable (fun sample => residual sample ^ 2) base) :
    (∫ sample, |residual sample| ∂base) ≤
      Real.sqrt (∫ sample, residual sample ^ 2 ∂base) := by
  have hone : MemLp (fun _ : X => (1 : Real)) 2 base :=
    (memLp_two_iff_integrable_sq
      stronglyMeasurable_const.aestronglyMeasurable).2 (by simp)
  have habs : MemLp (fun sample => |residual sample|) 2 base :=
    (memLp_two_iff_integrable_sq hmeas.norm).2
      (by simpa [sq_abs] using hsq)
  have hholder := integral_mul_le_Lp_mul_Lq_of_nonneg
    (μ := base) (p := (2 : Real)) (q := (2 : Real))
    Real.HolderConjugate.two_two
    (ae_of_all base fun _ : X => show 0 ≤ (1 : Real) by norm_num)
    (ae_of_all base fun sample => abs_nonneg (residual sample))
    (by simpa using hone) (by simpa using habs)
  simpa [Real.sqrt_eq_rpow, sq_abs] using hholder

/-- A square-integrable density residual gives uniform symmetric event control. -/
theorem UniformEventDistance.of_withDensity_sq_integral
    {X : Type*} [MeasurableSpace X]
    (source base : ProbabilityMeasure X) (ratio : X → Real) (distance : Real)
    (hRatio : Measurable ratio) (hNonneg : ∀ sample, 0 ≤ ratio sample)
    (hSource : (source : Measure X) =
      (base : Measure X).withDensity (fun sample => ENNReal.ofReal (ratio sample)))
    (hSq : Integrable (fun sample => (ratio sample - 1) ^ 2) (base : Measure X))
    (hDistance :
      Real.sqrt (∫ sample, (ratio sample - 1) ^ 2 ∂(base : Measure X)) ≤ distance) :
    UniformEventDistance (source : Measure X) (base : Measure X)
      (ENNReal.ofReal distance) := by
  let residualDensity : X → ENNReal := fun sample => ENNReal.ofReal |ratio sample - 1|
  have hResidualMeas : Measurable residualDensity := by
    dsimp [residualDensity]
    fun_prop
  have hResidualLp : MemLp (fun sample => |ratio sample - 1|) 2
      (base : Measure X) :=
    (memLp_two_iff_integrable_sq (by fun_prop)).2 (by simpa [sq_abs] using hSq)
  have hResidualIntegrable : Integrable (fun sample => |ratio sample - 1|)
      (base : Measure X) := hResidualLp.integrable (by norm_num)
  have hL1 : (base : Measure X).withDensity residualDensity Set.univ ≤
      ENNReal.ofReal distance := by
    rw [withDensity_apply _ MeasurableSet.univ, Measure.restrict_univ]
    rw [← ofReal_integral_eq_lintegral_ofReal hResidualIntegrable
      (ae_of_all _ fun sample => abs_nonneg (ratio sample - 1))]
    apply ENNReal.ofReal_le_ofReal
    exact (integral_abs_le_secondMomentRoot (base : Measure X)
      (fun sample => ratio sample - 1) (by fun_prop) hSq).trans hDistance
  have hForwardMeasure : (source : Measure X) ≤
      (base : Measure X) + (base : Measure X).withDensity residualDensity := by
    rw [hSource]
    calc
      (base : Measure X).withDensity (fun sample => ENNReal.ofReal (ratio sample)) ≤
          (base : Measure X).withDensity (fun sample => 1 + residualDensity sample) := by
        apply withDensity_mono
        filter_upwards with sample
        dsimp [residualDensity]
        rw [← ENNReal.ofReal_one,
          ← ENNReal.ofReal_add zero_le_one (abs_nonneg (ratio sample - 1))]
        apply ENNReal.ofReal_le_ofReal
        linarith [le_abs_self (ratio sample - 1)]
      _ = (base : Measure X) + (base : Measure X).withDensity residualDensity := by
        have hadd : (fun sample : X => 1 + residualDensity sample) =
            (fun _ : X => 1) + residualDensity := by rfl
        rw [hadd]
        rw [withDensity_add_left (μ := (base : Measure X))
          (f := fun _ => 1) measurable_const residualDensity]
        have hone : (base : Measure X).withDensity (fun _ : X => 1) =
            (base : Measure X) := by
          simpa using withDensity_one (μ := (base : Measure X))
        rw [hone]
  have hReverseMeasure : (base : Measure X) ≤
      (source : Measure X) + (base : Measure X).withDensity residualDensity := by
    calc
      (base : Measure X) = (base : Measure X).withDensity 1 := withDensity_one.symm
      _ ≤ (base : Measure X).withDensity
          (fun sample => ENNReal.ofReal (ratio sample) + residualDensity sample) := by
        apply withDensity_mono
        filter_upwards with sample
        dsimp [residualDensity]
        rw [← ENNReal.ofReal_add (hNonneg sample) (abs_nonneg (ratio sample - 1))]
        rw [← ENNReal.ofReal_one]
        apply ENNReal.ofReal_le_ofReal
        linarith [neg_le_abs (ratio sample - 1)]
      _ = (base : Measure X).withDensity (fun sample => ENNReal.ofReal (ratio sample)) +
          (base : Measure X).withDensity residualDensity := by
        have hadd :
            (fun sample : X => ENNReal.ofReal (ratio sample) + residualDensity sample) =
              (fun sample : X => ENNReal.ofReal (ratio sample)) + residualDensity := by rfl
        rw [hadd]
        rw [withDensity_add_left (μ := (base : Measure X))
          (f := fun sample => ENNReal.ofReal (ratio sample))
          hRatio.ennreal_ofReal residualDensity]
      _ = (source : Measure X) +
          (base : Measure X).withDensity residualDensity := by rw [← hSource]
  constructor
  · intro event _
    calc
      (source : Measure X) event ≤ ((base : Measure X) +
          (base : Measure X).withDensity residualDensity) event := hForwardMeasure event
      _ = (base : Measure X) event +
          (base : Measure X).withDensity residualDensity event := by simp
      _ ≤ (base : Measure X) event + ENNReal.ofReal distance := by
        gcongr
        exact ((base : Measure X).withDensity residualDensity).mono
          (Set.subset_univ event) |>.trans hL1
  · intro event _
    calc
      (base : Measure X) event ≤ ((source : Measure X) +
          (base : Measure X).withDensity residualDensity) event := hReverseMeasure event
      _ = (source : Measure X) event +
          (base : Measure X).withDensity residualDensity event := by simp
      _ ≤ (source : Measure X) event + ENNReal.ofReal distance := by
        gcongr
        exact ((base : Measure X).withDensity residualDensity).mono
          (Set.subset_univ event) |>.trans hL1

/-- Product centered mixtures are within the square root of their exact chi-square. -/
theorem centeredBernoulliGaussianProduct_uniformEventDistance
    (horizon : Nat) (samplingRate : NNReal) (hRate : samplingRate ≤ 1)
    (standardizedShift : Real) :
    UniformEventDistance
      (centeredBernoulliGaussianProductLaw horizon samplingRate hRate
        standardizedShift : Measure (Fin horizon → Real))
      (standardGaussianProductLaw horizon : Measure (Fin horizon → Real))
      (ENNReal.ofReal (Real.sqrt
        (centeredBernoulliGaussianProductChiSquare horizon samplingRate
          standardizedShift))) := by
  refine UniformEventDistance.of_withDensity_sq_integral
    (source := centeredBernoulliGaussianProductLaw horizon samplingRate hRate
      standardizedShift)
    (base := standardGaussianProductLaw horizon)
    (ratio := centeredBernoulliGaussianProductDensityRatio horizon samplingRate
      standardizedShift)
    (distance := Real.sqrt
      (centeredBernoulliGaussianProductChiSquare horizon samplingRate
        standardizedShift)) ?_ ?_ ?_ ?_ ?_
  · unfold centeredBernoulliGaussianProductDensityRatio
    unfold centeredBernoulliGaussianDensityRatio
    fun_prop
  · intro sample
    apply Finset.prod_nonneg
    intro coordinate _
    have hRateNonneg : 0 ≤ (samplingRate : Real) := NNReal.coe_nonneg samplingRate
    have hRateOne : (samplingRate : Real) ≤ 1 := by exact_mod_cast hRate
    unfold centeredBernoulliGaussianDensityRatio
    positivity
  · exact centeredBernoulliGaussianProductLaw_eq_withDensity
      horizon samplingRate hRate standardizedShift
  · exact integrable_centeredBernoulliGaussianProductDensityRatio_sub_one_sq
      horizon samplingRate standardizedShift
  · rfl

end

end Mf.DP
