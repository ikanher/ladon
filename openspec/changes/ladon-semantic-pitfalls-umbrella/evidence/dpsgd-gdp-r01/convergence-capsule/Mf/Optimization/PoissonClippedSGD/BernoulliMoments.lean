import Mathlib.MeasureTheory.Constructions.Pi
import Mathlib.MeasureTheory.Integral.Pi
import Mathlib.Probability.ProbabilityMassFunction.Constructions
import Mathlib.Probability.ProbabilityMassFunction.Integrals
import Mathlib.Probability.Independence.Basic
import Mathlib.Probability.Independence.Integration
import Mathlib.Analysis.InnerProductSpace.PiL2

/-!
# Independent Poisson inclusion moments

The explicit finite product Bernoulli law yields the mean and raw second
moment of a sampled vector sum. The off-diagonal contribution follows from
independence; the diagonal contribution retains random batch-size variation.
This is the finite mechanism calculation in Appendix A of
`docs/poisson-clipped-sgd/TARGET.md`.
-/

open MeasureTheory ProbabilityTheory Finset
open scoped BigOperators

noncomputable section

namespace Mf.Optimization.PoissonClippedSGD

def maskLaw (n : ℕ) (q : NNReal) (hq1 : q ≤ 1) :
    Measure (Fin n → Bool) :=
  Measure.pi fun _ : Fin n =>
    (PMF.bernoulli q hq1).toMeasure

def indicator (mask : Fin n → Bool) (i : Fin n) : ℝ :=
  if mask i then 1 else 0

theorem maskLaw_isProbability (n : ℕ) (q : NNReal) (hq1 : q ≤ 1) :
    IsProbabilityMeasure (maskLaw n q hq1) := by
  unfold maskLaw
  infer_instance

theorem indicator_integral (n : ℕ) (q : NNReal) (hq1 : q ≤ 1)
    (i : Fin n) :
    (∫ mask, indicator mask i ∂maskLaw n q hq1) = (q : ℝ) := by
  let μ : Fin n → Measure Bool := fun _ =>
    (PMF.bernoulli q hq1).toMeasure
  rw [show maskLaw n q hq1 = Measure.pi μ by rfl]
  change (∫ mask, (if mask i then (1 : ℝ) else 0) ∂Measure.pi μ) = (q : ℝ)
  rw [MeasureTheory.integral_comp_eval (μ := μ) (i := i)
    (f := fun b : Bool => if b then (1 : ℝ) else 0) (by fun_prop)]
  change (∫ b : Bool, (if b then (1 : ℝ) else 0)
    ∂(PMF.bernoulli q hq1).toMeasure) = (q : ℝ)
  simpa [Bool.cond_eq_ite] using (PMF.bernoulli_expectation (p := q) hq1)

theorem indicator_sq_integral (n : ℕ) (q : NNReal) (hq1 : q ≤ 1)
    (i : Fin n) :
    (∫ mask, indicator mask i ^ 2 ∂maskLaw n q hq1) = (q : ℝ) := by
  calc
    (∫ mask, indicator mask i ^ 2 ∂maskLaw n q hq1) =
        ∫ mask, indicator mask i ∂maskLaw n q hq1 := by
          apply integral_congr_ae
          filter_upwards [] with mask
          simp [indicator]
    _ = (q : ℝ) := indicator_integral n q hq1 i

theorem indicator_mul_integral_of_ne (n : ℕ) (q : NNReal) (hq1 : q ≤ 1)
    {i j : Fin n} (hij : i ≠ j) :
    (∫ mask, indicator mask i * indicator mask j ∂maskLaw n q hq1) =
      (q : ℝ) * (q : ℝ) := by
  let μ : Fin n → Measure Bool := fun _ => (PMF.bernoulli q hq1).toMeasure
  have hLaw : maskLaw n q hq1 = Measure.pi μ := rfl
  let X : Fin n → (Fin n → Bool) → Bool := fun k mask => mask k
  have hIndBool : iIndepFun (fun k mask => X k mask)
      (Measure.pi μ) := by
    exact iIndepFun_pi fun _ => aemeasurable_id
  have hInd := hIndBool.indepFun hij
  have hIndicator := hInd.comp
    (φ := fun b : Bool => if b then (1 : ℝ) else 0)
    (ψ := fun b : Bool => if b then (1 : ℝ) else 0)
    (by fun_prop) (by fun_prop)
  have hXmeas (k : Fin n) : Measurable (fun mask : Fin n → Bool =>
      if mask k then (1 : ℝ) else 0) := by
    fun_prop
  have hprod := hIndicator.integral_fun_mul_eq_mul_integral
    (hXmeas i).aestronglyMeasurable (hXmeas j).aestronglyMeasurable
  rw [hLaw]
  have hprod' :
      (∫ mask, indicator mask i * indicator mask j ∂Measure.pi μ) =
        (∫ mask, indicator mask i ∂Measure.pi μ) *
          (∫ mask, indicator mask j ∂Measure.pi μ) := by
    simpa [indicator, X, Function.comp_def] using hprod
  rw [hprod']
  have hi : (∫ mask, indicator mask i ∂Measure.pi μ) = (q : ℝ) := by
    simpa [hLaw] using indicator_integral n q hq1 i
  have hj : (∫ mask, indicator mask j ∂Measure.pi μ) = (q : ℝ) := by
    simpa [hLaw] using indicator_integral n q hq1 j
  rw [hi, hj]

theorem weighted_indicator_sum_integral (n : ℕ) (q : NNReal) (hq1 : q ≤ 1)
    (a : Fin n → ℝ) :
    (∫ mask, ∑ i, indicator mask i * a i ∂maskLaw n q hq1) =
      (q : ℝ) * ∑ i, a i := by
  letI : IsProbabilityMeasure (maskLaw n q hq1) :=
    maskLaw_isProbability n q hq1
  have hterm (i : Fin n) : Integrable
      (fun mask : Fin n → Bool => indicator mask i * a i)
      (maskLaw n q hq1) := Integrable.of_finite
  rw [integral_finsetSum Finset.univ (fun i _ => hterm i)]
  simp_rw [integral_mul_const, indicator_integral]
  simp [Finset.mul_sum]

def rawSampledSum (n d : ℕ) (h : Fin n → EuclideanSpace ℝ (Fin d))
    (mask : Fin n → Bool) : EuclideanSpace ℝ (Fin d) :=
  ∑ i, indicator mask i • h i

theorem rawSampledSum_integral (n d : ℕ) (q : NNReal) (hq1 : q ≤ 1)
    (h : Fin n → EuclideanSpace ℝ (Fin d)) :
    (∫ mask, rawSampledSum n d h mask ∂maskLaw n q hq1) =
      (q : ℝ) • ∑ i, h i := by
  letI : IsProbabilityMeasure (maskLaw n q hq1) :=
    maskLaw_isProbability n q hq1
  have hterm (i : Fin n) : Integrable
      (fun mask : Fin n → Bool => indicator mask i • h i)
      (maskLaw n q hq1) := Integrable.of_finite
  rw [show (fun mask => rawSampledSum n d h mask) =
      fun mask => ∑ i ∈ Finset.univ, indicator mask i • h i by
        funext mask
        simp [rawSampledSum]]
  rw [integral_finsetSum Finset.univ (fun i _ => hterm i)]
  simp_rw [integral_smul_const, indicator_integral]
  rw [Finset.smul_sum]

theorem rawSampledSum_norm_sq_expand (n d : ℕ)
    (h : Fin n → EuclideanSpace ℝ (Fin d)) (mask : Fin n → Bool) :
    ‖rawSampledSum n d h mask‖ ^ 2 =
      ∑ i, ∑ j,
        (indicator mask i * indicator mask j) * inner ℝ (h i) (h j) := by
  rw [← real_inner_self_eq_norm_sq]
  simp only [rawSampledSum, sum_inner, inner_sum,
    real_inner_smul_left, real_inner_smul_right]
  rw [Finset.sum_comm]
  apply Finset.sum_congr rfl
  intro i hi
  apply Finset.sum_congr rfl
  intro j hj
  rw [real_inner_comm]
  ring

theorem rawSampledSum_norm_sq_integral_pairExpansion (n d : ℕ)
    (q : NNReal) (hq1 : q ≤ 1) (h : Fin n → EuclideanSpace ℝ (Fin d)) :
    (∫ mask, ‖rawSampledSum n d h mask‖ ^ 2 ∂maskLaw n q hq1) =
      ∑ i, ∑ j,
        (if i = j then (q : ℝ) else (q : ℝ) ^ 2) * inner ℝ (h i) (h j) := by
  letI : IsProbabilityMeasure (maskLaw n q hq1) :=
    maskLaw_isProbability n q hq1
  have hpair (i j : Fin n) : Integrable
      (fun mask : Fin n → Bool =>
        (indicator mask i * indicator mask j) * inner ℝ (h i) (h j))
      (maskLaw n q hq1) := Integrable.of_finite
  calc
    (∫ mask, ‖rawSampledSum n d h mask‖ ^ 2 ∂maskLaw n q hq1) =
        ∫ mask, ∑ i ∈ Finset.univ, ∑ j ∈ Finset.univ,
          (indicator mask i * indicator mask j) * inner ℝ (h i) (h j)
          ∂maskLaw n q hq1 := by
            apply integral_congr_ae
            filter_upwards [] with mask
            exact rawSampledSum_norm_sq_expand n d h mask
    _ = ∑ i ∈ Finset.univ, ∑ j ∈ Finset.univ,
          ∫ mask, (indicator mask i * indicator mask j) *
            inner ℝ (h i) (h j) ∂maskLaw n q hq1 := by
          rw [integral_finsetSum Finset.univ
            (fun _ _ => Integrable.of_finite)]
          apply sum_congr rfl
          intro i hi
          rw [integral_finsetSum Finset.univ (fun j _ => hpair i j)]
    _ = ∑ i, ∑ j,
          (if i = j then (q : ℝ) else (q : ℝ) ^ 2) *
            inner ℝ (h i) (h j) := by
          simp_rw [integral_mul_const]
          apply sum_congr rfl
          intro i hi
          apply sum_congr rfl
          intro j hj
          by_cases hij : i = j
          · subst j
            simp only [if_pos rfl]
            have hsquare : (∫ mask, indicator mask i * indicator mask i
                ∂maskLaw n q hq1) = (q : ℝ) := by
              calc
                _ = ∫ mask, indicator mask i ^ 2 ∂maskLaw n q hq1 := by
                  apply integral_congr_ae
                  filter_upwards [] with mask
                  simp [indicator]
                _ = (q : ℝ) := indicator_sq_integral n q hq1 i
            rw [hsquare]
            simp
          · simp only [if_neg hij]
            have hcross := indicator_mul_integral_of_ne n q hq1 hij
            rw [hcross]
            ring

theorem inner_sum_norm_sq (n d : ℕ) (h : Fin n → EuclideanSpace ℝ (Fin d)) :
    ‖∑ i, h i‖ ^ 2 = ∑ i, ∑ j, inner ℝ (h i) (h j) := by
  rw [← real_inner_self_eq_norm_sq]
  simp only [sum_inner, inner_sum]
  rw [Finset.sum_comm]

theorem inner_diagonal_norm_sq (n d : ℕ) (h : Fin n → EuclideanSpace ℝ (Fin d)) :
    ∑ i, inner ℝ (h i) (h i) = ∑ i, ‖h i‖ ^ 2 := by
  apply sum_congr rfl
  intro i hi
  exact real_inner_self_eq_norm_sq (h i)

theorem pairCoefficient_sum_identity (n d : ℕ) (q : ℝ)
    (h : Fin n → EuclideanSpace ℝ (Fin d)) :
    ∑ i, ∑ j, (if i = j then q else q ^ 2) * inner ℝ (h i) (h j) =
      q ^ 2 * ‖∑ i, h i‖ ^ 2 + q * (1 - q) * ∑ i, ‖h i‖ ^ 2 := by
  calc
    ∑ i, ∑ j, (if i = j then q else q ^ 2) * inner ℝ (h i) (h j) =
        ∑ i, (q ^ 2 * ∑ j, inner ℝ (h i) (h j) +
          (q - q ^ 2) * inner ℝ (h i) (h i)) := by
          apply sum_congr rfl
          intro i hi
          calc
            ∑ j, (if i = j then q else q ^ 2) * inner ℝ (h i) (h j) =
                ∑ j, (q ^ 2 * inner ℝ (h i) (h j) +
                  if i = j then (q - q ^ 2) * inner ℝ (h i) (h j) else 0) := by
                    apply sum_congr rfl
                    intro j hj
                    by_cases hij : i = j <;> simp [hij] <;> ring
            _ = q ^ 2 * ∑ j, inner ℝ (h i) (h j) +
                  (q - q ^ 2) * inner ℝ (h i) (h i) := by
                    rw [Finset.sum_add_distrib, ← Finset.mul_sum]
                    simp [Finset.sum_ite_eq]
    _ = q ^ 2 * ‖∑ i, h i‖ ^ 2 +
          (q - q ^ 2) * ∑ i, ‖h i‖ ^ 2 := by
          rw [Finset.sum_add_distrib, ← Finset.mul_sum, ← Finset.mul_sum,
            inner_sum_norm_sq, inner_diagonal_norm_sq]
    _ = q ^ 2 * ‖∑ i, h i‖ ^ 2 + q * (1 - q) * ∑ i, ‖h i‖ ^ 2 := by ring

theorem rawSampledSum_norm_sq_integral (n d : ℕ)
    (q : NNReal) (hq1 : q ≤ 1) (h : Fin n → EuclideanSpace ℝ (Fin d)) :
    (∫ mask, ‖rawSampledSum n d h mask‖ ^ 2 ∂maskLaw n q hq1) =
      (q : ℝ) ^ 2 * ‖∑ i, h i‖ ^ 2 +
        (q : ℝ) * (1 - (q : ℝ)) * ∑ i, ‖h i‖ ^ 2 := by
  rw [rawSampledSum_norm_sq_integral_pairExpansion]
  exact pairCoefficient_sum_identity n d (q : ℝ) h


end Mf.Optimization.PoissonClippedSGD
