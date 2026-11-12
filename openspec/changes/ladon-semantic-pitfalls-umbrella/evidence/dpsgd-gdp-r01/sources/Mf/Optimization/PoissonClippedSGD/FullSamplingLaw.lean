import Mf.Optimization.PoissonClippedSGD.BernoulliMoments

/-! # Full sampling as an exact law

At rate one the product Bernoulli mask is the all-true mask. This identity
can remove sampling variability from any actual public-denominator consumer.
-/
noncomputable section
open MeasureTheory ProbabilityTheory
open scoped BigOperators
namespace Mf.Optimization.PoissonClippedSGD

theorem bernoulli_one_toMeasure :
    (PMF.bernoulli (1:NNReal) (by simp)).toMeasure = Measure.dirac true := by
  have hp : PMF.bernoulli (1:NNReal) (by simp) = PMF.pure true := by
    ext b
    cases b <;> simp [PMF.bernoulli_apply]
  rw [hp, PMF.toMeasure_pure]

theorem maskLaw_one (N : ℕ) :
    maskLaw N 1 (by simp) =
      Measure.dirac (fun _ : Fin N => true) := by
  classical
  unfold maskLaw
  simp_rw [bernoulli_one_toMeasure]
  apply Measure.pi_eq
  intro sets hsets
  rw [Measure.dirac_apply' _ (MeasurableSet.univ_pi hsets)]
  by_cases h : ∀ i, true ∈ sets i
  · simp [Set.mem_pi, h, Measure.dirac_apply' _ (hsets _)]
  · have hex : ∃ i, true ∉ sets i := not_forall.mp h
    obtain ⟨i,hi⟩ := hex
    have hnot : (fun _ : Fin N => true) ∉ Set.pi Set.univ sets := by
      simpa [Set.mem_pi] using h
    rw [Set.indicator_of_notMem hnot]
    symm
    apply Finset.prod_eq_zero_iff.mpr
    refine ⟨i,Finset.mem_univ _,?_⟩
    simp [Measure.dirac_apply' _ (hsets i), hi]

end Mf.Optimization.PoissonClippedSGD
