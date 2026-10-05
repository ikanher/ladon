import Mf.DP.PoissonFixedEpochTraceSignalInterpolation
import Mf.Probability.StandardGaussianTailBounds
import Mathlib.Analysis.Convex.Slope

/-!
# Fixed-center propagation for finite Poisson-participation traces

For a fixed positive Gaussian signal scale, this module studies the gap
between the exact finite participation-count average and its value at the
deterministic mean.  An exponential tilt controls the center derivative.
Strict convexity of that tilt, its strict deficit at zero, and the vanishing
right-center limit show that a nonnegative gap at one nonnegative boundary
propagates to a strict gap at every larger center.
-/

open Filter Set
open scoped BigOperators Topology

noncomputable section

set_option autoImplicit false

namespace Mf.DP

/-- Fixed-`h` center gap for the exact finite participation trace. -/
def fixedEpochCenterGap
    (point : PoissonFixedEpochPoint) (h theta : ℝ) : ℝ :=
  ∑ trace : ParticipationTrace point.horizon,
      poissonTraceProb (point.samplingRate : ℝ) trace *
        stdNormalCDFReal
          (h * ((participationCount trace : ℝ) - point.epoch - theta)) -
    stdNormalCDFReal (-h * theta)

/-- Exponential tilt controlling the sign of the center derivative. -/
def fixedEpochCenterTilt
    (point : PoissonFixedEpochPoint) (h theta : ℝ) : ℝ :=
  ∑ trace : ParticipationTrace point.horizon,
    poissonTraceProb (point.samplingRate : ℝ) trace *
      Real.exp
        ((h ^ 2 * ((participationCount trace : ℝ) - point.epoch)) * theta -
          h ^ 2 * ((participationCount trace : ℝ) - point.epoch) ^ 2 / 2)

def fixedEpochCenterTiltDerivative
    (point : PoissonFixedEpochPoint) (h theta : ℝ) : ℝ :=
  ∑ trace : ParticipationTrace point.horizon,
    poissonTraceProb (point.samplingRate : ℝ) trace *
      (h ^ 2 * ((participationCount trace : ℝ) - point.epoch)) *
      Real.exp
        ((h ^ 2 * ((participationCount trace : ℝ) - point.epoch)) * theta -
          h ^ 2 * ((participationCount trace : ℝ) - point.epoch) ^ 2 / 2)

def fixedEpochCenterTiltSecond
    (point : PoissonFixedEpochPoint) (h theta : ℝ) : ℝ :=
  ∑ trace : ParticipationTrace point.horizon,
    poissonTraceProb (point.samplingRate : ℝ) trace *
      (h ^ 2 * ((participationCount trace : ℝ) - point.epoch)) ^ 2 *
      Real.exp
        ((h ^ 2 * ((participationCount trace : ℝ) - point.epoch)) * theta -
          h ^ 2 * ((participationCount trace : ℝ) - point.epoch) ^ 2 / 2)

/-- Exact finite differentiation of the center gap. -/
theorem hasDerivAt_fixedEpochCenterGap
    (point : PoissonFixedEpochPoint) (h theta : ℝ) :
    HasDerivAt (fixedEpochCenterGap point h)
      (h * stdNormalPdfReal (h * theta) *
        (1 - fixedEpochCenterTilt point h theta)) theta := by
  have hSum : HasDerivAt
      (fun current : ℝ =>
        ∑ trace : ParticipationTrace point.horizon,
          poissonTraceProb (point.samplingRate : ℝ) trace *
            stdNormalCDFReal
              (h * ((participationCount trace : ℝ) - point.epoch - current)))
      (∑ trace : ParticipationTrace point.horizon,
        poissonTraceProb (point.samplingRate : ℝ) trace *
          (-h * stdNormalPdfReal
            (h * ((participationCount trace : ℝ) - point.epoch - theta)))) theta := by
    apply HasDerivAt.fun_sum
    intro trace _htrace
    have hArgument : HasDerivAt
        (fun current : ℝ =>
          h * ((participationCount trace : ℝ) - point.epoch - current))
        (-h) theta := by
      have hRaw := ((hasDerivAt_const theta
        ((participationCount trace : ℝ) - point.epoch)).sub
          (hasDerivAt_id' theta)).const_mul h
      convert hRaw using 1
      all_goals first | rfl | ring
    have hCdf := (hasDerivAt_stdNormalCDFReal
      (h * ((participationCount trace : ℝ) - point.epoch - theta))).comp
        theta hArgument
    have hWeighted := hCdf.const_mul
      (poissonTraceProb (point.samplingRate : ℝ) trace)
    convert hWeighted using 1
    all_goals first | rfl | ring
  have hBase : HasDerivAt (fun current : ℝ => stdNormalCDFReal (-h * current))
      (-h * stdNormalPdfReal (h * theta)) theta := by
    have hArgument : HasDerivAt (fun current : ℝ => -h * current) (-h) theta := by
      convert (hasDerivAt_id' theta).const_mul (-h) using 1
      all_goals first | rfl | ring
    have hCdf := (hasDerivAt_stdNormalCDFReal (-h * theta)).comp theta hArgument
    convert hCdf using 1
    all_goals first | rfl | (rw [show -h * theta = -(h * theta) by ring,
      stdNormalPdfReal_neg]; ring)
  have hRaw := hSum.sub hBase
  have hFunction : fixedEpochCenterGap point h =
      (fun current : ℝ =>
        ∑ trace : ParticipationTrace point.horizon,
          poissonTraceProb (point.samplingRate : ℝ) trace *
            stdNormalCDFReal
              (h * ((participationCount trace : ℝ) - point.epoch - current))) -
        fun current : ℝ => stdNormalCDFReal (-h * current) := by
    rfl
  rw [hFunction]
  have hSumFactor : (∑ trace : ParticipationTrace point.horizon,
      poissonTraceProb (point.samplingRate : ℝ) trace *
        (-h * stdNormalPdfReal
          (h * ((participationCount trace : ℝ) - point.epoch - theta)))) =
    -h * stdNormalPdfReal (h * theta) *
      fixedEpochCenterTilt point h theta := by
      unfold fixedEpochCenterTilt
      rw [Finset.mul_sum]
      apply Finset.sum_congr rfl
      intro trace _
      rw [show
        h * ((participationCount trace : ℝ) - point.epoch - theta) =
          -(h * theta) + h *
            ((participationCount trace : ℝ) - point.epoch) by ring]
      rw [stdNormalPdfReal_displacement_factor]
      rw [show
        h * theta *
              (h * ((participationCount trace : ℝ) - point.epoch)) -
            (h * ((participationCount trace : ℝ) - point.epoch)) ^ 2 / 2 =
          (h ^ 2 * ((participationCount trace : ℝ) - point.epoch)) * theta -
            h ^ 2 * ((participationCount trace : ℝ) - point.epoch) ^ 2 / 2 by ring]
      ring
  rw [hSumFactor] at hRaw
  have hDerivative :
      -h * stdNormalPdfReal (h * theta) * fixedEpochCenterTilt point h theta -
          -h * stdNormalPdfReal (h * theta) =
        h * stdNormalPdfReal (h * theta) *
          (1 - fixedEpochCenterTilt point h theta) := by
    ring
  rw [hDerivative] at hRaw
  exact hRaw

/-- First derivative of the exponential tilt. -/
theorem hasDerivAt_fixedEpochCenterTilt
    (point : PoissonFixedEpochPoint) (h theta : ℝ) :
    HasDerivAt (fixedEpochCenterTilt point h)
      (fixedEpochCenterTiltDerivative point h theta) theta := by
  unfold fixedEpochCenterTilt
  unfold fixedEpochCenterTiltDerivative
  apply HasDerivAt.fun_sum
  intro trace _htrace
  have hArg : HasDerivAt
      (fun current : ℝ =>
        (h ^ 2 * ((participationCount trace : ℝ) - point.epoch)) * current -
          h ^ 2 * ((participationCount trace : ℝ) - point.epoch) ^ 2 / 2)
      (h ^ 2 * ((participationCount trace : ℝ) - point.epoch)) theta := by
    have hRaw := ((hasDerivAt_id' theta).const_mul
      (h ^ 2 * ((participationCount trace : ℝ) - point.epoch))).sub_const
        (h ^ 2 * ((participationCount trace : ℝ) - point.epoch) ^ 2 / 2)
    simpa only [mul_one] using hRaw
  have hExp := (Real.hasDerivAt_exp _).comp theta hArg
  have hWeighted := hExp.const_mul
    (poissonTraceProb (point.samplingRate : ℝ) trace)
  convert hWeighted using 1
  all_goals first | rfl | ring

/-- Second derivative of the exponential tilt. -/
theorem hasDerivAt_fixedEpochCenterTiltDerivative
    (point : PoissonFixedEpochPoint) (h theta : ℝ) :
    HasDerivAt (fixedEpochCenterTiltDerivative point h)
      (fixedEpochCenterTiltSecond point h theta) theta := by
  unfold fixedEpochCenterTiltDerivative fixedEpochCenterTiltSecond
  apply HasDerivAt.fun_sum
  intro trace _htrace
  let coefficient : ℝ :=
    h ^ 2 * ((participationCount trace : ℝ) - point.epoch)
  let offset : ℝ :=
    h ^ 2 * ((participationCount trace : ℝ) - point.epoch) ^ 2 / 2
  have hArgument : HasDerivAt
      (fun current : ℝ => coefficient * current - offset) coefficient theta := by
    simpa only [mul_one] using
      ((hasDerivAt_id' theta).const_mul coefficient).sub_const offset
  have hExp := (Real.hasDerivAt_exp _).comp theta hArgument
  have hWeighted := (hExp.const_mul coefficient).const_mul
    (poissonTraceProb (point.samplingRate : ℝ) trace)
  dsimp [coefficient, offset] at hWeighted ⊢
  convert hWeighted using 1
  all_goals first | rfl | ring

/-- Every non-full fixed-epoch trace has a strictly convex center tilt. -/
theorem fixedEpochCenterTiltSecond_pos
    (point : PoissonFixedEpochPoint) (h theta : ℝ)
    (hNonFull : point.epoch < point.horizon) (hh : 0 < h) :
    0 < fixedEpochCenterTiltSecond point h theta := by
  unfold fixedEpochCenterTiltSecond
  rw [Finset.sum_pos_iff_of_nonneg]
  · refine ⟨trueTrace point.horizon, Finset.mem_univ _, ?_⟩
    have hRatePos : 0 < (point.samplingRate : ℝ) := by
      exact_mod_cast point.samplingRate_pos
    have hTrueWeight : 0 < poissonTraceProb (point.samplingRate : ℝ)
        (trueTrace point.horizon) := by
      unfold poissonTraceProb trueTrace
      apply Finset.prod_pos
      intro i _
      simp only [↓reduceIte, NNReal.coe_pos]
      exact hRatePos
    rw [participationCount_trueTrace]
    have hCentered : 0 < (point.horizon : ℝ) - point.epoch := by
      apply sub_pos.mpr
      exact_mod_cast hNonFull
    positivity
  · intro trace _
    have hRateNonneg : 0 ≤ (point.samplingRate : ℝ) := by positivity
    have hRateUpper : (point.samplingRate : ℝ) ≤ 1 := by
      exact_mod_cast point.samplingRate_le_one
    exact mul_nonneg
      (mul_nonneg (poissonTraceProb_nonneg hRateNonneg hRateUpper trace)
        (sq_nonneg _)) (Real.exp_pos _).le

/-- The finite tilt is strictly convex; this is stronger than the convexity
needed by `gap_pos_of_boundary_nonneg`. -/
theorem fixedEpochCenterTilt_strictConvex
    (point : PoissonFixedEpochPoint) (h : ℝ)
    (hNonFull : point.epoch < point.horizon) (hh : 0 < h) :
    StrictConvexOn ℝ univ (fixedEpochCenterTilt point h) := by
  have hDifferentiable : Differentiable ℝ (fixedEpochCenterTilt point h) :=
    fun theta => (hasDerivAt_fixedEpochCenterTilt point h theta).differentiableAt
  have hDeriv : deriv (fixedEpochCenterTilt point h) =
      fixedEpochCenterTiltDerivative point h := by
    funext theta
    exact (hasDerivAt_fixedEpochCenterTilt point h theta).deriv
  apply strictConvexOn_univ_of_deriv2_pos hDifferentiable.continuous
  intro theta
  change 0 < deriv (deriv (fixedEpochCenterTilt point h)) theta
  rw [hDeriv]
  rw [(hasDerivAt_fixedEpochCenterTiltDerivative point h theta).deriv]
  exact fixedEpochCenterTiltSecond_pos point h theta hNonFull hh

/-- At zero center the non-full tilt is strictly below one. -/
theorem fixedEpochCenterTilt_zero_lt_one
    (point : PoissonFixedEpochPoint) (h : ℝ)
    (hNonFull : point.epoch < point.horizon) (hh : 0 < h) :
    fixedEpochCenterTilt point h 0 < 1 := by
  have hRateNonneg : 0 ≤ (point.samplingRate : ℝ) := by positivity
  have hRateUpper : (point.samplingRate : ℝ) ≤ 1 := by
    exact_mod_cast point.samplingRate_le_one
  have hTermLe (trace : ParticipationTrace point.horizon) :
      poissonTraceProb (point.samplingRate : ℝ) trace *
          Real.exp
            (-h ^ 2 *
              ((participationCount trace : ℝ) - point.epoch) ^ 2 / 2) ≤
        poissonTraceProb (point.samplingRate : ℝ) trace := by
    have hWeight := poissonTraceProb_nonneg hRateNonneg hRateUpper trace
    have hExp : Real.exp
        (-h ^ 2 * ((participationCount trace : ℝ) - point.epoch) ^ 2 / 2) ≤ 1 := by
      rw [Real.exp_le_one_iff]
      nlinarith [sq_nonneg h,
        sq_nonneg ((participationCount trace : ℝ) - point.epoch)]
    nlinarith [mul_le_mul_of_nonneg_left hExp hWeight]
  have hStrict :
      poissonTraceProb (point.samplingRate : ℝ) (trueTrace point.horizon) *
          Real.exp
            (-h ^ 2 *
              ((participationCount (trueTrace point.horizon) : ℝ) -
                point.epoch) ^ 2 / 2) <
        poissonTraceProb (point.samplingRate : ℝ) (trueTrace point.horizon) := by
    have hRatePos : 0 < (point.samplingRate : ℝ) := by
      exact_mod_cast point.samplingRate_pos
    have hTrueWeight : 0 < poissonTraceProb (point.samplingRate : ℝ)
        (trueTrace point.horizon) := by
      unfold poissonTraceProb trueTrace
      apply Finset.prod_pos
      intro i _
      simp only [↓reduceIte, NNReal.coe_pos]
      exact hRatePos
    rw [participationCount_trueTrace]
    have hCentered : 0 < (point.horizon : ℝ) - point.epoch := by
      apply sub_pos.mpr
      exact_mod_cast hNonFull
    have hExp : Real.exp
        (-h ^ 2 * ((point.horizon : ℝ) - point.epoch) ^ 2 / 2) < 1 := by
      rw [Real.exp_lt_one_iff]
      have hhSq : 0 < h ^ 2 := sq_pos_of_pos hh
      have hCenteredSq : 0 < ((point.horizon : ℝ) - point.epoch) ^ 2 :=
        sq_pos_of_pos hCentered
      nlinarith [mul_pos hhSq hCenteredSq]
    nlinarith [mul_lt_mul_of_pos_left hExp hTrueWeight]
  calc
    fixedEpochCenterTilt point h 0 =
        ∑ trace : ParticipationTrace point.horizon,
          poissonTraceProb (point.samplingRate : ℝ) trace *
            Real.exp
              (-h ^ 2 *
                ((participationCount trace : ℝ) - point.epoch) ^ 2 / 2) := by
          unfold fixedEpochCenterTilt
          apply Finset.sum_congr rfl
          intro trace _
          congr 2
          ring
    _ < ∑ trace : ParticipationTrace point.horizon,
          poissonTraceProb (point.samplingRate : ℝ) trace := by
      apply Finset.sum_lt_sum
      · intro trace _
        exact hTermLe trace
      · exact ⟨trueTrace point.horizon, Finset.mem_univ _, hStrict⟩
    _ = 1 := sum_poissonTraceProb_eq_one _

/-- Finite support makes the center gap vanish at the right endpoint. -/
theorem tendsto_fixedEpochCenterGap_atTop_zero
    (point : PoissonFixedEpochPoint) (h : ℝ) (hh : 0 < h) :
    Tendsto (fixedEpochCenterGap point h) atTop (nhds 0) := by
  have hCdfAtBot : Tendsto stdNormalCDFReal atBot (nhds 0) := by
    change Tendsto (ProbabilityTheory.cdf stdNormalMeasure) atBot (nhds 0)
    exact ProbabilityTheory.tendsto_cdf_atBot (μ := stdNormalMeasure)
  have hTrace (trace : ParticipationTrace point.horizon) : Tendsto
      (fun theta : ℝ =>
        poissonTraceProb (point.samplingRate : ℝ) trace *
          stdNormalCDFReal
            (h * ((participationCount trace : ℝ) - point.epoch - theta)))
      atTop (nhds 0) := by
    have hArgument : Tendsto
        (fun theta : ℝ =>
          h * ((participationCount trace : ℝ) - point.epoch - theta))
        atTop atBot := by
      have hLinear : Tendsto (fun theta : ℝ => (-h) * theta) atTop atBot :=
        tendsto_id.const_mul_atTop_of_neg (by linarith)
      have hAffine := tendsto_atBot_add_const_right atTop
        (h * ((participationCount trace : ℝ) - point.epoch)) hLinear
      convert hAffine using 1
      funext theta
      ring
    simpa using (hCdfAtBot.comp hArgument).const_mul
      (poissonTraceProb (point.samplingRate : ℝ) trace)
  have hSum : Tendsto
      (fun theta : ℝ =>
        ∑ trace : ParticipationTrace point.horizon,
          poissonTraceProb (point.samplingRate : ℝ) trace *
            stdNormalCDFReal
              (h * ((participationCount trace : ℝ) - point.epoch - theta)))
      atTop (nhds 0) := by
    simpa using tendsto_finsetSum Finset.univ (fun trace _ => hTrace trace)
  have hBaseArgument : Tendsto (fun theta : ℝ => -h * theta) atTop atBot :=
    tendsto_id.const_mul_atTop_of_neg (by linarith)
  have hBase : Tendsto (fun theta : ℝ => stdNormalCDFReal (-h * theta))
      atTop (nhds 0) := hCdfAtBot.comp hBaseArgument
  unfold fixedEpochCenterGap
  simpa only [sub_zero, neg_mul] using hSum.sub hBase

/-- Abstract shape lemma isolated from the finite Gaussian trace.  Convexity
of the exponential tilt, its strict deficit at zero, the exact derivative
sign, and the vanishing right endpoint are the only inputs. -/
theorem gap_pos_of_boundary_nonneg
    (gap tilt positiveFactor : ℝ → ℝ) (boundary query : ℝ)
    (hBoundaryNonneg : 0 ≤ boundary)
    (hBoundaryQuery : boundary < query)
    (hTiltConvex : ConvexOn ℝ (Ici 0) tilt)
    (hTiltZero : tilt 0 < 1)
    (hFactor : ∀ x, 0 < positiveFactor x)
    (hGapDeriv : ∀ x,
      HasDerivAt gap (positiveFactor x * (1 - tilt x)) x)
    (hGapBoundary : 0 ≤ gap boundary)
    (hGapLimit : Tendsto gap atTop (nhds 0)) :
    0 < gap query := by
  have hBoundaryPos : 0 < query := hBoundaryNonneg.trans_lt hBoundaryQuery
  by_cases hQueryTilt : tilt query < 1
  · have hTiltLt : ∀ x ∈ Icc boundary query, tilt x < 1 := by
      intro x hx
      have hx0 : 0 ≤ x := hBoundaryNonneg.trans hx.1
      rcases eq_or_lt_of_le hx.2 with rfl | hxQuery
      · exact hQueryTilt
      rcases eq_or_lt_of_le hx0 with rfl | hxPos
      · exact hTiltZero
      · have hSecant := hTiltConvex.secant_mono_aux1
          (x := 0) (y := x) (z := query)
          (by simp) (by exact hBoundaryPos.le) hxPos hxQuery
        nlinarith
    have hGapContinuous : ContinuousOn gap (Icc boundary query) :=
      (continuous_iff_continuousAt.mpr fun x => (hGapDeriv x).continuousAt).continuousOn
    have hStrictMono : StrictMonoOn gap (Icc boundary query) := by
      apply strictMonoOn_of_hasDerivWithinAt_pos (convex_Icc boundary query)
        hGapContinuous
      · intro x _hx
        exact (hGapDeriv x).hasDerivWithinAt
      · intro x hx
        rw [interior_Icc] at hx
        exact mul_pos (hFactor x) (sub_pos.mpr (hTiltLt x ⟨hx.1.le, hx.2.le⟩))
    exact lt_of_le_of_lt hGapBoundary
      (hStrictMono ⟨le_rfl, hBoundaryQuery.le⟩ ⟨hBoundaryQuery.le, le_rfl⟩
        hBoundaryQuery)
  · have hTiltQuery : 1 ≤ tilt query := le_of_not_gt hQueryTilt
    have hTiltGt : ∀ x, query < x → 1 < tilt x := by
      intro x hQueryX
      have hSecant := hTiltConvex.secant_mono_aux1
        (x := 0) (y := query) (z := x)
        (by simp) (by simp; linarith) hBoundaryPos hQueryX
      nlinarith
    have hGapContinuousOn (upper : ℝ) (hUpper : query < upper) :
        ContinuousOn gap (Icc query upper) :=
      (continuous_iff_continuousAt.mpr fun x => (hGapDeriv x).continuousAt).continuousOn
    have hStrictAntiOn (upper : ℝ) (hUpper : query < upper) :
        StrictAntiOn gap (Icc query upper) := by
      apply strictAntiOn_of_hasDerivWithinAt_neg (convex_Icc query upper)
        (hGapContinuousOn upper hUpper)
      · intro x _hx
        exact (hGapDeriv x).hasDerivWithinAt
      · intro x hx
        rw [interior_Icc] at hx
        exact mul_neg_of_pos_of_neg (hFactor x)
          (sub_neg.mpr (hTiltGt x hx.1))
    have hTailLower (upper : ℝ) (hUpper : query + 1 < upper) :
        gap upper < gap (query + 1) := by
      exact hStrictAntiOn upper (by linarith)
        ⟨by linarith, hUpper.le⟩ ⟨by linarith, le_rfl⟩
        hUpper
    have hGapOneNonneg : 0 ≤ gap (query + 1) := by
      apply le_of_tendsto hGapLimit
      filter_upwards [eventually_gt_atTop (query + 1)] with upper hUpper
      exact (hTailLower upper hUpper).le
    have hQueryGtOne : gap (query + 1) < gap query := by
      exact hStrictAntiOn (query + 1) (by linarith)
        ⟨le_rfl, by linarith⟩ ⟨by linarith, le_rfl⟩ (by linarith)
    exact hGapOneNonneg.trans_lt hQueryGtOne

/-- Fixed-`h` center propagation for the exact finite trace.  A nonnegative
gap at one nonnegative boundary center becomes a strict positive gap at every
larger center. -/
theorem fixedEpochCenterGap_pos_of_boundary_nonneg
    (point : PoissonFixedEpochPoint) (h boundary query : ℝ)
    (hNonFull : point.epoch < point.horizon) (hh : 0 < h)
    (hBoundaryNonneg : 0 ≤ boundary) (hBoundaryQuery : boundary < query)
    (hBoundaryGap : 0 ≤ fixedEpochCenterGap point h boundary) :
    0 < fixedEpochCenterGap point h query := by
  apply gap_pos_of_boundary_nonneg
    (fixedEpochCenterGap point h)
    (fixedEpochCenterTilt point h)
    (fun theta => h * stdNormalPdfReal (h * theta))
    boundary query hBoundaryNonneg hBoundaryQuery
  · exact (fixedEpochCenterTilt_strictConvex point h hNonFull hh).convexOn.subset
      (by simp) (convex_Ici 0)
  · exact fixedEpochCenterTilt_zero_lt_one point h hNonFull hh
  · intro theta
    exact mul_pos hh (stdNormalPdfReal_pos _)
  · exact hasDerivAt_fixedEpochCenterGap point h
  · exact hBoundaryGap
  · exact tendsto_fixedEpochCenterGap_atTop_zero point h hh

/-- The abstract center gap is exactly the existing Gaussian count-test gap
after expressing the positive center distance in count-step units. -/
theorem fixedEpochCenterGap_eq_countTestAverage_sub
    (point : PoissonFixedEpochPoint) (centerDistance : Real)
    (signal : NNReal) (hSignal : 0 < signal) :
    fixedEpochCenterGap point ((signal : Real) / point.epoch)
        ((point.epoch : Real) * centerDistance / (signal : Real)) =
      poissonTraceCountAverage point.horizon point.samplingRate
          (fixedEpochGaussianCountTest point (-centerDistance) signal) -
        stdNormalCDFReal (-centerDistance) := by
  have hEpoch : (point.epoch : Real) ≠ 0 := by
    exact_mod_cast point.epoch_pos.ne'
  have hSignalReal : (signal : Real) ≠ 0 := by
    exact_mod_cast hSignal.ne'
  unfold fixedEpochCenterGap poissonTraceCountAverage fixedEpochGaussianCountTest
  have hBase :
      -((signal : Real) / point.epoch) *
          ((point.epoch : Real) * centerDistance / (signal : Real)) =
        -centerDistance := by
    field_simp [hEpoch, hSignalReal]
  rw [hBase]
  apply congrArg (fun value : Real ↦ value - stdNormalCDFReal (-centerDistance))
  apply Finset.sum_congr rfl
  intro trace _hTrace
  congr 2
  field_simp [hEpoch, hSignalReal]
  ring

end Mf.DP
