import Mf.Optimization.PoissonClippedSGD.History
import Mathlib.Algebra.BigOperators.Group.Finset.Basic

/-!
# Finite-horizon expected descent

This intermediate owner telescopes a one-step expected-descent inequality
through the actual independent-history recursion. Product integrability follows
from the next iterate's objective integrability via the history equivalence.
The concrete convergence theorem must supply the one-step and integrability
premises from the Gaussian mechanism.
-/

namespace Mf.Optimization.PoissonClippedSGD.Trajectory
open MeasureTheory
noncomputable section

variable {d : ℕ} {Mask : Type*} [MeasurableSpace Mask]

/-- Expected descent telescopes over the actual finite iid recursion. -/
theorem run_average_potential_le
    (ν : Measure (Step d Mask)) [IsProbabilityMeasure ν]
    (η error fLower : ℝ) (h : V d → Mask → V d) (x₀ : V d)
    (f φ : V d → ℝ) (T : ℕ)
    (hη : 0 < η) (herr : 0 ≤ error) (hlower : ∀ t (ω : History d Mask t),
      fLower ≤ f (run η h x₀ t ω))
    (hstep : ∀ x, (∫ sample : Step d Mask, f (update η h x sample) ∂ν) ≤
      f x - η / 4 * φ x + error)
    (hf : ∀ t, Integrable (fun ω : History d Mask t => f (run η h x₀ t ω))
      (historyLaw ν t))
    (hφ : ∀ t, Integrable (fun ω : History d Mask t => φ (run η h x₀ t ω))
      (historyLaw ν t))
    (hT : 0 < T) :
    (1 / T) * ∑ t ∈ Finset.range T,
      (∫ ω : History d Mask t, φ (run η h x₀ t ω) ∂historyLaw ν t) ≤
      4 * (f x₀ - fLower) / (η * T) + 4 * error / η := by
  have hstepInt (t : ℕ) :
      (∫ ω : History d Mask (t + 1), f (run η h x₀ (t + 1) ω)
        ∂historyLaw ν (t + 1)) ≤
      (∫ ω : History d Mask t, f (run η h x₀ t ω)
        ∂historyLaw ν t) - η / 4 *
        (∫ ω : History d Mask t, φ (run η h x₀ t ω) ∂historyLaw ν t) + error := by
    let split := fun ω : History d Mask (t + 1) => (ω 0, Fin.tail ω)
    letI : IsProbabilityMeasure (historyLaw ν t) := by dsimp [historyLaw]; infer_instance
    letI : IsProbabilityMeasure (historyLaw ν (t + 1)) := by dsimp [historyLaw]; infer_instance
    have hmp := history_split (d := d) (Mask := Mask) ν t
    have hfull := hf (t + 1)
    have hprod : Integrable
        (fun p : Step d Mask × History d Mask t =>
          f (update η h (run η h x₀ t p.2) p.1))
        (ν.prod (historyLaw ν t)) := by
      have hcomp : Integrable
          ((fun p : Step d Mask × History d Mask t =>
            f (update η h (run η h x₀ t p.2) p.1)) ∘ split)
          (historyLaw ν (t + 1)) ↔ Integrable
          (fun p : Step d Mask × History d Mask t =>
            f (update η h (run η h x₀ t p.2) p.1))
          (ν.prod (historyLaw ν t)) :=
        hmp.integrable_comp_emb
          (history_split_measurableEmbedding (d := d) (Mask := Mask) t)
      have hcompEq :
          (fun p : Step d Mask × History d Mask t =>
            f (update η h (run η h x₀ t p.2) p.1)) ∘ split =
          fun ω : History d Mask (t + 1) =>
            f (update η h (run η h x₀ t (Fin.tail ω)) (ω 0)) := by
        funext ω
        rfl
      have hcompFull : Integrable
          ((fun p : Step d Mask × History d Mask t =>
            f (update η h (run η h x₀ t p.2) p.1)) ∘ split)
          (historyLaw ν (t + 1)) := by
        rw [hcompEq]
        exact hfull
      exact hcomp.mp hcompFull
    rw [run_succ_integral_fubini ν η h x₀ t f hprod]
    have hleft : Integrable
        (fun past : History d Mask t => ∫ sample : Step d Mask,
          f (update η h (run η h x₀ t past) sample) ∂ν)
        (historyLaw ν t) := hprod.swap.integral_prod_left
    have hright : Integrable
        (fun past : History d Mask t =>
          f (run η h x₀ t past) - η / 4 * φ (run η h x₀ t past) + error)
        (historyLaw ν t) := by
      exact ((hf t).sub ((hφ t).const_mul (η / 4))).add (integrable_const error)
    calc
      (∫ past : History d Mask t, ∫ sample : Step d Mask,
          f (update η h (run η h x₀ t past) sample) ∂ν ∂historyLaw ν t) ≤
        ∫ past : History d Mask t,
          (f (run η h x₀ t past) - η / 4 * φ (run η h x₀ t past) + error)
          ∂historyLaw ν t := by
            apply integral_mono hleft hright
            intro past
            exact hstep (run η h x₀ t past)
      _ = (∫ ω : History d Mask t, f (run η h x₀ t ω) ∂historyLaw ν t) -
          η / 4 * (∫ ω : History d Mask t, φ (run η h x₀ t ω)
            ∂historyLaw ν t) + error := by
        have hsub : Integrable
            (fun ω : History d Mask t => f (run η h x₀ t ω) -
              η / 4 * φ (run η h x₀ t ω)) (historyLaw ν t) :=
          (hf t).sub ((hφ t).const_mul (η / 4))
        have hconst : Integrable (fun _ : History d Mask t => error)
            (historyLaw ν t) := integrable_const error
        have hsumfun : (fun ω : History d Mask t =>
            f (run η h x₀ t ω) - η / 4 * φ (run η h x₀ t ω) + error) =
            (fun ω => f (run η h x₀ t ω) - η / 4 * φ (run η h x₀ t ω)) +
              (fun _ => error) := rfl
        rw [hsumfun]
        change (∫ ω : History d Mask t,
          (f (run η h x₀ t ω) - η / 4 * φ (run η h x₀ t ω)) + error
          ∂historyLaw ν t) = _
        rw [integral_add hsub hconst]
        rw [integral_sub (hf t) ((hφ t).const_mul (η / 4)), integral_const_mul]
        simp [integral_const, measure_univ]
        <;> ring_nf
  have htelescope :
      (η / 4) * ∑ t ∈ Finset.range T,
        (∫ ω : History d Mask t, φ (run η h x₀ t ω) ∂historyLaw ν t) ≤
      f x₀ - fLower + T * error := by
    let A : ℕ → ℝ := fun n =>
      ∫ ω : History d Mask n, f (run η h x₀ n ω) ∂historyLaw ν n
    have hsumAll : ∀ n, ∑ t ∈ Finset.range n, (A t - A (t + 1)) = A 0 - A n := by
      intro n
      induction n with
      | zero => simp
      | succ n ih =>
        simp only [Finset.sum_range_succ]
        rw [ih]
        ring
    have hsum := hsumAll T
    have hstepSum :
        ∑ t ∈ Finset.range T,
          ((η / 4) * (∫ ω : History d Mask t,
            φ (run η h x₀ t ω) ∂historyLaw ν t)) ≤
        ∑ t ∈ Finset.range T,
          ((∫ ω : History d Mask t, f (run η h x₀ t ω) ∂historyLaw ν t) -
            (∫ ω : History d Mask (t + 1), f (run η h x₀ (t + 1) ω)
              ∂historyLaw ν (t + 1)) + error) := by
      apply Finset.sum_le_sum
      intro t ht
      have hs := hstepInt t
      linarith
    have hstart : A 0 = f x₀ := by simp [A, run, historyLaw]
    have hfinal : fLower ≤ A T := by
      letI : IsProbabilityMeasure (historyLaw ν T) := by dsimp [historyLaw]; infer_instance
      calc
        fLower = ∫ _ω : History d Mask T, fLower ∂historyLaw ν T := by simp
        _ ≤ ∫ ω : History d Mask T, f (run η h x₀ T ω) ∂historyLaw ν T :=
          integral_mono (integrable_const fLower) (hf T) (fun ω => hlower T ω)
        _ = A T := rfl
    have hsumError : ∑ t ∈ Finset.range T, error = (T : ℝ) * error := by simp
    have hsumrhs :
        (∑ t ∈ Finset.range T,
          ((∫ ω : History d Mask t, f (run η h x₀ t ω) ∂historyLaw ν t) -
            (∫ ω : History d Mask (t + 1), f (run η h x₀ (t + 1) ω)
              ∂historyLaw ν (t + 1)) + error)) =
        A 0 - A T + (T : ℝ) * error := by
      have hsumdiff : ∑ t ∈ Finset.range T, (A t - A (t + 1)) = A 0 - A T := hsum
      calc
        _ = (∑ t ∈ Finset.range T, (A t - A (t + 1))) +
              ∑ t ∈ Finset.range T, error := by
                rw [Finset.sum_add_distrib]

        _ = A 0 - A T + (T : ℝ) * error := by rw [hsumdiff, hsumError]
    have hss : (η / 4) * ∑ t ∈ Finset.range T,
        (∫ ω : History d Mask t, φ (run η h x₀ t ω) ∂historyLaw ν t) ≤
        A 0 - A T + (T : ℝ) * error := by
      have hh := hstepSum
      rw [← Finset.mul_sum] at hh
      rw [hsumrhs] at hh
      exact hh
    rw [hstart] at hss
    linarith
  have hcoef : 0 ≤ 4 / (η * T) := by positivity
  have hscaled := mul_le_mul_of_nonneg_right htelescope hcoef
  have hleftEq : (1 / (T : ℝ)) *
      (∑ t ∈ Finset.range T,
        (∫ ω : History d Mask t, φ (run η h x₀ t ω) ∂historyLaw ν t)) =
      ((η / 4) * ∑ t ∈ Finset.range T,
        (∫ ω : History d Mask t, φ (run η h x₀ t ω) ∂historyLaw ν t)) *
        (4 / (η * T)) := by
    field_simp
    <;> ring
  have hrightEq :
      (f x₀ - fLower + (T : ℝ) * error) * (4 / (η * T)) =
        4 * (f x₀ - fLower) / (η * T) + 4 * error / η := by
    field_simp
    <;> ring
  calc
    (1 / (T : ℝ)) *
        (∑ t ∈ Finset.range T,
          (∫ ω : History d Mask t, φ (run η h x₀ t ω) ∂historyLaw ν t)) =
      ((η / 4) * ∑ t ∈ Finset.range T,
        (∫ ω : History d Mask t, φ (run η h x₀ t ω) ∂historyLaw ν t)) *
        (4 / (η * T)) := hleftEq
    _ ≤ (f x₀ - fLower + (T : ℝ) * error) * (4 / (η * T)) := hscaled
    _ = 4 * (f x₀ - fLower) / (η * T) + 4 * error / η := hrightEq
/-- The same average bound expressed on one common finite-horizon history space. -/
theorem commonHistory_average_potential_le
    (ν : Measure (Step d Mask)) [IsProbabilityMeasure ν]
    (η error fLower : ℝ) (h : V d → Mask → V d) (x₀ : V d)
    (f φ : V d → ℝ) (T : ℕ)
    (hη : 0 < η) (herr : 0 ≤ error) (hlower : ∀ t (ω : History d Mask t),
      fLower ≤ f (run η h x₀ t ω))
    (hstep : ∀ x, (∫ sample : Step d Mask, f (update η h x sample) ∂ν) ≤
      f x - η / 4 * φ x + error)
    (hf : ∀ t, Integrable (fun ω : History d Mask t => f (run η h x₀ t ω))
      (historyLaw ν t))
    (hφ : ∀ t, Integrable (fun ω : History d Mask t => φ (run η h x₀ t ω))
      (historyLaw ν t))
    (hT : 0 < T) :
    (1 / T) * ∑ t ∈ Finset.range T,
      (∫ ω : History d Mask T, φ (iterateOnHistory η h x₀ T (min t T) (Nat.min_le_right t T) ω)
        ∂historyLaw ν T) ≤
      4 * (f x₀ - fLower) / (η * T) + 4 * error / η := by
  have hmarginal := run_average_potential_le ν η error fLower h x₀ f φ T hη herr
    hlower hstep hf hφ hT
  have heq : (∑ t ∈ Finset.range T,
      (∫ ω : History d Mask T, φ (iterateOnHistory η h x₀ T (min t T) (Nat.min_le_right t T) ω)
        ∂historyLaw ν T)) =
    ∑ t ∈ Finset.range T,
      (∫ ω : History d Mask t, φ (run η h x₀ t ω) ∂historyLaw ν t) := by
    apply Finset.sum_congr rfl
    intro t ht
    have hmin : min t T = t := Nat.min_eq_left (Nat.le_of_lt (by simpa using ht))
    have htrans := iterateOnHistory_integral_eq ν η h x₀
      (Nat.min_le_right t T) φ (hφ (min t T))
    convert htrans using 1
    rw [hmin]
  rw [heq]
  exact hmarginal

private theorem sum_fin_eq_sum_range_real {T : ℕ} (g : ℕ → ℝ) :
    (∑ i : Fin T, g i.val) = ∑ t ∈ Finset.range T, g t := by
  classical
  apply Finset.sum_bij (s := Finset.univ) (t := Finset.range T)
    (fun i _ => i.val)
  · intro i hi
    exact Finset.mem_range.mpr i.isLt
  · intro i hi j hj hij
    exact Fin.ext hij
  · intro b hb
    have hb' : b < T := Finset.mem_range.mp hb
    exact ⟨⟨b, hb'⟩, Finset.mem_univ _, rfl⟩
  · intro i hi
    rfl

/-- Common-history average with the usual `Fin T` time index. -/
theorem commonHistory_fin_average_potential_le
    (ν : Measure (Step d Mask)) [IsProbabilityMeasure ν]
    (η error fLower : ℝ) (h : V d → Mask → V d) (x₀ : V d)
    (f φ : V d → ℝ) (T : ℕ)
    (hη : 0 < η) (herr : 0 ≤ error) (hlower : ∀ t (ω : History d Mask t),
      fLower ≤ f (run η h x₀ t ω))
    (hstep : ∀ x, (∫ sample : Step d Mask, f (update η h x sample) ∂ν) ≤
      f x - η / 4 * φ x + error)
    (hf : ∀ t, Integrable (fun ω : History d Mask t => f (run η h x₀ t ω))
      (historyLaw ν t))
    (hφ : ∀ t, Integrable (fun ω : History d Mask t => φ (run η h x₀ t ω))
      (historyLaw ν t))
    (hT : 0 < T) :
    (1 / T) * ∑ i : Fin T,
      (∫ ω : History d Mask T, φ (iterateOnHistory η h x₀ T i.val i.isLt.le ω)
        ∂historyLaw ν T) ≤
      4 * (f x₀ - fLower) / (η * T) + 4 * error / η := by
  let g : ℕ → ℝ := fun t =>
    ∫ ω : History d Mask T,
      φ (iterateOnHistory η h x₀ T (min t T) (Nat.min_le_right t T) ω)
      ∂historyLaw ν T
  have hsum : (∑ i : Fin T,
      (∫ ω : History d Mask T,
        φ (iterateOnHistory η h x₀ T i.val i.isLt.le ω) ∂historyLaw ν T)) =
      ∑ t ∈ Finset.range T, g t := by
    apply Finset.sum_bij (s := Finset.univ) (t := Finset.range T)
      (fun i _ => i.val)
    · intro i hi
      exact Finset.mem_range.mpr i.isLt
    · intro i hi j hj hij
      exact Fin.ext hij
    · intro b hb
      have hb' : b < T := Finset.mem_range.mp hb
      exact ⟨⟨b, hb'⟩, Finset.mem_univ _, rfl⟩
    · intro i hi
      dsimp [g]
      have hm : min i.val T = i.val := Nat.min_eq_left (Nat.le_of_lt i.isLt)
      simpa only [hm]
  have hrange := commonHistory_average_potential_le ν η error fLower h x₀ f φ T
    hη herr hlower hstep hf hφ hT
  rw [hsum]
  exact hrange

