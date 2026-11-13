import Mf.DP.FiniteGaussianPrivacy
import Mf.DP.BSRGaussianCore

/-!
# Historical analytic Gaussian interface

The generic proof implementation is owned by `Mf.DP.FiniteGaussianPrivacy`.
This facade preserves existing names and the BSR mean-map consumers; new
mechanisms can import the neutral Gaussian pair owner directly.
-/

namespace Mf.DP
noncomputable section

abbrev analyticGaussianCondition := @Mf.DP.FiniteGaussianPrivacy.analyticGaussianCondition

@[simp] theorem analyticGaussianCondition_iff :
    ∀ (Δ σ ε δ : ℝ),
    analyticGaussianCondition Δ σ ε δ ↔ analyticGaussianExpr Δ σ ε ≤ δ :=
  @Mf.DP.FiniteGaussianPrivacy.analyticGaussianCondition_iff

theorem analyticGaussianCondition_mono_delta :
    ∀ {Δ σ ε δ₀ δ : ℝ}
    (h : analyticGaussianCondition Δ σ ε δ₀)
    (hδ : δ₀ ≤ δ),
    analyticGaussianCondition Δ σ ε δ :=
  @Mf.DP.FiniteGaussianPrivacy.analyticGaussianCondition_mono_delta

theorem analyticGaussianCondition_of_le :
    ∀ {Δ σ ε δ₀ δ : ℝ}
    (hδ : δ₀ ≤ δ)
    (h : analyticGaussianCondition Δ σ ε δ₀),
    analyticGaussianCondition Δ σ ε δ :=
  @Mf.DP.FiniteGaussianPrivacy.analyticGaussianCondition_of_le

theorem analyticGaussianCondition_of_one_le :
    ∀ {Δ σ ε δ : ℝ}
    (hδ : 1 ≤ δ),
    analyticGaussianCondition Δ σ ε δ :=
  @Mf.DP.FiniteGaussianPrivacy.analyticGaussianCondition_of_one_le

theorem analyticGaussianCondition_implies_neg_exp_le_delta :
    ∀ {Δ σ ε δ : ℝ}
    (h : analyticGaussianCondition Δ σ ε δ),
    -Real.exp ε ≤ δ :=
  @Mf.DP.FiniteGaussianPrivacy.analyticGaussianCondition_implies_neg_exp_le_delta

theorem analyticGaussianCondition_iff_event_form :
    ∀ (Δ σ ε δ : ℝ),
    analyticGaussianCondition Δ σ ε δ
          ↔ stdNormalMeasure.real (Set.Iic (privacyLossArgPlus Δ σ ε))
                - Real.exp ε
                    * stdNormalMeasure.real (Set.Iic (privacyLossArgMinus Δ σ ε))
          ≤ δ :=
  @Mf.DP.FiniteGaussianPrivacy.analyticGaussianCondition_iff_event_form

theorem analyticGaussianCondition_iff_bsrGaussianMeasure_eval_event_form :
    ∀ {n : ℕ} (i : Fin n)
    (Δ σ ε δ : ℝ)
    (hσ : 0 < σ),
    analyticGaussianCondition Δ σ ε δ
      ↔ (bsrGaussianMeasure σ (fun _ : Fin n => Δ / 2)).real
            (Function.eval i ⁻¹' Set.Iic (privacyEventThresholdPlus Δ σ ε))
          - Real.exp ε
              * (bsrGaussianMeasure σ (fun _ : Fin n => -Δ / 2)).real
                  (Function.eval i ⁻¹' Set.Iic (privacyEventThresholdMinus Δ σ ε))
        ≤ δ :=
  @Mf.DP.FiniteGaussianPrivacy.analyticGaussianCondition_iff_measure_eval_event_form

theorem analyticGaussianCondition_iff_gaussianReal_event_form :
    ∀ (Δ σ ε δ : ℝ)
    (hσ : 0 < σ),
    analyticGaussianCondition Δ σ ε δ
          ↔ (ProbabilityTheory.gaussianReal (Δ / 2) (⟨σ ^ 2, sq_nonneg σ⟩)).real
                (Set.Iic (privacyEventThresholdPlus Δ σ ε))
              - Real.exp ε
                  * (ProbabilityTheory.gaussianReal (-Δ / 2) (⟨σ ^ 2, sq_nonneg σ⟩)).real
                      (Set.Iic (privacyEventThresholdMinus Δ σ ε))
            ≤ δ :=
  @Mf.DP.FiniteGaussianPrivacy.analyticGaussianCondition_iff_gaussianReal_event_form

theorem analyticGaussianCondition_iff_gaussianReal_event_form_explicit :
    ∀ (Δ σ ε δ : ℝ)
    (hσ : 0 < σ),
    analyticGaussianCondition Δ σ ε δ
          ↔ (ProbabilityTheory.gaussianReal (Δ / 2) (⟨σ ^ 2, sq_nonneg σ⟩)).real
                (Set.Iic (Δ - (ε * σ ^ 2) / Δ))
              - Real.exp ε
                  * (ProbabilityTheory.gaussianReal (-Δ / 2) (⟨σ ^ 2, sq_nonneg σ⟩)).real
                      (Set.Iic (-Δ - (ε * σ ^ 2) / Δ))
            ≤ δ :=
  @Mf.DP.FiniteGaussianPrivacy.analyticGaussianCondition_iff_gaussianReal_event_form_explicit

theorem explicitGaussianEventBound_iff_gaussianReal_eventBound_explicit :
    ∀ (Δ σ ε δ : ℝ)
    (hσ : 0 < σ),
    (stdNormalMeasure.real (Set.Iic (privacyLossArgPlus Δ σ ε))
      - Real.exp ε * stdNormalMeasure.real (Set.Iic (privacyLossArgMinus Δ σ ε))
      ≤ δ)
      ↔
        (ProbabilityTheory.gaussianReal (Δ / 2) (⟨σ ^ 2, sq_nonneg σ⟩)).real
              (Set.Iic (Δ - (ε * σ ^ 2) / Δ))
            - Real.exp ε
                * (ProbabilityTheory.gaussianReal (-Δ / 2) (⟨σ ^ 2, sq_nonneg σ⟩)).real
                    (Set.Iic (-Δ - (ε * σ ^ 2) / Δ))
          ≤ δ :=
  @Mf.DP.FiniteGaussianPrivacy.explicitGaussianEventBound_iff_gaussianReal_eventBound_explicit

theorem privacyLossArgPlus_two_sqrt :
    ∀ (r σ ε : ℝ)
    (hσ : 0 < σ)
    (hr : 0 < r),
    privacyLossArgPlus (2 * Real.sqrt r) σ ε
      = Real.sqrt r / σ - (ε * σ) / (2 * Real.sqrt r) :=
  @Mf.DP.FiniteGaussianPrivacy.privacyLossArgPlus_two_sqrt

theorem privacyLossArgMinus_two_sqrt :
    ∀ (r σ ε : ℝ)
    (hσ : 0 < σ)
    (hr : 0 < r),
    privacyLossArgMinus (2 * Real.sqrt r) σ ε
      = -Real.sqrt r / σ - (ε * σ) / (2 * Real.sqrt r) :=
  @Mf.DP.FiniteGaussianPrivacy.privacyLossArgMinus_two_sqrt

theorem gaussianReal_event_plus_eq_stdNormal :
    ∀ (r σ ε : ℝ)
    (hσ : 0 < σ)
    (hr : 0 < r),
    (ProbabilityTheory.gaussianReal (-r)
      (⟨σ ^ 2 * r, mul_nonneg (sq_nonneg σ) (le_of_lt hr)⟩)).real
      (Set.Iic (-(centeredDotThreshold σ ε)))
      =
    stdNormalMeasure.real (Set.Iic (privacyLossArgPlus (2 * Real.sqrt r) σ ε)) :=
  @Mf.DP.FiniteGaussianPrivacy.gaussianReal_event_plus_eq_stdNormal

theorem gaussianReal_event_minus_eq_stdNormal :
    ∀ (r σ ε : ℝ)
    (hσ : 0 < σ)
    (hr : 0 < r),
    (ProbabilityTheory.gaussianReal r
      (⟨σ ^ 2 * r, mul_nonneg (sq_nonneg σ) (le_of_lt hr)⟩)).real
      (Set.Iic (-(centeredDotThreshold σ ε)))
      =
    stdNormalMeasure.real (Set.Iic (privacyLossArgMinus (2 * Real.sqrt r) σ ε)) :=
  @Mf.DP.FiniteGaussianPrivacy.gaussianReal_event_minus_eq_stdNormal

theorem explicitEventBound_two_sqrt_iff_centeredGaussianEventBound :
    ∀ (r σ ε δ : ℝ)
    (hσ : 0 < σ)
    (hr : 0 < r),
    (stdNormalMeasure.real (Set.Iic (privacyLossArgPlus (2 * Real.sqrt r) σ ε))
      - Real.exp ε * stdNormalMeasure.real (Set.Iic (privacyLossArgMinus (2 * Real.sqrt r) σ ε))
      ≤ δ)
      ↔
        ((ProbabilityTheory.gaussianReal (-r)
          (⟨σ ^ 2 * r, mul_nonneg (sq_nonneg σ) (le_of_lt hr)⟩)).real
          (Set.Iic (-(centeredDotThreshold σ ε)))
          - Real.exp ε
              * (ProbabilityTheory.gaussianReal r
                (⟨σ ^ 2 * r, mul_nonneg (sq_nonneg σ) (le_of_lt hr)⟩)).real
                (Set.Iic (-(centeredDotThreshold σ ε)))
          ≤ δ) :=
  @Mf.DP.FiniteGaussianPrivacy.explicitEventBound_two_sqrt_iff_centeredGaussianEventBound

abbrev bridgeU := @Mf.DP.FiniteGaussianPrivacy.bridgeU

abbrev bridgeV := @Mf.DP.FiniteGaussianPrivacy.bridgeV

abbrev bridgeProfile := @Mf.DP.FiniteGaussianPrivacy.bridgeProfile

theorem bridgeV_sq_sub_bridgeU_sq :
    ∀ (a ε : ℝ)
    (ha : a ≠ 0),
    (bridgeV a ε) ^ 2 - (bridgeU a ε) ^ 2 = 2 * ε :=
  @Mf.DP.FiniteGaussianPrivacy.bridgeV_sq_sub_bridgeU_sq

theorem exp_eps_mul_stdNormalPdf_bridgeV_eq_stdNormalPdf_bridgeU :
    ∀ (a ε : ℝ)
    (ha : a ≠ 0),
    Real.exp ε * stdNormalPdfReal (bridgeV a ε) = stdNormalPdfReal (bridgeU a ε) :=
  @Mf.DP.FiniteGaussianPrivacy.exp_eps_mul_stdNormalPdf_bridgeV_eq_stdNormalPdf_bridgeU

theorem hasDerivAt_bridgeU :
    ∀ (ε x : ℝ) (hx : x ≠ 0),
    HasDerivAt (fun a : ℝ => bridgeU a ε) (1 + ε / (2 * x ^ 2)) x :=
  @Mf.DP.FiniteGaussianPrivacy.hasDerivAt_bridgeU

theorem hasDerivAt_bridgeV :
    ∀ (ε x : ℝ) (hx : x ≠ 0),
    HasDerivAt (fun a : ℝ => bridgeV a ε) (-1 + ε / (2 * x ^ 2)) x :=
  @Mf.DP.FiniteGaussianPrivacy.hasDerivAt_bridgeV

theorem hasDerivAt_bridgeProfile :
    ∀ (ε x : ℝ) (hx : x ≠ 0),
    HasDerivAt (fun a : ℝ => bridgeProfile a ε) (2 * stdNormalPdfReal (bridgeU x ε)) x :=
  @Mf.DP.FiniteGaussianPrivacy.hasDerivAt_bridgeProfile

theorem deriv_bridgeProfile :
    ∀ (ε x : ℝ) (hx : x ≠ 0),
    deriv (fun a : ℝ => bridgeProfile a ε) x = 2 * stdNormalPdfReal (bridgeU x ε) :=
  @Mf.DP.FiniteGaussianPrivacy.deriv_bridgeProfile

theorem strictMonoOn_bridgeProfile :
    ∀ (ε : ℝ),
    StrictMonoOn (fun a : ℝ => bridgeProfile a ε) (Set.Ioi 0) :=
  @Mf.DP.FiniteGaussianPrivacy.strictMonoOn_bridgeProfile

theorem privacyLossArgPlus_eq_bridgeU :
    ∀ (Δ σ ε : ℝ)
    (hσ : 0 < σ)
    (hΔ : Δ ≠ 0),
    privacyLossArgPlus Δ σ ε = bridgeU (Δ / (2 * σ)) ε :=
  @Mf.DP.FiniteGaussianPrivacy.privacyLossArgPlus_eq_bridgeU

theorem privacyLossArgMinus_eq_bridgeV :
    ∀ (Δ σ ε : ℝ)
    (hσ : 0 < σ)
    (hΔ : Δ ≠ 0),
    privacyLossArgMinus Δ σ ε = bridgeV (Δ / (2 * σ)) ε :=
  @Mf.DP.FiniteGaussianPrivacy.privacyLossArgMinus_eq_bridgeV

theorem explicitEventExpr_eq_bridgeProfile :
    ∀ (Δ σ ε : ℝ)
    (hσ : 0 < σ)
    (hΔ : Δ ≠ 0),
    (stdNormalMeasure.real (Set.Iic (privacyLossArgPlus Δ σ ε))
      - Real.exp ε * stdNormalMeasure.real (Set.Iic (privacyLossArgMinus Δ σ ε)))
      = bridgeProfile (Δ / (2 * σ)) ε :=
  @Mf.DP.FiniteGaussianPrivacy.explicitEventExpr_eq_bridgeProfile

theorem explicitEventExpr_two_sqrt_eq_bridgeProfile :
    ∀ (r σ ε : ℝ)
    (hσ : 0 < σ)
    (hr : 0 < r),
    (stdNormalMeasure.real (Set.Iic (privacyLossArgPlus (2 * Real.sqrt r) σ ε))
      - Real.exp ε * stdNormalMeasure.real (Set.Iic (privacyLossArgMinus (2 * Real.sqrt r) σ ε)))
      = bridgeProfile (Real.sqrt r / σ) ε :=
  @Mf.DP.FiniteGaussianPrivacy.explicitEventExpr_two_sqrt_eq_bridgeProfile

theorem explicitEventExpr_two_sqrt_le_of_le :
    ∀ (r Δ σ ε : ℝ)
    (hσ : 0 < σ)
    (hr : 0 < r)
    (hΔ : 0 < Δ)
    (hrad : r ≤ (Δ / 2) ^ 2),
    (stdNormalMeasure.real (Set.Iic (privacyLossArgPlus (2 * Real.sqrt r) σ ε))
      - Real.exp ε * stdNormalMeasure.real (Set.Iic (privacyLossArgMinus (2 * Real.sqrt r) σ ε)))
    ≤
    (stdNormalMeasure.real (Set.Iic (privacyLossArgPlus Δ σ ε))
      - Real.exp ε * stdNormalMeasure.real (Set.Iic (privacyLossArgMinus Δ σ ε))) :=
  @Mf.DP.FiniteGaussianPrivacy.explicitEventExpr_two_sqrt_le_of_le

theorem explicitEventExpr_two_sqrt_le_of_le_nonneg :
    ∀ (r Δ σ ε : ℝ)
    (hσ : 0 < σ)
    (hr : 0 < r)
    (hΔ0 : 0 ≤ Δ)
    (hrad : r ≤ (Δ / 2) ^ 2),
    (stdNormalMeasure.real (Set.Iic (privacyLossArgPlus (2 * Real.sqrt r) σ ε))
      - Real.exp ε * stdNormalMeasure.real (Set.Iic (privacyLossArgMinus (2 * Real.sqrt r) σ ε)))
    ≤
    (stdNormalMeasure.real (Set.Iic (privacyLossArgPlus Δ σ ε))
      - Real.exp ε * stdNormalMeasure.real (Set.Iic (privacyLossArgMinus Δ σ ε))) :=
  @Mf.DP.FiniteGaussianPrivacy.explicitEventExpr_two_sqrt_le_of_le_nonneg

theorem centered_posRegion_gap_eq_explicitEventExpr_two_sqrt :
    ∀ {n : ℕ}
    (d : BSROutput n)
    (r σ ε : ℝ)
    (hσ : 0 < σ)
    (hr : 0 < r)
    (hrEq : r = bsrSqDist d (fun _ => (0 : ℝ))),
    (bsrGaussianMeasure σ d).real
        (posRegion
          (fun y : BSROutput n =>
            bsrGaussianDensity σ d y
              - Real.exp ε * bsrGaussianDensity σ (fun i => -d i) y))
      - Real.exp ε
          * (bsrGaussianMeasure σ (fun i => -d i)).real
              (posRegion
                (fun y : BSROutput n =>
                  bsrGaussianDensity σ d y
                    - Real.exp ε * bsrGaussianDensity σ (fun i => -d i) y))
    =
      (stdNormalMeasure.real
          (Set.Iic (privacyLossArgPlus (2 * Real.sqrt r) σ ε))
        - Real.exp ε
            * stdNormalMeasure.real
                (Set.Iic (privacyLossArgMinus (2 * Real.sqrt r) σ ε))) :=
  @Mf.DP.FiniteGaussianPrivacy.centered_posRegion_gap_eq_explicitEventExpr_two_sqrt

theorem explicitEventExpr_at_centerRadius_le_of_explicitBound :
    ∀ {n : ℕ}
    (d : BSROutput n)
    (Δ σ ε δ r : ℝ)
    (hσ : 0 < σ)
    (hΔ0 : 0 ≤ Δ)
    (hrEq : r = bsrSqDist d (fun _ => (0 : ℝ)))
    (hr : 0 < r)
    (hdist : bsrSqDist d (fun _ => (0 : ℝ)) ≤ (Δ / 2) ^ 2)
    (hExplicit :
      stdNormalMeasure.real (Set.Iic (privacyLossArgPlus Δ σ ε))
        - Real.exp ε * stdNormalMeasure.real (Set.Iic (privacyLossArgMinus Δ σ ε))
      ≤ δ),
    stdNormalMeasure.real (Set.Iic (privacyLossArgPlus (2 * Real.sqrt r) σ ε))
      - Real.exp ε * stdNormalMeasure.real (Set.Iic (privacyLossArgMinus (2 * Real.sqrt r) σ ε))
      ≤ δ :=
  @Mf.DP.FiniteGaussianPrivacy.explicitEventExpr_at_centerRadius_le_of_explicitBound

theorem centered_posRegion_gap_le_of_explicitBound_of_posRadius :
    ∀ {n : ℕ}
    (d : BSROutput n)
    (Δ σ ε δ r : ℝ)
    (hσ : 0 < σ)
    (hΔ0 : 0 ≤ Δ)
    (hrEq : r = bsrSqDist d (fun _ => (0 : ℝ)))
    (hr : 0 < r)
    (hdist : bsrSqDist d (fun _ => (0 : ℝ)) ≤ (Δ / 2) ^ 2)
    (hExplicit :
      stdNormalMeasure.real (Set.Iic (privacyLossArgPlus Δ σ ε))
        - Real.exp ε * stdNormalMeasure.real (Set.Iic (privacyLossArgMinus Δ σ ε))
      ≤ δ),
    (bsrGaussianMeasure σ d).real
        (posRegion
          (fun y : BSROutput n =>
            bsrGaussianDensity σ d y
              - Real.exp ε * bsrGaussianDensity σ (fun i => -d i) y))
      - Real.exp ε
          * (bsrGaussianMeasure σ (fun i => -d i)).real
              (posRegion
                (fun y : BSROutput n =>
                  bsrGaussianDensity σ d y
                    - Real.exp ε * bsrGaussianDensity σ (fun i => -d i) y))
      ≤ δ :=
  @Mf.DP.FiniteGaussianPrivacy.centered_posRegion_gap_le_of_explicitBound_of_posRadius

theorem centered_posRegion_gap_le_of_explicitBound_of_posDist :
    ∀ {n : ℕ}
    (d : BSROutput n)
    (Δ σ ε δ : ℝ)
    (hσ : 0 < σ)
    (hΔ0 : 0 ≤ Δ)
    (hdist : bsrSqDist d (fun _ => (0 : ℝ)) ≤ (Δ / 2) ^ 2)
    (hExplicit :
      stdNormalMeasure.real (Set.Iic (privacyLossArgPlus Δ σ ε))
        - Real.exp ε * stdNormalMeasure.real (Set.Iic (privacyLossArgMinus Δ σ ε))
      ≤ δ)
    (hpos : 0 < bsrSqDist d (fun _ => (0 : ℝ))),
    (bsrGaussianMeasure σ d).real
        (posRegion
          (fun y : BSROutput n =>
            bsrGaussianDensity σ d y
              - Real.exp ε * bsrGaussianDensity σ (fun i => -d i) y))
      - Real.exp ε
          * (bsrGaussianMeasure σ (fun i => -d i)).real
              (posRegion
                (fun y : BSROutput n =>
                  bsrGaussianDensity σ d y
                    - Real.exp ε * bsrGaussianDensity σ (fun i => -d i) y))
      ≤ δ :=
  @Mf.DP.FiniteGaussianPrivacy.centered_posRegion_gap_le_of_explicitBound_of_posDist

theorem centered_posRegion_gap_le_of_privacyLossEventBound_of_posDist :
    ∀ {n : ℕ}
    (d : BSROutput n)
    (Δ σ ε δ : ℝ)
    (hσ : 0 < σ)
    (hΔ0 : 0 ≤ Δ)
    (hdist : bsrSqDist d (fun _ => (0 : ℝ)) ≤ (Δ / 2) ^ 2)
    (hEvent :
      stdNormalMeasure.real (Set.Iic (privacyLossArgPlus Δ σ ε))
        - Real.exp ε * stdNormalMeasure.real (Set.Iic (privacyLossArgMinus Δ σ ε))
      ≤ δ)
    (hpos : 0 < bsrSqDist d (fun _ => (0 : ℝ))),
    (bsrGaussianMeasure σ d).real
        (posRegion
          (fun y : BSROutput n =>
            bsrGaussianDensity σ d y
              - Real.exp ε * bsrGaussianDensity σ (fun i => -d i) y))
      - Real.exp ε
          * (bsrGaussianMeasure σ (fun i => -d i)).real
              (posRegion
                (fun y : BSROutput n =>
                  bsrGaussianDensity σ d y
                    - Real.exp ε * bsrGaussianDensity σ (fun i => -d i) y))
      ≤ δ :=
  @Mf.DP.FiniteGaussianPrivacy.centered_posRegion_gap_le_of_privacyLossEventBound_of_posDist

theorem centered_posRegion_gap_le_of_analyticGaussianCondition_of_posDist :
    ∀ {n : ℕ}
    (d : BSROutput n)
    (Δ σ ε δ : ℝ)
    (hσ : 0 < σ)
    (hΔ0 : 0 ≤ Δ)
    (hdist : bsrSqDist d (fun _ => (0 : ℝ)) ≤ (Δ / 2) ^ 2)
    (hAnalytic : analyticGaussianCondition Δ σ ε δ)
    (hpos : 0 < bsrSqDist d (fun _ => (0 : ℝ))),
    (bsrGaussianMeasure σ d).real
        (posRegion
          (fun y : BSROutput n =>
            bsrGaussianDensity σ d y
              - Real.exp ε * bsrGaussianDensity σ (fun i => -d i) y))
      - Real.exp ε
          * (bsrGaussianMeasure σ (fun i => -d i)).real
              (posRegion
                (fun y : BSROutput n =>
                  bsrGaussianDensity σ d y
                    - Real.exp ε * bsrGaussianDensity σ (fun i => -d i) y))
      ≤ δ :=
  @Mf.DP.FiniteGaussianPrivacy.centered_posRegion_gap_le_of_analyticGaussianCondition_of_posDist

theorem signedMeasure_le_of_hahn_cap :
    ∀ {α : Type*}
    [MeasurableSpace α]
    (s : MeasureTheory.SignedMeasure α)
    (i : Set α)
    (δ : ℝ)
    (hi : MeasurableSet i)
    (hpos : ∀ ⦃j : Set α⦄, MeasurableSet j → j ⊆ i → 0 ≤ s j)
    (hneg : ∀ ⦃j : Set α⦄, MeasurableSet j → j ⊆ iᶜ → s j ≤ 0)
    (hcap : s i ≤ δ),
    ∀ t, MeasurableSet t → s t ≤ δ :=
  @Mf.DP.FiniteGaussianPrivacy.signedMeasure_le_of_hahn_cap

theorem measure_event_le_of_signed_gap_le :
    ∀ {α : Type*}
    [MeasurableSpace α]
    (μ ν : MeasureTheory.Measure α)
    [MeasureTheory.IsFiniteMeasure μ]
    [MeasureTheory.IsFiniteMeasure ν]
    (ε δ : ℝ)
    {t : Set α}
    (hgap : (μ.real t - Real.exp ε * ν.real t) ≤ δ),
    μ t ≤ ENNReal.ofReal (Real.exp ε) * ν t + ENNReal.ofReal δ :=
  @Mf.DP.FiniteGaussianPrivacy.measure_event_le_of_signed_gap_le

theorem centered_signed_gap_eq :
    ∀ {n : ℕ}
    (d : BSROutput n)
    (σ ε : ℝ)
    (s : Set (BSROutput n))
    (hs : MeasurableSet s),
    let c : NNReal := ⟨Real.exp ε, le_of_lt (Real.exp_pos ε)⟩
    ((bsrGaussianMeasure σ d).toSignedMeasure
      - ((c • bsrGaussianMeasure σ (fun i => -d i)).toSignedMeasure)) s
    =
    (bsrGaussianMeasure σ d).real s
        - Real.exp ε * (bsrGaussianMeasure σ (fun i => -d i)).real s :=
  @Mf.DP.FiniteGaussianPrivacy.centered_signed_gap_eq

theorem gaussianPair_centered_eventApproxDP_of_posRegion_hahn_cap :
    ∀ {n : ℕ}
    (d : BSROutput n)
    (σ ε δ : ℝ)
    (hpos :
      ∀ ⦃j : Set (BSROutput n)⦄, MeasurableSet j →
        j ⊆ posRegion
          (fun y : BSROutput n =>
            bsrGaussianDensity σ d y
              - Real.exp ε * bsrGaussianDensity σ (fun i => -d i) y) →
        0 ≤ (bsrGaussianMeasure σ d).real j
          - Real.exp ε * (bsrGaussianMeasure σ (fun i => -d i)).real j)
    (hneg :
      ∀ ⦃j : Set (BSROutput n)⦄, MeasurableSet j →
        j ⊆ (posRegion
          (fun y : BSROutput n =>
            bsrGaussianDensity σ d y
              - Real.exp ε * bsrGaussianDensity σ (fun i => -d i) y))ᶜ →
        (bsrGaussianMeasure σ d).real j
          - Real.exp ε * (bsrGaussianMeasure σ (fun i => -d i)).real j ≤ 0)
    (hcap :
      (bsrGaussianMeasure σ d).real
          (posRegion
            (fun y : BSROutput n =>
              bsrGaussianDensity σ d y
                - Real.exp ε * bsrGaussianDensity σ (fun i => -d i) y))
        - Real.exp ε
            * (bsrGaussianMeasure σ (fun i => -d i)).real
                (posRegion
                  (fun y : BSROutput n =>
                    bsrGaussianDensity σ d y
                      - Real.exp ε * bsrGaussianDensity σ (fun i => -d i) y))
      ≤ δ),
    ∀ s, MeasurableSet s →
      bsrGaussianMeasure σ d s
        ≤ ENNReal.ofReal (Real.exp ε) * bsrGaussianMeasure σ (fun i => -d i) s
            + ENNReal.ofReal δ :=
  @Mf.DP.FiniteGaussianPrivacy.gaussianPair_centered_eventApproxDP_of_posRegion_hahn_cap

theorem gaussianPair_centered_of_explicitGaussianEventBound_of_posDist_of_hahn :
    ∀ {n : ℕ}
    (d : BSROutput n)
    (Δ σ ε δ : ℝ)
    (hσ : 0 < σ)
    (hΔ0 : 0 ≤ Δ)
    (hdist : bsrSqDist d (fun _ => (0 : ℝ)) ≤ (Δ / 2) ^ 2)
    (hExplicit :
      stdNormalMeasure.real (Set.Iic (privacyLossArgPlus Δ σ ε))
        - Real.exp ε * stdNormalMeasure.real (Set.Iic (privacyLossArgMinus Δ σ ε))
      ≤ δ)
    (hposDist : 0 < bsrSqDist d (fun _ => (0 : ℝ)))
    (hpos :
      ∀ ⦃j : Set (BSROutput n)⦄, MeasurableSet j →
        j ⊆ posRegion
          (fun y : BSROutput n =>
            bsrGaussianDensity σ d y
              - Real.exp ε * bsrGaussianDensity σ (fun i => -d i) y) →
        0 ≤ (bsrGaussianMeasure σ d).real j
          - Real.exp ε * (bsrGaussianMeasure σ (fun i => -d i)).real j)
    (hneg :
      ∀ ⦃j : Set (BSROutput n)⦄, MeasurableSet j →
        j ⊆ (posRegion
          (fun y : BSROutput n =>
            bsrGaussianDensity σ d y
              - Real.exp ε * bsrGaussianDensity σ (fun i => -d i) y))ᶜ →
        (bsrGaussianMeasure σ d).real j
          - Real.exp ε * (bsrGaussianMeasure σ (fun i => -d i)).real j ≤ 0),
    ∀ s, MeasurableSet s →
      bsrGaussianMeasure σ d s
        ≤ ENNReal.ofReal (Real.exp ε) * bsrGaussianMeasure σ (fun i => -d i) s
            + ENNReal.ofReal δ :=
  @Mf.DP.FiniteGaussianPrivacy.gaussianPair_centered_of_explicitGaussianEventBound_of_posDist_of_hahn

theorem gaussianPair_centered_of_explicitGaussianEventBound_of_hahn_split :
    ∀ {n : ℕ}
    (d : BSROutput n)
    (Δ σ ε δ : ℝ)
    (hσ : 0 < σ)
    (hΔ0 : 0 ≤ Δ)
    (hdist : bsrSqDist d (fun _ => (0 : ℝ)) ≤ (Δ / 2) ^ 2)
    (hExplicit :
      stdNormalMeasure.real (Set.Iic (privacyLossArgPlus Δ σ ε))
        - Real.exp ε * stdNormalMeasure.real (Set.Iic (privacyLossArgMinus Δ σ ε))
      ≤ δ)
    (hpos :
      ∀ ⦃j : Set (BSROutput n)⦄, MeasurableSet j →
        j ⊆ posRegion
          (fun y : BSROutput n =>
            bsrGaussianDensity σ d y
              - Real.exp ε * bsrGaussianDensity σ (fun i => -d i) y) →
        0 ≤ (bsrGaussianMeasure σ d).real j
          - Real.exp ε * (bsrGaussianMeasure σ (fun i => -d i)).real j)
    (hneg :
      ∀ ⦃j : Set (BSROutput n)⦄, MeasurableSet j →
        j ⊆ (posRegion
          (fun y : BSROutput n =>
            bsrGaussianDensity σ d y
              - Real.exp ε * bsrGaussianDensity σ (fun i => -d i) y))ᶜ →
        (bsrGaussianMeasure σ d).real j
          - Real.exp ε * (bsrGaussianMeasure σ (fun i => -d i)).real j ≤ 0)
    (hzeroEvent :
      bsrSqDist d (fun _ => (0 : ℝ)) = 0 →
      ∀ s, MeasurableSet s →
        bsrGaussianMeasure σ d s
          ≤ ENNReal.ofReal (Real.exp ε) * bsrGaussianMeasure σ (fun i => -d i) s
              + ENNReal.ofReal δ),
    ∀ s, MeasurableSet s →
      bsrGaussianMeasure σ d s
        ≤ ENNReal.ofReal (Real.exp ε) * bsrGaussianMeasure σ (fun i => -d i) s
            + ENNReal.ofReal δ :=
  @Mf.DP.FiniteGaussianPrivacy.gaussianPair_centered_of_explicitGaussianEventBound_of_hahn_split

theorem centered_posRegion_hahn_nonneg_of_pos :
    ∀ {n : ℕ}
    (d : BSROutput n)
    (σ ε : ℝ),
    0 < σ →
    ∀ ⦃j : Set (BSROutput n)⦄, MeasurableSet j →
      j ⊆ posRegion
        (fun y : BSROutput n =>
          bsrGaussianDensity σ d y
            - Real.exp ε * bsrGaussianDensity σ (fun i => -d i) y) →
      0 ≤ (bsrGaussianMeasure σ d).real j
        - Real.exp ε * (bsrGaussianMeasure σ (fun i => -d i)).real j :=
  @Mf.DP.FiniteGaussianPrivacy.centered_posRegion_hahn_nonneg_of_pos

theorem centered_posRegion_hahn_nonpos_compl :
    ∀ {n : ℕ}
    (d : BSROutput n)
    (σ ε : ℝ),
    0 < σ →
    ∀ ⦃j : Set (BSROutput n)⦄, MeasurableSet j →
      j ⊆ (posRegion
        (fun y : BSROutput n =>
          bsrGaussianDensity σ d y
            - Real.exp ε * bsrGaussianDensity σ (fun i => -d i) y))ᶜ →
      (bsrGaussianMeasure σ d).real j
        - Real.exp ε * (bsrGaussianMeasure σ (fun i => -d i)).real j ≤ 0 :=
  @Mf.DP.FiniteGaussianPrivacy.centered_posRegion_hahn_nonpos_compl

theorem gaussianPair_centered_of_posRegionGap_le :
    ∀ {n : ℕ}
    (d : BSROutput n)
    (σ ε δ : ℝ)
    (hσ : 0 < σ)
    (hcap :
      (bsrGaussianMeasure σ d).real
          (posRegion
            (fun y : BSROutput n =>
              bsrGaussianDensity σ d y
                - Real.exp ε * bsrGaussianDensity σ (fun i => -d i) y))
        - Real.exp ε
            * (bsrGaussianMeasure σ (fun i => -d i)).real
                (posRegion
                  (fun y : BSROutput n =>
                    bsrGaussianDensity σ d y
                      - Real.exp ε * bsrGaussianDensity σ (fun i => -d i) y))
      ≤ δ),
    ∀ s, MeasurableSet s →
      bsrGaussianMeasure σ d s
        ≤ ENNReal.ofReal (Real.exp ε) * bsrGaussianMeasure σ (fun i => -d i) s
            + ENNReal.ofReal δ :=
  @Mf.DP.FiniteGaussianPrivacy.gaussianPair_centered_of_posRegionGap_le

theorem gaussianPair_centered_of_explicitGaussianEventBound_lt_one :
    ∀ {n : ℕ}
    (d : BSROutput n)
    (Δ σ ε δ : ℝ),
    0 < σ →
    0 ≤ ε →
    0 ≤ Δ →
    bsrSqDist d (fun _ => (0 : ℝ)) ≤ (Δ / 2) ^ 2 →
    (stdNormalMeasure.real (Set.Iic (privacyLossArgPlus Δ σ ε))
      - Real.exp ε * stdNormalMeasure.real (Set.Iic (privacyLossArgMinus Δ σ ε))
      ≤ δ) →
    δ < 1 →
    ∀ s, MeasurableSet s →
      bsrGaussianMeasure σ d s
        ≤ ENNReal.ofReal (Real.exp ε) * bsrGaussianMeasure σ (fun i => -d i) s
            + ENNReal.ofReal δ :=
  @Mf.DP.FiniteGaussianPrivacy.gaussianPair_centered_of_explicitGaussianEventBound_lt_one

theorem gaussianPair_centered_of_explicitGaussianEventBound_lt_one_of_pos :
    ∀ {n : ℕ}
    (d : BSROutput n)
    (Δ σ ε δ : ℝ),
    0 < σ →
    0 ≤ ε →
    0 ≤ Δ →
    bsrSqDist d (fun _ => (0 : ℝ)) ≤ (Δ / 2) ^ 2 →
    (stdNormalMeasure.real (Set.Iic (privacyLossArgPlus Δ σ ε))
      - Real.exp ε * stdNormalMeasure.real (Set.Iic (privacyLossArgMinus Δ σ ε))
      ≤ δ) →
    δ < 1 →
    ∀ s, MeasurableSet s →
      bsrGaussianMeasure σ d s
        ≤
          ENNReal.ofReal (Real.exp ε) * bsrGaussianMeasure σ (fun i => -d i) s
            + ENNReal.ofReal δ :=
  @Mf.DP.FiniteGaussianPrivacy.gaussianPair_centered_of_explicitGaussianEventBound_lt_one_of_pos

theorem gaussianPair_eventApproxDP_centered_of_analyticCondition_lt_one :
    ∀ {n : ℕ}
    (d : BSROutput n)
    (Δ σ ε δ : ℝ),
    0 < σ →
    0 ≤ ε →
    0 ≤ Δ →
    bsrSqDist d (fun _ => (0 : ℝ)) ≤ (Δ / 2) ^ 2 →
    analyticGaussianCondition Δ σ ε δ →
    δ < 1 →
    ∀ s, MeasurableSet s →
      bsrGaussianMeasure σ d s
        ≤
          ENNReal.ofReal (Real.exp ε) * bsrGaussianMeasure σ (fun i => -d i) s
            + ENNReal.ofReal δ :=
  @Mf.DP.FiniteGaussianPrivacy.gaussianPair_eventApproxDP_centered_of_analyticCondition_lt_one

theorem gaussianPair_eventApproxDP_centered_of_analyticCondition_lt_one_of_pos :
    ∀ {n : ℕ}
    (d : BSROutput n)
    (Δ σ ε δ : ℝ),
    0 < σ →
    0 ≤ ε →
    0 ≤ Δ →
    bsrSqDist d (fun _ => (0 : ℝ)) ≤ (Δ / 2) ^ 2 →
    analyticGaussianCondition Δ σ ε δ →
    δ < 1 →
    ∀ s, MeasurableSet s →
      bsrGaussianMeasure σ d s
        ≤
          ENNReal.ofReal (Real.exp ε) * bsrGaussianMeasure σ (fun i => -d i) s
            + ENNReal.ofReal δ :=
  @Mf.DP.FiniteGaussianPrivacy.gaussianPair_eventApproxDP_centered_of_analyticCondition_lt_one_of_pos

theorem gaussianPair_eventApproxDP_of_analyticCondition_lt_one :
    ∀ {n : ℕ}
    (μ μ' : BSROutput n)
    (Δ σ ε δ : ℝ),
    0 < σ →
    0 ≤ ε →
    0 ≤ Δ →
    bsrSqDist μ μ' ≤ Δ ^ 2 →
    analyticGaussianCondition Δ σ ε δ →
    δ < 1 →
    ∀ s, MeasurableSet s →
      bsrGaussianMeasure σ μ s
        ≤ ENNReal.ofReal (Real.exp ε) * bsrGaussianMeasure σ μ' s + ENNReal.ofReal δ :=
  @Mf.DP.FiniteGaussianPrivacy.gaussianPair_eventApproxDP_of_analyticCondition_lt_one

theorem gaussianPair_eventApproxDP_of_analyticCondition_lt_one_of_pos :
    ∀ {n : ℕ}
    (μ μ' : BSROutput n)
    (Δ σ ε δ : ℝ),
    0 < σ →
    0 ≤ ε →
    0 ≤ Δ →
    bsrSqDist μ μ' ≤ Δ ^ 2 →
    analyticGaussianCondition Δ σ ε δ →
    δ < 1 →
    ∀ s, MeasurableSet s →
      bsrGaussianMeasure σ μ s
        ≤ ENNReal.ofReal (Real.exp ε) * bsrGaussianMeasure σ μ' s + ENNReal.ofReal δ :=
  @Mf.DP.FiniteGaussianPrivacy.gaussianPair_eventApproxDP_of_analyticCondition_lt_one_of_pos

theorem gaussianCore_approxDP_of_analyticCondition_lt_one
    {X : Type} {n : ℕ}
    (adj : X → X → Prop)
    (mean : X → BSROutput n)
    (Δ σ ε δ : ℝ) :
    0 < σ →
    0 ≤ ε →
    0 ≤ Δ →
    BSRMeanL2SensitivityGoal adj mean Δ →
    analyticGaussianCondition Δ σ ε δ →
    δ < 1 →
    ApproxDP adj (bsrOneStepMeasure mean σ) ε δ := by
  intro hσ hε hΔ hSens hAnalytic hδlt x x' hAdj s hs
  have hdist : bsrSqDist (mean x) (mean x') ≤ Δ ^ 2 := hSens x x' hAdj
  simpa [bsrOneStepMeasure] using
    gaussianPair_eventApproxDP_of_analyticCondition_lt_one
      (μ := mean x) (μ' := mean x') Δ σ ε δ hσ hε hΔ hdist hAnalytic hδlt s hs

theorem gaussianCore_approxDP_of_analyticCondition_lt_one_of_pos
    {X : Type} {n : ℕ}
    (adj : X → X → Prop)
    (mean : X → BSROutput n)
    (Δ σ ε δ : ℝ) :
    0 < σ →
    0 ≤ ε →
    0 ≤ Δ →
    BSRMeanL2SensitivityGoal adj mean Δ →
    analyticGaussianCondition Δ σ ε δ →
    δ < 1 →
    ApproxDP adj (bsrOneStepMeasure mean σ) ε δ := by
  intro hσ hε hΔ hSens hAnalytic hδlt x x' hAdj s hs
  have hdist : bsrSqDist (mean x) (mean x') ≤ Δ ^ 2 := hSens x x' hAdj
  simpa [bsrOneStepMeasure] using
    gaussianPair_eventApproxDP_of_analyticCondition_lt_one_of_pos
      (μ := mean x) (μ' := mean x') Δ σ ε δ hσ hε hΔ hdist hAnalytic hδlt s hs

theorem gaussianCore_approxDP_of_analyticCondition
    {X : Type} {n : ℕ}
    (adj : X → X → Prop)
    (mean : X → BSROutput n)
    (Δ σ ε δ : ℝ) :
    0 < σ →
    0 ≤ ε →
    0 ≤ Δ →
    BSRMeanL2SensitivityGoal adj mean Δ →
    analyticGaussianCondition Δ σ ε δ →
    ApproxDP adj (bsrOneStepMeasure mean σ) ε δ := by
  intro hσ hε hΔ hSens hAnalytic
  by_cases hδ : 1 ≤ δ
  · refine approxDP_of_one_le_delta adj (bsrOneStepMeasure mean σ) ?_ hδ
    intro x
    simpa [bsrOneStepMeasure] using
      (bsrGaussianMeasure_isProbability (σ := σ) (μ := mean x))
  · exact gaussianCore_approxDP_of_analyticCondition_lt_one
      adj mean Δ σ ε δ hσ hε hΔ hSens hAnalytic (lt_of_not_ge hδ)

theorem gaussianCore_approxDP_of_analyticCondition_of_pos
    {X : Type} {n : ℕ}
    (adj : X → X → Prop)
    (mean : X → BSROutput n)
    (Δ σ ε δ : ℝ) :
    0 < σ →
    0 ≤ ε →
    0 ≤ Δ →
    BSRMeanL2SensitivityGoal adj mean Δ →
    analyticGaussianCondition Δ σ ε δ →
    ApproxDP adj (bsrOneStepMeasure mean σ) ε δ := by
  intro hσ hε hΔ hSens hAnalytic
  by_cases hδ : 1 ≤ δ
  · refine approxDP_of_one_le_delta adj (bsrOneStepMeasure mean σ) ?_ hδ
    intro x
    simpa [bsrOneStepMeasure] using
      (bsrGaussianMeasure_isProbability (σ := σ) (μ := mean x))
  · exact gaussianCore_approxDP_of_analyticCondition_lt_one_of_pos
      adj mean Δ σ ε δ hσ hε hΔ hSens hAnalytic (lt_of_not_ge hδ)

end
end Mf.DP
