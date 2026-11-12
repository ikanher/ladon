import Mf.Optimization.PoissonClippedSGD.GDPApplications

open MeasureTheory
open scoped BigOperators
open Mf.Optimization.PoissonClippedSGD
noncomputable section
namespace LadonDPsgdAudit

-- These are checking adapters, not new mathematical algorithms.
-- Keep the original general objective, query measurability and public gap bound.
theorem public_gap_convergence
    {n d : ℕ} (hn : 0 < n) (hd : 0 < d)
    (q : NNReal) (hq0 : 0 < q) (hq1 : q ≤ 1)
    (eta L c sigmaSG sigmaDP : ℝ)
    (heta : 0 < eta) (hL : 0 < L) (hc : 0 < c)
    (hsg : 0 ≤ sigmaSG) (hs : 0 ≤ sigmaDP)
    (hclip : 4 * sigmaSG ≤ c)
    (hstep : eta * L * (1 + (1 - (q : ℝ)) / ((q : ℝ) * n)) ≤ 1)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ i, Measurable (g i))
    (f : EuclideanSpace ℝ (Fin d) → ℝ)
    (hf : ∀ x, HasGradientAt f (vectorMean (fun i => g i x)) x)
    (hLip : ∀ x y,
      ‖vectorMean (fun i => g i x) - vectorMean (fun i => g i y)‖ ≤ L * ‖x-y‖)
    (hvariance : ∀ x,
      meanSqDeviation (fun i => g i x) (vectorMean (fun i => g i x)) ≤ sigmaSG^2)
    (fLower : ℝ) (hlower : ∀ x, fLower ≤ f x)
    (x0 : EuclideanSpace ℝ (Fin d)) (T : ℕ) (hT : 0 < T) (F : ℝ) (hF : f x0 - fLower ≤ F) :
    (T : ℝ)⁻¹ * ∑ t : Fin T,
      (∫ ω, ‖vectorMean (fun i => g i
        (gaussianIterate eta q c g x0 T t.val t.isLt.le ω))‖
        ∂gaussianHistoryLaw n d T q hq1 sigmaDP) ≤
      Real.sqrt (poissonRateD eta L ((1-(q:ℝ))/((q:ℝ)*n)) sigmaSG sigmaDP
        F T c) +
      poissonRateD eta L ((1-(q:ℝ))/((q:ℝ)*n)) sigmaSG sigmaDP
        F T c / c := by
  have hbase := gaussian_convergence hn hd q hq0 hq1 eta L c sigmaSG sigmaDP
    heta hL hc hsg hs hclip hstep g hg f hf hLip hvariance fLower hlower x0 T hT
  have hD : poissonRateD eta L ((1-(q:ℝ))/((q:ℝ)*n)) sigmaSG sigmaDP
      (f x0-fLower) T c ≤
      poissonRateD eta L ((1-(q:ℝ))/((q:ℝ)*n)) sigmaSG sigmaDP F T c := by
    unfold poissonRateD
    have hterm := div_le_div_of_nonneg_right
      (mul_le_mul_of_nonneg_left hF (by norm_num : (0 : ℝ) ≤ 4))
      (show 0 ≤ eta * (T : ℝ) by positivity)
    linarith
  exact hbase.trans (add_le_add (Real.sqrt_le_sqrt hD)
    (div_le_div_of_nonneg_right hD hc.le))

theorem general_objective_gdp_convergence
    {n d : ℕ} (hn : 0 < n) (hd : 0 < d)
    (q : NNReal) (hq0 : 0 < q) (hq1 : q ≤ 1)
    (eta L c sigmaSG mu : ℝ)
    (heta : 0 < eta) (hL : 0 < L) (hc : 0 < c)
    (hsg : 0 ≤ sigmaSG) (hmu : 0 < mu)
    (hclip : 4 * sigmaSG ≤ c)
    (hstep : eta * L * (1 + (1 - (q : ℝ)) / ((q : ℝ) * n)) ≤ 1)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ i, Measurable (g i))
    (f : EuclideanSpace ℝ (Fin d) → ℝ)
    (hf : ∀ x, HasGradientAt f (vectorMean (fun i => g i x)) x)
    (hLip : ∀ x y,
      ‖vectorMean (fun i => g i x) - vectorMean (fun i => g i y)‖ ≤ L * ‖x-y‖)
    (hvariance : ∀ x,
      meanSqDeviation (fun i => g i x) (vectorMean (fun i => g i x)) ≤ sigmaSG^2)
    (fLower : ℝ) (hlower : ∀ x, fLower ≤ f x)
    (x0 : EuclideanSpace ℝ (Fin d)) (T : ℕ) (hT : 0 < T) (F : ℝ) (hF : f x0 - fLower ≤ F) :
    (T : ℝ)⁻¹ * ∑ t : Fin T,
      (∫ ω, ‖vectorMean (fun i => g i
        (gaussianIterate eta q c g x0 T t.val t.isLt.le ω))‖
        ∂gaussianHistoryLaw n d T q hq1 (gdpFormulaNoise n d q T c mu)) ≤
      Real.sqrt (poissonRateD eta L ((1-(q:ℝ))/((q:ℝ)*n)) sigmaSG (gdpFormulaNoise n d q T c mu)
        F T c) +
      poissonRateD eta L ((1-(q:ℝ))/((q:ℝ)*n)) sigmaSG (gdpFormulaNoise n d q T c mu)
        F T c / c := by
  exact public_gap_convergence hn hd q hq0 hq1 eta L c sigmaSG
    (gdpFormulaNoise n d q T c mu) heta hL hc hsg
    (gdpFormulaNoise_nonneg (by exact_mod_cast hq0) (by exact_mod_cast hT) hc.le hmu)
    hclip hstep g hg f hf hLip hvariance fLower hlower x0 T hT F hF

-- This identity converts the previous conclusion to the exact printed coefficient.
theorem gdp_coefficient {n d : ℕ} (eta L sigma F c : ℝ)
    {q T mu : ℝ} (hq : 0 < q) (hT : 0 < T) (hmu : 0 < mu) :
    poissonRateD eta L ((1-q)/(q*n)) sigma (gdpFormulaNoise n d q T c mu) F T c =
      4*F/(eta*T) + 8*sigma^4/c^2 + 2*eta*L *
        ((1-q)/(q*n)*sigma^2 + c^2*d/(n^2*q^2*Real.log (1+mu^2/(T*q^2)))) := by
  simpa only [gdpFormulaD, gdpTotalVariance, gdpFormulaVariance] using
    poissonRateD_eq_gdpFormulaD eta L sigma F c hq hT hmu

theorem physical_optimizer {F T L kappa sigma s cap eta c : ℝ}
    (hF : 0 < F) (hT : 0 < T) (hL : 0 < L)
    (hW : 0 < kappa*sigma^2+s^2) (hcap : 0 < cap)
    (heta : 0 < eta) (hetacap : eta ≤ cap) (hc : 0 < c) :
    stationarityUpper c (poissonRateD
      (optimalStep F T L (kappa*sigma^2+s^2) cap) L kappa sigma s F T c) ≤
    stationarityUpper c (poissonRateD eta L kappa sigma s F T c) := by
  simpa only [stepRateD, poissonRateD] using
    stepUpper_optimal (bias := 8*sigma^4/c^2) hF hT hL hW hcap heta hetacap hc.le

-- Check the actual coordinate law, not only its second moment.
theorem gdp_coordinate_law (n d : ℕ) (q T c mu : ℝ) (hd : 0 < d) :
    gaussianCoordinateLaw d (gdpFormulaNoise n d q T c mu) =
      Mf.Probability.FiniteProductGaussian.law (fun _ => 0)
        (fun _ => c * gdpFormulaMultiplier q T mu / (q*n)) := by
  unfold gaussianCoordinateLaw gdpFormulaNoise
  rw [normalized_noise_coordinate_scale n d q c (gdpFormulaMultiplier q T mu) hd]


-- Cap admissibility must be checked separately from scalar optimality.
theorem optimal_step_admissible {F T L kappa W cap : ℝ}
    (hF : 0 < F) (hT : 0 < T) (hL : 0 < L) (hk : 0 ≤ kappa)
    (hW : 0 < W) (hcap : 0 < cap) (hcapBound : cap ≤ poissonStepCap L kappa) :
    0 < optimalStep F T L W cap ∧
      optimalStep F T L W cap * L * (1+kappa) ≤ 1 := by
  have hp := optimalStep_pos hF hT hL hW hcap
  exact ⟨hp, (le_poissonStepCap_iff hL hk).mp
    ((optimalStep_le_cap F T L W cap).trans hcapBound)⟩

theorem arbitrary_variance_energy {n d : ℕ} (hd : 0 < d)
    (q c V : ℝ) (hV : 0 ≤ V) :
    (∫ z, ‖z‖^2 ∂gaussianVectorLaw d
      (c * Real.sqrt (d:ℝ) / (q*n) * Real.sqrt V)) =
      c^2*d*V/(q*n)^2 := by
  rw [gaussianVectorLaw_energy hd, mul_pow, div_pow, mul_pow,
    Real.sq_sqrt (Nat.cast_nonneg d), Real.sq_sqrt hV]
  ring

theorem arbitrary_variance_coordinate_law (n d : ℕ) (hd : 0 < d)
    (q c V : ℝ) :
    gaussianCoordinateLaw d (c * Real.sqrt (d:ℝ)/(q*n)*Real.sqrt V) =
      Mf.Probability.FiniteProductGaussian.law (fun _ => 0)
        (fun _ => c*Real.sqrt V/(q*n)) := by
  unfold gaussianCoordinateLaw
  rw [normalized_noise_coordinate_scale n d q c (Real.sqrt V) hd]

end LadonDPsgdAudit

#check LadonDPsgdAudit.public_gap_convergence
#print axioms LadonDPsgdAudit.public_gap_convergence
#check LadonDPsgdAudit.general_objective_gdp_convergence
#print axioms LadonDPsgdAudit.general_objective_gdp_convergence
#check LadonDPsgdAudit.gdp_coefficient
#print axioms LadonDPsgdAudit.gdp_coefficient
#check LadonDPsgdAudit.physical_optimizer
#print axioms LadonDPsgdAudit.physical_optimizer
#check LadonDPsgdAudit.gdp_coordinate_law
#print axioms LadonDPsgdAudit.gdp_coordinate_law
#check Mf.Optimization.PoissonClippedSGD.gaussian_convergence
#print axioms Mf.Optimization.PoissonClippedSGD.gaussian_convergence
#check Mf.Optimization.PoissonClippedSGD.gdpFormulaNoise_energy
#print axioms Mf.Optimization.PoissonClippedSGD.gdpFormulaNoise_energy
#check Mf.Optimization.PoissonClippedSGD.optimalStep_pos
#print axioms Mf.Optimization.PoissonClippedSGD.optimalStep_pos
#check Mf.Optimization.PoissonClippedSGD.optimalStep_le_cap
#print axioms Mf.Optimization.PoissonClippedSGD.optimalStep_le_cap
#check Mf.Optimization.PoissonClippedSGD.gdpUpper_retuned_antitone_batch
#print axioms Mf.Optimization.PoissonClippedSGD.gdpUpper_retuned_antitone_batch
#check LadonDPsgdAudit.optimal_step_admissible
#print axioms LadonDPsgdAudit.optimal_step_admissible
#check LadonDPsgdAudit.arbitrary_variance_energy
#print axioms LadonDPsgdAudit.arbitrary_variance_energy
#check LadonDPsgdAudit.arbitrary_variance_coordinate_law
#print axioms LadonDPsgdAudit.arbitrary_variance_coordinate_law
