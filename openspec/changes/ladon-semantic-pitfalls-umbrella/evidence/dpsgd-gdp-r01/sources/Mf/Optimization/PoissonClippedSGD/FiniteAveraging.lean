import Mathlib.Analysis.Real.Sqrt
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Tactic

/-!
# Averaging expected progress bounds

Finite Cauchy--Schwarz converts per-iterate square-root envelopes into a
square root of the average progress. A finite average also bounds at least
one expected-iterate value; this does not choose a best iterate per sample.
-/

noncomputable section

namespace Mf.Optimization.PoissonClippedSGD

open scoped BigOperators

/-- Finite Jensen/Cauchy bound for the square root under uniform averaging. -/
theorem average_sqrt_le_sqrt_average
    {T : ℕ} (hT : 0 < T) (p : Fin T → ℝ) (hp : ∀ i, 0 ≤ p i) :
    (∑ i, Real.sqrt (p i)) / (T : ℝ) ≤
      Real.sqrt ((∑ i, p i) / (T : ℝ)) := by
  have hsumSq : (∑ i : Fin T, Real.sqrt (p i)) ^ 2 ≤
      (T : ℝ) * ∑ i : Fin T, p i := by
    have hc := Finset.sum_mul_sq_le_sq_mul_sq Finset.univ
      (fun _ : Fin T => (1:ℝ)) (fun i => Real.sqrt (p i))
    have h := hc
    simpa [Real.sq_sqrt (hp _)] using h
  have hTreal : 0 < (T : ℝ) := Nat.cast_pos.mpr hT
  have hsum0 : 0 ≤ ∑ i : Fin T, Real.sqrt (p i) :=
    Finset.sum_nonneg (by intro i hi; exact Real.sqrt_nonneg _)
  have hpavg0 : 0 ≤ (∑ i : Fin T, p i)/(T:ℝ) :=
    div_nonneg (Finset.sum_nonneg (by intro i hi; exact hp i)) hTreal.le
  apply (Real.le_sqrt (div_nonneg hsum0 hTreal.le) hpavg0).2
  change ((∑ i : Fin T, Real.sqrt (p i)) / (T : ℝ)) ^ 2 ≤
    (∑ i : Fin T, p i) / (T : ℝ)
  have hdiv := div_le_div_of_nonneg_right hsumSq (sq_nonneg (T:ℝ))
  have hTne : (T:ℝ) ≠ 0 := hTreal.ne'
  have hsimplify : ((T:ℝ) * (∑ i : Fin T, p i)) / (T:ℝ)^2 =
      (∑ i : Fin T, p i)/(T:ℝ) := by field_simp [hTne]
  rw [div_pow]
  rw [hsimplify] at hdiv
  exact hdiv

/-- The target expression is controlled by the average pointwise envelope. -/
theorem finite_average_sqrt_plus_linear_bound
    {T : ℕ} (hT : 0 < T) (c D : ℝ) (hc : 0 < c)
    (p g : Fin T → ℝ) (hp : ∀ i, 0 ≤ p i)
    (hpoint : ∀ i, g i ≤ Real.sqrt (p i) + p i / c)
    (havg : (∑ i, p i)/(T:ℝ) ≤ D) :
    (∑ i, g i)/(T:ℝ) ≤ Real.sqrt D + D/c := by
  let avgP : ℝ := (∑ i, p i)/(T:ℝ)
  have hTreal : 0 < (T:ℝ) := Nat.cast_pos.mpr hT
  have hpavg0 : 0 ≤ avgP := by
    dsimp [avgP]
    exact div_nonneg (Finset.sum_nonneg (by intro i hi; exact hp i)) hTreal.le
  have hD : 0 ≤ D := hpavg0.trans havg
  have hsum : (∑ i, g i) ≤ (∑ i, Real.sqrt (p i)) + (∑ i, p i)/c := by
    calc
      (∑ i, g i) ≤ ∑ i, (Real.sqrt (p i) + p i/c) :=
        Finset.sum_le_sum (by intro i hi; exact hpoint i)
      _ = (∑ i, Real.sqrt (p i)) + (∑ i, p i)/c := by
        rw [Finset.sum_add_distrib, ← Finset.sum_div]
  have havgG : (∑ i, g i)/(T:ℝ) ≤
      (∑ i, Real.sqrt (p i))/(T:ℝ) + avgP/c := by
    calc
      (∑ i, g i)/(T:ℝ) ≤ ((∑ i, Real.sqrt (p i)) + (∑ i, p i)/c)/(T:ℝ) :=
        div_le_div_of_nonneg_right hsum hTreal.le
      _ = (∑ i, Real.sqrt (p i))/(T:ℝ) + avgP/c := by
        dsimp [avgP]
        field_simp [hTreal.ne', hc.ne']
  have hroot := average_sqrt_le_sqrt_average hT p hp
  have hrootD : Real.sqrt avgP ≤ Real.sqrt D := Real.sqrt_le_sqrt havg
  have hratio : avgP/c ≤ D/c := div_le_div_of_nonneg_right havg hc.le
  calc
    (∑ i, g i)/(T:ℝ) ≤ (∑ i, Real.sqrt (p i))/(T:ℝ) + avgP/c := havgG
    _ ≤ Real.sqrt D + D/c := by
      calc
        (∑ i, Real.sqrt (p i))/(T:ℝ) + avgP/c ≤ Real.sqrt avgP + D/c :=
          add_le_add hroot hratio
        _ ≤ Real.sqrt D + D/c := add_le_add hrootD le_rfl

/-- A finite average is attained or exceeded by at least one term. -/
theorem exists_term_le_finite_average
    {T : ℕ} (hT : 0 < T) (g : Fin T → ℝ) :
    ∃ i, g i ≤ (∑ j, g j)/(T:ℝ) := by
  let avg : ℝ := (∑ j : Fin T, g j)/(T:ℝ)
  by_contra hn
  have hall : ∀ i : Fin T, avg < g i := by
    intro i
    have hnot : ¬ g i ≤ avg := by
      intro hi
      exact hn ⟨i, by simpa [avg] using hi⟩
    exact lt_of_not_ge hnot
  have hsumlt : (∑ i : Fin T, avg) < ∑ i : Fin T, g i := by
    apply Finset.sum_lt_sum
    · intro i hi
      exact (hall i).le
    · exact ⟨⟨0, hT⟩, Finset.mem_univ _, hall ⟨0, hT⟩⟩
  have hTreal : 0 < (T:ℝ) := Nat.cast_pos.mpr hT
  have hsumavg : (∑ i : Fin T, avg) = (∑ i : Fin T, g i) := by
    dsimp [avg]
    simp only [Finset.sum_const, Finset.card_fin, nsmul_eq_mul]
    field_simp [hTreal.ne']
  rw [hsumavg] at hsumlt
  exact (lt_irrefl _ hsumlt)

end Mf.Optimization.PoissonClippedSGD
