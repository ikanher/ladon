import Mf.Optimization.PoissonClippedSGD.FiniteMeans
import Mf.Optimization.PoissonClippedSGD.ClippingBias
import Mf.Optimization.FiniteMemoryAdam.ClippingAdaptedPairing

/-!
# Record clipping from a centered second-moment bound

The ordinary clipped mean splits into a positive multiple of the actual
record mean and a centered deviation term. A second-moment bound alone gives
both a lower attenuation profile and the bias bound `min(s, s^2 / C)`.
No uniform record-deviation bound or individual gradient regularity is used.

The radial clipping multiplier is `1/C`-Lipschitz. Centering its deviation
before taking norms yields the quadratic bias bound; finite reciprocal
Jensen and Cauchy--Schwarz give the attenuation profile. These are query
bounds, prior to any adaptive optimizer normalization.
-/

namespace Mf.Optimization.PoissonClippedSGD.ClippingVariance

noncomputable section
set_option autoImplicit false
open scoped BigOperators
open Mf.Optimization.PoissonClippedSGD
open Mf.Optimization.FiniteMemoryAdam.ClippingAdapted
open Mf.DP

variable {n d : ℕ}

/-- Scalar radial factor as a function of the input norm. -/
def radialClipFactor (C r : ℝ) : ℝ := C / max C r

/-- Scalar multiplier in radial clipping at radius `C`. -/
def clipWeight (C : ℝ) (x : EuclideanSpace ℝ (Fin d)) : ℝ :=
  radialClipFactor C ‖x‖

/-- Mean multiplier of the recordwise radial clip. -/
def meanClipWeight (C : ℝ) (g : Fin n → EuclideanSpace ℝ (Fin d)) : ℝ :=
  (n : ℝ)⁻¹ * ∑ i, clipWeight C (g i)

/-- Centered clipping charge after extracting the mean multiplier. -/
def centeredClipBias (C : ℝ) (g : Fin n → EuclideanSpace ℝ (Fin d)) :
    EuclideanSpace ℝ (Fin d) :=
  vectorMean fun i => clipWeight C (g i) • (g i - vectorMean g)

/-- Radial clipping is multiplication by its scalar clipping factor. -/
theorem euclideanBallClip_eq_clipWeight_smul
    {C : ℝ} (hC : 0 < C) (x : EuclideanSpace ℝ (Fin d)) :
    euclideanBallClip C x = clipWeight C x • x := by
  by_cases hx : ‖x‖ ≤ C
  · rw [euclideanBallClip, if_pos hx, clipWeight, radialClipFactor, max_eq_left hx]
    rw [div_self (ne_of_gt hC), one_smul]
  · have hxC : C < ‖x‖ := lt_of_not_ge hx
    rw [euclideanBallClip, if_neg hx, clipWeight, radialClipFactor, max_eq_right hxC.le]

/-- The radial multiplier is in `[0,1]`. -/
theorem clipWeight_mem_Icc_one
    {C : ℝ} (hC : 0 < C) (x : EuclideanSpace ℝ (Fin d)) :
    clipWeight C x ∈ Set.Icc 0 1 := by
  unfold clipWeight radialClipFactor
  have hden : 0 < max C ‖x‖ := hC.trans_le (le_max_left _ _)
  constructor
  · exact div_nonneg hC.le hden.le
  · exact (div_le_one hden).2 (le_max_left _ _)

/-- The scalar radial factor is `1/C`-Lipschitz on nonnegative radii. -/
theorem radialClipFactor_sub_le
    {C r s : ℝ} (hC : 0 < C) (hr : 0 ≤ r) (hs : 0 ≤ s) :
    |radialClipFactor C r - radialClipFactor C s| ≤ |r - s| / C := by
  have hcross (lo hi : ℝ) (hlo : 0 ≤ lo) (hhi : C < hi)
      (hloC : lo ≤ C) :
      |radialClipFactor C lo-radialClipFactor C hi| ≤ |lo-hi|/C := by
    have hhipos : 0 < hi := hC.trans hhi
    rw [radialClipFactor, max_eq_left hloC, radialClipFactor, max_eq_right hhi.le]
    have hleft : 0 ≤ 1-C/hi := by
      exact (sub_nonneg.mpr ((div_le_one hhipos).2 hhi.le))
    have hright : lo-hi ≤ 0 := by linarith
    rw [show C / C = 1 by rw [div_self hC.ne'], abs_of_nonneg hleft,
      abs_of_nonpos hright]
    have hform : 1-C/hi = (hi-C)/hi := by field_simp
    rw [hform, div_le_div_iff₀ hhipos hC]
    have hfactor : C*(hi-C) ≤ hi*(hi-lo) := by nlinarith
    nlinarith [hfactor]
  by_cases hrC : r ≤ C <;> by_cases hsC : s ≤ C
  · simp [radialClipFactor, max_eq_left hrC, max_eq_left hsC, div_self hC.ne']
    exact div_nonneg (abs_nonneg _) hC.le
  · exact hcross r s hr (lt_of_not_ge hsC) hrC
  · have h := hcross s r hs (lt_of_not_ge hrC) hsC
    simpa [abs_sub_comm] using h
  · have hr : C < r := lt_of_not_ge hrC
    have hs : C < s := lt_of_not_ge hsC
    have hrpos : 0 < r := hC.trans hr
    have hspos : 0 < s := hC.trans hs
    have hprod : C^2 ≤ r*s := by nlinarith [mul_nonneg (sub_nonneg.mpr hr.le) (sub_nonneg.mpr hs.le)]
    by_cases hrs : r ≤ s
    · have hfactor : C/r-C/s = C*(s-r)/(r*s) := by field_simp
      rw [radialClipFactor, max_eq_right hr.le, radialClipFactor, max_eq_right hs.le,
        hfactor, abs_of_nonneg (div_nonneg (mul_nonneg hC.le (sub_nonneg.mpr hrs)) (mul_nonneg hrpos.le hspos.le)),
        abs_of_nonpos (by linarith)]
      rw [div_le_div_iff₀ (mul_pos hrpos hspos) hC]
      nlinarith [mul_nonneg (sub_nonneg.mpr hrs) (sub_nonneg.mpr hprod)]
    · have hsr : s ≤ r := le_of_lt (lt_of_not_ge hrs)
      have hfactor : C/s-C/r = C*(r-s)/(r*s) := by field_simp
      rw [abs_sub_comm, radialClipFactor, max_eq_right hs.le, radialClipFactor, max_eq_right hr.le,
        hfactor, abs_of_nonneg (div_nonneg (mul_nonneg hC.le (sub_nonneg.mpr hsr)) (mul_nonneg hrpos.le hspos.le)),
        abs_of_nonneg (sub_nonneg.mpr hsr)]
      rw [div_le_div_iff₀ (mul_pos hrpos hspos) hC]
      nlinarith [mul_nonneg (sub_nonneg.mpr hsr) (sub_nonneg.mpr hprod)]

/-- The vector clipping multiplier is `1/C`-Lipschitz in its input. -/
theorem clipWeight_sub_le_norm_div
    {C : ℝ} (hC : 0 < C) (x y : EuclideanSpace ℝ (Fin d)) :
    |clipWeight C x - clipWeight C y| ≤ ‖x - y‖ / C := by
  unfold clipWeight
  calc
    |radialClipFactor C ‖x‖ - radialClipFactor C ‖y‖| ≤
        |‖x‖ - ‖y‖| / C :=
      radialClipFactor_sub_le hC (norm_nonneg _) (norm_nonneg _)
    _ ≤ ‖x - y‖ / C := by
      exact div_le_div_of_nonneg_right (abs_norm_sub_norm_le x y) hC.le

/-- The mean clipped query splits into an attenuated population mean and a
centered record clipping charge. -/
theorem clippedMean_eq_meanWeight_smul_add_bias
    {C : ℝ} (hC : 0 < C) (g : Fin n → EuclideanSpace ℝ (Fin d)) :
    clippedMean C g = meanClipWeight C g • vectorMean g + centeredClipBias C g := by
  let G := vectorMean g
  have hclip (i : Fin n) := euclideanBallClip_eq_clipWeight_smul hC (g i)
  have hdecomp (i : Fin n) : g i = G + (g i - G) := by abel
  calc
    clippedMean C g =
        vectorMean (fun i => clipWeight C (g i) • G +
          clipWeight C (g i) • (g i - G)) := by
      unfold clippedMean
      congr 1
      funext i
      calc
        euclideanBallClip C (g i) = clipWeight C (g i) • g i := hclip i
        _ = clipWeight C (g i) • (G + (g i - G)) := by congr 1 <;> abel
        _ = _ := by rw [smul_add]
    _ = meanClipWeight C g • vectorMean g + centeredClipBias C g := by
      have hadd (f h : Fin n → EuclideanSpace ℝ (Fin d)) :
          vectorMean (fun i => f i+h i) = vectorMean f+vectorMean h := by
        unfold vectorMean
        rw [Finset.sum_add_distrib, smul_add]
      have hfirst : vectorMean (fun i => clipWeight C (g i) • G) =
          meanClipWeight C g • vectorMean g := by
        unfold vectorMean meanClipWeight
        rw [← Finset.sum_smul]
        change (n:ℝ)⁻¹ • ((∑ i, clipWeight C (g i)) • G) =
          ((n:ℝ)⁻¹ * ∑ i, clipWeight C (g i)) • ((n:ℝ)⁻¹ • ∑ i, g i)
        rw [show G = (n:ℝ)⁻¹ • ∑ i, g i by rfl, smul_smul, smul_smul]
      rw [hadd, hfirst]
      rfl

/-- The centered clipping charge has the first-moment bound `s`. -/
theorem centeredClipBias_norm_le
    {C s : ℝ} (hC : 0 < C) (hn : 0 < n) (hs : 0 ≤ s)
    (g : Fin n → EuclideanSpace ℝ (Fin d))
    (hvar : meanSqDeviation g (vectorMean g) ≤ s ^ 2) :
    ‖centeredClipBias C g‖ ≤ s := by
  let δ : Fin n → EuclideanSpace ℝ (Fin d) := fun i => g i-vectorMean g
  have hcs : (∑ i, ‖δ i‖)^2 ≤ (n : ℝ) * ∑ i, ‖δ i‖^2 := by
    simpa using (Finset.sum_mul_sq_le_sq_mul_sq (Finset.univ : Finset (Fin n))
      (fun _ : Fin n => (1 : ℝ)) (fun i => ‖δ i‖))
  have hnR : (n : ℝ) ≠ 0 := by exact_mod_cast (Nat.ne_of_gt hn)
  have hmeanSq : ((n : ℝ)⁻¹ * ∑ i, ‖δ i‖)^2 ≤ meanSqDeviation g (vectorMean g) := by
    rw [meanSqDeviation]
    have hdiv := div_le_div_of_nonneg_right hcs (sq_nonneg (n : ℝ))
    have hne : (n : ℝ)^2 ≠ 0 := pow_ne_zero 2 hnR
    have heq : ((n : ℝ)⁻¹ * ∑ i, ‖δ i‖)^2 = (∑ i, ‖δ i‖)^2 / (n : ℝ)^2 := by
      field_simp [hnR] <;> ring
    rw [heq]
    calc
      (∑ i, ‖δ i‖)^2 / (n : ℝ)^2 ≤ ((n : ℝ) * ∑ i, ‖δ i‖^2) / (n : ℝ)^2 :=
        div_le_div_of_nonneg_right hcs (sq_nonneg _)
      _ = (n : ℝ)⁻¹ * ∑ i, ‖δ i‖^2 := by field_simp [hnR] <;> ring
  have havg : (n : ℝ)⁻¹ * ∑ i, ‖δ i‖ ≤ s := by
    have hnonneg : 0 ≤ (n : ℝ)⁻¹ * ∑ i, ‖δ i‖ := by positivity
    nlinarith [hmeanSq, hvar]
  unfold centeredClipBias
  calc
    ‖vectorMean (fun i => clipWeight C (g i) • δ i)‖ ≤
        (n : ℝ)⁻¹ * ∑ i, ‖clipWeight C (g i) • δ i‖ := norm_vectorMean_le _
    _ ≤ (n : ℝ)⁻¹ * ∑ i, ‖δ i‖ := by
      apply mul_le_mul_of_nonneg_left _ (by positivity)
      apply Finset.sum_le_sum
      intro i hi
      rw [norm_smul, Real.norm_eq_abs, abs_of_nonneg (clipWeight_mem_Icc_one hC (g i)).1]
      exact mul_le_of_le_one_left (norm_nonneg _) (clipWeight_mem_Icc_one hC (g i)).2
    _ ≤ s := havg

/-- Centering and the multiplier Lipschitz estimate give the quadratic bias
bound `s^2/C`. -/
theorem centeredClipBias_norm_le_variance_div
    {C s : ℝ} (hC : 0 < C) (hn : 0 < n) (hs : 0 ≤ s)
    (g : Fin n → EuclideanSpace ℝ (Fin d))
    (hvar : meanSqDeviation g (vectorMean g) ≤ s ^ 2) :
    ‖centeredClipBias C g‖ ≤ s ^ 2 / C := by
  let G := vectorMean g
  have hconstMean (x : EuclideanSpace ℝ (Fin d)) :
      vectorMean (fun _ : Fin n => x) = x := by
    ext a
    have hnR : (n:ℝ) ≠ 0 := by exact_mod_cast (Nat.ne_of_gt hn)
    simp [vectorMean, PiLp.smul_apply, Finset.sum_const, Finset.card_fin]
    field_simp [hnR] <;> ring
  have hcenter : vectorMean (fun i => g i-G) = 0 := by
    rw [vectorMean_sub]
    change vectorMean g-vectorMean (fun _ : Fin n => G) = 0
    rw [show vectorMean (fun _ : Fin n => G) = G from hconstMean G]
    simp [G]
  have hscalarMean (c : ℝ) (f : Fin n → EuclideanSpace ℝ (Fin d)) :
      vectorMean (fun i => c • f i) = c • vectorMean f := by
    unfold vectorMean
    ext a
    simp only [PiLp.smul_apply, smul_eq_mul, WithLp.ofLp_sum, Finset.sum_apply]
    rw [← Finset.mul_sum]
    ring
  have hconst : vectorMean (fun i => clipWeight C G • (g i-G)) = 0 := by
    calc
      _ = clipWeight C G • vectorMean (fun i => g i-G) := by
        rw [hscalarMean]
      _ = 0 := by rw [hcenter]; simp
  have hrepr : centeredClipBias C g = vectorMean (fun i =>
      (clipWeight C (g i)-clipWeight C G) • (g i-G)) := by
    have hdiff : vectorMean (fun i => clipWeight C (g i) • (g i-G)) -
        vectorMean (fun i => clipWeight C G • (g i-G)) =
        vectorMean (fun i => (clipWeight C (g i)-clipWeight C G) • (g i-G)) := by
      rw [← vectorMean_sub]
      congr 1
      funext i
      module
    dsimp [centeredClipBias]
    rw [hconst] at hdiff
    simpa using hdiff
  rw [hrepr]
  calc
    ‖vectorMean (fun i => (clipWeight C (g i)-clipWeight C G) • (g i-G))‖ ≤
        (n : ℝ)⁻¹ * ∑ i, ‖(clipWeight C (g i)-clipWeight C G) • (g i-G)‖ :=
      norm_vectorMean_le _
    _ ≤ (n : ℝ)⁻¹ * ∑ i, ‖g i-G‖^2/C := by
      apply mul_le_mul_of_nonneg_left _ (by positivity)
      apply Finset.sum_le_sum
      intro i hi
      rw [norm_smul, Real.norm_eq_abs]
      have hw := clipWeight_sub_le_norm_div hC (g i) G
      have hnorm : 0 ≤ ‖g i-G‖ := norm_nonneg _
      calc
        |clipWeight C (g i)-clipWeight C G| * ‖g i-G‖ ≤
            (‖g i-G‖/C) * ‖g i-G‖ := mul_le_mul_of_nonneg_right hw hnorm
        _ = ‖g i-G‖^2/C := by field_simp <;> ring
    _ = meanSqDeviation g (vectorMean g) / C := by
      simp [meanSqDeviation, G, Finset.sum_div, mul_div_assoc]
    _ ≤ s^2/C := by exact div_le_div_of_nonneg_right hvar hC.le

/-- The mean clipped-query multiplier has a variance-only lower bound. -/
theorem meanClipWeight_lower
    {C s : ℝ} (hC : 0 < C) (hn : 0 < n) (hs : 0 ≤ s)
    (g : Fin n → EuclideanSpace ℝ (Fin d))
    (hvar : meanSqDeviation g (vectorMean g) ≤ s ^ 2) :
    C / (C + ‖vectorMean g‖ + s) ≤ meanClipWeight C g := by
  let G := vectorMean g
  let p : Fin n → ℝ := fun _ => (n : ℝ)⁻¹
  let z : Fin n → ℝ := fun i => C+‖G‖+‖g i-G‖
  have hp0 : ∀ i, 0 ≤ p i := by intro i; positivity
  have hp : ∑ i, p i = 1 := by
    simp [p, Finset.sum_const, nsmul_eq_mul]
    field_simp [show (n:ℝ) ≠ 0 by exact_mod_cast (Nat.ne_of_gt hn)]
  have hz : ∀ i, 0 < z i := by intro i; dsimp [z]; positivity
  have havg : (n:ℝ)⁻¹*∑ i, ‖g i-G‖ ≤ s := by
    have hcs : (∑ i, ‖g i-G‖)^2 ≤ (n:ℝ)*∑ i, ‖g i-G‖^2 := by
      simpa using (Finset.sum_mul_sq_le_sq_mul_sq (Finset.univ : Finset (Fin n))
        (fun _ : Fin n => (1:ℝ)) (fun i => ‖g i-G‖))
    have hnR : (n:ℝ) ≠ 0 := by exact_mod_cast (Nat.ne_of_gt hn)
    have hmeanSq : ((n:ℝ)⁻¹*∑ i, ‖g i-G‖)^2 ≤ meanSqDeviation g G := by
      rw [meanSqDeviation]
      have heq : ((n:ℝ)⁻¹*∑ i, ‖g i-G‖)^2 = (∑ i, ‖g i-G‖)^2/(n:ℝ)^2 := by
        field_simp [hnR] <;> ring
      rw [heq]
      calc
        (∑ i, ‖g i-G‖)^2/(n:ℝ)^2 ≤ ((n:ℝ)*∑ i, ‖g i-G‖^2)/(n:ℝ)^2 := div_le_div_of_nonneg_right hcs (sq_nonneg _)
        _ = (n:ℝ)⁻¹*∑ i, ‖g i-G‖^2 := by field_simp [hnR] <;> ring
    have hnonneg : 0 ≤ (n:ℝ)⁻¹*∑ i, ‖g i-G‖ := by positivity
    have hvar' : meanSqDeviation g G ≤ s^2 := by simpa [G] using hvar
    nlinarith [hmeanSq, hvar']
  have hmeanZ : ∑ i, p i*z i ≤ C+‖G‖+s := by
    have hnR : (n:ℝ) ≠ 0 := by exact_mod_cast (Nat.ne_of_gt hn)
    calc
      ∑ i, p i*z i = (n:ℝ)⁻¹ * ∑ i, (C+‖G‖+‖g i-G‖) := by
        simp [p, z, Finset.mul_sum]
      _ = C+‖G‖+(n:ℝ)⁻¹*∑ i, ‖g i-G‖ := by
        simp only [Finset.sum_add_distrib, Finset.sum_const, Finset.card_fin, nsmul_eq_mul]
        field_simp [hnR] <;> ring
      _ ≤ C+‖G‖+s := by linarith [havg]
  have hden (i : Fin n) : max C ‖g i‖ ≤ z i := by
    dsimp [z]
    apply max_le
    · have hG : 0 ≤ ‖G‖ := norm_nonneg G
      have hd : 0 ≤ ‖g i-G‖ := norm_nonneg _
      linarith
    · have ht : ‖g i‖ ≤ ‖g i-G‖+‖G‖ := by
        calc
          ‖g i‖ = ‖(g i-G)+G‖ := by congr 1 <;> abel
          _ ≤ ‖g i-G‖+‖G‖ := norm_add_le _ _
      linarith
  have hfactor (i : Fin n) : C/z i ≤ clipWeight C (g i) := by
    unfold clipWeight radialClipFactor
    apply (div_le_div_of_nonneg_left hC.le (by positivity) (hden i))
  have hjensen := Mf.Optimization.FiniteMemoryAdam.ClippingAdapted.weighted_reciprocal_lower
    (Finset.univ : Finset (Fin n)) p z (C := C) (s := C+‖G‖+s) hC.le (by positivity)
    (fun i _ => hp0 i) (by simpa using hp) (fun i _ => hz i) (by simpa using hmeanZ)
  calc
    C/(C+‖G‖+s) ≤ ∑ i, p i*(C/z i) := hjensen
    _ ≤ ∑ i, p i*clipWeight C (g i) := by
      apply Finset.sum_le_sum
      intro i hi
      exact mul_le_mul_of_nonneg_left (hfactor i) (hp0 i)
    _ = meanClipWeight C g := by
      simp [p, meanClipWeight, Finset.mul_sum, mul_comm, mul_left_comm, mul_assoc]

/-- The centered clipping charge obeys both the first- and second-moment
budgets under only the finite centered variance premise. -/
theorem centeredClipBias_norm_le_min
    {C s : ℝ} (hC : 0 < C) (hn : 0 < n) (hs : 0 ≤ s)
    (g : Fin n → EuclideanSpace ℝ (Fin d))
    (hvar : meanSqDeviation g (vectorMean g) ≤ s ^ 2) :
    ‖centeredClipBias C g‖ ≤ min s (s ^ 2 / C) := by
  exact le_min (centeredClipBias_norm_le hC hn hs g hvar)
    (centeredClipBias_norm_le_variance_div hC hn hs g hvar)

end
end Mf.Optimization.PoissonClippedSGD.ClippingVariance
