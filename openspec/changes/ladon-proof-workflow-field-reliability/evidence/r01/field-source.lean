import Mf.Optimization.FiniteMemoryAdam.CumulativePairing
import Mf.Optimization.FiniteMemoryAdam.AnchoredExpectation
import Mathlib.Analysis.SpecialFunctions.Log.Basic

namespace Mf.Optimization.FiniteMemoryAdam.Cumulative.Energy
open Finset Mf.Optimization.SDE
open Mf.Optimization.SDE.DPAdamBiasCorrectionTimeScaling
noncomputable section

def potential (β₂ ε : ℝ) (y : ℕ → ℝ) (t : ℕ) : ℝ := secondHistory β₂ y t + ε^2

theorem potential_pos {β₂ ε : ℝ} (hβ₂ : β₂ ∈ Set.Icc 0 1) (hε : 0 < ε)
    (y : ℕ → ℝ) (t : ℕ) : 0 < potential β₂ ε y t := by
  unfold potential
  exact add_pos_of_nonneg_of_pos (secondHistory_nonneg hβ₂.1 hβ₂.2 y t) (sq_pos_of_pos hε)

theorem potential_succ (β₂ ε : ℝ) (y : ℕ → ℝ) (t : ℕ) :
    potential β₂ ε y (t+1) = β₂*potential β₂ ε y t+(1-β₂)*(y t^2+ε^2) := by
  simp only [potential,secondHistory,nextSecond,Mf.Optimization.adamSecondMomentStep]
  ring

theorem potential_forgetting {β₂ ε : ℝ} (hβ₂ : β₂ ∈ Set.Icc 0 1)
    (y : ℕ → ℝ) (t : ℕ) : β₂*potential β₂ ε y t ≤ potential β₂ ε y (t+1) := by
  rw [potential_succ]
  nlinarith [mul_nonneg (sub_nonneg.mpr hβ₂.2) (add_nonneg (sq_nonneg (y t)) (sq_nonneg ε))]

theorem potential_history_le {β₂ ε : ℝ} (hβ₂ : β₂ ∈ Set.Icc 0 1)
    (y : ℕ → ℝ) (j k : ℕ) : β₂^k*potential β₂ ε y j ≤ potential β₂ ε y (j+k) := by
  induction k with
  | zero => simp
  | succ k ih =>
    have h := mul_le_mul_of_nonneg_left ih hβ₂.1
    have h' := potential_forgetting (ε := ε) hβ₂ y (j+k)
    calc
      _ = β₂*(β₂^k*potential β₂ ε y j) := by rw [pow_succ]; ring
      _ ≤ potential β₂ ε y (j+k+1) := h.trans h'
      _ = _ := by congr 1

/-- One logarithmic increment retains the forgetting penalty. -/
theorem normalized_energy_log_step {β₂ ε : ℝ} (hβ₂ : β₂ ∈ Set.Ioo 0 1) (hε : 0 < ε)
    (y : ℕ → ℝ) (t : ℕ) :
    (1-β₂)*(y t)^2/potential β₂ ε y (t+1) ≤
      Real.log (potential β₂ ε y (t+1))-Real.log (potential β₂ ε y t)-Real.log β₂ := by
  have hs := potential_pos ⟨hβ₂.1.le,hβ₂.2.le⟩ hε y (t+1)
  have hp := potential_pos ⟨hβ₂.1.le,hβ₂.2.le⟩ hε y t
  have hr : 0 < potential β₂ ε y (t+1)/(β₂*potential β₂ ε y t) := div_pos hs (mul_pos hβ₂.1 hp)
  have hl := Real.one_sub_inv_le_log_of_pos hr
  rw [Real.log_div hs.ne' (mul_pos hβ₂.1 hp).ne',Real.log_mul hβ₂.1.ne' hp.ne'] at hl
  have hi : (potential β₂ ε y (t+1)/(β₂*potential β₂ ε y t))⁻¹ =
      β₂*potential β₂ ε y t/potential β₂ ε y (t+1) := by rw [inv_div]
  rw [hi] at hl
  have hnum : (1-β₂)*y t^2 ≤ potential β₂ ε y (t+1)-β₂*potential β₂ ε y t := by
    rw [potential_succ]
    nlinarith [mul_nonneg (sub_nonneg.mpr hβ₂.2.le) (sq_nonneg ε)]
  have hdiv := div_le_div_of_nonneg_right hnum hs.le
  rw [sub_div,div_self hs.ne'] at hdiv
  linarith

/-- The logarithmic energy telescope holds for every signed release history. -/
theorem normalized_energy_log_sum {β₂ ε : ℝ} (hβ₂ : β₂ ∈ Set.Ioo 0 1) (hε : 0 < ε)
    (y : ℕ → ℝ) (T : ℕ) :
    (1-β₂)*(∑ t ∈ range T, y t^2/potential β₂ ε y (t+1)) ≤
      Real.log (potential β₂ ε y T/(ε^2))-(T:ℝ)*Real.log β₂ := by
  have hsum : (∑ t ∈ range T,
      (Real.log (potential β₂ ε y (t+1))-Real.log (potential β₂ ε y t)-Real.log β₂)) =
      Real.log (potential β₂ ε y T)-Real.log (ε^2)-(T:ℝ)*Real.log β₂ := by
    induction T with
    | zero => simp [potential,secondHistory]
    | succ T ih => rw [sum_range_succ,ih]; push_cast; ring
  have h := sum_le_sum (s := range T) (fun t _ => normalized_energy_log_step hβ₂ hε y t)
  rw [hsum] at h
  rw [Real.log_div (potential_pos ⟨hβ₂.1.le,hβ₂.2.le⟩ hε y T).ne' (sq_pos_of_pos hε).ne']
  simpa only [mul_sum,mul_div_assoc] using h
/-- The actual corrected direction is dominated by a raw-memory potential.
The proof potential does not replace the optimizer denominator. -/
theorem direction_square_le_potential {β₁ β₂ ε : ℝ}
    (hβ₁ : β₁ ∈ Set.Ico 0 1) (hβ₂ : β₂ ∈ Set.Ico 0 1) (hε : 0 < ε)
    (y : ℕ → ℝ) (t : ℕ) :
    (scalarDirection β₁ β₂ ε (t+1) (firstHistory β₁ y t)
      (secondHistory β₂ y t) (y t))^2 ≤
      (∑ j ∈ range (t+1), correctedGeometricWeight β₁ (t+1) j*y j^2) /
        potential β₂ ε y (t+1) := by
  have hv := secondHistory_nonneg hβ₂.1 hβ₂.2.le y (t+1)
  have hc := correction_pos hβ₂.1 hβ₂.2 (Nat.succ_pos t)
  have hpow : 0 ≤ β₂^(t+1) := pow_nonneg hβ₂.1 _
  have hvh : secondHistory β₂ y (t+1) ≤ secondHistory β₂ y (t+1)/(1-β₂^(t+1)) := by
    apply (le_div_iff₀ hc).mpr
    change secondHistory β₂ y (t+1)*(1-β₂^(t+1)) ≤ secondHistory β₂ y (t+1)
    nlinarith [mul_nonneg hv hpow]
  have hvh0 := hv.trans hvh
  have hm : firstHistory β₁ y (t+1)/(1-β₁^(t+1)) =
      ∑ j ∈ range (t+1), correctedGeometricWeight β₁ (t+1) j*y j := by
    simpa only [biasCorrectedFirstMoment,biasCorrectionMultiplier,div_eq_mul_inv,mul_comm] using
      firstHistory_corrected_eq β₁ y (t+1)
  have hj := AnchoredExpectation.sq_sum_weight_mul_le (range (t+1))
    (correctedGeometricWeight β₁ (t+1)) (fun _ => 1) y
    (fun j _ => correctedGeometricWeight_nonneg hβ₁.1 hβ₁.2 (t+1) j)
  simp only [one_mul,one_pow,mul_one,sum_correctedGeometricWeight hβ₁.1 hβ₁.2 (Nat.succ_pos t)] at hj
  let B := Real.sqrt (secondHistory β₂ y (t+1)/(1-β₂^(t+1)))+ε
  have hB : 0 < B := by dsimp [B]; positivity
  have hBS : potential β₂ ε y (t+1) ≤ B^2 := by
    dsimp [potential,B]
    have hs := Real.sq_sqrt hvh0
    have hs0 := Real.sqrt_nonneg (secondHistory β₂ y (t+1)/(1-β₂^(t+1)))
    nlinarith
  have hS := potential_pos ⟨hβ₂.1,hβ₂.2.le⟩ hε y (t+1)
  change ((firstHistory β₁ y (t+1)/(1-β₁^(t+1)))/B)^2 ≤ _
  rw [hm,div_pow]
  exact (div_le_div_of_nonneg_left (sq_nonneg _) hS hBS).trans
    (div_le_div_of_nonneg_right hj hS.le)

def convolution (b : ℝ) (f : ℕ → ℝ) (t : ℕ) : ℝ :=
  ∑ j ∈ range t, b^(t-1-j)*f j

theorem convolution_nonneg {b : ℝ} (hb : 0 ≤ b) {f : ℕ → ℝ} (hf : ∀ j, 0 ≤ f j) (t : ℕ) :
    0 ≤ convolution b f t := sum_nonneg (fun j _ => mul_nonneg (pow_nonneg hb _) (hf j))

theorem convolution_succ (b : ℝ) (f : ℕ → ℝ) (t : ℕ) :
    convolution b f (t+1) = b*convolution b f t+f t := by
  unfold convolution
  rw [sum_range_succ,mul_sum]
  have he : ∑ j ∈ range t, b^(t+1-1-j)*f j = ∑ j ∈ range t, b*(b^(t-1-j)*f j) := by
    apply sum_congr rfl
    intro j hj
    rw [show t+1-1-j = (t-1-j)+1 by have := mem_range.mp hj; omega,pow_succ]
    ring
  rw [he]
  simp

theorem convolution_telescope (b : ℝ) (f : ℕ → ℝ) (T : ℕ) :
    (1-b)*(∑ t ∈ range T, convolution b f (t+1)) =
      (∑ t ∈ range T, f t)-b*convolution b f T := by
  induction T with
  | zero => simp [convolution]
  | succ T ih =>
    rw [sum_range_succ,sum_range_succ,mul_add,ih,convolution_succ]
    ring

theorem convolution_sum_le {b : ℝ} (hb : b ∈ Set.Ico 0 1)
    {f : ℕ → ℝ} (hf : ∀ j, 0 ≤ f j) (T : ℕ) :
    (∑ t ∈ range T, convolution b f (t+1)) ≤ (∑ t ∈ range T, f t)/(1-b) := by
  apply (le_div_iff₀ (sub_pos.mpr hb.2)).mpr
  have he := convolution_telescope b f T
  have hp := mul_nonneg hb.1 (convolution_nonneg hb.1 hf T)
  nlinarith

/-- Same-history potential decay converts corrected memory into a geometric convolution. -/
theorem direction_square_le_convolution {β₁ β₂ ε : ℝ}
    (hβ₁ : β₁ ∈ Set.Ico 0 1) (hβ₂ : β₂ ∈ Set.Ioo 0 1) (hε : 0 < ε)
    (y : ℕ → ℝ) (t : ℕ) :
    (scalarDirection β₁ β₂ ε (t+1) (firstHistory β₁ y t)
      (secondHistory β₂ y t) (y t))^2 ≤
      (1-β₁)/(1-β₁^(t+1)) *
        convolution (β₁/β₂) (fun j => y j^2/potential β₂ ε y (j+1)) (t+1) := by
  apply (direction_square_le_potential hβ₁ ⟨hβ₂.1.le,hβ₂.2⟩ hε y t).trans
  unfold convolution
  rw [sum_div,mul_sum]
  apply sum_le_sum
  intro j hj
  have hjt : j ≤ t := by have := mem_range.mp hj; omega
  have hs := potential_history_le (ε := ε) ⟨hβ₂.1.le,hβ₂.2.le⟩ y (j+1) (t-j)
  rw [show j+1+(t-j)=t+1 by omega] at hs
  have hjS := potential_pos ⟨hβ₂.1.le,hβ₂.2.le⟩ hε y (j+1)
  have hp := pow_pos hβ₂.1 (t-j)
  have hn : 0 ≤ correctedGeometricWeight β₁ (t+1) j*y j^2 :=
    mul_nonneg (correctedGeometricWeight_nonneg hβ₁.1 hβ₁.2 _ _) (sq_nonneg _)
  apply (div_le_div_of_nonneg_left hn (mul_pos hp hjS) hs).trans_eq
  simp only [correctedGeometricWeight,Nat.add_sub_cancel,div_pow]
  field_simp

/-- The post-startup first-memory coefficient retains finite bias correction. -/
theorem correction_coefficient_le {β : ℝ} (hβ : β ∈ Set.Ico 0 1)
    {r t : ℕ} (hr : 0 < r) (hrt : r ≤ t) :
    (1-β)/(1-β^t) ≤ (1-β)/(1-β^r) := by
  have hp := pow_le_pow_of_le_one hβ.1 hβ.2.le hrt
  exact div_le_div_of_nonneg_left (sub_nonneg.mpr hβ.2.le)
    (correction_pos hβ.1 hβ.2 hr) (by linarith)

/-- The initial prefix is paid even when the chosen split exceeds the horizon. -/
theorem startup_charge_sum_le (T r : ℕ) {K : ℝ} :
    (∑ t ∈ range T, if t < r-1 then K^2 else 0) ≤ ((r-1:ℕ):ℝ)*K^2 := by
  rw [← sum_filter]
  calc
    _ ≤ ∑ _t ∈ range (r-1), K^2 := by
      apply sum_le_sum_of_subset_of_nonneg
      · intro t ht
        exact mem_range.mpr (mem_filter.mp ht).2
      · intro t _ _; exact sq_nonneg K
    _ = _ := by simp

/-- Universal initialized default-Adam energy; startup and forgetting are explicit. -/
theorem default_direction_energy_log_le {ε : ℝ} (hε : 0 < ε)
    (y : ℕ → ℝ) {r : ℕ} (hr : 0 < r) (T : ℕ) :
    (∑ t ∈ range T, (scalarDirection (9/10) (999/1000) ε (t+1)
      (firstHistory (9/10) y t) (secondHistory (999/1000) y t) (y t))^2) ≤
    ((r-1:ℕ):ℝ)*(73/10)^2 +
      ((1-(9/10:ℝ))/((1-(9/10:ℝ)^r)*(1-(9/10:ℝ)/(999/1000)))) /
        (1-(999/1000:ℝ)) *
      (Real.log (potential (999/1000) ε y T/(ε^2))-(T:ℝ)*Real.log (999/1000)) := by
  let f := fun j => y j^2/potential (999/1000) ε y (j+1)
  let A := (1-(9/10:ℝ))/(1-(9/10:ℝ)^r)
  have hA : 0 ≤ A := by
    dsimp [A]
    exact div_nonneg (by norm_num)
      (correction_pos (by norm_num : (0:ℝ) ≤ 9/10) (by norm_num : (9/10:ℝ)<1) hr).le
  have hf (j : ℕ) : 0 ≤ f j := div_nonneg (sq_nonneg _)
    (potential_pos (by norm_num : (999/1000:ℝ) ∈ Set.Icc 0 1) hε y (j+1)).le
  have he (t : ℕ) : (scalarDirection (9/10) (999/1000) ε (t+1)
      (firstHistory (9/10) y t) (secondHistory (999/1000) y t) (y t))^2 ≤
      (if t < r-1 then (73/10:ℝ)^2 else 0) + A*convolution ((9/10)/(999/1000)) f (t+1) := by
    have hc := convolution_nonneg (by norm_num : (0:ℝ) ≤ (9/10)/(999/1000)) hf (t+1)
    split_ifs with ht
    · have hb := default_history_direction_cap hε y t
      have hs := (sq_le_sq₀ (abs_nonneg _) (by norm_num : (0:ℝ) ≤ 73/10)).mpr hb
      rw [sq_abs] at hs
      linarith [mul_nonneg hA hc]
    · rw [zero_add]
      apply (direction_square_le_convolution (by norm_num : (9/10:ℝ) ∈ Set.Ico 0 1)
        (by norm_num : (999/1000:ℝ) ∈ Set.Ioo 0 1) hε y t).trans
      exact mul_le_mul_of_nonneg_right
        (correction_coefficient_le (by norm_num : (9/10:ℝ) ∈ Set.Ico 0 1) hr (by omega)) hc
  have hs := sum_le_sum (s := range T) (fun t _ => he t)
  rw [sum_add_distrib,← mul_sum] at hs
  have hconv := convolution_sum_le (by norm_num : ((9/10:ℝ)/(999/1000)) ∈ Set.Ico 0 1) hf T
  have hlog := normalized_energy_log_sum (by norm_num : (999/1000:ℝ) ∈ Set.Ioo 0 1) hε y T
  have hlog' : (∑ t ∈ range T, f t) ≤
      (Real.log (potential (999/1000) ε y T/ε^2)-(T:ℝ)*Real.log (999/1000))/(1-(999/1000:ℝ)) := by
    apply (le_div_iff₀ (by norm_num : (0:ℝ)<1-999/1000)).mpr
    simpa only [f,mul_comm] using hlog
  calc
    _ ≤ ((r-1:ℕ):ℝ)*(73/10)^2 + A*((∑ t ∈ range T, f t)/(1-(9/10:ℝ)/(999/1000))) :=
      hs.trans (add_le_add (startup_charge_sum_le T r) (mul_le_mul_of_nonneg_left hconv hA))
    _ ≤ ((r-1:ℕ):ℝ)*(73/10)^2 + A*
        (((Real.log (potential (999/1000) ε y T/ε^2)-(T:ℝ)*Real.log (999/1000))/(1-(999/1000:ℝ))) /
          (1-(9/10:ℝ)/(999/1000))) := by
      exact add_le_add_left (mul_le_mul_of_nonneg_left
        (div_le_div_of_nonneg_right hlog'
          (show (0:ℝ) ≤ 1-(9/10:ℝ)/(999/1000) by norm_num)) hA) _
    _ = _ := by
      dsimp [A]
      field_simp
      <;> ring

end
end Mf.Optimization.FiniteMemoryAdam.Cumulative.Energy
