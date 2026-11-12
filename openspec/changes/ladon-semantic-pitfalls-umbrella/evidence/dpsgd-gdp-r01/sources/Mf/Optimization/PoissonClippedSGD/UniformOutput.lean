import Mf.Optimization.PoissonClippedSGD.Convergence
import Mf.Optimization.FiniteMemoryAdam.CorrectedMomentumUniformIndex

/-!
# Independent uniform output for Poisson clipped SGD

The independent uniform index converts the finite average in
`gaussian_convergence` to the expected true-gradient norm at a pre-update
iterate. Integrability follows from the actual Bernoulli / Gaussian history law.
The finite-index identity is shared with the corrected-momentum development.
-/

noncomputable section
namespace Mf.Optimization.PoissonClippedSGD
open MeasureTheory
open scoped BigOperators

def outputLaw (n d T : ℕ) [NeZero T] (q : NNReal) (hq1 : q ≤ 1) (s : ℝ) :=
  (PMF.uniformOfFintype (Fin T)).toMeasure.prod (gaussianHistoryLaw n d T q hq1 s)

instance outputLaw_probability (n d T : ℕ) [NeZero T]
    (q : NNReal) (hq1 : q ≤ 1) (s : ℝ) :
    IsProbabilityMeasure (outputLaw n d T q hq1 s) := by
  unfold outputLaw
  infer_instance

def output {n d T : ℕ} (eta q c : ℝ)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (x0 : EuclideanSpace ℝ (Fin d))
    (p : Fin T × (Fin T → (Fin n → Bool) × EuclideanSpace ℝ (Fin d))) :=
  gaussianIterate eta q c g x0 T p.1.val p.1.isLt.le p.2

theorem output_norm_integrable {n d T : ℕ} [NeZero T] (hn : 0 < n)
    (q : NNReal) (hq0 : 0 < q) (hq1 : q ≤ 1)
    (eta c s L : ℝ) (hc : 0 ≤ c) (hL : 0 ≤ L)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ i, Measurable (g i)) (x0 : EuclideanSpace ℝ (Fin d))
    (hLip : ∀ x y,
      ‖vectorMean (fun i => g i x) - vectorMean (fun i => g i y)‖ ≤ L * ‖x - y‖) :
    Integrable (fun p => ‖vectorMean (fun i => g i (output eta q c g x0 p))‖)
      (outputLaw n d T q hq1 s) := by
  let grad := fun x => vectorMean (fun i => g i x)
  have hgrad : Measurable grad :=
    (Finset.measurable_sum _ (fun i _ => hg i)).const_smul ((n : ℝ)⁻¹)
  have hm : Measurable (output (T := T) eta q c g x0) := by
    apply measurable_from_prod_countable_right
    intro t
    exact gaussianIterate_measurable eta q c hc g hg x0 T t.val t.isLt.le
  apply (integrable_prod_iff (hgrad.comp hm).norm.aestronglyMeasurable).mpr
  constructor
  · apply ae_of_all
    intro t
    exact integrable_norm_gradient_comp_of_memLp_two _
      (gaussianIterate_measurable eta q c hc g hg x0 T t.val t.isLt.le)
      (gaussianIterate_memLp hn eta c s q hq0 hq1 hc g hg x0 T t.val t.isLt.le)
      grad L hL hLip x0
  · exact Integrable.of_finite

theorem output_integral_average {n d T : ℕ} [NeZero T] (hn : 0 < n)
    (q : NNReal) (hq0 : 0 < q) (hq1 : q ≤ 1)
    (eta c s L : ℝ) (hc : 0 ≤ c) (hL : 0 ≤ L)
    (g : Fin n → EuclideanSpace ℝ (Fin d) → EuclideanSpace ℝ (Fin d))
    (hg : ∀ i, Measurable (g i)) (x0 : EuclideanSpace ℝ (Fin d))
    (hLip : ∀ x y,
      ‖vectorMean (fun i => g i x) - vectorMean (fun i => g i y)‖ ≤ L * ‖x - y‖) :
    (∫ p, ‖vectorMean (fun i => g i (output eta q c g x0 p))‖
      ∂outputLaw n d T q hq1 s) =
    (T : ℝ)⁻¹ * ∑ t : Fin T,
      ∫ ω, ‖vectorMean (fun i => g i
        (gaussianIterate eta q c g x0 T t.val t.isLt.le ω))‖
        ∂gaussianHistoryLaw n d T q hq1 s := by
  let grad := fun x => vectorMean (fun i => g i x)
  have hgrad : Measurable grad :=
    (Finset.measurable_sum _ (fun i _ => hg i)).const_smul ((n : ℝ)⁻¹)
  apply FiniteMemoryAdam.CorrectedColumns.independent_uniform_index_integral
    (gaussianHistoryLaw n d T q hq1 s) T
    (fun t ω => ‖grad (gaussianIterate eta q c g x0 T t.val t.isLt.le ω)‖)
  · intro t
    exact (hgrad.comp (gaussianIterate_measurable eta q c hc g hg x0 T t.val t.isLt.le)).norm
  · intro t
    exact integrable_norm_gradient_comp_of_memLp_two _
      (gaussianIterate_measurable eta q c hc g hg x0 T t.val t.isLt.le)
      (gaussianIterate_memLp hn eta c s q hq0 hq1 hc g hg x0 T t.val t.isLt.le)
      grad L hL hLip x0

theorem uniform_output_convergence
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
      ‖vectorMean (fun i => g i x) - vectorMean (fun i => g i y)‖ ≤ L * ‖x - y‖)
    (hvariance : ∀ x,
      meanSqDeviation (fun i => g i x) (vectorMean (fun i => g i x)) ≤ sigmaSG ^ 2)
    (fLower : ℝ) (hlower : ∀ x, fLower ≤ f x)
    (x0 : EuclideanSpace ℝ (Fin d)) (T : ℕ) [NeZero T] (hT : 0 < T) :
    (∫ p, ‖vectorMean (fun i => g i (output eta q c g x0 p))‖
      ∂outputLaw n d T q hq1 sigmaDP) ≤
      Real.sqrt (poissonRateD eta L ((1-(q:ℝ)) / ((q:ℝ) * n)) sigmaSG sigmaDP
        (f x0-fLower) T c) + poissonRateD eta L ((1-(q:ℝ)) / ((q:ℝ) * n)) sigmaSG sigmaDP
        (f x0-fLower) T c / c := by
  rw [output_integral_average hn q hq0 hq1 eta c sigmaDP L hc.le hL.le g hg x0 hLip]
  exact gaussian_convergence hn hd q hq0 hq1 eta L c sigmaSG sigmaDP heta hL hc
    hsg hs hclip hstep g hg f hf hLip hvariance fLower hlower x0 T hT

end Mf.Optimization.PoissonClippedSGD
