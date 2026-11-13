import Mathlib.Algebra.Order.Chebyshev
import Mathlib.Analysis.Calculus.Taylor
import Mathlib.Analysis.SpecialFunctions.Log.Deriv
import Mathlib.Combinatorics.Pigeonhole
import Mf.DP.PLDRandomAllocation

namespace Mf
namespace DP

noncomputable section

open Filter Asymptotics
open scoped Topology

/-!
# Optimal-subsampling BIS likelihood-ratio kernel

This module records the finite accountant kernel from
`paper/optimal-subsampling/main_arxiv.tex`, Section 4.  It is intentionally
narrow: the paper's low-noise and high-noise asymptotic optimality claims are
not formalized here.

The exact likelihood-ratio kernel is the elementary symmetric sum of the
coordinate likelihood ratios.  Existing random-allocation code already proves
that this subset-ratio average is the quotient of the exact `k`-out-of-`T`
active density by the inactive product density; this module gives that fact a
paper-facing name and adds the recursive dynamic-programming surface.
-/

/--
Elementary product sum over a list of weights.

`bisElementaryProductSum ws r` is the sum of all products of `r` distinct
weights chosen from `ws`.  The recursive definition is the dynamic program from
Section 4 of `paper/optimal-subsampling`: either skip the head weight or use it
and place one fewer participation in the suffix.
-/
def bisElementaryProductSum : List ℝ → ℕ → ℝ
  | _ws, 0 => 1
  | [], _r + 1 => 0
  | w :: ws, r + 1 => bisElementaryProductSum ws (r + 1) + w * bisElementaryProductSum ws r

@[simp] theorem bisElementaryProductSum_zero (ws : List ℝ) :
    bisElementaryProductSum ws 0 = 1 := by
  cases ws <;> rfl

@[simp] theorem bisElementaryProductSum_nil_succ (r : ℕ) :
    bisElementaryProductSum [] (r + 1) = 0 := rfl

/-- Paper recurrence: placing zero remaining participations has contribution `1`. -/
theorem bisElementaryProductSum_boundary_zero (ws : List ℝ) :
    bisElementaryProductSum ws 0 = 1 := by
  simp

/-- Paper recurrence: no suffix left and positive remaining participations gives `0`. -/
theorem bisElementaryProductSum_boundary_empty (r : ℕ) :
    bisElementaryProductSum [] (r + 1) = 0 := by
  rfl

/--
Paper recurrence for the BIS exact likelihood-ratio dynamic program.

The head term is skipped in the first summand and selected in the second
summand, matching `F(t,r) = F(t+1,r) + w_t F(t+1,r-1)`.
-/
theorem bisElementaryProductSum_cons_succ (w : ℝ) (ws : List ℝ) (r : ℕ) :
    bisElementaryProductSum (w :: ws) (r + 1)
      = bisElementaryProductSum ws (r + 1) + w * bisElementaryProductSum ws r := by
  rfl

/-- The normalized exact BIS subset-ratio kernel over `Fin (t+1)`. -/
def bisExactSubsetRatioAverage {t : ℕ}
    (ratio : Fin (t + 1) → ℝ) (k : ℕ) : ℝ :=
  (Finset.sum ((Finset.univ : Finset (Fin (t + 1))).powersetCard k)
      (fun s => Finset.prod s ratio) / (Nat.choose (t + 1) k : ℝ))

/--
Paper-facing exact likelihood-ratio identity for uniform `k`-out-of-`T` BIS.

For coordinate densities `p` and `q`, dividing the exact active `k`-out-of-`T`
mixture density by the inactive product density gives the average size-`k`
product of coordinate likelihood ratios.  This is exactly the formula used in
`paper/optimal-subsampling/main_arxiv.tex` before introducing the dynamic
program.
-/
theorem kOutOfTBarDensity_div_prodDensity_eq_bisExactSubsetRatioAverage
    {α : Type} {t : ℕ}
    (p q : α → ℝ)
    (k : ℕ)
    (x : Fin (t + 1) → α)
    (hq : ∀ i : Fin (t + 1), q (x i) ≠ 0) :
    kOutOfTBarDensity p q k x / prodDensity q x
      = bisExactSubsetRatioAverage (fun i => p (x i) / q (x i)) k := by
  rw [kOutOfTBarDensity_div_prodDensity_eq_avg_subsetRatio p q k x hq]
  rfl

/-- Paper-facing name for the finite BIS screening left-hand side. -/
def bisScreeningAverage {t : ℕ}
    (ratio : Fin (t + 1) → ℝ) (k : ℕ) : ℝ :=
  bisExactSubsetRatioAverage ratio k

/--
The finite screening inequality from Section 4 of
`paper/optimal-subsampling/main_arxiv.tex`.

This is the elementary-symmetric mean/Maclaurin inequality for nonnegative
coordinate ratios.  The easy boundary cases are proved below; the general
`k` case is the remaining theorem-facing target.
-/
def bisScreeningBoundTarget {t : ℕ}
    (ratio : Fin (t + 1) → ℝ) (k : ℕ) : Prop :=
  (∀ i, 0 ≤ ratio i) →
    bisScreeningAverage ratio k
      ≤ ((Finset.sum Finset.univ ratio) / (t + 1 : ℝ)) ^ k

/--
The isolated Maclaurin inequality needed for the full finite screening theorem.

This is intentionally the same mathematical inequality as the screening target,
but without the implication-shaped nonnegativity hypothesis.  Future proof work
can focus on this single finite inequality and then use
`bisScreeningBoundTarget_of_maclaurin` below to recover the paper-facing target.
-/
def bisMaclaurinScreeningInequality {t : ℕ}
    (ratio : Fin (t + 1) → ℝ) (k : ℕ) : Prop :=
  (∀ i, 0 ≤ ratio i) ∧
    bisScreeningAverage ratio k
      ≤ ((Finset.sum Finset.univ ratio) / (t + 1 : ℝ)) ^ k

theorem bisScreeningBoundTarget_of_maclaurin {t : ℕ}
    {ratio : Fin (t + 1) → ℝ} {k : ℕ}
    (h : (∀ i, 0 ≤ ratio i) → bisMaclaurinScreeningInequality ratio k) :
    bisScreeningBoundTarget ratio k := by
  intro hnonneg
  exact (h hnonneg).2

/--
A direct sufficient condition for the Maclaurin screening seam.

If every coordinate ratio is already bounded by the full coordinate average,
then each selected product is bounded by the corresponding power of that
average.  This does not prove the full Maclaurin inequality, but it is a useful
sanity theorem for the equalized endpoint of the paper's pair-smoothing proof.
-/
theorem bisMaclaurinScreeningInequality_of_forall_le_average {t : ℕ}
    {ratio : Fin (t + 1) → ℝ} {k : ℕ}
    (hk : k ≤ t + 1)
    (hnonneg : ∀ i, 0 ≤ ratio i)
    (hle :
      ∀ i, ratio i ≤ (Finset.sum Finset.univ ratio) / (t + 1 : ℝ)) :
    bisMaclaurinScreeningInequality ratio k := by
  classical
  refine ⟨hnonneg, ?_⟩
  set avg : ℝ := (Finset.sum Finset.univ ratio) / (t + 1 : ℝ)
  set subsets : Finset (Finset (Fin (t + 1))) :=
    (Finset.univ : Finset (Fin (t + 1))).powersetCard k
  have hprod : ∀ s ∈ subsets, Finset.prod s ratio ≤ avg ^ k := by
    intro s hs
    have hcard : s.card = k := (Finset.mem_powersetCard.mp hs).2
    calc
      Finset.prod s ratio ≤ Finset.prod s (fun _ => avg) := by
        exact Finset.prod_le_prod (fun i _hi => hnonneg i) (fun i _hi => hle i)
      _ = avg ^ s.card := by
        simp
      _ = avg ^ k := by rw [hcard]
  have hsum :
      Finset.sum subsets (fun s => Finset.prod s ratio)
        ≤ subsets.card * avg ^ k := by
    calc
      Finset.sum subsets (fun s => Finset.prod s ratio)
          ≤ Finset.sum subsets (fun _s => avg ^ k) := by
            exact Finset.sum_le_sum hprod
      _ = subsets.card * avg ^ k := by
            simp [nsmul_eq_mul]
  have hcardSubsets :
      subsets.card = Nat.choose (t + 1) k := by
    simp [subsets]
  have hchoose_pos : 0 < (Nat.choose (t + 1) k : ℝ) := by
    exact_mod_cast Nat.choose_pos hk
  have hdiv :
      Finset.sum subsets (fun s => Finset.prod s ratio) / (Nat.choose (t + 1) k : ℝ)
        ≤ ((Nat.choose (t + 1) k : ℝ) * avg ^ k)
            / (Nat.choose (t + 1) k : ℝ) := by
    refine div_le_div_of_nonneg_right ?_ hchoose_pos.le
    simpa [hcardSubsets] using hsum
  have hcancel :
      ((Nat.choose (t + 1) k : ℝ) * avg ^ k) / (Nat.choose (t + 1) k : ℝ)
        = avg ^ k := by
    exact mul_div_cancel_left₀ (avg ^ k) hchoose_pos.ne'
  simpa [bisMaclaurinScreeningInequality, bisScreeningAverage,
    bisExactSubsetRatioAverage, avg, subsets, hcancel] using hdiv

/--
Replace two coordinates by their common arithmetic mean.

This is the theorem-facing object for the pair-smoothing proof of the paper's
screening bound.  If the two indices coincide, this definition is still
well-behaved: the selected coordinate is replaced by its original value.
-/
def bisPairAveragedRatio {t : ℕ}
    (ratio : Fin (t + 1) → ℝ) (a b : Fin (t + 1)) :
    Fin (t + 1) → ℝ :=
  fun i =>
    if i = a then (ratio a + ratio b) / 2
    else if i = b then (ratio a + ratio b) / 2
    else ratio i

@[simp] theorem bisPairAveragedRatio_apply_left {t : ℕ}
    (ratio : Fin (t + 1) → ℝ) (a b : Fin (t + 1)) :
    bisPairAveragedRatio ratio a b a = (ratio a + ratio b) / 2 := by
  simp [bisPairAveragedRatio]

@[simp] theorem bisPairAveragedRatio_apply_right {t : ℕ}
    (ratio : Fin (t + 1) → ℝ) (a b : Fin (t + 1)) :
    bisPairAveragedRatio ratio a b b = (ratio a + ratio b) / 2 := by
  by_cases hba : b = a
  · simp [bisPairAveragedRatio, hba]
  · simp [bisPairAveragedRatio, hba]

/-- Pair averaging preserves the total coordinate sum. -/
theorem bisPairAveragedRatio_sum {t : ℕ}
    (ratio : Fin (t + 1) → ℝ) (a b : Fin (t + 1)) :
    Finset.sum Finset.univ (bisPairAveragedRatio ratio a b)
      = Finset.sum Finset.univ ratio := by
  classical
  by_cases hab : a = b
  · subst b
    apply Finset.sum_congr rfl
    intro i _hi
    by_cases hia : i = a
    · simp [bisPairAveragedRatio, hia]
    · simp [bisPairAveragedRatio, hia]
  · let s : Finset (Fin (t + 1)) := Finset.univ
    have ha : a ∈ s := by simp [s]
    have hb : b ∈ s.erase a := by
      exact Finset.mem_erase.mpr ⟨(fun hba => hab hba.symm), by simp [s]⟩
    have hrest :
        Finset.sum ((s.erase a).erase b) (bisPairAveragedRatio ratio a b)
          = Finset.sum ((s.erase a).erase b) ratio := by
      apply Finset.sum_congr rfl
      intro i hi
      have hib : i ≠ b := (Finset.mem_erase.mp hi).1
      have hia : i ≠ a := (Finset.mem_erase.mp (Finset.mem_erase.mp hi).2).1
      simp [bisPairAveragedRatio, hia, hib]
    calc
      Finset.sum Finset.univ (bisPairAveragedRatio ratio a b)
          = Finset.sum ((s.erase a).erase b) (bisPairAveragedRatio ratio a b)
              + (ratio a + ratio b) / 2 + (ratio a + ratio b) / 2 := by
            rw [show (Finset.univ : Finset (Fin (t + 1))) = s by rfl]
            rw [← Finset.sum_erase_add s (bisPairAveragedRatio ratio a b) ha]
            rw [← Finset.sum_erase_add (s.erase a) (bisPairAveragedRatio ratio a b) hb]
            simp [add_assoc]
      _ = Finset.sum ((s.erase a).erase b) ratio + ratio b + ratio a := by
            rw [hrest]
            ring
      _ = Finset.sum Finset.univ ratio := by
            rw [show (Finset.univ : Finset (Fin (t + 1))) = s by rfl]
            rw [← Finset.sum_erase_add s ratio ha]
            rw [← Finset.sum_erase_add (s.erase a) ratio hb]

theorem bisPairAveragedRatio_nonneg {t : ℕ}
    {ratio : Fin (t + 1) → ℝ} {a b : Fin (t + 1)}
    (hnonneg : ∀ i, 0 ≤ ratio i) :
    ∀ i, 0 ≤ bisPairAveragedRatio ratio a b i := by
  intro i
  have havg : 0 ≤ (ratio a + ratio b) / 2 := by
    exact div_nonneg (add_nonneg (hnonneg a) (hnonneg b))
      (by norm_num : (0 : ℝ) ≤ 2)
  by_cases hia : i = a
  · simpa [bisPairAveragedRatio, hia] using havg
  · by_cases hib : i = b
    · simpa [bisPairAveragedRatio, hia, hib] using havg
    · simpa [bisPairAveragedRatio, hia, hib] using hnonneg i

/--
One-step pair-smoothing target for the Finset screening average.

The paper's full proof shows this for every pair `(a,b)`: replacing two
coordinates by their common average cannot decrease the elementary-symmetric
screening average.
-/
def bisPairSmoothingStepTarget {t : ℕ}
    (ratio : Fin (t + 1) → ℝ) (k : ℕ) (a b : Fin (t + 1)) : Prop :=
  bisScreeningAverage ratio k
    ≤ bisScreeningAverage (bisPairAveragedRatio ratio a b) k

@[simp] theorem bisPairSmoothingStepTarget_zero {t : ℕ}
    (ratio : Fin (t + 1) → ℝ) (a b : Fin (t + 1)) :
    bisPairSmoothingStepTarget ratio 0 a b := by
  simp [bisPairSmoothingStepTarget, bisScreeningAverage,
    bisExactSubsetRatioAverage]

@[simp] theorem bisPairSmoothingStepTarget_one {t : ℕ}
    (ratio : Fin (t + 1) → ℝ) (a b : Fin (t + 1)) :
    bisPairSmoothingStepTarget ratio 1 a b := by
  simp [bisPairSmoothingStepTarget, bisScreeningAverage,
    bisExactSubsetRatioAverage, Finset.powersetCard_one,
    bisPairAveragedRatio_sum]

/--
Compositional seam for the pair-smoothing proof.

If a single smoothing step is monotone and the smoothed vector satisfies the
Maclaurin screening inequality, then the original vector does too.  The only
normalization fact needed here is that pair averaging preserves the coordinate
sum.
-/
theorem bisMaclaurinScreeningInequality_of_pairSmoothingStep {t : ℕ}
    {ratio : Fin (t + 1) → ℝ} {k : ℕ} {a b : Fin (t + 1)}
    (hnonneg : ∀ i, 0 ≤ ratio i)
    (hstep : bisPairSmoothingStepTarget ratio k a b)
    (hsmoothed :
      bisMaclaurinScreeningInequality (bisPairAveragedRatio ratio a b) k) :
    bisMaclaurinScreeningInequality ratio k := by
  refine ⟨hnonneg, ?_⟩
  refine le_trans hstep ?_
  simpa [bisMaclaurinScreeningInequality, bisPairAveragedRatio_sum]
    using hsmoothed.2

/--
The scalar algebra behind pair smoothing.

For fixed sum `a + b`, replacing `(a,b)` by their common average cannot
decrease the product.  This is the `u_a(s-u_a) <= s^2/4` step in the paper.
-/
theorem bis_pair_product_le_average_sq (a b : ℝ) :
    a * b ≤ ((a + b) / 2) ^ 2 := by
  nlinarith [sq_nonneg (a - b)]

/-- Nonnegativity of the elementary-product DP for nonnegative list weights. -/
theorem bisElementaryProductSum_nonneg {ws : List ℝ} {r : ℕ}
    (hws : ∀ w ∈ ws, 0 ≤ w) :
    0 ≤ bisElementaryProductSum ws r := by
  induction ws generalizing r with
  | nil =>
      cases r <;> simp [bisElementaryProductSum]
  | cons w ws ih =>
      cases r with
      | zero => simp [bisElementaryProductSum]
      | succ r =>
          have hw : 0 ≤ w := hws w (by simp)
          have htail : ∀ x ∈ ws, 0 ≤ x := by
            intro x hx
            exact hws x (by simp [hx])
          have hskip : 0 ≤ bisElementaryProductSum ws (r + 1) := ih htail
          have htake : 0 ≤ w * bisElementaryProductSum ws r :=
            mul_nonneg hw (ih htail)
          simpa [bisElementaryProductSum] using add_nonneg hskip htake

/-- Selecting more factors than a list contains gives zero elementary sum. -/
theorem bisElementaryProductSum_eq_zero_of_length_lt {ws : List ℝ} {r : ℕ}
    (h : ws.length < r) :
    bisElementaryProductSum ws r = 0 := by
  induction ws generalizing r with
  | nil =>
      cases r with
      | zero => omega
      | succ r => simp [bisElementaryProductSum]
  | cons a ws ih =>
      cases r with
      | zero => omega
      | succ r =>
          have hlen : ws.length + 1 < r + 1 := by
            simpa using h
          have htail_lt_r : ws.length < r :=
            Nat.succ_lt_succ_iff.mp hlen
          have hskip : bisElementaryProductSum ws (r + 1) = 0 := by
            exact ih (Nat.lt_trans htail_lt_r (Nat.lt_succ_self r))
          by_cases hr0 : r = 0
          · subst r
            omega
          · have htake : bisElementaryProductSum ws r = 0 := ih htail_lt_r
            simp [bisElementaryProductSum, hskip, htake]

/-- A nonnegative real list with zero sum has every entry equal to zero. -/
theorem list_forall_eq_zero_of_sum_eq_zero_of_nonneg {ws : List ℝ}
    (hws : ∀ w ∈ ws, 0 ≤ w) (hsum : ws.sum = 0) :
    ∀ w ∈ ws, w = 0 := by
  induction ws with
  | nil =>
      simp
  | cons a ws ih =>
      have ha_nonneg : 0 ≤ a := hws a (by simp)
      have hws_nonneg : ∀ w ∈ ws, 0 ≤ w := by
        intro w hw
        exact hws w (by simp [hw])
      have hsum_nonneg : 0 ≤ ws.sum :=
        List.sum_nonneg hws_nonneg
      have hsum_cons : a + ws.sum = 0 := by
        simpa using hsum
      have ha_zero : a = 0 := by
        nlinarith
      have htail_sum : ws.sum = 0 := by
        nlinarith
      intro w hw
      rcases (List.mem_cons.mp hw) with rfl | hw_tail
      · exact ha_zero
      · exact ih hws_nonneg htail_sum w hw_tail

/-- If every list entry is zero, every positive elementary sum is zero. -/
theorem bisElementaryProductSum_eq_zero_of_forall_eq_zero {ws : List ℝ} {r : ℕ}
    (hr : 0 < r) (hzero : ∀ w ∈ ws, w = 0) :
    bisElementaryProductSum ws r = 0 := by
  induction ws generalizing r with
  | nil =>
      cases r with
      | zero => contradiction
      | succ r => simp [bisElementaryProductSum]
  | cons a ws ih =>
      cases r with
      | zero => contradiction
      | succ r =>
          have ha : a = 0 := hzero a (by simp)
          have htail : ∀ w ∈ ws, w = 0 := by
            intro w hw
            exact hzero w (by simp [hw])
          have hskip : bisElementaryProductSum ws (r + 1) = 0 :=
            ih (r := r + 1) (by omega) htail
          cases r with
          | zero =>
              simp [bisElementaryProductSum, ha, hskip]
          | succ r =>
              have htake : bisElementaryProductSum ws (r + 1) = 0 :=
                ih (r := r + 1) (by omega) htail
              simp [bisElementaryProductSum, ha, hskip, htake]

/--
Nonnegative zero-sum lists have zero positive elementary sums.

This is the zero-average branch needed by the list-induction proof of the
Maclaurin screening inequality.
-/
theorem bisElementaryProductSum_eq_zero_of_sum_eq_zero_of_nonneg
    {ws : List ℝ} {r : ℕ}
    (hr : 0 < r) (hws : ∀ w ∈ ws, 0 ≤ w) (hsum : ws.sum = 0) :
    bisElementaryProductSum ws r = 0 :=
  bisElementaryProductSum_eq_zero_of_forall_eq_zero hr
    (list_forall_eq_zero_of_sum_eq_zero_of_nonneg hws hsum)

/--
Two-head expansion of the elementary-product DP.

This is the list-recursive form of the paper's
`C0 + C1 (u_a + u_b) + C2 u_a u_b` decomposition.
-/
theorem bisElementaryProductSum_cons_cons_succ_succ
    (a b : ℝ) (ws : List ℝ) (r : ℕ) :
    bisElementaryProductSum (a :: b :: ws) (r + 2)
      = bisElementaryProductSum ws (r + 2)
        + (a + b) * bisElementaryProductSum ws (r + 1)
        + (a * b) * bisElementaryProductSum ws r := by
  simp [bisElementaryProductSum, add_mul, mul_add, add_assoc, add_left_comm,
    add_comm, mul_assoc]

/--
Pair smoothing for the recursive elementary-product DP when the smoothed pair is
at the head of the list.

The only nontrivial case is selecting both head coordinates.  The coefficient
of that product is the nonnegative suffix DP value, while
`a * b <= ((a+b)/2)^2`.
-/
theorem bisElementaryProductSum_pairAverage_head_le
    {a b : ℝ} {ws : List ℝ} {r : ℕ}
    (hws : ∀ w ∈ ws, 0 ≤ w) :
    bisElementaryProductSum (a :: b :: ws) r
      ≤ bisElementaryProductSum (((a + b) / 2) :: ((a + b) / 2) :: ws) r := by
  cases r with
  | zero =>
      simp [bisElementaryProductSum]
  | succ r =>
      cases r with
      | zero =>
          simp [bisElementaryProductSum]
          ring_nf
          exact le_refl (bisElementaryProductSum ws 1 + b + a)
      | succ r =>
          have hcoeff : 0 ≤ bisElementaryProductSum ws r :=
            bisElementaryProductSum_nonneg hws
          have hprod : a * b ≤ ((a + b) / 2) ^ 2 :=
            bis_pair_product_le_average_sq a b
          have hscaled :
              (a * b) * bisElementaryProductSum ws r
                ≤ (((a + b) / 2) ^ 2) * bisElementaryProductSum ws r :=
            mul_le_mul_of_nonneg_right hprod hcoeff
          rw [bisElementaryProductSum_cons_cons_succ_succ]
          rw [bisElementaryProductSum_cons_cons_succ_succ]
          nlinarith

/-- Unnormalized elementary subset-product sum over an arbitrary finset. -/
def bisFinsetElementaryProductSum {α : Type} [DecidableEq α]
    (s : Finset α) (ratio : α → ℝ) (k : ℕ) : ℝ :=
  Finset.sum (s.powersetCard k) (fun u => Finset.prod u ratio)

/-- Generic two-coordinate averaging for an arbitrary decidable finite type. -/
def bisPairAveragedFunction {α : Type} [DecidableEq α]
    (ratio : α → ℝ) (a b : α) : α → ℝ :=
  fun i =>
    if i = a then (ratio a + ratio b) / 2
    else if i = b then (ratio a + ratio b) / 2
    else ratio i

/-- Nonnegativity of the Finset elementary-product sum. -/
theorem bisFinsetElementaryProductSum_nonneg {α : Type} [DecidableEq α]
    {s : Finset α} {ratio : α → ℝ} {k : ℕ}
    (hs : ∀ i ∈ s, 0 ≤ ratio i) :
    0 ≤ bisFinsetElementaryProductSum s ratio k := by
  unfold bisFinsetElementaryProductSum
  exact Finset.sum_nonneg fun u hu =>
    Finset.prod_nonneg fun i hi => hs i ((Finset.mem_powersetCard.mp hu).1 hi)

/--
Fresh-head recurrence for the Finset elementary subset-product sum.

This is the Finset analogue of `bisElementaryProductSum_cons_succ`: subsets of
`insert x s` either skip `x`, or select `x` and choose one fewer element from
the suffix set `s`.
-/
theorem bisFinsetElementaryProductSum_insert_succ {α : Type} [DecidableEq α]
    {x : α} {s : Finset α} (hx : x ∉ s) (ratio : α → ℝ) (k : ℕ) :
    bisFinsetElementaryProductSum (insert x s) ratio (k + 1)
      = bisFinsetElementaryProductSum s ratio (k + 1)
        + ratio x * bisFinsetElementaryProductSum s ratio k := by
  classical
  unfold bisFinsetElementaryProductSum
  rw [Finset.powersetCard_succ_insert hx k]
  have hdisj :
      Disjoint (Finset.powersetCard (k + 1) s)
        ((Finset.powersetCard k s).image (insert x)) := by
    rw [Finset.disjoint_left]
    intro u hu
    rw [Finset.mem_image]
    rintro ⟨v, _hv, rfl⟩
    have hxsubset : x ∉ insert x v := by
      exact fun hxu => hx ((Finset.mem_powersetCard.mp hu).1 hxu)
    exact hxsubset (Finset.mem_insert_self x v)
  rw [Finset.sum_union hdisj]
  have hinj : Set.InjOn (insert x)
      (↑(Finset.powersetCard k s) : Set (Finset α)) := by
    exact Finset.insert_erase_invOn.right.injOn.mono
      (by
        intro u hu
        exact fun hxu => hx ((Finset.mem_powersetCard.mp hu).1 hxu))
  rw [Finset.sum_image hinj]
  have hprod :
      ∀ u ∈ Finset.powersetCard k s,
        Finset.prod (insert x u) ratio = ratio x * Finset.prod u ratio := by
    intro u hu
    have hxu : x ∉ u := fun hxu => hx ((Finset.mem_powersetCard.mp hu).1 hxu)
    exact Finset.prod_insert hxu
  calc
    Finset.sum (Finset.powersetCard (k + 1) s) (fun u => Finset.prod u ratio)
        + Finset.sum (Finset.powersetCard k s)
            (fun u => Finset.prod (insert x u) ratio)
        = Finset.sum (Finset.powersetCard (k + 1) s) (fun u => Finset.prod u ratio)
          + Finset.sum (Finset.powersetCard k s)
              (fun u => ratio x * Finset.prod u ratio) := by
            rw [Finset.sum_congr rfl hprod]
    _ = Finset.sum (Finset.powersetCard (k + 1) s) (fun u => Finset.prod u ratio)
        + ratio x * Finset.sum (Finset.powersetCard k s)
            (fun u => Finset.prod u ratio) := by
          rw [Finset.mul_sum]

/--
Two-fresh-head expansion for the Finset elementary-product sum.

This is the direct Finset version of the paper's
`C0 + C1 (u_a + u_b) + C2 u_a u_b` decomposition.
-/
theorem bisFinsetElementaryProductSum_insert_insert_succ_succ
    {α : Type} [DecidableEq α] {a b : α} {s : Finset α}
    (ha : a ∉ s) (hb : b ∉ s) (hab : a ≠ b)
    (ratio : α → ℝ) (k : ℕ) :
    bisFinsetElementaryProductSum (insert a (insert b s)) ratio (k + 2)
      = bisFinsetElementaryProductSum s ratio (k + 2)
        + (ratio a + ratio b) * bisFinsetElementaryProductSum s ratio (k + 1)
        + (ratio a * ratio b) * bisFinsetElementaryProductSum s ratio k := by
  have ha_insert : a ∉ insert b s := by
    simp [ha, hab]
  rw [bisFinsetElementaryProductSum_insert_succ ha_insert ratio (k + 1)]
  rw [bisFinsetElementaryProductSum_insert_succ hb ratio (k + 1)]
  rw [bisFinsetElementaryProductSum_insert_succ hb ratio k]
  ring

/--
Pair smoothing for the Finset elementary-product sum when the smoothed pair is
represented as two fresh heads over a suffix set.
-/
theorem bisFinsetElementaryProductSum_pairAverage_insert_insert_succ_succ_le
    {α : Type} [DecidableEq α] {a b : α} {s : Finset α}
    (ha : a ∉ s) (hb : b ∉ s) (hab : a ≠ b)
    {ratio : α → ℝ} {k : ℕ}
    (hsnonneg : ∀ i ∈ s, 0 ≤ ratio i) :
    bisFinsetElementaryProductSum (insert a (insert b s)) ratio (k + 2)
      ≤ bisFinsetElementaryProductSum (insert a (insert b s))
          (bisPairAveragedFunction ratio a b) (k + 2) := by
  let avgRatio : α → ℝ := bisPairAveragedFunction ratio a b
  have hsame : ∀ i ∈ s, avgRatio i = ratio i := by
    intro i hi
    have hia : i ≠ a := fun hia => ha (hia ▸ hi)
    have hib : i ≠ b := fun hib => hb (hib ▸ hi)
    simp [avgRatio, bisPairAveragedFunction, hia, hib]
  have hsumEq : ∀ m, bisFinsetElementaryProductSum s avgRatio m
      = bisFinsetElementaryProductSum s ratio m := by
    intro m
    unfold bisFinsetElementaryProductSum
    apply Finset.sum_congr rfl
    intro u hu
    apply Finset.prod_congr rfl
    intro i hi
    exact hsame i ((Finset.mem_powersetCard.mp hu).1 hi)
  have hcoeff : 0 ≤ bisFinsetElementaryProductSum s ratio k :=
    bisFinsetElementaryProductSum_nonneg hsnonneg
  have hprod : ratio a * ratio b ≤ ((ratio a + ratio b) / 2) ^ 2 :=
    bis_pair_product_le_average_sq (ratio a) (ratio b)
  have hscaled :
      (ratio a * ratio b) * bisFinsetElementaryProductSum s ratio k
        ≤ (((ratio a + ratio b) / 2) ^ 2) * bisFinsetElementaryProductSum s ratio k :=
    mul_le_mul_of_nonneg_right hprod hcoeff
  rw [bisFinsetElementaryProductSum_insert_insert_succ_succ ha hb hab ratio k]
  rw [bisFinsetElementaryProductSum_insert_insert_succ_succ ha hb hab avgRatio k]
  simp [avgRatio, bisPairAveragedFunction, hsumEq]
  nlinarith

/-- The exact BIS subset-ratio numerator is the Finset elementary-product sum. -/
theorem bisExactSubsetRatioAverage_eq_finsetElementaryProductSum {t : ℕ}
    (ratio : Fin (t + 1) → ℝ) (k : ℕ) :
    bisExactSubsetRatioAverage ratio k
      = bisFinsetElementaryProductSum Finset.univ ratio k
          / (Nat.choose (t + 1) k : ℝ) := by
  rfl

/-- Paper-facing screening average through the Finset elementary-product sum. -/
theorem bisScreeningAverage_eq_finsetElementaryProductSum {t : ℕ}
    (ratio : Fin (t + 1) → ℝ) (k : ℕ) :
    bisScreeningAverage ratio k
      = bisFinsetElementaryProductSum Finset.univ ratio k
          / (Nat.choose (t + 1) k : ℝ) := by
  rfl

theorem bisPairSmoothingStepTarget_succ_succ {t : ℕ}
    {ratio : Fin (t + 1) → ℝ} {a b : Fin (t + 1)} {k : ℕ}
    (hk : k + 2 ≤ t + 1)
    (hab : a ≠ b)
    (hnonneg : ∀ i, 0 ≤ ratio i) :
    bisPairSmoothingStepTarget ratio (k + 2) a b := by
  classical
  let suffix : Finset (Fin (t + 1)) := (Finset.univ.erase a).erase b
  have ha : a ∉ suffix := by
    simp [suffix]
  have hb : b ∉ suffix := by
    simp [suffix]
  have huniv : insert a (insert b suffix) = (Finset.univ : Finset (Fin (t + 1))) := by
    ext i
    by_cases hia : i = a
    · simp [hia]
    · by_cases hib : i = b
      · simp [hib]
      · simp [suffix, hia, hib]
  have hsnonneg : ∀ i ∈ suffix, 0 ≤ ratio i := by
    intro i _hi
    exact hnonneg i
  have hnum :
      bisFinsetElementaryProductSum Finset.univ ratio (k + 2)
        ≤ bisFinsetElementaryProductSum Finset.univ
            (bisPairAveragedRatio ratio a b) (k + 2) := by
    have h :=
      bisFinsetElementaryProductSum_pairAverage_insert_insert_succ_succ_le
        (a := a) (b := b) (s := suffix) ha hb hab
        (ratio := ratio) (k := k) hsnonneg
    have haverage :
        bisPairAveragedFunction ratio a b = bisPairAveragedRatio ratio a b := by
      rfl
    rw [haverage] at h
    simpa [huniv] using h
  have hchoose_pos : 0 < (Nat.choose (t + 1) (k + 2) : ℝ) := by
    exact_mod_cast Nat.choose_pos hk
  unfold bisPairSmoothingStepTarget
  rw [bisScreeningAverage_eq_finsetElementaryProductSum]
  rw [bisScreeningAverage_eq_finsetElementaryProductSum]
  exact div_le_div_of_nonneg_right hnum hchoose_pos.le

/--
Pair smoothing is monotone for every valid subset size and every distinct
coordinate pair.
-/
theorem bisPairSmoothingStepTarget_of_nonneg {t : ℕ}
    {ratio : Fin (t + 1) → ℝ} {k : ℕ} {a b : Fin (t + 1)}
    (hk : k ≤ t + 1)
    (hab : a ≠ b)
    (hnonneg : ∀ i, 0 ≤ ratio i) :
    bisPairSmoothingStepTarget ratio k a b := by
  cases k with
  | zero =>
      exact bisPairSmoothingStepTarget_zero ratio a b
  | succ k =>
      cases k with
      | zero =>
          exact bisPairSmoothingStepTarget_one ratio a b
      | succ k =>
          exact bisPairSmoothingStepTarget_succ_succ
            (t := t) (ratio := ratio) (a := a) (b := b) (k := k)
            (by simpa [Nat.succ_eq_add_one, Nat.add_assoc] using hk)
            hab hnonneg

/--
Global equalization seam for the finite Maclaurin screening proof.

It is enough to produce a transformed vector with the same coordinate sum,
screening average at least the original one, and all transformed coordinates
bounded by their own average.  The endpoint theorem then proves the transformed
Maclaurin bound, and this theorem transports it back to the original vector.
-/
theorem bisMaclaurinScreeningInequality_of_equalizationTransform {t : ℕ}
    {ratio smoothed : Fin (t + 1) → ℝ} {k : ℕ}
    (hk : k ≤ t + 1)
    (hnonneg : ∀ i, 0 ≤ ratio i)
    (hsmoothed_nonneg : ∀ i, 0 ≤ smoothed i)
    (hmono : bisScreeningAverage ratio k ≤ bisScreeningAverage smoothed k)
    (hsum : Finset.sum Finset.univ smoothed = Finset.sum Finset.univ ratio)
    (hle_avg :
      ∀ i, smoothed i ≤ (Finset.sum Finset.univ smoothed) / (t + 1 : ℝ)) :
    bisMaclaurinScreeningInequality ratio k := by
  refine ⟨hnonneg, ?_⟩
  have hsmoothed :
      bisMaclaurinScreeningInequality smoothed k :=
    bisMaclaurinScreeningInequality_of_forall_le_average
      (t := t) (ratio := smoothed) (k := k) hk hsmoothed_nonneg hle_avg
  refine le_trans hmono ?_
  simpa [bisMaclaurinScreeningInequality, hsum] using hsmoothed.2

/--
The remaining global equalization obligation for the pair-smoothing proof.

The local pair-smoothing theorem should be used to produce such a transformed
vector.  Once this proposition is available, the finite Maclaurin screening
inequality follows by `bisMaclaurinScreeningInequality_of_globalEqualization`.
-/
def bisGlobalEqualizationTransformExists {t : ℕ}
    (ratio : Fin (t + 1) → ℝ) (k : ℕ) : Prop :=
  ∃ smoothed : Fin (t + 1) → ℝ,
    (∀ i, 0 ≤ smoothed i) ∧
    bisScreeningAverage ratio k ≤ bisScreeningAverage smoothed k ∧
    Finset.sum Finset.univ smoothed = Finset.sum Finset.univ ratio ∧
    (∀ i, smoothed i ≤ (Finset.sum Finset.univ smoothed) / (t + 1 : ℝ))

theorem bisMaclaurinScreeningInequality_of_globalEqualization {t : ℕ}
    {ratio : Fin (t + 1) → ℝ} {k : ℕ}
    (hk : k ≤ t + 1)
    (hnonneg : ∀ i, 0 ≤ ratio i)
    (hexists : bisGlobalEqualizationTransformExists ratio k) :
    bisMaclaurinScreeningInequality ratio k := by
  rcases hexists with ⟨smoothed, hsmoothed_nonneg, hmono, hsum, hle_avg⟩
  exact bisMaclaurinScreeningInequality_of_equalizationTransform
    (t := t) (ratio := ratio) (smoothed := smoothed) (k := k)
    hk hnonneg hsmoothed_nonneg hmono hsum hle_avg

/--
Scalar Bernoulli inequality for the one-coordinate Maclaurin induction step.

After normalizing the old suffix average to `1`, adding a new coordinate with
relative size `y` reduces to this inequality:
`(n - k + k y) / n <= ((n - 1 + y) / n)^k`.
-/
theorem bisScalarBernoulliScreening
    {n k : ℕ} {y : ℝ}
    (hn : 0 < n) (hy : 0 ≤ y) :
    ((((n : ℝ) - (k : ℝ)) + (k : ℝ) * y) / (n : ℝ))
      ≤ ((((n : ℝ) - 1) + y) / (n : ℝ)) ^ k := by
  have hnR : (0 : ℝ) < n := by exact_mod_cast hn
  have hn1N : 1 ≤ n := Nat.succ_le_of_lt hn
  have hn1R : (1 : ℝ) ≤ n := by exact_mod_cast hn1N
  have hz : -1 ≤ (y - 1) / (n : ℝ) := by
    rw [le_div_iff₀ hnR]
    nlinarith [hy, hn1R]
  have hz2 : -2 ≤ (y - 1) / (n : ℝ) := by
    linarith
  have hbern := one_add_mul_le_pow (a := (y - 1) / (n : ℝ)) hz2 k
  have hbase :
      1 + (y - 1) / (n : ℝ) = (((n : ℝ) - 1) + y) / (n : ℝ) := by
    field_simp [hnR.ne']
    ring
  have hlin :
      1 + (k : ℝ) * ((y - 1) / (n : ℝ))
        = ((((n : ℝ) - (k : ℝ)) + (k : ℝ) * y) / (n : ℝ)) := by
    field_simp [hnR.ne']
    ring
  simpa [hbase, hlin] using hbern

/--
Real-cast binomial identity used by the Maclaurin induction step:
`n * choose(n-1,k) = (n-k) * choose(n,k)`.
-/
theorem bisChoosePredMulSelf_cast {n k : ℕ}
    (hn : 0 < n) (hkn : k ≤ n) :
    (n : ℝ) * (Nat.choose (n - 1) k : ℝ)
      = (((n : ℝ) - (k : ℝ)) * (Nat.choose n k : ℝ)) := by
  have hnat := Nat.choose_mul_succ_eq (n - 1) k
  have hnsub : n - 1 + 1 = n :=
    Nat.sub_add_cancel (Nat.succ_le_of_lt hn)
  have hnat' : Nat.choose (n - 1) k * n = Nat.choose n k * (n - k) := by
    simpa [hnsub, Nat.mul_comm] using hnat
  have hcast : ((n - k : ℕ) : ℝ) = (n : ℝ) - (k : ℝ) := by
    simpa using (Nat.cast_sub (R := ℝ) hkn)
  calc
    (n : ℝ) * (Nat.choose (n - 1) k : ℝ)
        = (Nat.choose (n - 1) k * n : ℕ) := by
          norm_num [Nat.mul_comm]
    _ = (Nat.choose n k * (n - k) : ℕ) := by
          rw [hnat']
    _ = ((Nat.choose n k : ℝ) * (n - k : ℕ)) := by
          norm_num
    _ = (((n : ℝ) - (k : ℝ)) * (Nat.choose n k : ℝ)) := by
          rw [hcast]
          ring

/--
Real-cast binomial identity used by the Maclaurin induction step:
`n * choose(n-1,k-1) = k * choose(n,k)`.
-/
theorem bisChoosePredPredMulSelf_cast {n k : ℕ}
    (hn : 0 < n) (hk : 0 < k) :
    (n : ℝ) * (Nat.choose (n - 1) (k - 1) : ℝ)
      = (k : ℝ) * (Nat.choose n k : ℝ) := by
  have hnat := Nat.add_one_mul_choose_eq (n - 1) (k - 1)
  have hnsub : n - 1 + 1 = n :=
    Nat.sub_add_cancel (Nat.succ_le_of_lt hn)
  have hksub : k - 1 + 1 = k :=
    Nat.sub_add_cancel (Nat.succ_le_of_lt hk)
  have hnat' :
      n * Nat.choose (n - 1) (k - 1) = Nat.choose n k * k := by
    simpa [hnsub, hksub] using hnat
  calc
    (n : ℝ) * (Nat.choose (n - 1) (k - 1) : ℝ)
        = (n * Nat.choose (n - 1) (k - 1) : ℕ) := by
          norm_num
    _ = (Nat.choose n k * k : ℕ) := by
          rw [hnat']
    _ = (k : ℝ) * (Nat.choose n k : ℝ) := by
          norm_num [Nat.mul_comm]

/--
Positive-suffix-average algebra for the one-coordinate Maclaurin induction.

If the old suffix average `a` is positive and the new coordinate is `x >= 0`,
then the two induction-hypothesis terms are bounded by the new mean term.
The zero-average branch is deliberately left separate, since it should use
nonnegativity plus `sum = 0` instead of dividing by `a`.
-/
theorem bisElementarySymmetricInductionStepBound_pos
    {n k : ℕ} {a x : ℝ}
    (hn : 0 < n) (hk : 0 < k) (hkn : k ≤ n)
    (ha : 0 < a) (hx : 0 ≤ x) :
    (Nat.choose (n - 1) k : ℝ) * a ^ k
      + x * (Nat.choose (n - 1) (k - 1) : ℝ) * a ^ (k - 1)
      ≤
    (Nat.choose n k : ℝ) * ((((n : ℝ) - 1) * a + x) / (n : ℝ)) ^ k := by
  have hnR : (0 : ℝ) < n := by exact_mod_cast hn
  have hchoose_nonneg : 0 ≤ (Nat.choose n k : ℝ) := by
    positivity
  have hpow_nonneg : 0 ≤ a ^ k := pow_nonneg ha.le k
  have hy : 0 ≤ x / a := div_nonneg hx ha.le
  have hscalar :=
    bisScalarBernoulliScreening (n := n) (k := k) (y := x / a) hn hy
  have hscaled :
      a ^ k * (((((n : ℝ) - (k : ℝ)) + (k : ℝ) * (x / a)) / (n : ℝ)))
        ≤ a ^ k * (((((n : ℝ) - 1) + (x / a)) / (n : ℝ)) ^ k) :=
    mul_le_mul_of_nonneg_left hscalar hpow_nonneg
  have hleft :
      a ^ k * (((((n : ℝ) - (k : ℝ)) + (k : ℝ) * (x / a)) / (n : ℝ)))
        = ((((n : ℝ) - (k : ℝ)) * a ^ k
            + (k : ℝ) * x * a ^ (k - 1)) / (n : ℝ)) := by
    have hpow : a ^ k = a ^ (k - 1) * a := by
      have hksub : k - 1 + 1 = k :=
        Nat.sub_add_cancel (Nat.succ_le_of_lt hk)
      calc
        a ^ k = a ^ ((k - 1) + 1) := by rw [hksub]
        _ = a ^ (k - 1) * a := by rw [pow_succ]
    rw [hpow]
    field_simp [hnR.ne', ha.ne']
  have hright :
      a ^ k * (((((n : ℝ) - 1) + x / a) / (n : ℝ)) ^ k)
        = ((((n : ℝ) - 1) * a + x) / (n : ℝ)) ^ k := by
    have hbase :
        a * (((((n : ℝ) - 1) + x / a) / (n : ℝ)))
          = ((((n : ℝ) - 1) * a + x) / (n : ℝ)) := by
      field_simp [hnR.ne', ha.ne']
    calc
      a ^ k * (((((n : ℝ) - 1) + x / a) / (n : ℝ)) ^ k)
          = (a * (((((n : ℝ) - 1) + x / a) / (n : ℝ)))) ^ k := by
            rw [mul_pow]
      _ = ((((n : ℝ) - 1) * a + x) / (n : ℝ)) ^ k := by
            rw [hbase]
  have hmain_div :
      ((((n : ℝ) - (k : ℝ)) * a ^ k
          + (k : ℝ) * x * a ^ (k - 1)) / (n : ℝ))
        ≤ ((((n : ℝ) - 1) * a + x) / (n : ℝ)) ^ k := by
    simpa [hleft, hright] using hscaled
  have hmain :
      (((n : ℝ) - (k : ℝ)) * a ^ k
          + (k : ℝ) * x * a ^ (k - 1))
        ≤ (n : ℝ) * (((((n : ℝ) - 1) * a + x) / (n : ℝ)) ^ k) := by
    have := (div_le_iff₀ hnR).mp hmain_div
    simpa [mul_comm, mul_left_comm, mul_assoc] using this
  have hmain_choose :
      (Nat.choose n k : ℝ) *
          (((n : ℝ) - (k : ℝ)) * a ^ k
            + (k : ℝ) * x * a ^ (k - 1))
        ≤ (Nat.choose n k : ℝ) *
          ((n : ℝ) * (((((n : ℝ) - 1) * a + x) / (n : ℝ)) ^ k)) :=
    mul_le_mul_of_nonneg_left hmain hchoose_nonneg
  have hnlhs :
      (n : ℝ) * ((Nat.choose (n - 1) k : ℝ) * a ^ k
        + x * (Nat.choose (n - 1) (k - 1) : ℝ) * a ^ (k - 1))
      = (Nat.choose n k : ℝ) *
          (((n : ℝ) - (k : ℝ)) * a ^ k
            + (k : ℝ) * x * a ^ (k - 1)) := by
    calc
      (n : ℝ) * ((Nat.choose (n - 1) k : ℝ) * a ^ k
        + x * (Nat.choose (n - 1) (k - 1) : ℝ) * a ^ (k - 1))
          = ((n : ℝ) * (Nat.choose (n - 1) k : ℝ)) * a ^ k
            + x * ((n : ℝ) * (Nat.choose (n - 1) (k - 1) : ℝ))
              * a ^ (k - 1) := by
            ring
      _ = (((n : ℝ) - (k : ℝ)) * (Nat.choose n k : ℝ)) * a ^ k
            + x * ((k : ℝ) * (Nat.choose n k : ℝ)) * a ^ (k - 1) := by
          rw [bisChoosePredMulSelf_cast (n := n) (k := k) hn hkn]
          rw [bisChoosePredPredMulSelf_cast (n := n) (k := k) hn hk]
      _ = (Nat.choose n k : ℝ) *
          (((n : ℝ) - (k : ℝ)) * a ^ k
            + (k : ℝ) * x * a ^ (k - 1)) := by
            ring
  have hnrhs :
      (n : ℝ) *
          ((Nat.choose n k : ℝ)
            * (((((n : ℝ) - 1) * a + x) / (n : ℝ)) ^ k))
      = (Nat.choose n k : ℝ) *
          ((n : ℝ) * (((((n : ℝ) - 1) * a + x) / (n : ℝ)) ^ k)) := by
    ring
  have hnineq :
      (n : ℝ) * ((Nat.choose (n - 1) k : ℝ) * a ^ k
        + x * (Nat.choose (n - 1) (k - 1) : ℝ) * a ^ (k - 1))
      ≤ (n : ℝ) *
          ((Nat.choose n k : ℝ)
            * (((((n : ℝ) - 1) * a + x) / (n : ℝ)) ^ k)) := by
    simpa [hnlhs, hnrhs] using hmain_choose
  exact le_of_mul_le_mul_left hnineq hnR

/--
Maclaurin elementary-symmetric mean inequality for the recursive list DP.

This is the induction route recommended by the review packet: expand the head
coordinate, apply the induction hypotheses to `k` and `k-1` on the suffix, and
close the positive-average branch with `bisElementarySymmetricInductionStepBound_pos`.
The zero-average suffix branch is handled separately by nonnegativity.
-/
theorem bisElementaryProductSum_le_choose_mul_mean_pow
    (ws : List ℝ) (k : ℕ)
    (hws : ∀ w ∈ ws, 0 ≤ w) :
    bisElementaryProductSum ws k
      ≤ (Nat.choose ws.length k : ℝ) * (ws.sum / (ws.length : ℝ)) ^ k := by
  induction ws generalizing k with
  | nil =>
      cases k with
      | zero =>
          simp [bisElementaryProductSum]
      | succ k =>
          simp [bisElementaryProductSum]
  | cons x ws ih =>
      have hx : 0 ≤ x := hws x (by simp)
      have htail : ∀ w ∈ ws, 0 ≤ w := by
        intro w hw
        exact hws w (by simp [hw])
      cases k with
      | zero =>
          simp [bisElementaryProductSum]
      | succ k =>
          by_cases hout : (x :: ws).length < k + 1
          · have hE : bisElementaryProductSum (x :: ws) (k + 1) = 0 :=
              bisElementaryProductSum_eq_zero_of_length_lt hout
            have hsum_nonneg : 0 ≤ (x :: ws).sum := by
              simpa [List.sum_cons] using add_nonneg hx (List.sum_nonneg htail)
            have hmean_nonneg :
                0 ≤ ((x :: ws).sum) / ((x :: ws).length : ℝ) :=
              div_nonneg hsum_nonneg (by positivity)
            have hrhs_nonneg :
                0 ≤ (Nat.choose (x :: ws).length (k + 1) : ℝ)
                    * (((x :: ws).sum) / ((x :: ws).length : ℝ)) ^ (k + 1) :=
              mul_nonneg (by positivity) (pow_nonneg hmean_nonneg (k + 1))
            simpa [hE] using hrhs_nonneg
          · have hkn : k + 1 ≤ (x :: ws).length := Nat.le_of_not_gt hout
            by_cases htail_len0 : ws.length = 0
            · have hwsnil : ws = [] := List.eq_nil_of_length_eq_zero htail_len0
              subst ws
              cases k with
              | zero =>
                  simp [bisElementaryProductSum]
              | succ k =>
                  have hcontradiction : k + 1 + 1 ≤ 1 := by simpa using hkn
                  omega
            · have hmpos : 0 < ws.length := Nat.pos_of_ne_zero htail_len0
              have hmR : (0 : ℝ) < ws.length := by exact_mod_cast hmpos
              have htail_sum_nonneg : 0 ≤ ws.sum := List.sum_nonneg htail
              by_cases hsum0 : ws.sum = 0
              · cases k with
                | zero =>
                    have htailE : bisElementaryProductSum ws 1 = 0 :=
                      bisElementaryProductSum_eq_zero_of_sum_eq_zero_of_nonneg
                        (r := 1) (by norm_num) htail hsum0
                    have hlen_pos : (0 : ℝ) < (ws.length + 1 : ℝ) := by
                      positivity
                    simp [bisElementaryProductSum, htailE, hsum0,
                      List.sum_cons, List.length_cons]
                    field_simp [hlen_pos.ne']
                    exact le_rfl
                | succ k =>
                    have hskip : bisElementaryProductSum ws (k + 2) = 0 :=
                      bisElementaryProductSum_eq_zero_of_sum_eq_zero_of_nonneg
                        (r := k + 2) (by omega) htail hsum0
                    have htake : bisElementaryProductSum ws (k + 1) = 0 :=
                      bisElementaryProductSum_eq_zero_of_sum_eq_zero_of_nonneg
                        (r := k + 1) (by omega) htail hsum0
                    have hE : bisElementaryProductSum (x :: ws) (k + 2) = 0 := by
                      simp [bisElementaryProductSum, hskip, htake]
                    have hsum_nonneg : 0 ≤ (x :: ws).sum := by
                      simpa [List.sum_cons] using add_nonneg hx (List.sum_nonneg htail)
                    have hmean_nonneg :
                        0 ≤ ((x :: ws).sum) / ((x :: ws).length : ℝ) :=
                      div_nonneg hsum_nonneg (by positivity)
                    have hrhs_nonneg :
                        0 ≤ (Nat.choose (x :: ws).length (k + 2) : ℝ)
                          * (((x :: ws).sum) / ((x :: ws).length : ℝ)) ^ (k + 2) :=
                      mul_nonneg (by positivity) (pow_nonneg hmean_nonneg (k + 2))
                    simpa [hE] using hrhs_nonneg
              · have htail_sum_pos : 0 < ws.sum :=
                  lt_of_le_of_ne htail_sum_nonneg (Ne.symm hsum0)
                have htail_avg_pos : 0 < ws.sum / (ws.length : ℝ) :=
                  div_pos htail_sum_pos hmR
                have hskip_ih := ih (k + 1) htail
                have htake_ih := ih k htail
                have htake_scaled :
                    x * bisElementaryProductSum ws k
                      ≤ x * ((Nat.choose ws.length k : ℝ)
                          * (ws.sum / (ws.length : ℝ)) ^ k) :=
                  mul_le_mul_of_nonneg_left htake_ih hx
                have hcomb :
                    bisElementaryProductSum ws (k + 1)
                        + x * bisElementaryProductSum ws k
                      ≤ (Nat.choose ws.length (k + 1) : ℝ)
                          * (ws.sum / (ws.length : ℝ)) ^ (k + 1)
                        + x * ((Nat.choose ws.length k : ℝ)
                          * (ws.sum / (ws.length : ℝ)) ^ k) :=
                  add_le_add hskip_ih htake_scaled
                have hkn_step : k + 1 ≤ ws.length + 1 := by
                  simpa [List.length_cons] using hkn
                have hstep :=
                  bisElementarySymmetricInductionStepBound_pos
                    (n := ws.length + 1) (k := k + 1)
                    (a := ws.sum / (ws.length : ℝ)) (x := x)
                    (by omega) (by omega) hkn_step htail_avg_pos hx
                have htarget_mean :
                    (((ws.length : ℝ) * (ws.sum / (ws.length : ℝ)) + x)
                        / ((ws.length : ℝ) + 1))
                      = (x + ws.sum) / (((ws.length : ℕ) : ℝ) + 1) := by
                  have hm1R : (0 : ℝ) < ((ws.length : ℝ) + 1) := by
                    positivity
                  field_simp [hmR.ne', hm1R.ne']
                  ring
                have hbound :
                    (Nat.choose ws.length (k + 1) : ℝ)
                          * (ws.sum / (ws.length : ℝ)) ^ (k + 1)
                        + x * ((Nat.choose ws.length k : ℝ)
                          * (ws.sum / (ws.length : ℝ)) ^ k)
                      ≤ (Nat.choose (ws.length + 1) (k + 1) : ℝ)
                          * ((x + ws.sum) / ((ws.length : ℝ) + 1)) ^ (k + 1) := by
                  simpa [htarget_mean, mul_assoc, mul_left_comm, mul_comm] using hstep
                calc
                  bisElementaryProductSum (x :: ws) (k + 1)
                      = bisElementaryProductSum ws (k + 1)
                        + x * bisElementaryProductSum ws k := by
                          rfl
                  _ ≤ (Nat.choose ws.length (k + 1) : ℝ)
                          * (ws.sum / (ws.length : ℝ)) ^ (k + 1)
                        + x * ((Nat.choose ws.length k : ℝ)
                          * (ws.sum / (ws.length : ℝ)) ^ k) := hcomb
                  _ ≤ (Nat.choose (ws.length + 1) (k + 1) : ℝ)
                          * ((x + ws.sum) / ((ws.length : ℝ) + 1)) ^ (k + 1) := hbound
                  _ = (Nat.choose (x :: ws).length (k + 1) : ℝ)
                          * ((x :: ws).sum / ((x :: ws).length : ℝ)) ^ (k + 1) := by
                        simp [List.sum_cons, List.length_cons]

/-- Selecting more elements than a finset contains gives zero elementary sum. -/
theorem bisFinsetElementaryProductSum_eq_zero_of_card_lt {α : Type} [DecidableEq α]
    {s : Finset α} {ratio : α → ℝ} {k : ℕ}
    (h : s.card < k) :
    bisFinsetElementaryProductSum s ratio k = 0 := by
  unfold bisFinsetElementaryProductSum
  rw [Finset.powersetCard_eq_empty.mpr h]
  simp

/-- Nonnegative zero-sum finsets have zero positive elementary sums. -/
theorem bisFinsetElementaryProductSum_eq_zero_of_sum_eq_zero_of_nonneg
    {α : Type} [DecidableEq α]
    {s : Finset α} {ratio : α → ℝ} {k : ℕ}
    (hk : 0 < k) (hs : ∀ i ∈ s, 0 ≤ ratio i)
    (hsum : Finset.sum s ratio = 0) :
    bisFinsetElementaryProductSum s ratio k = 0 := by
  have hzero : ∀ i ∈ s, ratio i = 0 :=
    (Finset.sum_eq_zero_iff_of_nonneg hs).mp hsum
  unfold bisFinsetElementaryProductSum
  refine Finset.sum_eq_zero ?_
  intro u hu
  have hcard : u.card = k := (Finset.mem_powersetCard.mp hu).2
  have hpos : 0 < u.card := by
    omega
  rcases (Finset.card_pos.mp hpos) with ⟨i, hi⟩
  have his : i ∈ s := (Finset.mem_powersetCard.mp hu).1 hi
  exact Finset.prod_eq_zero hi (hzero i his)

/--
Maclaurin elementary-symmetric mean inequality for a finset.

This is the finite theorem needed by the BIS screening target.  It repeats the
list induction directly over `Finset.induction_on`, avoiding a separate
enumeration bridge between lists and `powersetCard`.
-/
theorem bisFinsetElementaryProductSum_le_choose_mul_mean_pow
    {α : Type} [DecidableEq α]
    (s : Finset α) (ratio : α → ℝ) (k : ℕ)
    (hs : ∀ i ∈ s, 0 ≤ ratio i) :
    bisFinsetElementaryProductSum s ratio k
      ≤ (Nat.choose s.card k : ℝ) * ((Finset.sum s ratio) / (s.card : ℝ)) ^ k := by
  classical
  induction s using Finset.induction_on generalizing k with
  | empty =>
      cases k with
      | zero =>
          simp [bisFinsetElementaryProductSum]
      | succ k =>
          unfold bisFinsetElementaryProductSum
          rw [Finset.powersetCard_eq_empty.mpr (by simp)]
          simp
  | insert x s hxnot ih =>
      have hx : 0 ≤ ratio x := hs x (by simp)
      have htail : ∀ i ∈ s, 0 ≤ ratio i := by
        intro i hi
        exact hs i (by simp [hi])
      cases k with
      | zero =>
          simp [bisFinsetElementaryProductSum]
      | succ k =>
          by_cases hout : (insert x s).card < k + 1
          · have hE :
                bisFinsetElementaryProductSum (insert x s) ratio (k + 1) = 0 :=
              bisFinsetElementaryProductSum_eq_zero_of_card_lt hout
            have hsum_nonneg : 0 ≤ Finset.sum (insert x s) ratio :=
              Finset.sum_nonneg fun i hi => hs i hi
            have hmean_nonneg :
                0 ≤ (Finset.sum (insert x s) ratio) / ((insert x s).card : ℝ) :=
              div_nonneg hsum_nonneg (by positivity)
            have hrhs_nonneg :
                0 ≤ (Nat.choose (insert x s).card (k + 1) : ℝ)
                  * ((Finset.sum (insert x s) ratio)
                    / ((insert x s).card : ℝ)) ^ (k + 1) :=
              mul_nonneg (by positivity) (pow_nonneg hmean_nonneg (k + 1))
            simpa [hE] using hrhs_nonneg
          · have hkn : k + 1 ≤ (insert x s).card := Nat.le_of_not_gt hout
            by_cases hcard0 : s.card = 0
            · have hs_empty : s = ∅ := Finset.card_eq_zero.mp hcard0
              subst s
              cases k with
              | zero =>
                  simp [bisFinsetElementaryProductSum, Finset.powersetCard_one]
              | succ k =>
                  have : False := by
                    simp at hkn
                  exact False.elim this
            · have hmpos : 0 < s.card := Nat.pos_of_ne_zero hcard0
              have hmR : (0 : ℝ) < s.card := by exact_mod_cast hmpos
              have htail_sum_nonneg : 0 ≤ Finset.sum s ratio :=
                Finset.sum_nonneg htail
              by_cases hsum0 : Finset.sum s ratio = 0
              · cases k with
                | zero =>
                    have htailE : bisFinsetElementaryProductSum s ratio 1 = 0 :=
                      bisFinsetElementaryProductSum_eq_zero_of_sum_eq_zero_of_nonneg
                        (k := 1) (by norm_num) htail hsum0
                    have hlen_pos : (0 : ℝ) < (s.card + 1 : ℝ) := by
                      positivity
                    rw [bisFinsetElementaryProductSum_insert_succ hxnot ratio 0]
                    rw [htailE]
                    simp [hsum0, Finset.sum_insert hxnot,
                      Finset.card_insert_of_notMem hxnot, bisFinsetElementaryProductSum]
                    field_simp [hlen_pos.ne']
                    exact le_rfl
                | succ k =>
                    have hskip : bisFinsetElementaryProductSum s ratio (k + 2) = 0 :=
                      bisFinsetElementaryProductSum_eq_zero_of_sum_eq_zero_of_nonneg
                        (k := k + 2) (by omega) htail hsum0
                    have htake : bisFinsetElementaryProductSum s ratio (k + 1) = 0 :=
                      bisFinsetElementaryProductSum_eq_zero_of_sum_eq_zero_of_nonneg
                        (k := k + 1) (by omega) htail hsum0
                    have hE :
                        bisFinsetElementaryProductSum (insert x s) ratio (k + 2) = 0 := by
                      rw [bisFinsetElementaryProductSum_insert_succ hxnot ratio (k + 1)]
                      simp [hskip, htake]
                    have hsum_nonneg : 0 ≤ Finset.sum (insert x s) ratio :=
                      Finset.sum_nonneg fun i hi => hs i hi
                    have hmean_nonneg :
                        0 ≤ (Finset.sum (insert x s) ratio)
                          / ((insert x s).card : ℝ) :=
                      div_nonneg hsum_nonneg (by positivity)
                    have hrhs_nonneg :
                        0 ≤ (Nat.choose (insert x s).card (k + 2) : ℝ)
                          * ((Finset.sum (insert x s) ratio)
                            / ((insert x s).card : ℝ)) ^ (k + 2) :=
                      mul_nonneg (by positivity) (pow_nonneg hmean_nonneg (k + 2))
                    simpa [hE] using hrhs_nonneg
              · have htail_sum_pos : 0 < Finset.sum s ratio :=
                  lt_of_le_of_ne htail_sum_nonneg (Ne.symm hsum0)
                have htail_avg_pos :
                    0 < Finset.sum s ratio / (s.card : ℝ) :=
                  div_pos htail_sum_pos hmR
                have hskip_ih := ih (k + 1) htail
                have htake_ih := ih k htail
                have htake_scaled :
                    ratio x * bisFinsetElementaryProductSum s ratio k
                      ≤ ratio x * ((Nat.choose s.card k : ℝ)
                          * (Finset.sum s ratio / (s.card : ℝ)) ^ k) :=
                  mul_le_mul_of_nonneg_left htake_ih hx
                have hcomb :
                    bisFinsetElementaryProductSum s ratio (k + 1)
                        + ratio x * bisFinsetElementaryProductSum s ratio k
                      ≤ (Nat.choose s.card (k + 1) : ℝ)
                          * (Finset.sum s ratio / (s.card : ℝ)) ^ (k + 1)
                        + ratio x * ((Nat.choose s.card k : ℝ)
                          * (Finset.sum s ratio / (s.card : ℝ)) ^ k) :=
                  add_le_add hskip_ih htake_scaled
                have hkn_step : k + 1 ≤ s.card + 1 := by
                  simpa [Finset.card_insert_of_notMem hxnot] using hkn
                have hstep :=
                  bisElementarySymmetricInductionStepBound_pos
                    (n := s.card + 1) (k := k + 1)
                    (a := Finset.sum s ratio / (s.card : ℝ)) (x := ratio x)
                    (by omega) (by omega) hkn_step htail_avg_pos hx
                have htarget_mean :
                    (((s.card : ℝ) * (Finset.sum s ratio / (s.card : ℝ)) + ratio x)
                        / ((s.card : ℝ) + 1))
                      = (ratio x + Finset.sum s ratio) / (((s.card : ℕ) : ℝ) + 1) := by
                  have hm1R : (0 : ℝ) < ((s.card : ℝ) + 1) := by
                    positivity
                  field_simp [hmR.ne', hm1R.ne']
                  ring
                have hbound :
                    (Nat.choose s.card (k + 1) : ℝ)
                          * (Finset.sum s ratio / (s.card : ℝ)) ^ (k + 1)
                        + ratio x * ((Nat.choose s.card k : ℝ)
                          * (Finset.sum s ratio / (s.card : ℝ)) ^ k)
                      ≤ (Nat.choose (s.card + 1) (k + 1) : ℝ)
                          * ((ratio x + Finset.sum s ratio)
                            / ((s.card : ℝ) + 1)) ^ (k + 1) := by
                  simpa [htarget_mean, mul_assoc, mul_left_comm, mul_comm] using hstep
                calc
                  bisFinsetElementaryProductSum (insert x s) ratio (k + 1)
                      = bisFinsetElementaryProductSum s ratio (k + 1)
                        + ratio x * bisFinsetElementaryProductSum s ratio k := by
                          rw [bisFinsetElementaryProductSum_insert_succ hxnot]
                  _ ≤ (Nat.choose s.card (k + 1) : ℝ)
                          * (Finset.sum s ratio / (s.card : ℝ)) ^ (k + 1)
                        + ratio x * ((Nat.choose s.card k : ℝ)
                          * (Finset.sum s ratio / (s.card : ℝ)) ^ k) := hcomb
                  _ ≤ (Nat.choose (s.card + 1) (k + 1) : ℝ)
                          * ((ratio x + Finset.sum s ratio)
                            / ((s.card : ℝ) + 1)) ^ (k + 1) := hbound
                  _ = (Nat.choose (insert x s).card (k + 1) : ℝ)
                          * ((Finset.sum (insert x s) ratio)
                            / ((insert x s).card : ℝ)) ^ (k + 1) := by
                        simp [Finset.sum_insert hxnot, Finset.card_insert_of_notMem hxnot]

/--
Closed finite Maclaurin screening inequality for BIS coordinate ratios.

This discharges the theorem seam that was previously represented by
`bisGlobalEqualizationTransformExists`: for nonnegative ratios, the exact
`k`-out-of-`T` subset-ratio average is bounded by the `k`th power of the
coordinate arithmetic mean.
-/
theorem bisMaclaurinScreeningInequality_of_nonneg {t : ℕ}
    {ratio : Fin (t + 1) → ℝ} {k : ℕ}
    (hnonneg : ∀ i, 0 ≤ ratio i) :
    bisMaclaurinScreeningInequality ratio k := by
  classical
  refine ⟨hnonneg, ?_⟩
  by_cases hk : k ≤ t + 1
  · have hfin :=
      bisFinsetElementaryProductSum_le_choose_mul_mean_pow
        (s := (Finset.univ : Finset (Fin (t + 1)))) (ratio := ratio) (k := k)
        (by
          intro i _hi
          exact hnonneg i)
    have hchoose_pos : 0 < (Nat.choose (t + 1) k : ℝ) := by
      exact_mod_cast Nat.choose_pos hk
    have hdiv :
        bisFinsetElementaryProductSum (Finset.univ : Finset (Fin (t + 1))) ratio k
            / (Nat.choose (t + 1) k : ℝ)
          ≤ ((Nat.choose (t + 1) k : ℝ)
              * ((Finset.sum Finset.univ ratio) / (t + 1 : ℝ)) ^ k)
              / (Nat.choose (t + 1) k : ℝ) := by
      refine div_le_div_of_nonneg_right ?_ hchoose_pos.le
      simpa using hfin
    have hcancel :
        ((Nat.choose (t + 1) k : ℝ)
              * ((Finset.sum Finset.univ ratio) / (t + 1 : ℝ)) ^ k)
              / (Nat.choose (t + 1) k : ℝ)
          = ((Finset.sum Finset.univ ratio) / (t + 1 : ℝ)) ^ k := by
      exact mul_div_cancel_left₀ _ hchoose_pos.ne'
    simpa [bisMaclaurinScreeningInequality,
      bisScreeningAverage_eq_finsetElementaryProductSum,
      Finset.card_univ, hcancel] using hdiv
  · have hlt : t + 1 < k := Nat.lt_of_not_ge hk
    have hE :
        bisFinsetElementaryProductSum (Finset.univ : Finset (Fin (t + 1))) ratio k
          = 0 := by
      apply bisFinsetElementaryProductSum_eq_zero_of_card_lt
      simpa [Finset.card_univ] using hlt
    have hmean_nonneg : 0 ≤ (Finset.sum Finset.univ ratio) / (t + 1 : ℝ) := by
      exact div_nonneg (Finset.sum_nonneg fun i _ => hnonneg i) (by positivity)
    have hrhs : 0 ≤ ((Finset.sum Finset.univ ratio) / (t + 1 : ℝ)) ^ k :=
      pow_nonneg hmean_nonneg k
    simpa [bisMaclaurinScreeningInequality,
      bisScreeningAverage_eq_finsetElementaryProductSum, hE] using hrhs

/-- Unconditional paper-facing finite BIS screening bound. -/
theorem bisScreeningBoundTarget_all {t : ℕ}
    (ratio : Fin (t + 1) → ℝ) (k : ℕ) :
    bisScreeningBoundTarget ratio k := by
  intro hnonneg
  exact (bisMaclaurinScreeningInequality_of_nonneg
    (t := t) (ratio := ratio) (k := k) hnonneg).2

/--
Density-ratio screening bridge for the exact fixed-cardinality active law.

After dividing the exact `k`-out-of-`T` active density by the inactive product
density, the result is bounded by the `k`th power of the average coordinate
likelihood ratio.  This is the paper-facing bridge from the random-allocation
density quotient to the closed finite Maclaurin screening theorem.
-/
theorem kOutOfTBarDensity_div_prodDensity_le_average_ratio_pow
    {α : Type} {t : ℕ}
    (p q : α → ℝ) (k : ℕ) (x : Fin (t + 1) → α)
    (hq : ∀ i : Fin (t + 1), q (x i) ≠ 0)
    (hnonneg : ∀ i : Fin (t + 1), 0 ≤ p (x i) / q (x i)) :
    kOutOfTBarDensity p q k x / prodDensity q x
      ≤ ((Finset.sum Finset.univ
            (fun i : Fin (t + 1) => p (x i) / q (x i)))
          / (t + 1 : ℝ)) ^ k := by
  rw [kOutOfTBarDensity_div_prodDensity_eq_bisExactSubsetRatioAverage p q k x hq]
  exact
    bisScreeningBoundTarget_all
      (t := t) (ratio := fun i : Fin (t + 1) => p (x i) / q (x i)) k
      hnonneg

/-
## Low-noise first-layer algebra

The paper's low-noise optimality argument first isolates participation-count
variation: the leading privacy-loss term is proportional to the participation
count.  The following finite facts do not formalize the Gaussian asymptotic,
but they capture the algebraic certificate used by that first layer: a
nonnegative weighted squared count deviation is minimized at zero, and zero
deviation forces every positive-mass state to have the target count.
-/

/-- Weighted squared deviation of a finite participation-count law. -/
def bisWeightedCountSqDeviation {α : Type} [DecidableEq α]
    (s : Finset α) (mass : α → ℝ) (count : α → ℕ) (target : ℝ) : ℝ :=
  Finset.sum s fun x => mass x * ((count x : ℝ) - target) ^ 2

/-- Count squared deviation is nonnegative under nonnegative weights. -/
theorem bisWeightedCountSqDeviation_nonneg {α : Type} [DecidableEq α]
    (s : Finset α) (mass : α → ℝ) (count : α → ℕ) (target : ℝ)
    (hmass : ∀ x ∈ s, 0 ≤ mass x) :
    0 ≤ bisWeightedCountSqDeviation s mass count target := by
  unfold bisWeightedCountSqDeviation
  exact Finset.sum_nonneg fun x hx =>
    mul_nonneg (hmass x hx) (sq_nonneg ((count x : ℝ) - target))

/--
Zero weighted count deviation is equivalent to fixed count on the positive-mass
support.

This is the theorem-facing algebraic core of the low-noise first optimization
layer: if the expected count target is fixed, the only way to eliminate the
leading count fluctuation is to put all positive probability on states with
that count.
-/
theorem bisWeightedCountSqDeviation_eq_zero_iff_positive_mass_count_eq
    {α : Type} [DecidableEq α]
    (s : Finset α) (mass : α → ℝ) (count : α → ℕ) (target : ℝ)
    (hmass : ∀ x ∈ s, 0 ≤ mass x) :
    bisWeightedCountSqDeviation s mass count target = 0
      ↔ ∀ x ∈ s, 0 < mass x → (count x : ℝ) = target := by
  constructor
  · intro hzero x hx hpos
    have hterm_nonneg :
        ∀ y ∈ s, 0 ≤ mass y * ((count y : ℝ) - target) ^ 2 := by
      intro y hy
      exact mul_nonneg (hmass y hy) (sq_nonneg ((count y : ℝ) - target))
    have hterm :
        mass x * ((count x : ℝ) - target) ^ 2 = 0 := by
      exact ((Finset.sum_eq_zero_iff_of_nonneg hterm_nonneg).mp hzero) x hx
    have hsquare : ((count x : ℝ) - target) ^ 2 = 0 :=
      (mul_eq_zero.mp hterm).resolve_left hpos.ne'
    have hdiff : (count x : ℝ) - target = 0 := sq_eq_zero_iff.mp hsquare
    linarith
  · intro hfixed
    unfold bisWeightedCountSqDeviation
    refine Finset.sum_eq_zero ?_
    intro x hx
    by_cases hpos : 0 < mass x
    · have hcount := hfixed x hx hpos
      simp [hcount]
    · have hmass_zero : mass x = 0 := by
        exact le_antisymm (le_of_not_gt hpos) (hmass x hx)
      simp [hmass_zero]

/--
Natural-number version of the zero-deviation support characterization.

When the target count is an integer, zero deviation means every positive-mass
state has exactly that natural count.
-/
theorem bisWeightedCountSqDeviation_eq_zero_iff_positive_mass_count_eq_nat
    {α : Type} [DecidableEq α]
    (s : Finset α) (mass : α → ℝ) (count : α → ℕ) (target : ℕ)
    (hmass : ∀ x ∈ s, 0 ≤ mass x) :
    bisWeightedCountSqDeviation s mass count (target : ℝ) = 0
      ↔ ∀ x ∈ s, 0 < mass x → count x = target := by
  rw [bisWeightedCountSqDeviation_eq_zero_iff_positive_mass_count_eq
    (s := s) (mass := mass) (count := count) (target := (target : ℝ)) hmass]
  constructor
  · intro h x hx hpos
    exact_mod_cast h x hx hpos
  · intro h x hx hpos
    exact_mod_cast h x hx hpos

/--
Variance decomposition for the participation count.

If the theorem-facing masses are normalized and the weighted mean count is the
target, then the weighted squared deviation from the target is exactly the
second count moment minus the squared target.  This is the finite algebra that
identifies participation-count variance with the all-ones covariance direction
used later in the paper's high-noise discussion.
-/
theorem bisWeightedCountSqDeviation_eq_secondMoment_sub_sq_of_mean
    {α : Type} [DecidableEq α]
    (s : Finset α) (mass : α → ℝ) (count : α → ℕ) (target : ℝ)
    (hmass_total : Finset.sum s mass = 1)
    (hmean : Finset.sum s (fun x => mass x * (count x : ℝ)) = target) :
    bisWeightedCountSqDeviation s mass count target
      = Finset.sum s (fun x => mass x * (count x : ℝ) ^ 2) - target ^ 2 := by
  unfold bisWeightedCountSqDeviation
  calc
    Finset.sum s (fun x => mass x * ((count x : ℝ) - target) ^ 2)
        = Finset.sum s (fun x =>
            mass x * (count x : ℝ) ^ 2
              - 2 * target * (mass x * (count x : ℝ))
              + target ^ 2 * mass x) := by
          refine Finset.sum_congr rfl ?_
          intro x _hx
          ring_nf
    _ = Finset.sum s (fun x => mass x * (count x : ℝ) ^ 2)
          - 2 * target * Finset.sum s (fun x => mass x * (count x : ℝ))
          + target ^ 2 * Finset.sum s mass := by
          rw [Finset.sum_add_distrib]
          rw [Finset.sum_sub_distrib]
          simp only [Finset.mul_sum]
    _ = Finset.sum s (fun x => mass x * (count x : ℝ) ^ 2) - target ^ 2 := by
          rw [hmean, hmass_total]
          ring

/-- Participation count of a Boolean `T`-step participation vector. -/
def bisBoolParticipationCount {T : ℕ} (x : Fin T → Bool) : ℕ :=
  ((Finset.univ : Finset (Fin T)).filter fun i => x i).card

/-- Real-valued `0/1` vector associated with a Boolean participation pattern. -/
def bisBoolParticipationVec {T : ℕ} (x : Fin T → Bool) (i : Fin T) : ℝ :=
  if x i then 1 else 0

/--
For Boolean participation vectors, squared Euclidean norm equals participation
count.

This is the finite identity behind the paper's low-noise leading term
`‖x‖₂²`: for binary vectors, the norm-squared is exactly the number of
participating iterations.
-/
theorem bisBoolParticipationVec_sq_sum_eq_count
    {T : ℕ} (x : Fin T → Bool) :
    Finset.sum Finset.univ (fun i => bisBoolParticipationVec x i ^ 2)
      = (bisBoolParticipationCount x : ℝ) := by
  unfold bisBoolParticipationVec bisBoolParticipationCount
  calc
    Finset.sum Finset.univ (fun i : Fin T => (if x i then (1 : ℝ) else 0) ^ 2)
        = Finset.sum Finset.univ (fun i : Fin T => if x i then (1 : ℝ) else 0) := by
          refine Finset.sum_congr rfl ?_
          intro i _hi
          by_cases h : x i
          · simp [h]
          · simp [h]
    _ = (((Finset.univ : Finset (Fin T)).filter fun i => x i).card : ℝ) := by
          rw [← Finset.sum_filter]
          simp

/--
The uniform fixed-cardinality BIS support has zero participation-count
deviation, independently of the masses assigned inside that support.

This names the algebraic reason the `k`-out-of-`T` BIS family eliminates the
leading low-noise participation-count fluctuation.
-/
theorem bisFixedCardSupport_weightedCountSqDeviation_zero
    {α : Type} [DecidableEq α]
    (base : Finset α) (mass : Finset α → ℝ) (k : ℕ) :
    bisWeightedCountSqDeviation (base.powersetCard k) mass
        (fun u : Finset α => u.card) (k : ℝ) = 0 := by
  unfold bisWeightedCountSqDeviation
  refine Finset.sum_eq_zero ?_
  intro u hu
  have hcard : u.card = k := (Finset.mem_powersetCard.mp hu).2
  simp [hcard]

/--
Uniform theorem-facing mass on the fixed-cardinality BIS support.

The mass is intentionally defined on all subsets, but is nonzero only on
`base.powersetCard k`.
-/
def bisFixedCardUniformMass {α : Type} [DecidableEq α]
    (base : Finset α) (k : ℕ) (u : Finset α) : ℝ :=
  if u ∈ base.powersetCard k then ((Nat.choose base.card k : ℝ)⁻¹) else 0

/-- Coordinate marginal induced by the uniform fixed-cardinality BIS mass. -/
def bisFixedCardUniformMarginal {α : Type} [DecidableEq α]
    (base : Finset α) (k : ℕ) (a : α) : ℝ :=
  Finset.sum (base.powersetCard k)
    (fun u : Finset α =>
      bisFixedCardUniformMass base k u * if a ∈ u then (1 : ℝ) else 0)

/-- Joint coordinate marginal induced by the uniform fixed-cardinality BIS mass. -/
def bisFixedCardUniformPairMarginal {α : Type} [DecidableEq α]
    (base : Finset α) (k : ℕ) (a b : α) : ℝ :=
  Finset.sum (base.powersetCard k)
    (fun u : Finset α =>
      bisFixedCardUniformMass base k u * if a ∈ u ∧ b ∈ u then (1 : ℝ) else 0)

/-- Covariance entry induced by the uniform fixed-cardinality BIS mass. -/
def bisFixedCardUniformCovarianceEntry {α : Type} [DecidableEq α]
    (base : Finset α) (k : ℕ) (a b : α) : ℝ :=
  bisFixedCardUniformPairMarginal base k a b
    - bisFixedCardUniformMarginal base k a * bisFixedCardUniformMarginal base k b

/-- Uniform fixed-cardinality mass is nonnegative. -/
theorem bisFixedCardUniformMass_nonneg
    {α : Type} [DecidableEq α]
    (base : Finset α) (k : ℕ) (u : Finset α) :
    0 ≤ bisFixedCardUniformMass base k u := by
  unfold bisFixedCardUniformMass
  by_cases h : u ∈ base.powersetCard k
  · simp [h, inv_nonneg]
  · simp [h]

/-- Uniform fixed-cardinality mass normalizes on its support. -/
theorem bisFixedCardUniformMass_sum_support_eq_one
    {α : Type} [DecidableEq α]
    (base : Finset α) (k : ℕ) (hk : k ≤ base.card) :
    Finset.sum (base.powersetCard k) (bisFixedCardUniformMass base k) = 1 := by
  unfold bisFixedCardUniformMass
  have hchoose_pos : (0 : ℝ) < (Nat.choose base.card k : ℝ) := by
    exact_mod_cast Nat.choose_pos hk
  calc
    Finset.sum (base.powersetCard k)
        (fun u => if u ∈ base.powersetCard k then ((Nat.choose base.card k : ℝ)⁻¹) else 0)
        = Finset.sum (base.powersetCard k)
            (fun _u => ((Nat.choose base.card k : ℝ)⁻¹)) := by
          refine Finset.sum_congr rfl ?_
          intro u hu
          simp [hu]
    _ = (Nat.choose base.card k : ℝ) * (Nat.choose base.card k : ℝ)⁻¹ := by
          simp [Finset.card_powersetCard, nsmul_eq_mul]
    _ = 1 := by
          exact mul_inv_cancel₀ hchoose_pos.ne'

/-- Uniform fixed-cardinality mass normalizes as a full finite-type sum. -/
theorem bisFixedCardUniformMass_sum_univ_eq_one
    {α : Type} [Fintype α] [DecidableEq α]
    (base : Finset α) (k : ℕ) (hk : k ≤ base.card) :
    Finset.sum Finset.univ (bisFixedCardUniformMass base k) = 1 := by
  calc
    Finset.sum Finset.univ (bisFixedCardUniformMass base k)
      = Finset.sum (base.powersetCard k) (bisFixedCardUniformMass base k) := by
          symm
          refine Finset.sum_subset (by intro u hu; simp) ?_
          intro u _hu hnot
          unfold bisFixedCardUniformMass
          simp [hnot]
    _ = 1 := by
          rw [bisFixedCardUniformMass_sum_support_eq_one base k hk]

/-- Uniform fixed-cardinality mass has mean participation count `k`. -/
theorem bisFixedCardUniformMass_mean_count_eq
    {α : Type} [DecidableEq α]
    (base : Finset α) (k : ℕ) (hk : k ≤ base.card) :
    Finset.sum (base.powersetCard k)
        (fun u => bisFixedCardUniformMass base k u * (u.card : ℝ))
      = (k : ℝ) := by
  have hnorm := bisFixedCardUniformMass_sum_support_eq_one base k hk
  calc
    Finset.sum (base.powersetCard k)
        (fun u => bisFixedCardUniformMass base k u * (u.card : ℝ))
        = Finset.sum (base.powersetCard k)
            (fun u => bisFixedCardUniformMass base k u * (k : ℝ)) := by
          refine Finset.sum_congr rfl ?_
          intro u hu
          have hcard : u.card = k := (Finset.mem_powersetCard.mp hu).2
          simp [hcard]
    _ = (Finset.sum (base.powersetCard k) (bisFixedCardUniformMass base k))
          * (k : ℝ) := by
          rw [Finset.sum_mul]
    _ = (k : ℝ) := by
          rw [hnorm]
          ring

/-- Uniform fixed-cardinality mass has second count moment `k^2`. -/
theorem bisFixedCardUniformMass_secondMoment_count_eq_sq
    {α : Type} [DecidableEq α]
    (base : Finset α) (k : ℕ) (hk : k ≤ base.card) :
    Finset.sum (base.powersetCard k)
        (fun u : Finset α => bisFixedCardUniformMass base k u * (u.card : ℝ) ^ 2)
      = (k : ℝ) ^ 2 := by
  calc
    Finset.sum (base.powersetCard k)
        (fun u : Finset α => bisFixedCardUniformMass base k u * (u.card : ℝ) ^ 2)
        = Finset.sum (base.powersetCard k)
            (fun u : Finset α => bisFixedCardUniformMass base k u * (k : ℝ) ^ 2) := by
          refine Finset.sum_congr rfl ?_
          intro u hu
          have hcard : u.card = k := (Finset.mem_powersetCard.mp hu).2
          simp [hcard]
    _ = (Finset.sum (base.powersetCard k) (bisFixedCardUniformMass base k))
          * (k : ℝ) ^ 2 := by
          rw [Finset.sum_mul]
    _ = (k : ℝ) ^ 2 := by
          rw [bisFixedCardUniformMass_sum_support_eq_one base k hk]
          ring

/--
Uniform fixed-cardinality mass has zero participation-count variance in
second-moment form.

This is the finite all-ones-direction covariance fact used by the high-noise
second layer: `E[count^2] - E[count]^2 = 0` for exact `k`-out-of-`T`
participation.
-/
theorem bisFixedCardUniformMass_countVariance_zero
    {α : Type} [DecidableEq α]
    (base : Finset α) (k : ℕ) (hk : k ≤ base.card) :
    Finset.sum (base.powersetCard k)
        (fun u : Finset α => bisFixedCardUniformMass base k u * (u.card : ℝ) ^ 2)
      - (k : ℝ) ^ 2 = 0 := by
  rw [bisFixedCardUniformMass_secondMoment_count_eq_sq base k hk]
  ring

/-- Uniform fixed-cardinality BIS mass has zero count deviation. -/
theorem bisFixedCardUniformMass_countDeviation_zero
    {α : Type} [DecidableEq α]
    (base : Finset α) (k : ℕ) :
    bisWeightedCountSqDeviation (base.powersetCard k)
        (bisFixedCardUniformMass base k) (fun u : Finset α => u.card) (k : ℝ)
      = 0 := by
  exact bisFixedCardSupport_weightedCountSqDeviation_zero base
    (bisFixedCardUniformMass base k) k

/--
Fixed-cardinality subset support has uniform coordinate counts.

For any element `a` in the base set, exactly `choose (|base|-1) k` subsets of
size `k+1` contain `a`.  This is the finite combinatorial core behind the fact
that uniform fixed-cardinality BIS has uniform marginal participation
probabilities.
-/
theorem bisFixedCardSupport_memberIndicator_sum_succ
    {α : Type} [DecidableEq α]
    (base : Finset α) (a : α) (ha : a ∈ base) (k : ℕ) :
    Finset.sum (base.powersetCard (k + 1))
        (fun u : Finset α => if a ∈ u then (1 : ℝ) else 0)
      = (Nat.choose (base.card - 1) k : ℝ) := by
  have hbase : base = insert a (base.erase a) := by
    exact (Finset.insert_erase ha).symm
  rw [hbase]
  rw [Finset.powersetCard_succ_insert (Finset.notMem_erase a base) k]
  have hdisj : Disjoint ((base.erase a).powersetCard (k + 1))
      (((base.erase a).powersetCard k).image (insert a)) := by
    rw [Finset.disjoint_left]
    intro u hu himg
    have hau : a ∉ u := by
      intro hau
      have hsub : u ⊆ base.erase a := (Finset.mem_powersetCard.mp hu).1
      exact (Finset.notMem_erase a base) (hsub hau)
    rcases Finset.mem_image.mp himg with ⟨v, _hv, huv⟩
    rw [← huv] at hau
    exact hau (Finset.mem_insert_self a v)
  rw [Finset.sum_union hdisj]
  have hleft : Finset.sum ((base.erase a).powersetCard (k + 1))
        (fun u : Finset α => if a ∈ u then (1 : ℝ) else 0) = 0 := by
    refine Finset.sum_eq_zero ?_
    intro u hu
    have hsub : u ⊆ base.erase a := (Finset.mem_powersetCard.mp hu).1
    have hau : a ∉ u := by
      intro hau
      exact (Finset.notMem_erase a base) (hsub hau)
    simp [hau]
  have hinj : ∀ x ∈ (base.erase a).powersetCard k,
      ∀ y ∈ (base.erase a).powersetCard k, insert a x = insert a y → x = y := by
    intro x hx y hy hxy
    apply Finset.ext
    intro z
    have hax : a ∉ x := by
      intro hzx
      have hsub : x ⊆ base.erase a := (Finset.mem_powersetCard.mp hx).1
      exact (Finset.notMem_erase a base) (hsub hzx)
    have hay : a ∉ y := by
      intro hzy
      have hsub : y ⊆ base.erase a := (Finset.mem_powersetCard.mp hy).1
      exact (Finset.notMem_erase a base) (hsub hzy)
    by_cases hza : z = a
    · subst z
      simp [hax, hay]
    · have hz := congrArg (fun u : Finset α => z ∈ u) hxy
      simpa [hza] using hz
  have himage : Finset.sum (((base.erase a).powersetCard k).image (insert a))
        (fun u : Finset α => if a ∈ u then (1 : ℝ) else 0)
      = (((base.erase a).powersetCard k).card : ℝ) := by
    rw [Finset.sum_image]
    · simp
    · exact hinj
  rw [hleft, himage, zero_add]
  rw [Finset.card_powersetCard]
  simp [Finset.card_insert_of_notMem, Finset.card_erase_of_mem ha]

/--
Uniform fixed-cardinality BIS has identical marginal mass at each base
coordinate.

This keeps the result in exact binomial-ratio form.  The ratio simplifies to
`(k+1)/|base|` when `k+1 <= |base|`; the binomial form is usually the safer
theorem-facing handoff.
-/
theorem bisFixedCardUniformMass_memberMarginal_succ
    {α : Type} [DecidableEq α]
    (base : Finset α) (a : α) (ha : a ∈ base) (k : ℕ) :
    Finset.sum (base.powersetCard (k + 1))
        (fun u : Finset α =>
          bisFixedCardUniformMass base (k + 1) u
            * if a ∈ u then (1 : ℝ) else 0)
      = (Nat.choose (base.card - 1) k : ℝ)
          / (Nat.choose base.card (k + 1) : ℝ) := by
  unfold bisFixedCardUniformMass
  calc
    Finset.sum (base.powersetCard (k + 1))
        (fun u : Finset α =>
          (if u ∈ base.powersetCard (k + 1) then
              ((Nat.choose base.card (k + 1) : ℝ)⁻¹) else 0)
            * if a ∈ u then (1 : ℝ) else 0)
        = Finset.sum (base.powersetCard (k + 1))
            (fun u : Finset α =>
              ((Nat.choose base.card (k + 1) : ℝ)⁻¹)
                * if a ∈ u then (1 : ℝ) else 0) := by
          refine Finset.sum_congr rfl ?_
          intro u hu
          simp [hu]
    _ = Finset.sum (base.powersetCard (k + 1))
        (fun u : Finset α =>
          ((Nat.choose base.card (k + 1) : ℝ)⁻¹)
            * (if a ∈ u then (1 : ℝ) else 0)) := by
          rfl
    _ 
        = ((Nat.choose base.card (k + 1) : ℝ)⁻¹)
            * Finset.sum (base.powersetCard (k + 1))
                (fun u : Finset α => if a ∈ u then (1 : ℝ) else 0) := by
          rw [← Finset.mul_sum]
    _ = ((Nat.choose base.card (k + 1) : ℝ)⁻¹)
            * (Nat.choose (base.card - 1) k : ℝ) := by
          rw [bisFixedCardSupport_memberIndicator_sum_succ base a ha k]
    _ = (Nat.choose (base.card - 1) k : ℝ)
          / (Nat.choose base.card (k + 1) : ℝ) := by
          rw [div_eq_mul_inv]
          ring

/--
Paper-facing uniform marginal form.

When `k+1 <= |base|`, the exact binomial ratio from
`bisFixedCardUniformMass_memberMarginal_succ` simplifies to `(k+1)/|base|`.
-/
theorem bisFixedCardUniformMass_memberMarginal_succ_eq_div_card
    {α : Type} [DecidableEq α]
    (base : Finset α) (a : α) (ha : a ∈ base) (k : ℕ)
    (hk : k + 1 ≤ base.card) :
    Finset.sum (base.powersetCard (k + 1))
        (fun u : Finset α =>
          bisFixedCardUniformMass base (k + 1) u
            * if a ∈ u then (1 : ℝ) else 0)
      = (k + 1 : ℝ) / (base.card : ℝ) := by
  rw [bisFixedCardUniformMass_memberMarginal_succ base a ha k]
  have hcard_pos : 0 < base.card := lt_of_lt_of_le (Nat.succ_pos k) hk
  have hn_pred : base.card - 1 + 1 = base.card :=
    Nat.sub_one_add_one (ne_of_gt hcard_pos)
  have hnat := Nat.add_one_mul_choose_eq (base.card - 1) k
  rw [hn_pred] at hnat
  have hreal : (base.card : ℝ) * (Nat.choose (base.card - 1) k : ℝ)
      = (Nat.choose base.card (k + 1) : ℝ) * (k + 1 : ℝ) := by
    exact_mod_cast hnat
  have hcard_posR : (0 : ℝ) < base.card := by
    exact_mod_cast hcard_pos
  have hchoose_pos : (0 : ℝ) < (Nat.choose base.card (k + 1) : ℝ) := by
    exact_mod_cast Nat.choose_pos hk
  field_simp [hcard_posR.ne', hchoose_pos.ne']
  linarith

/--
Uniform fixed-cardinality BIS has marginal participation rate `k/|base|` at
every base coordinate, including the `k=0` boundary.
-/
theorem bisFixedCardUniformMarginal_eq_div_card
    {α : Type} [DecidableEq α]
    (base : Finset α) (a : α) (ha : a ∈ base) (k : ℕ)
    (hk : k ≤ base.card) :
    bisFixedCardUniformMarginal base k a = (k : ℝ) / (base.card : ℝ) := by
  cases k with
  | zero =>
      unfold bisFixedCardUniformMarginal bisFixedCardUniformMass
      simp
  | succ k =>
      unfold bisFixedCardUniformMarginal
      simpa using
        bisFixedCardUniformMass_memberMarginal_succ_eq_div_card base a ha k hk

/-
## High-noise first-layer algebra

The paper's high-noise first layer minimizes the squared norm of the marginal
participation vector under a fixed total expected participation count.  This is
the finite Cauchy-Schwarz algebra behind the statement that uniform marginals
are optimal at leading order.
-/

/--
Fixed-total marginal norm lower bound.

For any finite marginal vector with total mass `total`, the squared norm is at
least `total^2 / card`.  This is the Cauchy-Schwarz step used by the high-noise
first layer of the paper.
-/
theorem bisMarginalSqNorm_ge_uniformOfSum {α : Type}
    (s : Finset α) (mu : α → ℝ) (total : ℝ)
    (hs : s.Nonempty)
    (hsum : Finset.sum s mu = total) :
    total ^ 2 / (s.card : ℝ) ≤ Finset.sum s fun i => mu i ^ 2 := by
  have hcard_pos_nat : 0 < s.card := Finset.card_pos.mpr hs
  have hcard_pos : (0 : ℝ) < (s.card : ℝ) := by
    exact_mod_cast hcard_pos_nat
  have h :=
    (sq_sum_le_card_mul_sum_sq (s := s) (f := mu) :
      (Finset.sum s mu) ^ 2
        ≤ (s.card : ℝ) * Finset.sum s (fun i => mu i ^ 2))
  rw [hsum] at h
  rw [div_le_iff₀ hcard_pos]
  simpa [mul_comm, mul_left_comm, mul_assoc] using h

/--
Uniform marginals attain the fixed-total marginal norm lower bound.

This is the equality side of the high-noise first-layer algebra: if every
coordinate marginal is the arithmetic mean `total / card`, then the squared
norm is exactly `total^2 / card`.
-/
theorem bisMarginalSqNorm_eq_uniformOfForallEq {α : Type}
    (s : Finset α) (mu : α → ℝ) (total : ℝ)
    (hs : s.Nonempty)
    (hmu : ∀ i ∈ s, mu i = total / (s.card : ℝ)) :
    (Finset.sum s fun i => mu i ^ 2) = total ^ 2 / (s.card : ℝ) := by
  have hcard_pos_nat : 0 < s.card := Finset.card_pos.mpr hs
  have hcard_ne : (s.card : ℝ) ≠ 0 := by
    exact_mod_cast (ne_of_gt hcard_pos_nat)
  calc
    (Finset.sum s fun i => mu i ^ 2)
        = Finset.sum s (fun _i => (total / (s.card : ℝ)) ^ 2) := by
          refine Finset.sum_congr rfl ?_
          intro i hi
          rw [hmu i hi]
    _ = (s.card : ℝ) * (total / (s.card : ℝ)) ^ 2 := by
          simp [nsmul_eq_mul]
    _ = total ^ 2 / (s.card : ℝ) := by
          field_simp [hcard_ne]

/-- High-noise first-layer lower bound on `Fin T` marginal vectors. -/
theorem bisFinMarginalSqNorm_ge_uniformOfSum
    {T : ℕ} (mu : Fin T → ℝ) (total : ℝ)
    (hT : 0 < T)
    (hsum : Finset.sum Finset.univ mu = total) :
    total ^ 2 / (T : ℝ) ≤ Finset.sum Finset.univ fun i => mu i ^ 2 := by
  have hs : (Finset.univ : Finset (Fin T)).Nonempty := by
    exact ⟨⟨0, hT⟩, by simp⟩
  simpa [Finset.card_univ] using
    bisMarginalSqNorm_ge_uniformOfSum
      (s := (Finset.univ : Finset (Fin T))) (mu := mu) (total := total) hs hsum

/-- Uniform `Fin T` marginals attain the high-noise first-layer lower bound. -/
theorem bisFinMarginalSqNorm_eq_uniformOfForallEq
    {T : ℕ} (mu : Fin T → ℝ) (total : ℝ)
    (hT : 0 < T)
    (hmu : ∀ i : Fin T, mu i = total / (T : ℝ)) :
    (Finset.sum Finset.univ fun i => mu i ^ 2) = total ^ 2 / (T : ℝ) := by
  have hs : (Finset.univ : Finset (Fin T)).Nonempty := by
    exact ⟨⟨0, hT⟩, by simp⟩
  simpa [Finset.card_univ] using
    bisMarginalSqNorm_eq_uniformOfForallEq
      (s := (Finset.univ : Finset (Fin T))) (mu := mu) (total := total) hs
      (by
        intro i _hi
        simpa [Finset.card_univ] using hmu i)

/--
Uniform `k`-out-of-`T` BIS marginals attain the high-noise first-layer Cauchy
lower bound.

This composes the fixed-cardinality marginal theorem with
`bisFinMarginalSqNorm_eq_uniformOfForallEq`.
-/
theorem bisFixedCardUniformMarginalSqNorm_eq_uniform
    {T k : ℕ} (hT : 0 < T) (hk : k ≤ T) :
    Finset.sum Finset.univ
        (fun i : Fin T =>
          bisFixedCardUniformMarginal (Finset.univ : Finset (Fin T)) k i ^ 2)
      = (k : ℝ) ^ 2 / (T : ℝ) := by
  exact bisFinMarginalSqNorm_eq_uniformOfForallEq
    (mu := fun i : Fin T =>
      bisFixedCardUniformMarginal (Finset.univ : Finset (Fin T)) k i)
    (total := (k : ℝ)) hT
    (by
      intro i
      simpa [Finset.card_univ] using
        bisFixedCardUniformMarginal_eq_div_card
          (base := (Finset.univ : Finset (Fin T))) (a := i)
          (ha := by simp) (k := k)
          (by simpa [Finset.card_univ] using hk))

/--
Fixed-cardinality subset support has uniform pair-coordinate counts.

For distinct `a,b ∈ base`, exactly `choose (|base|-2) k` subsets of size
`k+2` contain both `a` and `b`.
-/
theorem bisFixedCardSupport_pairIndicator_sum_succ_succ
    {α : Type} [DecidableEq α]
    (base : Finset α) (a b : α) (ha : a ∈ base) (hb : b ∈ base)
    (hab : a ≠ b) (k : ℕ) :
    Finset.sum (base.powersetCard (k + 2))
        (fun u : Finset α => if a ∈ u ∧ b ∈ u then (1 : ℝ) else 0)
      = (Nat.choose (base.card - 2) k : ℝ) := by
  let rest := (base.erase a).erase b
  have hb_erase_a : b ∈ base.erase a := by
    exact Finset.mem_erase.mpr ⟨fun h => hab h.symm, hb⟩
  have hbr : insert b rest = base.erase a := by
    unfold rest
    exact Finset.insert_erase hb_erase_a
  have hbase : base = insert a (insert b rest) := by
    rw [hbr]
    exact (Finset.insert_erase ha).symm
  have ha_not : a ∉ insert b rest := by
    unfold rest
    simp [hab]
  rw [hbase]
  rw [Finset.powersetCard_succ_insert ha_not (k + 1)]
  have hdisj1 : Disjoint ((insert b rest).powersetCard (k + 2))
      (((insert b rest).powersetCard (k + 1)).image (insert a)) := by
    rw [Finset.disjoint_left]
    intro u hu himg
    have hau : a ∉ u := by
      intro hau
      have hsub : u ⊆ insert b rest := (Finset.mem_powersetCard.mp hu).1
      exact ha_not (hsub hau)
    rcases Finset.mem_image.mp himg with ⟨v, _hv, huv⟩
    rw [← huv] at hau
    exact hau (Finset.mem_insert_self a v)
  rw [Finset.sum_union hdisj1]
  have hleft1 : Finset.sum ((insert b rest).powersetCard (k + 2))
        (fun u : Finset α => if a ∈ u ∧ b ∈ u then (1 : ℝ) else 0) = 0 := by
    refine Finset.sum_eq_zero ?_
    intro u hu
    have hau : a ∉ u := by
      intro hau
      have hsub : u ⊆ insert b rest := (Finset.mem_powersetCard.mp hu).1
      exact ha_not (hsub hau)
    simp [hau]
  rw [hleft1, zero_add]
  have hinj_a : ∀ x ∈ (insert b rest).powersetCard (k + 1),
      ∀ y ∈ (insert b rest).powersetCard (k + 1), insert a x = insert a y → x = y := by
    intro x hx y hy hxy
    apply Finset.ext
    intro z
    have hax : a ∉ x := by
      intro hzx
      have hsub : x ⊆ insert b rest := (Finset.mem_powersetCard.mp hx).1
      exact ha_not (hsub hzx)
    have hay : a ∉ y := by
      intro hzy
      have hsub : y ⊆ insert b rest := (Finset.mem_powersetCard.mp hy).1
      exact ha_not (hsub hzy)
    by_cases hza : z = a
    · subst z
      simp [hax, hay]
    · have hz := congrArg (fun u : Finset α => z ∈ u) hxy
      simpa [hza] using hz
  rw [Finset.sum_image]
  · simp only [Finset.mem_insert, true_or, true_and]
    have hmem := bisFixedCardSupport_memberIndicator_sum_succ (insert b rest)
      b (by simp) k
    have hcard : (insert b rest).card - 1 = (insert a (insert b rest)).card - 2 := by
      simp [Finset.card_insert_of_notMem, ha_not]
    have hba : b ≠ a := fun h => hab h.symm
    simpa [hba, hcard] using hmem
  · exact hinj_a

/--
Uniform fixed-cardinality pair marginal in exact binomial-ratio form.
-/
theorem bisFixedCardUniformMass_pairMarginal_succ_succ
    {α : Type} [DecidableEq α]
    (base : Finset α) (a b : α) (ha : a ∈ base) (hb : b ∈ base)
    (hab : a ≠ b) (k : ℕ) :
    Finset.sum (base.powersetCard (k + 2))
        (fun u : Finset α =>
          bisFixedCardUniformMass base (k + 2) u
            * if a ∈ u ∧ b ∈ u then (1 : ℝ) else 0)
      = (Nat.choose (base.card - 2) k : ℝ)
          / (Nat.choose base.card (k + 2) : ℝ) := by
  unfold bisFixedCardUniformMass
  calc
    Finset.sum (base.powersetCard (k + 2))
        (fun u : Finset α =>
          (if u ∈ base.powersetCard (k + 2) then
              ((Nat.choose base.card (k + 2) : ℝ)⁻¹) else 0)
            * if a ∈ u ∧ b ∈ u then (1 : ℝ) else 0)
        = Finset.sum (base.powersetCard (k + 2))
            (fun u : Finset α =>
              ((Nat.choose base.card (k + 2) : ℝ)⁻¹)
                * if a ∈ u ∧ b ∈ u then (1 : ℝ) else 0) := by
          refine Finset.sum_congr rfl ?_
          intro u hu
          simp [hu]
    _ = ((Nat.choose base.card (k + 2) : ℝ)⁻¹)
            * Finset.sum (base.powersetCard (k + 2))
                (fun u : Finset α => if a ∈ u ∧ b ∈ u then (1 : ℝ) else 0) := by
          rw [← Finset.mul_sum]
    _ = ((Nat.choose base.card (k + 2) : ℝ)⁻¹)
            * (Nat.choose (base.card - 2) k : ℝ) := by
          rw [bisFixedCardSupport_pairIndicator_sum_succ_succ base a b ha hb hab k]
    _ = (Nat.choose (base.card - 2) k : ℝ)
          / (Nat.choose base.card (k + 2) : ℝ) := by
          rw [div_eq_mul_inv]
          ring

/--
Paper-facing uniform pair marginal form.

When `k+2 <= |base|`, the exact binomial ratio from
`bisFixedCardUniformMass_pairMarginal_succ_succ` simplifies to
`(k+2)(k+1) / (|base|(|base|-1))`.
-/
theorem bisFixedCardUniformMass_pairMarginal_succ_succ_eq_div_card
    {α : Type} [DecidableEq α]
    (base : Finset α) (a b : α) (ha : a ∈ base) (hb : b ∈ base)
    (hab : a ≠ b) (k : ℕ) (hk : k + 2 ≤ base.card) :
    Finset.sum (base.powersetCard (k + 2))
        (fun u : Finset α =>
          bisFixedCardUniformMass base (k + 2) u
            * if a ∈ u ∧ b ∈ u then (1 : ℝ) else 0)
      = ((k + 2 : ℝ) * (k + 1 : ℝ))
          / ((base.card : ℝ) * ((base.card - 1 : ℕ) : ℝ)) := by
  rw [bisFixedCardUniformMass_pairMarginal_succ_succ base a b ha hb hab k]
  have hcard2 : 2 ≤ base.card := le_trans (by omega) hk
  have hcard_pos : 0 < base.card := lt_of_lt_of_le (by norm_num) hcard2
  have hcard1_pos_nat : 0 < base.card - 1 := Nat.sub_pos_of_lt hcard2
  have hcard_posR : (0 : ℝ) < (base.card : ℝ) := by
    exact_mod_cast hcard_pos
  have hcard1_posR : (0 : ℝ) < ((base.card - 1 : ℕ) : ℝ) := by
    exact_mod_cast hcard1_pos_nat
  have hchoose_pos : (0 : ℝ) < (Nat.choose base.card (k + 2) : ℝ) := by
    exact_mod_cast Nat.choose_pos hk
  have hstep1_nat := Nat.add_one_mul_choose_eq (base.card - 1) (k + 1)
  have hcard_minus1 : base.card - 1 + 1 = base.card :=
    Nat.sub_one_add_one (ne_of_gt hcard_pos)
  rw [hcard_minus1] at hstep1_nat
  have hstep1 : (base.card : ℝ) * (Nat.choose (base.card - 1) (k + 1) : ℝ)
      = (Nat.choose base.card (k + 2) : ℝ) * (k + 2 : ℝ) := by
    exact_mod_cast hstep1_nat
  have hstep2_nat := Nat.add_one_mul_choose_eq (base.card - 2) k
  have hcard_minus2 : base.card - 2 + 1 = base.card - 1 := by
    omega
  rw [hcard_minus2] at hstep2_nat
  have hstep2 :
      ((base.card - 1 : ℕ) : ℝ) * (Nat.choose (base.card - 2) k : ℝ)
        = (Nat.choose (base.card - 1) (k + 1) : ℝ) * (k + 1 : ℝ) := by
    exact_mod_cast hstep2_nat
  field_simp [hchoose_pos.ne', hcard_posR.ne', hcard1_posR.ne']
  nlinarith

/--
Uniform fixed-cardinality pair marginal for arbitrary `k`.

The `k=0` and `k=1` boundaries are zero for distinct coordinates; the
`k>=2` case is the shifted pair-count theorem above.
-/
theorem bisFixedCardUniformPairMarginal_eq_div_card
    {α : Type} [DecidableEq α]
    (base : Finset α) (a b : α) (ha : a ∈ base) (hb : b ∈ base)
    (hab : a ≠ b) (k : ℕ) (hk : k ≤ base.card) :
    bisFixedCardUniformPairMarginal base k a b
      = ((k : ℝ) * ((k - 1 : ℕ) : ℝ))
          / ((base.card : ℝ) * ((base.card - 1 : ℕ) : ℝ)) := by
  cases k with
  | zero =>
      unfold bisFixedCardUniformPairMarginal bisFixedCardUniformMass
      simp
  | succ k =>
      cases k with
      | zero =>
          have hleft : bisFixedCardUniformPairMarginal base 1 a b = 0 := by
            unfold bisFixedCardUniformPairMarginal
            rw [Finset.powersetCard_one]
            apply Finset.sum_eq_zero
            intro u hu
            simp only [Finset.mem_map, Function.Embedding.coeFn_mk] at hu
            rcases hu with ⟨x, _hx, rfl⟩
            by_cases hcond : a ∈ ({x} : Finset α) ∧ b ∈ ({x} : Finset α)
            · rcases hcond with ⟨hax, hbx⟩
              simp at hax hbx
              exact False.elim (hab (hax.trans hbx.symm))
            · have hcondEq : ¬ (a = x ∧ b = x) := by
                rintro ⟨hax, hbx⟩
                apply hcond
                simp [hax, hbx]
              simp [hcondEq]
          rw [hleft]
          simp
      | succ k =>
          unfold bisFixedCardUniformPairMarginal
          have hpair := bisFixedCardUniformMass_pairMarginal_succ_succ_eq_div_card
            base a b ha hb hab k hk
          simpa [Nat.cast_add, Nat.cast_one, Nat.cast_ofNat, add_assoc] using hpair

/-- Diagonal pair marginal equals the one-coordinate marginal. -/
theorem bisFixedCardUniformPairMarginal_diag
    {α : Type} [DecidableEq α]
    (base : Finset α) (k : ℕ) (a : α) :
    bisFixedCardUniformPairMarginal base k a a
      = bisFixedCardUniformMarginal base k a := by
  unfold bisFixedCardUniformPairMarginal bisFixedCardUniformMarginal
  refine Finset.sum_congr rfl ?_
  intro u _hu
  by_cases h : a ∈ u
  · simp [h]
  · simp [h]

/-- Diagonal covariance entry in moment form. -/
theorem bisFixedCardUniformCovarianceEntry_diag
    {α : Type} [DecidableEq α]
    (base : Finset α) (k : ℕ) (a : α) :
    bisFixedCardUniformCovarianceEntry base k a a
      = bisFixedCardUniformMarginal base k a
          - bisFixedCardUniformMarginal base k a ^ 2 := by
  unfold bisFixedCardUniformCovarianceEntry
  rw [bisFixedCardUniformPairMarginal_diag]
  ring

/--
Off-diagonal covariance entry in finite moment form.

This is the theorem-facing covariance ingredient for the high-noise spectrum
route.  It deliberately leaves the final scalar expression as
`pair marginal - marginal^2`, using the already-proved uniform marginal and
pair-marginal formulas.
-/
theorem bisFixedCardUniformCovarianceEntry_offdiag_fin
    {T k : ℕ} (_hT : 2 ≤ T) (hk : k ≤ T) {i j : Fin T} (hij : i ≠ j) :
    bisFixedCardUniformCovarianceEntry (Finset.univ : Finset (Fin T)) k i j
      = ((k : ℝ) * ((k - 1 : ℕ) : ℝ))
          / ((T : ℝ) * ((T - 1 : ℕ) : ℝ))
        - ((k : ℝ) / (T : ℝ)) * ((k : ℝ) / (T : ℝ)) := by
  unfold bisFixedCardUniformCovarianceEntry
  rw [bisFixedCardUniformPairMarginal_eq_div_card
    (base := (Finset.univ : Finset (Fin T))) (a := i) (b := j)
    (ha := by simp) (hb := by simp) (hab := hij) (k := k)
    (by simpa [Finset.card_univ] using hk)]
  rw [bisFixedCardUniformMarginal_eq_div_card
    (base := (Finset.univ : Finset (Fin T))) (a := i) (ha := by simp) (k := k)
    (by simpa [Finset.card_univ] using hk)]
  rw [bisFixedCardUniformMarginal_eq_div_card
    (base := (Finset.univ : Finset (Fin T))) (a := j) (ha := by simp) (k := k)
    (by simpa [Finset.card_univ] using hk)]
  simp [Finset.card_univ]

/-- Diagonal covariance entry for uniform `k`-out-of-`T` BIS marginals. -/
theorem bisFixedCardUniformCovarianceEntry_diag_fin
    {T k : ℕ} (_hT : 0 < T) (hk : k ≤ T) (i : Fin T) :
    bisFixedCardUniformCovarianceEntry (Finset.univ : Finset (Fin T)) k i i
      = (k : ℝ) / (T : ℝ) - ((k : ℝ) / (T : ℝ)) ^ 2 := by
  rw [bisFixedCardUniformCovarianceEntry_diag]
  rw [bisFixedCardUniformMarginal_eq_div_card
    (base := (Finset.univ : Finset (Fin T))) (a := i) (ha := by simp) (k := k)
    (by simpa [Finset.card_univ] using hk)]
  simp [Finset.card_univ]

/-- Diagonal covariance entry in spectrum-ready scalar form. -/
theorem bisFixedCardUniformCovarianceEntry_diag_fin_spectrum
    {T k : ℕ} (hT : 0 < T) (hk : k ≤ T) (i : Fin T) :
    bisFixedCardUniformCovarianceEntry (Finset.univ : Finset (Fin T)) k i i
      = ((k : ℝ) * ((T - k : ℕ) : ℝ)) / ((T : ℝ) ^ 2) := by
  rw [bisFixedCardUniformCovarianceEntry_diag_fin hT hk i]
  have hTpos : (0 : ℝ) < (T : ℝ) := by exact_mod_cast hT
  rw [Nat.cast_sub hk]
  field_simp [hTpos.ne']

/-- Off-diagonal covariance entry in spectrum-ready scalar form. -/
theorem bisFixedCardUniformCovarianceEntry_offdiag_fin_spectrum
    {T k : ℕ} (hT : 2 ≤ T) (hk : k ≤ T) {i j : Fin T} (hij : i ≠ j) :
    bisFixedCardUniformCovarianceEntry (Finset.univ : Finset (Fin T)) k i j
      = - (((k : ℝ) * ((T - k : ℕ) : ℝ))
          / (((T : ℝ) ^ 2) * ((T - 1 : ℕ) : ℝ))) := by
  rw [bisFixedCardUniformCovarianceEntry_offdiag_fin hT hk hij]
  cases k with
  | zero =>
      simp
  | succ k =>
      have hksucc : k.succ ≤ T := hk
      have hkpos : 0 < k.succ := Nat.succ_pos k
      have hTposNat : 0 < T := lt_of_lt_of_le (by norm_num) hT
      have hTpos : (0 : ℝ) < (T : ℝ) := by exact_mod_cast hTposNat
      have hTone : 1 ≤ T := le_trans (by norm_num) hT
      have hTminus1_ne : (T : ℝ) - 1 ≠ 0 := by
        have : (1 : ℝ) < (T : ℝ) := by exact_mod_cast hT
        linarith
      rw [Nat.cast_sub hksucc]
      rw [Nat.cast_sub (Nat.succ_le_iff.mp hkpos)]
      rw [Nat.cast_sub hTone]
      field_simp [hTpos.ne', hTminus1_ne]
      ring

/--
Quadratic form for a constant diagonal/off-diagonal matrix.

This is the matrix-algebra bridge used by the high-noise covariance route:
the off-diagonal constant contributes to the square of the coordinate sum, and
the diagonal excess contributes to the squared norm.
-/
theorem bisConstantDiagOffdiagQuadraticForm
    {T : ℕ} (d o : ℝ) (x : Fin T → ℝ) :
    (Finset.sum Finset.univ fun i : Fin T =>
      Finset.sum Finset.univ fun j : Fin T =>
        x i * x j * (if i = j then d else o))
      = o * (Finset.sum Finset.univ x) ^ 2
        + (d - o) * Finset.sum Finset.univ (fun i : Fin T => x i ^ 2) := by
  classical
  have hif : ∀ i j : Fin T, (if i = j then d else o) =
      o + (if i = j then d - o else 0) := by
    intro i j
    by_cases h : i = j <;> simp [h]
  have hfirst : (Finset.sum Finset.univ fun i : Fin T =>
      Finset.sum Finset.univ fun j : Fin T => x i * x j * o)
      = o * (Finset.sum Finset.univ x) ^ 2 := by
    calc
      (Finset.sum Finset.univ fun i : Fin T =>
          Finset.sum Finset.univ fun j : Fin T => x i * x j * o)
          = (Finset.sum Finset.univ fun i : Fin T =>
              Finset.sum Finset.univ fun j : Fin T => x i * x j) * o := by
              simp_rw [← Finset.sum_mul]
      _ = ((Finset.sum Finset.univ x) * (Finset.sum Finset.univ x)) * o := by
              rw [Fintype.sum_mul_sum]
      _ = o * (Finset.sum Finset.univ x) ^ 2 := by
              ring
  have hsecond : (Finset.sum Finset.univ fun i : Fin T =>
      Finset.sum Finset.univ fun j : Fin T => x i * x j * (if i = j then d - o else 0))
      = (d - o) * Finset.sum Finset.univ (fun i : Fin T => x i ^ 2) := by
    simp_rw [mul_ite, mul_zero]
    have hinner : ∀ i : Fin T,
        (Finset.sum Finset.univ fun j : Fin T =>
            if i = j then x i * x j * (d - o) else 0)
          = x i ^ 2 * (d - o) := by
      intro i
      rw [Finset.sum_eq_single i]
      · rw [if_pos rfl]
        ring
      · intro j _hj hji
        rw [if_neg (fun h : i = j => hji h.symm)]
      · intro hi
        exact False.elim (hi (by simp))
    simp_rw [hinner]
    rw [← Finset.sum_mul]
    ring
  calc
    (Finset.sum Finset.univ fun i : Fin T =>
      Finset.sum Finset.univ fun j : Fin T =>
        x i * x j * (if i = j then d else o))
        = (Finset.sum Finset.univ fun i : Fin T =>
            Finset.sum Finset.univ fun j : Fin T => x i * x j * o)
          + (Finset.sum Finset.univ fun i : Fin T =>
            Finset.sum Finset.univ fun j : Fin T =>
              x i * x j * (if i = j then d - o else 0)) := by
          simp_rw [hif, mul_add, Finset.sum_add_distrib]
    _ = o * (Finset.sum Finset.univ x) ^ 2
        + (d - o) * Finset.sum Finset.univ (fun i : Fin T => x i ^ 2) := by
          rw [hfirst, hsecond]

/-- Projection of a finite vector onto the constant all-ones direction. -/
noncomputable def bisAllOnesComponent {T : ℕ} (w : Fin T → ℝ) : Fin T → ℝ :=
  fun _ => (Finset.sum Finset.univ w) / (T : ℝ)

/-- Residual after subtracting the all-ones projection. -/
noncomputable def bisZeroSumComponent {T : ℕ} (w : Fin T → ℝ) : Fin T → ℝ :=
  fun i => w i - (Finset.sum Finset.univ w) / (T : ℝ)

/-- The all-ones component plus the residual recovers the original vector. -/
theorem bisAllOnesComponent_add_zeroSumComponent {T : ℕ} (w : Fin T → ℝ) (i : Fin T) :
    bisAllOnesComponent w i + bisZeroSumComponent w i = w i := by
  simp [bisAllOnesComponent, bisZeroSumComponent]

/-- The residual after subtracting the all-ones projection has coordinate sum zero. -/
theorem bisZeroSumComponent_sum_eq_zero {T : ℕ} (hT : 0 < T) (w : Fin T → ℝ) :
    Finset.sum Finset.univ (bisZeroSumComponent w) = 0 := by
  let s : ℝ := Finset.sum Finset.univ w
  have hTne : (T : ℝ) ≠ 0 := by exact_mod_cast (ne_of_gt hT)
  calc
    Finset.sum Finset.univ (bisZeroSumComponent w)
        = Finset.sum Finset.univ (fun i : Fin T => w i - s / (T : ℝ)) := by
            change (∑ i : Fin T, (w i - s / (T : ℝ))) = _
            rfl
    _ = s - (T : ℝ) * (s / (T : ℝ)) := by
            change (∑ i : Fin T, (w i - s / (T : ℝ))) = _
            rw [Finset.sum_sub_distrib]
            have hconst :
                (∑ _i : Fin T, s / (T : ℝ)) = (T : ℝ) * (s / (T : ℝ)) := by
              simp [Finset.sum_const, Finset.card_univ]
            rw [hconst]
    _ = 0 := by
            field_simp [hTne]
            ring

/--
Squared norm of the zero-sum component.

This is the finite projection identity behind the paper's
`w = z 1 / sqrt(T) + w_perp` decomposition, stated without square roots:

```text
||w_perp||² = ||w||² - (Σ_i w_i)² / T.
```
-/
theorem bisZeroSumComponent_sqNorm_eq_centeredNorm
    {T : ℕ} (hT : 0 < T) (w : Fin T → ℝ) :
    Finset.sum Finset.univ (fun i : Fin T => (bisZeroSumComponent w i) ^ 2)
      = Finset.sum Finset.univ (fun i : Fin T => w i ^ 2)
        - (Finset.sum Finset.univ w) ^ 2 / (T : ℝ) := by
  let s : ℝ := Finset.sum Finset.univ w
  have hs : Finset.sum Finset.univ w = s := rfl
  have hTne : (T : ℝ) ≠ 0 := by exact_mod_cast (ne_of_gt hT)
  calc
    Finset.sum Finset.univ (fun i : Fin T => (bisZeroSumComponent w i) ^ 2)
        = Finset.sum Finset.univ (fun i : Fin T => (w i - s / (T : ℝ)) ^ 2) := by
            simp [bisZeroSumComponent, s]
    _ = Finset.sum Finset.univ
          (fun i : Fin T => w i ^ 2 - 2 * (s / (T : ℝ)) * w i + (s / (T : ℝ)) ^ 2) := by
            refine Finset.sum_congr rfl ?_
            intro i _
            ring
    _ = Finset.sum Finset.univ (fun i : Fin T => w i ^ 2)
          - 2 * (s / (T : ℝ)) * Finset.sum Finset.univ w
          + (T : ℝ) * (s / (T : ℝ)) ^ 2 := by
            rw [Finset.sum_add_distrib, Finset.sum_sub_distrib]
            simp [Finset.mul_sum, Finset.card_univ]
    _ = Finset.sum Finset.univ (fun i : Fin T => w i ^ 2) - s ^ 2 / (T : ℝ) := by
            rw [hs]
            field_simp [hTne]
            ring
    _ = Finset.sum Finset.univ (fun i : Fin T => w i ^ 2)
          - (Finset.sum Finset.univ w) ^ 2 / (T : ℝ) := by
            rw [hs]

/--
Quadratic form of the uniform fixed-cardinality covariance entries.

This theorem is the finite matrix-level bridge from entrywise covariance
formulas to the high-noise spectrum route.  The coefficient of the squared sum
is the off-diagonal covariance, while the coefficient of the squared norm is
the diagonal excess over the off-diagonal covariance.
-/
theorem bisFixedCardUniformCovarianceQuadraticForm_fin
    {T k : ℕ} (hT : 2 ≤ T) (hk : k ≤ T) (x : Fin T → ℝ) :
    let d := ((k : ℝ) * ((T - k : ℕ) : ℝ)) / ((T : ℝ) ^ 2)
    let o := - (((k : ℝ) * ((T - k : ℕ) : ℝ))
          / (((T : ℝ) ^ 2) * ((T - 1 : ℕ) : ℝ)))
    (Finset.sum Finset.univ fun i : Fin T =>
      Finset.sum Finset.univ fun j : Fin T =>
        x i * x j *
          bisFixedCardUniformCovarianceEntry (Finset.univ : Finset (Fin T)) k i j)
      = o * (Finset.sum Finset.univ x) ^ 2
        + (d - o) * Finset.sum Finset.univ (fun i : Fin T => x i ^ 2) := by
  classical
  dsimp only
  let d := ((k : ℝ) * ((T - k : ℕ) : ℝ)) / ((T : ℝ) ^ 2)
  let o := - (((k : ℝ) * ((T - k : ℕ) : ℝ))
          / (((T : ℝ) ^ 2) * ((T - 1 : ℕ) : ℝ)))
  have hentry : ∀ i j : Fin T,
      bisFixedCardUniformCovarianceEntry (Finset.univ : Finset (Fin T)) k i j
        = if i = j then d else o := by
    intro i j
    by_cases h : i = j
    · subst j
      simp [d, bisFixedCardUniformCovarianceEntry_diag_fin_spectrum
        (lt_of_lt_of_le (by norm_num) hT) hk i]
    · simp [h, o, bisFixedCardUniformCovarianceEntry_offdiag_fin_spectrum hT hk h]
  simp_rw [hentry]
  exact bisConstantDiagOffdiagQuadraticForm d o x

/-- Difference between diagonal and off-diagonal constants. -/
theorem bisFixedCardUniformCovarianceDiagSubOffdiag_fin_spectrum
    {T k : ℕ} (hT : 2 ≤ T) :
    ((k : ℝ) * ((T - k : ℕ) : ℝ)) / ((T : ℝ) ^ 2)
      - (- (((k : ℝ) * ((T - k : ℕ) : ℝ))
          / (((T : ℝ) ^ 2) * ((T - 1 : ℕ) : ℝ))))
      = ((k : ℝ) * ((T - k : ℕ) : ℝ))
          / ((T : ℝ) * ((T - 1 : ℕ) : ℝ)) := by
  have hTposNat : 0 < T := lt_of_lt_of_le (by norm_num) hT
  have hTpos : (0 : ℝ) < (T : ℝ) := by exact_mod_cast hTposNat
  have hTone : 1 ≤ T := le_trans (by norm_num) hT
  have hTminus1_ne : (T : ℝ) - 1 ≠ 0 := by
    have : (1 : ℝ) < (T : ℝ) := by exact_mod_cast hT
    linarith
  rw [Nat.cast_sub hTone]
  field_simp [hTpos.ne', hTminus1_ne]
  ring

/--
Zero-sum quadratic-form spectrum for uniform fixed-cardinality covariance.

On the subspace orthogonal to the all-ones vector, the covariance quadratic
form is exactly the finite-population factor
`k(T-k)/(T(T-1))` times the squared norm.
-/
theorem bisFixedCardUniformCovarianceQuadraticForm_zeroSum_fin
    {T k : ℕ} (hT : 2 ≤ T) (hk : k ≤ T) (x : Fin T → ℝ)
    (hsum : Finset.sum Finset.univ x = 0) :
    (Finset.sum Finset.univ fun i : Fin T =>
      Finset.sum Finset.univ fun j : Fin T =>
        x i * x j *
          bisFixedCardUniformCovarianceEntry (Finset.univ : Finset (Fin T)) k i j)
      = (((k : ℝ) * ((T - k : ℕ) : ℝ))
          / ((T : ℝ) * ((T - 1 : ℕ) : ℝ)))
          * Finset.sum Finset.univ (fun i : Fin T => x i ^ 2) := by
  have hcoef := bisFixedCardUniformCovarianceDiagSubOffdiag_fin_spectrum
    (T := T) (k := k) hT
  rw [bisFixedCardUniformCovarianceQuadraticForm_fin hT hk x]
  rw [hsum]
  simp [hcoef]

/--
Rayleigh-quotient form of BIS centered covariance isotropy.

For any nonzero zero-sum direction, the uniform fixed-cardinality covariance
quotient is exactly the finite-population factor.  This is the BIS attainment
half of the covariance-minimax theorem, stated without a supremum.
-/
theorem bisFixedCardUniformCovarianceRayleigh_zeroSum_fin
    {T k : ℕ} (hT : 2 ≤ T) (hk : k ≤ T) (x : Fin T → ℝ)
    (hsum : Finset.sum Finset.univ x = 0)
    (hnorm : Finset.sum Finset.univ (fun i : Fin T => x i ^ 2) ≠ 0) :
    ((Finset.sum Finset.univ fun i : Fin T =>
      Finset.sum Finset.univ fun j : Fin T =>
        x i * x j *
          bisFixedCardUniformCovarianceEntry (Finset.univ : Finset (Fin T)) k i j)
      / Finset.sum Finset.univ (fun i : Fin T => x i ^ 2))
      = (((k : ℝ) * ((T - k : ℕ) : ℝ))
          / ((T : ℝ) * ((T - 1 : ℕ) : ℝ))) := by
  rw [bisFixedCardUniformCovarianceQuadraticForm_zeroSum_fin hT hk x hsum]
  field_simp [hnorm]

/-- Weighted coordinate mean for a finite participation-vector law. -/
noncomputable def bisWeightedMeanCoord {α : Type} [Fintype α] {T : ℕ}
    (mass : α → ℝ) (x : α → Fin T → ℝ) (i : Fin T) : ℝ :=
  Finset.sum Finset.univ fun a : α => mass a * x a i

/-- Weighted second-moment entry for a finite participation-vector law. -/
noncomputable def bisWeightedSecondMomentEntry {α : Type} [Fintype α] {T : ℕ}
    (mass : α → ℝ) (x : α → Fin T → ℝ) (i j : Fin T) : ℝ :=
  Finset.sum Finset.univ fun a : α => mass a * x a i * x a j

/-- Weighted covariance entry for a finite participation-vector law. -/
noncomputable def bisWeightedCovarianceEntry {α : Type} [Fintype α] {T : ℕ}
    (mass : α → ℝ) (x : α → Fin T → ℝ) (i j : Fin T) : ℝ :=
  bisWeightedSecondMomentEntry mass x i j
    - bisWeightedMeanCoord mass x i * bisWeightedMeanCoord mass x j

/-- Weighted covariance entries are symmetric. -/
theorem bisWeightedCovarianceEntry_symm
    {α : Type} [Fintype α] {T : ℕ}
    (mass : α → ℝ) (x : α → Fin T → ℝ) (i j : Fin T) :
    bisWeightedCovarianceEntry mass x i j = bisWeightedCovarianceEntry mass x j i := by
  unfold bisWeightedCovarianceEntry bisWeightedSecondMomentEntry
  congr 1
  · refine Finset.sum_congr rfl ?_
    intro a _
    ring
  · ring

/--
Finite expansion of the second moment of an inner product through the
coordinate second-moment matrix.

This is the algebraic part of the high-noise expansion before subtracting the
mean-square term.
-/
theorem bisWeightedInnerSecondMoment_eq_secondMomentQuadraticForm
    {α : Type} [Fintype α] {T : ℕ}
    (mass : α → ℝ) (x : α → Fin T → ℝ) (w : Fin T → ℝ) :
    (Finset.sum Finset.univ fun a : α =>
        mass a * (Finset.sum Finset.univ fun i : Fin T => x a i * w i) ^ 2)
      = Finset.sum Finset.univ fun i : Fin T =>
          Finset.sum Finset.univ fun j : Fin T =>
            w i * w j * bisWeightedSecondMomentEntry mass x i j := by
  unfold bisWeightedSecondMomentEntry
  calc
    (Finset.sum Finset.univ fun a : α =>
        mass a * (Finset.sum Finset.univ fun i : Fin T => x a i * w i) ^ 2)
        = Finset.sum Finset.univ fun a : α =>
            mass a * ((Finset.sum Finset.univ fun i : Fin T => x a i * w i)
              * (Finset.sum Finset.univ fun i : Fin T => x a i * w i)) := by
            simp [sq]
    _ = Finset.sum Finset.univ fun a : α =>
          mass a * (Finset.sum Finset.univ fun i : Fin T =>
            Finset.sum Finset.univ fun j : Fin T => (x a i * w i) * (x a j * w j)) := by
            simp_rw [Fintype.sum_mul_sum]
    _ = Finset.sum Finset.univ fun a : α =>
          Finset.sum Finset.univ fun i : Fin T =>
            Finset.sum Finset.univ fun j : Fin T =>
              mass a * ((x a i * w i) * (x a j * w j)) := by
            simp_rw [Finset.mul_sum]
    _ = Finset.sum Finset.univ fun i : Fin T =>
          Finset.sum Finset.univ fun a : α =>
            Finset.sum Finset.univ fun j : Fin T =>
              mass a * ((x a i * w i) * (x a j * w j)) := by
            rw [Finset.sum_comm]
    _ = Finset.sum Finset.univ fun i : Fin T =>
          Finset.sum Finset.univ fun j : Fin T =>
            Finset.sum Finset.univ fun a : α =>
              mass a * ((x a i * w i) * (x a j * w j)) := by
            refine Finset.sum_congr rfl ?_
            intro i _
            rw [Finset.sum_comm]
    _ = Finset.sum Finset.univ fun i : Fin T =>
          Finset.sum Finset.univ fun j : Fin T =>
            w i * w j * (Finset.sum Finset.univ fun a : α => mass a * x a i * x a j) := by
            refine Finset.sum_congr rfl ?_
            intro i _
            refine Finset.sum_congr rfl ?_
            intro j _
            calc
              (Finset.sum Finset.univ fun a : α =>
                  mass a * ((x a i * w i) * (x a j * w j)))
                  = Finset.sum Finset.univ fun a : α =>
                      (w i * w j) * (mass a * x a i * x a j) := by
                    refine Finset.sum_congr rfl ?_
                    intro a _
                    ring
              _ = w i * w j *
                    (Finset.sum Finset.univ fun a : α => mass a * x a i * x a j) := by
                    rw [Finset.mul_sum]

/-- Square of the mean inner product as a mean-vector quadratic form. -/
theorem bisWeightedMeanInnerSq_eq_meanQuadraticForm
    {α : Type} [Fintype α] {T : ℕ}
    (mass : α → ℝ) (x : α → Fin T → ℝ) (w : Fin T → ℝ) :
    (Finset.sum Finset.univ fun i : Fin T => bisWeightedMeanCoord mass x i * w i) ^ 2
      = Finset.sum Finset.univ fun i : Fin T =>
          Finset.sum Finset.univ fun j : Fin T =>
            w i * w j * (bisWeightedMeanCoord mass x i * bisWeightedMeanCoord mass x j) := by
  calc
    (Finset.sum Finset.univ fun i : Fin T => bisWeightedMeanCoord mass x i * w i) ^ 2
      = (Finset.sum Finset.univ fun i : Fin T => bisWeightedMeanCoord mass x i * w i)
          * (Finset.sum Finset.univ fun i : Fin T => bisWeightedMeanCoord mass x i * w i) := by
          simp [sq]
    _ = Finset.sum Finset.univ fun i : Fin T =>
          Finset.sum Finset.univ fun j : Fin T =>
            (bisWeightedMeanCoord mass x i * w i) * (bisWeightedMeanCoord mass x j * w j) := by
          rw [Fintype.sum_mul_sum]
    _ = Finset.sum Finset.univ fun i : Fin T =>
          Finset.sum Finset.univ fun j : Fin T =>
            w i * w j * (bisWeightedMeanCoord mass x i * bisWeightedMeanCoord mass x j) := by
          refine Finset.sum_congr rfl ?_
          intro i _
          refine Finset.sum_congr rfl ?_
          intro j _
          ring

/--
High-noise finite covariance algebra.

For any finite weighted participation-vector law, the centered second moment of
the linear statistic `<X,w>` equals the covariance quadratic form.  This is the
finite algebraic core behind the paper's
`E[<X,w>^2] - <E X,w>^2 = w^T Sigma w` term.
-/
theorem bisWeightedInnerCenteredSecondMoment_eq_covarianceQuadraticForm
    {α : Type} [Fintype α] {T : ℕ}
    (mass : α → ℝ) (x : α → Fin T → ℝ) (w : Fin T → ℝ) :
    (Finset.sum Finset.univ fun a : α =>
        mass a * (Finset.sum Finset.univ fun i : Fin T => x a i * w i) ^ 2)
      - (Finset.sum Finset.univ fun i : Fin T => bisWeightedMeanCoord mass x i * w i) ^ 2
      = Finset.sum Finset.univ fun i : Fin T =>
          Finset.sum Finset.univ fun j : Fin T =>
            w i * w j * bisWeightedCovarianceEntry mass x i j := by
  rw [bisWeightedInnerSecondMoment_eq_secondMomentQuadraticForm,
    bisWeightedMeanInnerSq_eq_meanQuadraticForm]
  unfold bisWeightedCovarianceEntry
  simp_rw [mul_sub]
  rw [← Finset.sum_sub_distrib]
  refine Finset.sum_congr rfl ?_
  intro i _
  rw [← Finset.sum_sub_distrib]

/--
Scalar weighted variance identity for normalized finite masses.

This is the probability-facing algebra behind covariance PSD: under masses
summing to one, the second moment minus the squared mean is the weighted mean
of squared deviations.
-/
theorem bisWeightedScalarSecondMoment_sub_meanSq_eq_sqDeviation
    {α : Type} [Fintype α]
    (mass : α → ℝ) (y : α → ℝ)
    (hmass_total : Finset.sum Finset.univ mass = 1) :
    (Finset.sum Finset.univ fun a : α => mass a * y a ^ 2)
      - (Finset.sum Finset.univ fun a : α => mass a * y a) ^ 2
      = Finset.sum Finset.univ fun a : α =>
          mass a * (y a - Finset.sum Finset.univ (fun b : α => mass b * y b)) ^ 2 := by
  let μ : ℝ := Finset.sum Finset.univ fun a : α => mass a * y a
  calc
    (Finset.sum Finset.univ fun a : α => mass a * y a ^ 2)
        - (Finset.sum Finset.univ fun a : α => mass a * y a) ^ 2
        = (Finset.sum Finset.univ fun a : α => mass a * y a ^ 2) - μ ^ 2 := by
            simp [μ]
    _ = Finset.sum Finset.univ fun a : α => mass a * (y a - μ) ^ 2 := by
          calc
            (Finset.sum Finset.univ fun a : α => mass a * y a ^ 2) - μ ^ 2
                = (Finset.sum Finset.univ fun a : α => mass a * y a ^ 2)
                    - 2 * μ * μ + μ ^ 2 * 1 := by
                    ring
            _ = (Finset.sum Finset.univ fun a : α => mass a * y a ^ 2)
                    - 2 * μ * Finset.sum Finset.univ (fun a : α => mass a * y a)
                    + μ ^ 2 * Finset.sum Finset.univ mass := by
                    rw [show Finset.sum Finset.univ (fun a : α => mass a * y a) = μ from rfl,
                      hmass_total]
            _ = Finset.sum Finset.univ fun a : α =>
                    mass a * (y a ^ 2 - 2 * μ * y a + μ ^ 2) := by
                    calc
                      (Finset.sum Finset.univ fun a : α => mass a * y a ^ 2)
                          - 2 * μ * Finset.sum Finset.univ (fun a : α => mass a * y a)
                          + μ ^ 2 * Finset.sum Finset.univ mass
                          = Finset.sum Finset.univ fun a : α =>
                                mass a * y a ^ 2 - 2 * μ * (mass a * y a)
                                  + μ ^ 2 * mass a := by
                                rw [Finset.sum_add_distrib, Finset.sum_sub_distrib]
                                simp_rw [Finset.mul_sum]
                      _ = Finset.sum Finset.univ fun a : α =>
                              mass a * (y a ^ 2 - 2 * μ * y a + μ ^ 2) := by
                              refine Finset.sum_congr rfl ?_
                              intro a _
                              ring
            _ = Finset.sum Finset.univ fun a : α => mass a * (y a - μ) ^ 2 := by
                    refine Finset.sum_congr rfl ?_
                    intro a _
                    ring
    _ = Finset.sum Finset.univ fun a : α =>
          mass a * (y a - Finset.sum Finset.univ (fun b : α => mass b * y b)) ^ 2 := by
          simp [μ]

/-- Weighted scalar variance is nonnegative for nonnegative normalized masses. -/
theorem bisWeightedScalarSecondMoment_sub_meanSq_nonneg
    {α : Type} [Fintype α]
    (mass : α → ℝ) (y : α → ℝ)
    (hmass_nonneg : ∀ a : α, 0 ≤ mass a)
    (hmass_total : Finset.sum Finset.univ mass = 1) :
    0 ≤ (Finset.sum Finset.univ fun a : α => mass a * y a ^ 2)
      - (Finset.sum Finset.univ fun a : α => mass a * y a) ^ 2 := by
  rw [bisWeightedScalarSecondMoment_sub_meanSq_eq_sqDeviation mass y hmass_total]
  exact Finset.sum_nonneg fun a _ =>
    mul_nonneg (hmass_nonneg a)
      (sq_nonneg (y a - Finset.sum Finset.univ (fun b : α => mass b * y b)))

/--
Finite covariance quadratic forms are positive semidefinite under probability
masses.

This is the theorem-facing PSD bridge for the minimax layer: the covariance
quadratic form equals a weighted squared deviation, so it is nonnegative when
the masses are nonnegative and normalized.
-/
theorem bisWeightedCovarianceQuadraticForm_nonneg
    {α : Type} [Fintype α] {T : ℕ}
    (mass : α → ℝ) (x : α → Fin T → ℝ) (w : Fin T → ℝ)
    (hmass_nonneg : ∀ a : α, 0 ≤ mass a)
    (hmass_total : Finset.sum Finset.univ mass = 1) :
    0 ≤ Finset.sum Finset.univ fun i : Fin T =>
          Finset.sum Finset.univ fun j : Fin T =>
            w i * w j * bisWeightedCovarianceEntry mass x i j := by
  let y : α → ℝ := fun a => Finset.sum Finset.univ fun i : Fin T => x a i * w i
  have hscalar := bisWeightedScalarSecondMoment_sub_meanSq_nonneg mass y hmass_nonneg hmass_total
  have hmean :
      (Finset.sum Finset.univ fun a : α => mass a * y a)
        = Finset.sum Finset.univ fun i : Fin T => bisWeightedMeanCoord mass x i * w i := by
    unfold y bisWeightedMeanCoord
    calc
      (Finset.sum Finset.univ fun a : α =>
          mass a * (Finset.sum Finset.univ fun i : Fin T => x a i * w i))
          = Finset.sum Finset.univ fun a : α =>
              Finset.sum Finset.univ fun i : Fin T => mass a * (x a i * w i) := by
              simp_rw [Finset.mul_sum]
      _ = Finset.sum Finset.univ fun i : Fin T =>
            Finset.sum Finset.univ fun a : α => mass a * (x a i * w i) := by
            rw [Finset.sum_comm]
      _ = Finset.sum Finset.univ fun i : Fin T =>
            (Finset.sum Finset.univ fun a : α => mass a * x a i) * w i := by
            refine Finset.sum_congr rfl ?_
            intro i _
            rw [Finset.sum_mul]
            refine Finset.sum_congr rfl ?_
            intro a _
            ring
  rw [← bisWeightedInnerCenteredSecondMoment_eq_covarianceQuadraticForm mass x w]
  simpa [y, hmean] using hscalar

/--
Fixed coordinate sum forces the weighted mean vector to have the same all-ones
sum.

This is the generic finite-law version of the fixed-count first-order
constraint: if every support state has coordinate sum `target`, then the mean
participation vector also has coordinate sum `target`.
-/
theorem bisWeightedMeanCoord_sum_eq_fixedCoordSum
    {α : Type} [Fintype α] {T : ℕ}
    (mass : α → ℝ) (x : α → Fin T → ℝ) (target : ℝ)
    (hmass_total : Finset.sum Finset.univ mass = 1)
    (hsum : ∀ a : α, Finset.sum Finset.univ (fun i : Fin T => x a i) = target) :
    Finset.sum Finset.univ (fun i : Fin T => bisWeightedMeanCoord mass x i)
      = target := by
  unfold bisWeightedMeanCoord
  calc
    Finset.sum Finset.univ (fun i : Fin T =>
        Finset.sum Finset.univ fun a : α => mass a * x a i)
        = Finset.sum Finset.univ fun a : α =>
            Finset.sum Finset.univ fun i : Fin T => mass a * x a i := by
            rw [Finset.sum_comm]
    _ = Finset.sum Finset.univ fun a : α =>
          mass a * Finset.sum Finset.univ (fun i : Fin T => x a i) := by
          refine Finset.sum_congr rfl ?_
          intro a _
          rw [Finset.mul_sum]
    _ = Finset.sum Finset.univ fun a : α => mass a * target := by
          refine Finset.sum_congr rfl ?_
          intro a _
          rw [hsum a]
    _ = target := by
          rw [← Finset.sum_mul, hmass_total, one_mul]

/--
Fixed coordinate sum annihilates row sums of the covariance matrix.

Equivalently, for a finite law whose support lies in the affine hyperplane
`sum_i X_i = target`, the covariance operator sends the all-ones vector to
zero.  This is the theorem-facing bridge from fixed participation count to
vanishing all-ones/cross covariance terms.
-/
theorem bisWeightedCovarianceEntry_rowSum_eq_zero_of_fixedCoordSum
    {α : Type} [Fintype α] {T : ℕ}
    (mass : α → ℝ) (x : α → Fin T → ℝ) (target : ℝ)
    (hmass_total : Finset.sum Finset.univ mass = 1)
    (hsum : ∀ a : α, Finset.sum Finset.univ (fun i : Fin T => x a i) = target)
    (i : Fin T) :
    Finset.sum Finset.univ (fun j : Fin T => bisWeightedCovarianceEntry mass x i j)
      = 0 := by
  have hmean_sum := bisWeightedMeanCoord_sum_eq_fixedCoordSum mass x target hmass_total hsum
  have hsecond :
      Finset.sum Finset.univ (fun j : Fin T => bisWeightedSecondMomentEntry mass x i j)
        = target * bisWeightedMeanCoord mass x i := by
    unfold bisWeightedSecondMomentEntry bisWeightedMeanCoord
    calc
      Finset.sum Finset.univ (fun j : Fin T =>
          Finset.sum Finset.univ fun a : α => mass a * x a i * x a j)
          = Finset.sum Finset.univ fun a : α =>
              Finset.sum Finset.univ fun j : Fin T => mass a * x a i * x a j := by
              rw [Finset.sum_comm]
      _ = Finset.sum Finset.univ fun a : α =>
            mass a * x a i * Finset.sum Finset.univ (fun j : Fin T => x a j) := by
            refine Finset.sum_congr rfl ?_
            intro a _
            rw [Finset.mul_sum]
      _ = Finset.sum Finset.univ fun a : α => mass a * x a i * target := by
            refine Finset.sum_congr rfl ?_
            intro a _
            rw [hsum a]
      _ = target * Finset.sum Finset.univ (fun a : α => mass a * x a i) := by
            rw [Finset.mul_sum]
            refine Finset.sum_congr rfl ?_
            intro a _
            ring
  unfold bisWeightedCovarianceEntry
  rw [Finset.sum_sub_distrib, hsecond]
  calc
    target * bisWeightedMeanCoord mass x i
        - Finset.sum Finset.univ
            (fun j : Fin T => bisWeightedMeanCoord mass x i * bisWeightedMeanCoord mass x j)
        = target * bisWeightedMeanCoord mass x i
            - bisWeightedMeanCoord mass x i
              * Finset.sum Finset.univ (fun j : Fin T => bisWeightedMeanCoord mass x j) := by
            rw [Finset.mul_sum]
    _ = 0 := by
            rw [hmean_sum]
            ring

/--
Fixed coordinate sum annihilates column sums of the covariance matrix.

This is the transpose-facing form of
`bisWeightedCovarianceEntry_rowSum_eq_zero_of_fixedCoordSum`; together these
facts make the all-ones direction and centered directions decouple in the
generic fixed-count covariance algebra.
-/
theorem bisWeightedCovarianceEntry_colSum_eq_zero_of_fixedCoordSum
    {α : Type} [Fintype α] {T : ℕ}
    (mass : α → ℝ) (x : α → Fin T → ℝ) (target : ℝ)
    (hmass_total : Finset.sum Finset.univ mass = 1)
    (hsum : ∀ a : α, Finset.sum Finset.univ (fun i : Fin T => x a i) = target)
    (j : Fin T) :
    Finset.sum Finset.univ (fun i : Fin T => bisWeightedCovarianceEntry mass x i j)
      = 0 := by
  have hmean_sum := bisWeightedMeanCoord_sum_eq_fixedCoordSum mass x target hmass_total hsum
  have hsecond :
      Finset.sum Finset.univ (fun i : Fin T => bisWeightedSecondMomentEntry mass x i j)
        = target * bisWeightedMeanCoord mass x j := by
    unfold bisWeightedSecondMomentEntry bisWeightedMeanCoord
    calc
      Finset.sum Finset.univ (fun i : Fin T =>
          Finset.sum Finset.univ fun a : α => mass a * x a i * x a j)
          = Finset.sum Finset.univ fun a : α =>
              Finset.sum Finset.univ fun i : Fin T => mass a * x a i * x a j := by
              rw [Finset.sum_comm]
      _ = Finset.sum Finset.univ fun a : α =>
            mass a * x a j * Finset.sum Finset.univ (fun i : Fin T => x a i) := by
            refine Finset.sum_congr rfl ?_
            intro a _
            rw [Finset.mul_sum]
            refine Finset.sum_congr rfl ?_
            intro i _
            ring
      _ = Finset.sum Finset.univ fun a : α => mass a * x a j * target := by
            refine Finset.sum_congr rfl ?_
            intro a _
            rw [hsum a]
      _ = target * Finset.sum Finset.univ (fun a : α => mass a * x a j) := by
            rw [Finset.mul_sum]
            refine Finset.sum_congr rfl ?_
            intro a _
            ring
  unfold bisWeightedCovarianceEntry
  rw [Finset.sum_sub_distrib, hsecond]
  calc
    target * bisWeightedMeanCoord mass x j
        - Finset.sum Finset.univ
            (fun i : Fin T => bisWeightedMeanCoord mass x i * bisWeightedMeanCoord mass x j)
        = target * bisWeightedMeanCoord mass x j
            - (Finset.sum Finset.univ (fun i : Fin T => bisWeightedMeanCoord mass x i))
              * bisWeightedMeanCoord mass x j := by
            rw [Finset.sum_mul]
    _ = 0 := by
            rw [hmean_sum]
            ring

/--
Trace identity for binary fixed-coordinate-sum finite laws.

If every support vector is binary in the sense `X_i^2 = X_i` and has fixed
coordinate sum `target`, then the covariance trace is the fixed count minus the
squared norm of the mean vector:

`sum_i Cov(i,i) = target - sum_i mean_i^2`.

This is the finite trace bridge immediately preceding the centered minimax
eigenvalue theorem.  It is still generic finite algebra and does not assert
isotropy.
-/
theorem bisWeightedCovarianceTrace_eq_fixedCoordSum_sub_meanSqNorm_of_binary
    {α : Type} [Fintype α] {T : ℕ}
    (mass : α → ℝ) (x : α → Fin T → ℝ) (target : ℝ)
    (hmass_total : Finset.sum Finset.univ mass = 1)
    (hsum : ∀ a : α, Finset.sum Finset.univ (fun i : Fin T => x a i) = target)
    (hbinary : ∀ (a : α) (i : Fin T), x a i * x a i = x a i) :
    Finset.sum Finset.univ (fun i : Fin T => bisWeightedCovarianceEntry mass x i i)
      = target - Finset.sum Finset.univ
          (fun i : Fin T => (bisWeightedMeanCoord mass x i) ^ 2) := by
  have hsecond :
      Finset.sum Finset.univ (fun i : Fin T => bisWeightedSecondMomentEntry mass x i i)
        = target := by
    unfold bisWeightedSecondMomentEntry
    calc
      Finset.sum Finset.univ (fun i : Fin T =>
          Finset.sum Finset.univ fun a : α => mass a * x a i * x a i)
          = Finset.sum Finset.univ fun a : α =>
              Finset.sum Finset.univ fun i : Fin T => mass a * x a i * x a i := by
              rw [Finset.sum_comm]
      _ = Finset.sum Finset.univ fun a : α =>
            mass a * Finset.sum Finset.univ (fun i : Fin T => x a i) := by
            refine Finset.sum_congr rfl ?_
            intro a _
            calc
              Finset.sum Finset.univ (fun i : Fin T => mass a * x a i * x a i)
                  = Finset.sum Finset.univ (fun i : Fin T => mass a * x a i) := by
                  refine Finset.sum_congr rfl ?_
                  intro i _
                  calc
                    mass a * x a i * x a i = mass a * (x a i * x a i) := by ring
                    _ = mass a * x a i := by rw [hbinary a i]
              _ = mass a * Finset.sum Finset.univ (fun i : Fin T => x a i) := by
                  rw [Finset.mul_sum]
      _ = Finset.sum Finset.univ fun a : α => mass a * target := by
            refine Finset.sum_congr rfl ?_
            intro a _
            rw [hsum a]
      _ = target := by
            rw [← Finset.sum_mul, hmass_total, one_mul]
  unfold bisWeightedCovarianceEntry
  rw [Finset.sum_sub_distrib, hsecond]
  refine congrArg (fun y => target - y) ?_
  refine Finset.sum_congr rfl ?_
  intro i _
  ring

/--
Uniform-mean specialization of the binary fixed-count covariance trace.

If a binary fixed-count law has coordinate mean `target / T` at every
coordinate, then its covariance trace is `target - target^2 / T`.  This is the
finite trace invariant used by the centered minimax route before specializing
`target = k`.
-/
theorem bisWeightedCovarianceTrace_eq_fixedCoordSum_sub_uniformMeanSq_of_binary
    {α : Type} [Fintype α] {T : ℕ}
    (mass : α → ℝ) (x : α → Fin T → ℝ) (target : ℝ)
    (hT : 0 < T)
    (hmass_total : Finset.sum Finset.univ mass = 1)
    (hsum : ∀ a : α, Finset.sum Finset.univ (fun i : Fin T => x a i) = target)
    (hbinary : ∀ (a : α) (i : Fin T), x a i * x a i = x a i)
    (hmean : ∀ i : Fin T, bisWeightedMeanCoord mass x i = target / (T : ℝ)) :
    Finset.sum Finset.univ (fun i : Fin T => bisWeightedCovarianceEntry mass x i i)
      = target - target ^ 2 / (T : ℝ) := by
  have htrace := bisWeightedCovarianceTrace_eq_fixedCoordSum_sub_meanSqNorm_of_binary
    mass x target hmass_total hsum hbinary
  rw [htrace]
  have hTne : (T : ℝ) ≠ 0 := by exact_mod_cast (ne_of_gt hT)
  have hmeanSq :
      Finset.sum Finset.univ (fun i : Fin T => (bisWeightedMeanCoord mass x i) ^ 2)
        = target ^ 2 / (T : ℝ) := by
    calc
      Finset.sum Finset.univ (fun i : Fin T => (bisWeightedMeanCoord mass x i) ^ 2)
          = Finset.sum Finset.univ (fun _i : Fin T => (target / (T : ℝ)) ^ 2) := by
          refine Finset.sum_congr rfl ?_
          intro i _
          rw [hmean i]
      _ = (T : ℝ) * (target / (T : ℝ)) ^ 2 := by
          simp [Finset.card_univ]
      _ = target ^ 2 / (T : ℝ) := by
          field_simp [hTne]
  rw [hmeanSq]

/--
Natural-count version of the uniform-marginal binary fixed-count trace.

For a `k`-out-of-`T` binary law with uniform coordinate mean `k / T`, the
covariance trace is the centered-subspace invariant `k(T-k)/T`.  This is the
paper-facing trace constant used by the pairwise-contrast minimax route.
-/
theorem bisWeightedCovarianceTrace_eq_k_mul_T_sub_k_div_T_of_binary
    {α : Type} [Fintype α] {T k : ℕ}
    (mass : α → ℝ) (x : α → Fin T → ℝ)
    (hT : 0 < T) (hk : k ≤ T)
    (hmass_total : Finset.sum Finset.univ mass = 1)
    (hsum : ∀ a : α, Finset.sum Finset.univ (fun i : Fin T => x a i) = (k : ℝ))
    (hbinary : ∀ (a : α) (i : Fin T), x a i * x a i = x a i)
    (hmean : ∀ i : Fin T, bisWeightedMeanCoord mass x i = (k : ℝ) / (T : ℝ)) :
    Finset.sum Finset.univ (fun i : Fin T => bisWeightedCovarianceEntry mass x i i)
      = ((k : ℝ) * ((T - k : ℕ) : ℝ)) / (T : ℝ) := by
  rw [bisWeightedCovarianceTrace_eq_fixedCoordSum_sub_uniformMeanSq_of_binary
    mass x (k : ℝ) hT hmass_total hsum hbinary hmean]
  have hTne : (T : ℝ) ≠ 0 := by exact_mod_cast (ne_of_gt hT)
  rw [Nat.cast_sub hk]
  field_simp [hTne]

/--
Subtracting a constant from both arguments leaves a quadratic form unchanged
when row and column sums vanish.

This is the abstract finite algebra behind centered projection: a covariance
matrix with the all-ones direction in both kernels only sees the centered
component of a vector.
-/
theorem bisQuadraticForm_sub_const_eq_of_rowColZero
    {T : ℕ} (C : Fin T → Fin T → ℝ) (w : Fin T → ℝ) (c : ℝ)
    (hrow : ∀ i : Fin T, Finset.sum Finset.univ (fun j : Fin T => C i j) = 0)
    (hcol : ∀ j : Fin T, Finset.sum Finset.univ (fun i : Fin T => C i j) = 0) :
    (Finset.sum Finset.univ fun i : Fin T =>
        Finset.sum Finset.univ fun j : Fin T => (w i - c) * (w j - c) * C i j)
      = Finset.sum Finset.univ fun i : Fin T =>
          Finset.sum Finset.univ fun j : Fin T => w i * w j * C i j := by
  have hrowTerm :
      (Finset.sum Finset.univ fun i : Fin T =>
        Finset.sum Finset.univ fun j : Fin T => w i * c * C i j) = 0 := by
    calc
      (Finset.sum Finset.univ fun i : Fin T =>
        Finset.sum Finset.univ fun j : Fin T => w i * c * C i j)
          = Finset.sum Finset.univ fun i : Fin T =>
              (w i * c) * Finset.sum Finset.univ (fun j : Fin T => C i j) := by
              refine Finset.sum_congr rfl ?_
              intro i _
              rw [Finset.mul_sum]
      _ = 0 := by
          simp [hrow]
  have hcolTerm :
      (Finset.sum Finset.univ fun i : Fin T =>
        Finset.sum Finset.univ fun j : Fin T => c * w j * C i j) = 0 := by
    calc
      (Finset.sum Finset.univ fun i : Fin T =>
        Finset.sum Finset.univ fun j : Fin T => c * w j * C i j)
          = Finset.sum Finset.univ fun j : Fin T =>
              Finset.sum Finset.univ fun i : Fin T => c * w j * C i j := by
              rw [Finset.sum_comm]
      _ = Finset.sum Finset.univ fun j : Fin T =>
            (c * w j) * Finset.sum Finset.univ (fun i : Fin T => C i j) := by
            refine Finset.sum_congr rfl ?_
            intro j _
            rw [Finset.mul_sum]
      _ = 0 := by
          simp [hcol]
  have hallTerm :
      (Finset.sum Finset.univ fun i : Fin T =>
        Finset.sum Finset.univ fun j : Fin T => c * c * C i j) = 0 := by
    calc
      (Finset.sum Finset.univ fun i : Fin T =>
        Finset.sum Finset.univ fun j : Fin T => c * c * C i j)
          = Finset.sum Finset.univ fun i : Fin T =>
              (c * c) * Finset.sum Finset.univ (fun j : Fin T => C i j) := by
              refine Finset.sum_congr rfl ?_
              intro i _
              rw [Finset.mul_sum]
      _ = 0 := by
          simp [hrow]
  calc
    (Finset.sum Finset.univ fun i : Fin T =>
        Finset.sum Finset.univ fun j : Fin T => (w i - c) * (w j - c) * C i j)
        = Finset.sum Finset.univ fun i : Fin T =>
            Finset.sum Finset.univ fun j : Fin T =>
              w i * w j * C i j - w i * c * C i j
                - c * w j * C i j + c * c * C i j := by
            refine Finset.sum_congr rfl ?_
            intro i _
            refine Finset.sum_congr rfl ?_
            intro j _
            ring
    _ = (Finset.sum Finset.univ fun i : Fin T =>
            Finset.sum Finset.univ fun j : Fin T => w i * w j * C i j)
          - (Finset.sum Finset.univ fun i : Fin T =>
              Finset.sum Finset.univ fun j : Fin T => w i * c * C i j)
          - (Finset.sum Finset.univ fun i : Fin T =>
              Finset.sum Finset.univ fun j : Fin T => c * w j * C i j)
          + (Finset.sum Finset.univ fun i : Fin T =>
              Finset.sum Finset.univ fun j : Fin T => c * c * C i j) := by
          simp_rw [Finset.sum_add_distrib, Finset.sum_sub_distrib]
    _ = Finset.sum Finset.univ fun i : Fin T =>
          Finset.sum Finset.univ fun j : Fin T => w i * w j * C i j := by
          rw [hrowTerm, hcolTerm, hallTerm]
          ring

/--
Quadratic forms with zero row and column sums depend only on the centered
projection `w_perp`.

This is the square-root-free generic version of
`w^T Sigma w = w_perp^T Sigma w_perp` for covariance matrices that annihilate
the all-ones direction.
-/
theorem bisQuadraticForm_zeroSumComponent_eq_of_rowColZero
    {T : ℕ} (C : Fin T → Fin T → ℝ) (w : Fin T → ℝ)
    (hrow : ∀ i : Fin T, Finset.sum Finset.univ (fun j : Fin T => C i j) = 0)
    (hcol : ∀ j : Fin T, Finset.sum Finset.univ (fun i : Fin T => C i j) = 0) :
    (Finset.sum Finset.univ fun i : Fin T =>
        Finset.sum Finset.univ fun j : Fin T =>
          bisZeroSumComponent w i * bisZeroSumComponent w j * C i j)
      = Finset.sum Finset.univ fun i : Fin T =>
          Finset.sum Finset.univ fun j : Fin T => w i * w j * C i j := by
  simpa [bisZeroSumComponent] using
    bisQuadraticForm_sub_const_eq_of_rowColZero C w
      ((Finset.sum Finset.univ w) / (T : ℝ)) hrow hcol

/--
Generic fixed-count covariance quadratic forms depend only on centered
directions.

Combining the r06 row/column annihilation theorem with the abstract projection
identity gives the finite-law version of all-ones decoupling needed before the
centered covariance minimax theorem.
-/
theorem bisWeightedCovarianceQuadraticForm_zeroSumComponent_eq_of_fixedCoordSum
    {α : Type} [Fintype α] {T : ℕ}
    (mass : α → ℝ) (x : α → Fin T → ℝ) (target : ℝ) (w : Fin T → ℝ)
    (hmass_total : Finset.sum Finset.univ mass = 1)
    (hsum : ∀ a : α, Finset.sum Finset.univ (fun i : Fin T => x a i) = target) :
    (Finset.sum Finset.univ fun i : Fin T =>
        Finset.sum Finset.univ fun j : Fin T =>
          bisZeroSumComponent w i * bisZeroSumComponent w j
            * bisWeightedCovarianceEntry mass x i j)
      = Finset.sum Finset.univ fun i : Fin T =>
          Finset.sum Finset.univ fun j : Fin T =>
            w i * w j * bisWeightedCovarianceEntry mass x i j := by
  exact bisQuadraticForm_zeroSumComponent_eq_of_rowColZero
    (fun i j => bisWeightedCovarianceEntry mass x i j) w
    (bisWeightedCovarianceEntry_rowSum_eq_zero_of_fixedCoordSum mass x target hmass_total hsum)
    (bisWeightedCovarianceEntry_colSum_eq_zero_of_fixedCoordSum mass x target hmass_total hsum)

/--
Ordered-pair half-contrast sum for a row/column-zero quadratic form.

For the contrast `e_i-e_j`, the half contrast value is

```text
(C_ii + C_jj - C_ij - C_ji) / 2.
```

Summing this over all ordered pairs gives `T * trace(C)` when the all-ones
row and column sums vanish.  The diagonal terms are zero automatically.
-/
theorem bisPairwiseHalfContrastSum_eq_card_mul_trace_of_rowColZero
    {T : ℕ} (C : Fin T → Fin T → ℝ)
    (hrow : ∀ i : Fin T, Finset.sum Finset.univ (fun j : Fin T => C i j) = 0)
    (hcol : ∀ j : Fin T, Finset.sum Finset.univ (fun i : Fin T => C i j) = 0) :
    (Finset.sum Finset.univ fun i : Fin T =>
        Finset.sum Finset.univ fun j : Fin T =>
          (C i i + C j j - C i j - C j i) / 2)
      = (T : ℝ) * Finset.sum Finset.univ (fun i : Fin T => C i i) := by
  have hdiagLeft :
      (Finset.sum Finset.univ fun i : Fin T =>
        Finset.sum Finset.univ fun _j : Fin T => C i i)
        = (T : ℝ) * Finset.sum Finset.univ (fun i : Fin T => C i i) := by
    calc
      (Finset.sum Finset.univ fun i : Fin T =>
        Finset.sum Finset.univ fun _j : Fin T => C i i)
          = Finset.sum Finset.univ fun i : Fin T => (T : ℝ) * C i i := by
          refine Finset.sum_congr rfl ?_
          intro i _
          simp [Finset.card_univ]
      _ = (T : ℝ) * Finset.sum Finset.univ (fun i : Fin T => C i i) := by
          rw [Finset.mul_sum]
  have hdiagRight :
      (Finset.sum Finset.univ fun i : Fin T =>
        Finset.sum Finset.univ fun j : Fin T => C j j)
        = (T : ℝ) * Finset.sum Finset.univ (fun j : Fin T => C j j) := by
    rw [Finset.sum_comm]
    exact hdiagLeft
  have hrowAll :
      (Finset.sum Finset.univ fun i : Fin T =>
        Finset.sum Finset.univ fun j : Fin T => C i j) = 0 := by
    simp [hrow]
  have hcolAll :
      (Finset.sum Finset.univ fun i : Fin T =>
        Finset.sum Finset.univ fun j : Fin T => C j i) = 0 := by
    simp [hcol]
  have hraw :
      (Finset.sum Finset.univ fun i : Fin T =>
        Finset.sum Finset.univ fun j : Fin T =>
          C i i + C j j - C i j - C j i)
        = 2 * ((T : ℝ) * Finset.sum Finset.univ (fun i : Fin T => C i i)) := by
    have hinner : ∀ i : Fin T,
        (Finset.sum Finset.univ fun j : Fin T =>
          C i i + C j j - C i j - C j i)
          = (Finset.sum Finset.univ fun j : Fin T => C i i)
              + (Finset.sum Finset.univ fun j : Fin T => C j j)
              - (Finset.sum Finset.univ fun j : Fin T => C i j)
              - (Finset.sum Finset.univ fun j : Fin T => C j i) := by
      intro i
      calc
        (Finset.sum Finset.univ fun j : Fin T =>
          C i i + C j j - C i j - C j i)
            = (Finset.sum Finset.univ fun j : Fin T =>
                C i i + C j j - C i j)
                - (Finset.sum Finset.univ fun j : Fin T => C j i) := by
                rw [Finset.sum_sub_distrib]
        _ = ((Finset.sum Finset.univ fun j : Fin T =>
                C i i + C j j)
                - (Finset.sum Finset.univ fun j : Fin T => C i j))
                - (Finset.sum Finset.univ fun j : Fin T => C j i) := by
                rw [Finset.sum_sub_distrib]
        _ = (Finset.sum Finset.univ fun j : Fin T => C i i)
              + (Finset.sum Finset.univ fun j : Fin T => C j j)
              - (Finset.sum Finset.univ fun j : Fin T => C i j)
              - (Finset.sum Finset.univ fun j : Fin T => C j i) := by
              rw [Finset.sum_add_distrib]
    calc
      (Finset.sum Finset.univ fun i : Fin T =>
        Finset.sum Finset.univ fun j : Fin T =>
          C i i + C j j - C i j - C j i)
          = ((Finset.sum Finset.univ fun i : Fin T =>
                Finset.sum Finset.univ fun j : Fin T => C i i)
              + (Finset.sum Finset.univ fun i : Fin T =>
                Finset.sum Finset.univ fun j : Fin T => C j j)
              - (Finset.sum Finset.univ fun i : Fin T =>
                Finset.sum Finset.univ fun j : Fin T => C i j)
              - (Finset.sum Finset.univ fun i : Fin T =>
                Finset.sum Finset.univ fun j : Fin T => C j i)) := by
              calc
                (Finset.sum Finset.univ fun i : Fin T =>
                  Finset.sum Finset.univ fun j : Fin T =>
                    C i i + C j j - C i j - C j i)
                    = (Finset.sum Finset.univ fun i : Fin T =>
                        (Finset.sum Finset.univ fun j : Fin T => C i i)
                          + (Finset.sum Finset.univ fun j : Fin T => C j j)
                          - (Finset.sum Finset.univ fun j : Fin T => C i j)
                          - (Finset.sum Finset.univ fun j : Fin T => C j i)) := by
                          simp_rw [hinner]
                _ = (Finset.sum Finset.univ fun i : Fin T =>
                        (Finset.sum Finset.univ fun j : Fin T => C i i)
                          + (Finset.sum Finset.univ fun j : Fin T => C j j)
                          - (Finset.sum Finset.univ fun j : Fin T => C i j))
                      - (Finset.sum Finset.univ fun i : Fin T =>
                        Finset.sum Finset.univ fun j : Fin T => C j i) := by
                          rw [Finset.sum_sub_distrib]
                _ = ((Finset.sum Finset.univ fun i : Fin T =>
                        (Finset.sum Finset.univ fun j : Fin T => C i i)
                          + (Finset.sum Finset.univ fun j : Fin T => C j j))
                      - (Finset.sum Finset.univ fun i : Fin T =>
                        Finset.sum Finset.univ fun j : Fin T => C i j))
                      - (Finset.sum Finset.univ fun i : Fin T =>
                        Finset.sum Finset.univ fun j : Fin T => C j i) := by
                          rw [Finset.sum_sub_distrib]
                _ = ((Finset.sum Finset.univ fun i : Fin T =>
                        Finset.sum Finset.univ fun j : Fin T => C i i)
                      + (Finset.sum Finset.univ fun i : Fin T =>
                        Finset.sum Finset.univ fun j : Fin T => C j j)
                      - (Finset.sum Finset.univ fun i : Fin T =>
                        Finset.sum Finset.univ fun j : Fin T => C i j))
                      - (Finset.sum Finset.univ fun i : Fin T =>
                        Finset.sum Finset.univ fun j : Fin T => C j i) := by
                          rw [Finset.sum_add_distrib]
                _ = ((Finset.sum Finset.univ fun i : Fin T =>
                        Finset.sum Finset.univ fun j : Fin T => C i i)
                      + (Finset.sum Finset.univ fun i : Fin T =>
                        Finset.sum Finset.univ fun j : Fin T => C j j)
                      - (Finset.sum Finset.univ fun i : Fin T =>
                        Finset.sum Finset.univ fun j : Fin T => C i j)
                      - (Finset.sum Finset.univ fun i : Fin T =>
                        Finset.sum Finset.univ fun j : Fin T => C j i)) := by
                          ring
      _ = 2 * ((T : ℝ) * Finset.sum Finset.univ (fun i : Fin T => C i i)) := by
            rw [hdiagLeft, hdiagRight, hrowAll, hcolAll]
            ring
  calc
    (Finset.sum Finset.univ fun i : Fin T =>
        Finset.sum Finset.univ fun j : Fin T =>
          (C i i + C j j - C i j - C j i) / 2)
        = (Finset.sum Finset.univ fun i : Fin T =>
            (Finset.sum Finset.univ fun j : Fin T =>
              C i i + C j j - C i j - C j i) * 2⁻¹) := by
            simp_rw [div_eq_mul_inv]
            refine Finset.sum_congr rfl ?_
            intro i _
            rw [← Finset.sum_mul]
    _ = (Finset.sum Finset.univ fun i : Fin T =>
            Finset.sum Finset.univ fun j : Fin T =>
              C i i + C j j - C i j - C j i) / 2 := by
          simp_rw [div_eq_mul_inv]
          rw [← Finset.sum_mul]
    _ = (T : ℝ) * Finset.sum Finset.univ (fun i : Fin T => C i i) := by
          rw [hraw]
          ring

/--
Off-diagonal ordered-pair half-contrast sum.

This is the same identity as
`bisPairwiseHalfContrastSum_eq_card_mul_trace_of_rowColZero`, but with the
diagonal pairs explicitly removed.  It is the finite average identity used by
the pairwise-contrast minimax route.
-/
theorem bisPairwiseHalfContrastOffdiagSum_eq_card_mul_trace_of_rowColZero
    {T : ℕ} (C : Fin T → Fin T → ℝ)
    (hrow : ∀ i : Fin T, Finset.sum Finset.univ (fun j : Fin T => C i j) = 0)
    (hcol : ∀ j : Fin T, Finset.sum Finset.univ (fun i : Fin T => C i j) = 0) :
    (Finset.sum Finset.univ fun i : Fin T =>
        Finset.sum Finset.univ fun j : Fin T =>
          if i = j then 0 else (C i i + C j j - C i j - C j i) / 2)
      = (T : ℝ) * Finset.sum Finset.univ (fun i : Fin T => C i i) := by
  rw [← bisPairwiseHalfContrastSum_eq_card_mul_trace_of_rowColZero C hrow hcol]
  refine Finset.sum_congr rfl ?_
  intro i _
  refine Finset.sum_congr rfl ?_
  intro j _
  by_cases hij : i = j
  · subst j
    simp
  · simp [hij]

/--
Average off-diagonal pairwise half-contrast value.

For `2 <= T`, dividing the ordered off-diagonal sum by `T(T-1)` gives
`trace(C)/(T-1)`.  This is the pairwise-contrast averaging bridge to the
centered covariance minimax theorem; it avoids eigenvalue machinery.
-/
theorem bisPairwiseHalfContrastOffdiagAverage_eq_trace_div_of_rowColZero
    {T : ℕ} (C : Fin T → Fin T → ℝ) (hT : 2 ≤ T)
    (hrow : ∀ i : Fin T, Finset.sum Finset.univ (fun j : Fin T => C i j) = 0)
    (hcol : ∀ j : Fin T, Finset.sum Finset.univ (fun i : Fin T => C i j) = 0) :
    ((Finset.sum Finset.univ fun i : Fin T =>
        Finset.sum Finset.univ fun j : Fin T =>
          if i = j then 0 else (C i i + C j j - C i j - C j i) / 2)
      / ((T : ℝ) * ((T - 1 : ℕ) : ℝ)))
      = (Finset.sum Finset.univ (fun i : Fin T => C i i))
          / ((T - 1 : ℕ) : ℝ) := by
  have hTposNat : 0 < T := lt_of_lt_of_le (by norm_num) hT
  have hTpos : (0 : ℝ) < (T : ℝ) := by exact_mod_cast hTposNat
  have hTone : 1 ≤ T := le_trans (by norm_num) hT
  have hTminus_ne : (((T - 1 : ℕ) : ℝ) ≠ 0) := by
    have hpos : 0 < T - 1 := Nat.sub_pos_of_lt hT
    exact_mod_cast (ne_of_gt hpos)
  rw [bisPairwiseHalfContrastOffdiagSum_eq_card_mul_trace_of_rowColZero C hrow hcol]
  field_simp [hTpos.ne', hTminus_ne]

/--
Product-filter form of the ordered off-diagonal sum.

This repackages the nested `if i = j then 0 else ...` form into a finset of
ordered off-diagonal pairs.  It is the finite-pigeonhole bridge used to extract
one contrast at least as large as the average.
-/
theorem bisOffdiagPairSum_eq_nestedIte
    {T : ℕ} (f : Fin T → Fin T → ℝ) :
    (Finset.sum
      ((Finset.univ.product Finset.univ).filter (fun p : Fin T × Fin T => p.1 ≠ p.2))
      (fun p => f p.1 p.2))
      = (Finset.sum Finset.univ fun i : Fin T =>
          Finset.sum Finset.univ fun j : Fin T =>
            if i = j then 0 else f i j) := by
  rw [Finset.sum_filter]
  calc
    (∑ a ∈ Finset.univ.product Finset.univ,
        if a.1 ≠ a.2 then f a.1 a.2 else 0)
        = (∑ i : Fin T, ∑ j : Fin T,
            if (i, j).1 ≠ (i, j).2 then f (i, j).1 (i, j).2 else 0) := by
            simpa using
              (Finset.sum_product
                (s := (Finset.univ : Finset (Fin T)))
                (t := (Finset.univ : Finset (Fin T)))
                (f := fun p : Fin T × Fin T =>
                  if p.1 ≠ p.2 then f p.1 p.2 else 0))
    _ = (Finset.sum Finset.univ fun i : Fin T =>
          Finset.sum Finset.univ fun j : Fin T =>
            if i = j then 0 else f i j) := by
          refine Finset.sum_congr rfl ?_
          intro i _
          refine Finset.sum_congr rfl ?_
          intro j _
          by_cases hij : i = j
          · simp [hij]
          · simp [hij]

/-- Constant ordered off-diagonal pair sum. -/
theorem bisOffdiagPairConstSum_eq_card_mul
    {T : ℕ} (B : ℝ) :
    (Finset.sum
      ((Finset.univ.product Finset.univ).filter (fun p : Fin T × Fin T => p.1 ≠ p.2))
      (fun _p => B))
      = (T : ℝ) * ((T - 1 : ℕ) : ℝ) * B := by
  rw [bisOffdiagPairSum_eq_nestedIte (T := T) (fun _ _ => B)]
  have hinner : ∀ i : Fin T,
      (Finset.sum Finset.univ fun j : Fin T => if i = j then 0 else B)
        = ((T - 1 : ℕ) : ℝ) * B := by
    intro i
    calc
      (Finset.sum Finset.univ fun j : Fin T => if i = j then 0 else B)
          = Finset.sum (Finset.univ.erase i)
              (fun j : Fin T => if i = j then 0 else B) := by
              rw [← Finset.sum_erase (s := Finset.univ) (a := i)
                (f := fun j : Fin T => if i = j then 0 else B)]
              simp
      _ = Finset.sum (Finset.univ.erase i) (fun _j : Fin T => B) := by
              refine Finset.sum_congr rfl ?_
              intro j hj
              have hji : i ≠ j := by
                intro h
                exact (Finset.mem_erase.mp hj).1 h.symm
              simp [hji]
      _ = ((Finset.univ.erase i).card : ℝ) * B := by
              simp [Finset.sum_const, nsmul_eq_mul]
      _ = ((T - 1 : ℕ) : ℝ) * B := by
              rw [Finset.card_erase_of_mem]
              · simp [Finset.card_univ]
              · simp
  calc
    (Finset.sum Finset.univ fun i : Fin T =>
      Finset.sum Finset.univ fun j : Fin T => if i = j then 0 else B)
        = Finset.sum Finset.univ
            (fun _i : Fin T => ((T - 1 : ℕ) : ℝ) * B) := by
            refine Finset.sum_congr rfl ?_
            intro i _
            rw [hinner i]
    _ = (T : ℝ) * ((T - 1 : ℕ) : ℝ) * B := by
            simp [Finset.sum_const, nsmul_eq_mul, mul_assoc]

/--
Existence form of the pairwise-contrast average bridge.

For `2 <= T`, if a finite quadratic form has zero all-ones row and column sums,
then at least one ordered off-diagonal pair has half-contrast at least
`trace(C)/(T-1)`.  This is the elementary minimax lower-bound seed: the worst
centered direction is at least the average pairwise contrast.
-/
theorem exists_pairwiseHalfContrast_ge_trace_div_of_rowColZero
    {T : ℕ} (C : Fin T → Fin T → ℝ) (hT : 2 ≤ T)
    (hrow : ∀ i : Fin T, Finset.sum Finset.univ (fun j : Fin T => C i j) = 0)
    (hcol : ∀ j : Fin T, Finset.sum Finset.univ (fun i : Fin T => C i j) = 0) :
    ∃ i j : Fin T, i ≠ j ∧
      (Finset.sum Finset.univ (fun a : Fin T => C a a))
          / ((T - 1 : ℕ) : ℝ)
        ≤ (C i i + C j j - C i j - C j i) / 2 := by
  classical
  let b : ℝ := (Finset.sum Finset.univ (fun a : Fin T => C a a))
    / ((T - 1 : ℕ) : ℝ)
  let half : Fin T → Fin T → ℝ :=
    fun i j => (C i i + C j j - C i j - C j i) / 2
  let pairs : Finset (Fin T × Fin T) :=
    (Finset.univ.product Finset.univ).filter (fun p : Fin T × Fin T => p.1 ≠ p.2)
  have hTposNat : 0 < T := lt_of_lt_of_le (by norm_num) hT
  have hTpos : (0 : ℝ) < (T : ℝ) := by exact_mod_cast hTposNat
  have hTone : 1 ≤ T := le_trans (by norm_num) hT
  have hTminus_ne : (((T - 1 : ℕ) : ℝ) ≠ 0) := by
    have hpos : 0 < T - 1 := Nat.sub_pos_of_lt hT
    exact_mod_cast (ne_of_gt hpos)
  have hden_ne : ((T : ℝ) * ((T - 1 : ℕ) : ℝ)) ≠ 0 := by
    exact mul_ne_zero hTpos.ne' hTminus_ne
  have hpairs_nonempty : pairs.Nonempty := by
    let i0 : Fin T := ⟨0, hTposNat⟩
    let i1 : Fin T := ⟨1, lt_of_lt_of_le (by norm_num) hT⟩
    have hne : i0 ≠ i1 := by
      intro h
      have hc := congrArg Fin.val h
      norm_num [i0, i1] at hc
    refine ⟨(i0, i1), ?_⟩
    simp [pairs, hne]
  have havg := bisPairwiseHalfContrastOffdiagAverage_eq_trace_div_of_rowColZero
    C hT hrow hcol
  have hhalfNested :
      (Finset.sum Finset.univ fun i : Fin T =>
        Finset.sum Finset.univ fun j : Fin T =>
          if i = j then 0 else half i j)
        = ((T : ℝ) * ((T - 1 : ℕ) : ℝ)) * b := by
    calc
      (Finset.sum Finset.univ fun i : Fin T =>
        Finset.sum Finset.univ fun j : Fin T =>
          if i = j then 0 else half i j)
          = ((Finset.sum Finset.univ fun i : Fin T =>
              Finset.sum Finset.univ fun j : Fin T =>
                if i = j then 0 else half i j)
              / ((T : ℝ) * ((T - 1 : ℕ) : ℝ)))
              * ((T : ℝ) * ((T - 1 : ℕ) : ℝ)) := by
              field_simp [hden_ne]
      _ = b * ((T : ℝ) * ((T - 1 : ℕ) : ℝ)) := by
              rw [havg]
      _ = ((T : ℝ) * ((T - 1 : ℕ) : ℝ)) * b := by
              ring
  have hhalfSum :
      Finset.sum pairs (fun p : Fin T × Fin T => half p.1 p.2)
        = ((T : ℝ) * ((T - 1 : ℕ) : ℝ)) * b := by
    rw [bisOffdiagPairSum_eq_nestedIte (T := T) half]
    exact hhalfNested
  have hconstSum :
      Finset.sum pairs (fun _p : Fin T × Fin T => b)
        = ((T : ℝ) * ((T - 1 : ℕ) : ℝ)) * b := by
    exact bisOffdiagPairConstSum_eq_card_mul (T := T) b
  have hsum_le :
      Finset.sum pairs (fun _p : Fin T × Fin T => b)
        ≤ Finset.sum pairs (fun p : Fin T × Fin T => half p.1 p.2) := by
    rw [hconstSum, hhalfSum]
  rcases Finset.exists_le_of_sum_le hpairs_nonempty hsum_le with ⟨p, hp, hp_le⟩
  refine ⟨p.1, p.2, ?_, ?_⟩
  · simpa [pairs] using hp
  · simpa [b, half] using hp_le

/--
Fixed-count covariance specialization of the pairwise existence bridge.

If a finite participation law has fixed coordinate sum, its covariance has zero
all-ones row and column sums.  Therefore one off-diagonal pairwise contrast is
at least the covariance trace divided by `T-1`.
-/
theorem exists_weightedCovariancePairwiseHalfContrast_ge_trace_div_of_fixedCoordSum
    {α : Type} [Fintype α] {T : ℕ}
    (mass : α → ℝ) (x : α → Fin T → ℝ) (target : ℝ) (hT : 2 ≤ T)
    (hmass_total : Finset.sum Finset.univ mass = 1)
    (hsum : ∀ a : α, Finset.sum Finset.univ (fun i : Fin T => x a i) = target) :
    ∃ i j : Fin T, i ≠ j ∧
      (Finset.sum Finset.univ
        (fun a : Fin T => bisWeightedCovarianceEntry mass x a a))
          / ((T - 1 : ℕ) : ℝ)
        ≤ (bisWeightedCovarianceEntry mass x i i
            + bisWeightedCovarianceEntry mass x j j
            - bisWeightedCovarianceEntry mass x i j
            - bisWeightedCovarianceEntry mass x j i) / 2 := by
  exact exists_pairwiseHalfContrast_ge_trace_div_of_rowColZero
    (fun i j => bisWeightedCovarianceEntry mass x i j) hT
    (bisWeightedCovarianceEntry_rowSum_eq_zero_of_fixedCoordSum
      mass x target hmass_total hsum)
    (bisWeightedCovarianceEntry_colSum_eq_zero_of_fixedCoordSum
      mass x target hmass_total hsum)

/--
Paper-facing fixed-count uniform-marginal binary covariance lower contrast.

For every binary `k`-out-of-`T` law with uniform coordinate mean `k/T`, some
off-diagonal centered pairwise contrast has covariance value at least the BIS
isotropic factor `k(T-k)/(T(T-1))`.  This is the finite covariance minimax
lower-bound seed before stating a supremum over all centered directions.
-/
theorem exists_weightedCovariancePairwiseHalfContrast_ge_k_factor_of_fixedCount_uniformMean_binary
    {α : Type} [Fintype α] {T k : ℕ}
    (mass : α → ℝ) (x : α → Fin T → ℝ) (hT : 2 ≤ T) (hk : k ≤ T)
    (hmass_total : Finset.sum Finset.univ mass = 1)
    (hsum : ∀ a : α, Finset.sum Finset.univ (fun i : Fin T => x a i) = (k : ℝ))
    (hbinary : ∀ (a : α) (i : Fin T), x a i * x a i = x a i)
    (hmean : ∀ i : Fin T, bisWeightedMeanCoord mass x i = (k : ℝ) / (T : ℝ)) :
    ∃ i j : Fin T, i ≠ j ∧
      ((k : ℝ) * ((T - k : ℕ) : ℝ))
          / ((T : ℝ) * ((T - 1 : ℕ) : ℝ))
        ≤ (bisWeightedCovarianceEntry mass x i i
            + bisWeightedCovarianceEntry mass x j j
            - bisWeightedCovarianceEntry mass x i j
            - bisWeightedCovarianceEntry mass x j i) / 2 := by
  rcases exists_weightedCovariancePairwiseHalfContrast_ge_trace_div_of_fixedCoordSum
      mass x (k : ℝ) hT hmass_total hsum with ⟨i, j, hij, hle⟩
  refine ⟨i, j, hij, ?_⟩
  have hTposNat : 0 < T := lt_of_lt_of_le (by norm_num) hT
  have hTpos : (0 : ℝ) < (T : ℝ) := by exact_mod_cast hTposNat
  have hTminus_ne : (((T - 1 : ℕ) : ℝ) ≠ 0) := by
    have hpos : 0 < T - 1 := Nat.sub_pos_of_lt hT
    exact_mod_cast (ne_of_gt hpos)
  have htrace := bisWeightedCovarianceTrace_eq_k_mul_T_sub_k_div_T_of_binary
    mass x hTposNat hk hmass_total hsum hbinary hmean
  have hfactor :
      ((k : ℝ) * ((T - k : ℕ) : ℝ))
          / ((T : ℝ) * ((T - 1 : ℕ) : ℝ))
        = (Finset.sum Finset.univ
            (fun a : Fin T => bisWeightedCovarianceEntry mass x a a))
          / ((T - 1 : ℕ) : ℝ) := by
    rw [htrace]
    field_simp [hTpos.ne', hTminus_ne]
  rw [hfactor]
  exact hle

/--
The generic weighted mean of the fixed-cardinality indicator law is the
previously defined one-coordinate marginal.
-/
theorem bisFixedCardUniformWeightedMeanCoord_eq_marginal
    {T k : ℕ} (i : Fin T) :
    bisWeightedMeanCoord
      (fun u : Finset (Fin T) => bisFixedCardUniformMass (Finset.univ : Finset (Fin T)) k u)
      (fun u i => if i ∈ u then (1 : ℝ) else 0) i
      = bisFixedCardUniformMarginal (Finset.univ : Finset (Fin T)) k i := by
  unfold bisWeightedMeanCoord bisFixedCardUniformMarginal
  symm
  refine Finset.sum_subset (by intro u hu; simp) ?_
  intro u _hu hnot
  unfold bisFixedCardUniformMass
  simp [hnot]

/--
The generic weighted second-moment entry of the fixed-cardinality indicator law
is the previously defined pair marginal.
-/
theorem bisFixedCardUniformWeightedSecondMomentEntry_eq_pairMarginal
    {T k : ℕ} (i j : Fin T) :
    bisWeightedSecondMomentEntry
      (fun u : Finset (Fin T) => bisFixedCardUniformMass (Finset.univ : Finset (Fin T)) k u)
      (fun u i => if i ∈ u then (1 : ℝ) else 0) i j
      = bisFixedCardUniformPairMarginal (Finset.univ : Finset (Fin T)) k i j := by
  unfold bisWeightedSecondMomentEntry bisFixedCardUniformPairMarginal
  calc
    (∑ a, bisFixedCardUniformMass Finset.univ k a * (if i ∈ a then (1 : ℝ) else 0) *
        (if j ∈ a then (1 : ℝ) else 0))
        = ∑ u ∈ (Finset.univ : Finset (Fin T)).powersetCard k,
            bisFixedCardUniformMass Finset.univ k u * (if i ∈ u then (1 : ℝ) else 0) *
              (if j ∈ u then (1 : ℝ) else 0) := by
          symm
          refine Finset.sum_subset (by intro u hu; simp) ?_
          intro u _hu hnot
          unfold bisFixedCardUniformMass
          simp [hnot]
    _ = ∑ u ∈ (Finset.univ : Finset (Fin T)).powersetCard k,
            bisFixedCardUniformMass Finset.univ k u *
              if i ∈ u ∧ j ∈ u then (1 : ℝ) else 0 := by
          refine Finset.sum_congr rfl ?_
          intro u _hu
          by_cases hi : i ∈ u <;> by_cases hj : j ∈ u <;> simp [hi, hj]

/--
The generic weighted covariance entry of the fixed-cardinality indicator law is
the fixed-cardinality covariance entry.
-/
theorem bisFixedCardUniformWeightedCovarianceEntry_eq_covarianceEntry
    {T k : ℕ} (i j : Fin T) :
    bisWeightedCovarianceEntry
      (fun u : Finset (Fin T) => bisFixedCardUniformMass (Finset.univ : Finset (Fin T)) k u)
      (fun u i => if i ∈ u then (1 : ℝ) else 0) i j
      = bisFixedCardUniformCovarianceEntry (Finset.univ : Finset (Fin T)) k i j := by
  unfold bisWeightedCovarianceEntry bisFixedCardUniformCovarianceEntry
  rw [bisFixedCardUniformWeightedSecondMomentEntry_eq_pairMarginal,
    bisFixedCardUniformWeightedMeanCoord_eq_marginal,
    bisFixedCardUniformWeightedMeanCoord_eq_marginal]

/--
High-noise covariance moment identity instantiated for the uniform
fixed-cardinality indicator law.
-/
theorem bisFixedCardUniformInnerCenteredSecondMoment_eq_covarianceQuadraticForm_fin
    {T k : ℕ} (w : Fin T → ℝ) :
    (Finset.sum Finset.univ fun u : Finset (Fin T) =>
        bisFixedCardUniformMass (Finset.univ : Finset (Fin T)) k u *
          (Finset.sum Finset.univ fun i : Fin T => (if i ∈ u then (1 : ℝ) else 0) * w i) ^ 2)
      - (Finset.sum Finset.univ fun i : Fin T =>
          bisWeightedMeanCoord
            (fun u : Finset (Fin T) =>
              bisFixedCardUniformMass (Finset.univ : Finset (Fin T)) k u)
            (fun u i => if i ∈ u then (1 : ℝ) else 0) i * w i) ^ 2
      = Finset.sum Finset.univ fun i : Fin T =>
          Finset.sum Finset.univ fun j : Fin T =>
            w i * w j *
              bisFixedCardUniformCovarianceEntry (Finset.univ : Finset (Fin T)) k i j := by
  rw [bisWeightedInnerCenteredSecondMoment_eq_covarianceQuadraticForm]
  refine Finset.sum_congr rfl ?_
  intro i _
  refine Finset.sum_congr rfl ?_
  intro j _
  rw [bisFixedCardUniformWeightedCovarianceEntry_eq_covarianceEntry]

/--
Zero-sum high-noise covariance moment for the uniform fixed-cardinality law.

This is the finite law-specific version of the paper's high-noise covariance
term after projecting away the all-ones direction.
-/
theorem bisFixedCardUniformInnerCenteredSecondMoment_zeroSum_fin
    {T k : ℕ} (hT : 2 ≤ T) (hk : k ≤ T) (w : Fin T → ℝ)
    (hsum : Finset.sum Finset.univ w = 0) :
    (Finset.sum Finset.univ fun u : Finset (Fin T) =>
        bisFixedCardUniformMass (Finset.univ : Finset (Fin T)) k u *
          (Finset.sum Finset.univ fun i : Fin T => (if i ∈ u then (1 : ℝ) else 0) * w i) ^ 2)
      - (Finset.sum Finset.univ fun i : Fin T =>
          bisWeightedMeanCoord
            (fun u : Finset (Fin T) =>
              bisFixedCardUniformMass (Finset.univ : Finset (Fin T)) k u)
            (fun u i => if i ∈ u then (1 : ℝ) else 0) i * w i) ^ 2
      = (((k : ℝ) * ((T - k : ℕ) : ℝ))
          / ((T : ℝ) * ((T - 1 : ℕ) : ℝ)))
          * Finset.sum Finset.univ (fun i : Fin T => w i ^ 2) := by
  rw [bisFixedCardUniformInnerCenteredSecondMoment_eq_covarianceQuadraticForm_fin]
  exact bisFixedCardUniformCovarianceQuadraticForm_zeroSum_fin hT hk w hsum

/--
Full centered-moment spectrum for the uniform fixed-cardinality law.

The covariance is the finite-population factor times projection away from the
all-ones direction:

```text
Var(<X,w>) = k(T-k)/(T(T-1)) * (||w||² - (sum_i w_i)² / T).
```

The zero-sum theorem is the special case where the projection term is just
`||w||²`; the all-ones theorem below is the special case where the projected
norm is zero.
-/
theorem bisFixedCardUniformInnerCenteredSecondMoment_centeredNorm_fin
    {T k : ℕ} (hT : 2 ≤ T) (hk : k ≤ T) (w : Fin T → ℝ) :
    (Finset.sum Finset.univ fun u : Finset (Fin T) =>
        bisFixedCardUniformMass (Finset.univ : Finset (Fin T)) k u *
          (Finset.sum Finset.univ fun i : Fin T => (if i ∈ u then (1 : ℝ) else 0) * w i) ^ 2)
      - (Finset.sum Finset.univ fun i : Fin T =>
          bisWeightedMeanCoord
            (fun u : Finset (Fin T) =>
              bisFixedCardUniformMass (Finset.univ : Finset (Fin T)) k u)
            (fun u i => if i ∈ u then (1 : ℝ) else 0) i * w i) ^ 2
      = (((k : ℝ) * ((T - k : ℕ) : ℝ))
          / ((T : ℝ) * ((T - 1 : ℕ) : ℝ)))
          * (Finset.sum Finset.univ (fun i : Fin T => w i ^ 2)
            - (Finset.sum Finset.univ w) ^ 2 / (T : ℝ)) := by
  rw [bisFixedCardUniformInnerCenteredSecondMoment_eq_covarianceQuadraticForm_fin]
  rw [bisFixedCardUniformCovarianceQuadraticForm_fin hT hk w]
  have hcoef := bisFixedCardUniformCovarianceDiagSubOffdiag_fin_spectrum
    (T := T) (k := k) hT
  have hTposNat : 0 < T := lt_of_lt_of_le (by norm_num) hT
  have hTpos : (0 : ℝ) < (T : ℝ) := by exact_mod_cast hTposNat
  have hTone : 1 ≤ T := le_trans (by norm_num) hT
  have hTminus1_ne : (T : ℝ) - 1 ≠ 0 := by
    have : (1 : ℝ) < (T : ℝ) := by exact_mod_cast hT
    linarith
  have hTminus1Nat_ne : (((T - 1 : ℕ) : ℝ) ≠ 0) := by
    rw [Nat.cast_sub hTone]
    simpa using hTminus1_ne
  rw [hcoef]
  field_simp [hTpos.ne', hTminus1Nat_ne]
  ring

/--
Projected-form version of the fixed-cardinality centered-moment spectrum.

This is the same theorem as
`bisFixedCardUniformInnerCenteredSecondMoment_centeredNorm_fin`, but stated
using the named zero-sum component `w_perp`.
-/
theorem bisFixedCardUniformInnerCenteredSecondMoment_zeroSumComponent_fin
    {T k : ℕ} (hT : 2 ≤ T) (hk : k ≤ T) (w : Fin T → ℝ) :
    (Finset.sum Finset.univ fun u : Finset (Fin T) =>
        bisFixedCardUniformMass (Finset.univ : Finset (Fin T)) k u *
          (Finset.sum Finset.univ fun i : Fin T => (if i ∈ u then (1 : ℝ) else 0) * w i) ^ 2)
      - (Finset.sum Finset.univ fun i : Fin T =>
          bisWeightedMeanCoord
            (fun u : Finset (Fin T) =>
              bisFixedCardUniformMass (Finset.univ : Finset (Fin T)) k u)
            (fun u i => if i ∈ u then (1 : ℝ) else 0) i * w i) ^ 2
      = (((k : ℝ) * ((T - k : ℕ) : ℝ))
          / ((T : ℝ) * ((T - 1 : ℕ) : ℝ)))
          * Finset.sum Finset.univ (fun i : Fin T => (bisZeroSumComponent w i) ^ 2) := by
  rw [bisFixedCardUniformInnerCenteredSecondMoment_centeredNorm_fin hT hk w]
  rw [bisZeroSumComponent_sqNorm_eq_centeredNorm (lt_of_lt_of_le (by norm_num) hT)]

/--
The first-order high-noise direction for uniform fixed-cardinality BIS is the
uniform marginal direction.
-/
theorem bisFixedCardUniformMeanInner_eq_uniform
    {T k : ℕ} (hk : k ≤ T) (w : Fin T → ℝ) :
    (Finset.sum Finset.univ fun i : Fin T =>
      bisWeightedMeanCoord
        (fun u : Finset (Fin T) =>
          bisFixedCardUniformMass (Finset.univ : Finset (Fin T)) k u)
        (fun u i => if i ∈ u then (1 : ℝ) else 0) i * w i)
      = ((k : ℝ) / (T : ℝ)) * Finset.sum Finset.univ w := by
  calc
    (Finset.sum Finset.univ fun i : Fin T =>
      bisWeightedMeanCoord
        (fun u : Finset (Fin T) =>
          bisFixedCardUniformMass (Finset.univ : Finset (Fin T)) k u)
        (fun u i => if i ∈ u then (1 : ℝ) else 0) i * w i)
      = Finset.sum Finset.univ fun i : Fin T => ((k : ℝ) / (T : ℝ)) * w i := by
        refine Finset.sum_congr rfl ?_
        intro i _
        rw [bisFixedCardUniformWeightedMeanCoord_eq_marginal]
        rw [bisFixedCardUniformMarginal_eq_div_card
          (base := (Finset.univ : Finset (Fin T))) (a := i) (ha := by simp) (k := k)
          (by simpa [Finset.card_univ] using hk)]
        simp [Finset.card_univ]
    _ = ((k : ℝ) / (T : ℝ)) * Finset.sum Finset.univ w := by
      rw [Finset.mul_sum]

/-- Uniform fixed-cardinality BIS has zero first-order term in zero-sum directions. -/
theorem bisFixedCardUniformMeanInner_zero_of_zeroSum
    {T k : ℕ} (hk : k ≤ T) (w : Fin T → ℝ)
    (hsum : Finset.sum Finset.univ w = 0) :
    (Finset.sum Finset.univ fun i : Fin T =>
      bisWeightedMeanCoord
        (fun u : Finset (Fin T) =>
          bisFixedCardUniformMass (Finset.univ : Finset (Fin T)) k u)
        (fun u i => if i ∈ u then (1 : ℝ) else 0) i * w i)
      = 0 := by
  rw [bisFixedCardUniformMeanInner_eq_uniform hk w, hsum, mul_zero]

/-- Weighted squared-norm mean for a finite participation-vector law. -/
noncomputable def bisWeightedSqNormMean {α : Type} [Fintype α] {T : ℕ}
    (mass : α → ℝ) (x : α → Fin T → ℝ) : ℝ :=
  Finset.sum Finset.univ fun a : α =>
    mass a * Finset.sum Finset.univ (fun i : Fin T => x a i ^ 2)

/--
Formal second-order coefficient in the high-noise log-likelihood expansion.

This is only the finite algebraic coefficient:

```text
(E[<X,w>^2] - <E X,w>^2 - E[||X||^2]) / 2.
```

The theorem stack here does not claim the analytic Taylor remainder.
-/
noncomputable def bisFormalHighNoiseLogSecondCoeff
    {α : Type} [Fintype α] {T : ℕ}
    (mass : α → ℝ) (x : α → Fin T → ℝ) (w : Fin T → ℝ) : ℝ :=
  (((Finset.sum Finset.univ fun a : α =>
        mass a * (Finset.sum Finset.univ fun i : Fin T => x a i * w i) ^ 2)
      - (Finset.sum Finset.univ fun i : Fin T => bisWeightedMeanCoord mass x i * w i) ^ 2)
      - bisWeightedSqNormMean mass x) / 2

/--
Generic coefficient rewrite: the centered inner-product term in the formal
second-order log coefficient is the covariance quadratic form.
-/
theorem bisFormalHighNoiseLogSecondCoeff_eq_covariance_sub_sqNormMean
    {α : Type} [Fintype α] {T : ℕ}
    (mass : α → ℝ) (x : α → Fin T → ℝ) (w : Fin T → ℝ) :
    bisFormalHighNoiseLogSecondCoeff mass x w
      = ((Finset.sum Finset.univ fun i : Fin T =>
          Finset.sum Finset.univ fun j : Fin T =>
            w i * w j * bisWeightedCovarianceEntry mass x i j)
          - bisWeightedSqNormMean mass x) / 2 := by
  unfold bisFormalHighNoiseLogSecondCoeff
  rw [bisWeightedInnerCenteredSecondMoment_eq_covarianceQuadraticForm]

/-- Squared norm of a subset indicator vector equals its cardinality. -/
theorem bisSubsetIndicator_sqNorm_eq_card {T : ℕ} (u : Finset (Fin T)) :
    Finset.sum Finset.univ (fun i : Fin T => (if i ∈ u then (1 : ℝ) else 0) ^ 2)
      = (u.card : ℝ) := by
  calc
    Finset.sum Finset.univ (fun i : Fin T => (if i ∈ u then (1 : ℝ) else 0) ^ 2)
        = Finset.sum Finset.univ (fun i : Fin T => if i ∈ u then (1 : ℝ) else 0) := by
          refine Finset.sum_congr rfl ?_
          intro i _
          by_cases h : i ∈ u <;> simp [h]
    _ = (u.card : ℝ) := by
          rw [← Finset.sum_filter]
          simp

/-- Sum of a subset indicator vector equals its cardinality. -/
theorem bisSubsetIndicator_sum_eq_card {T : ℕ} (u : Finset (Fin T)) :
    Finset.sum Finset.univ (fun i : Fin T => if i ∈ u then (1 : ℝ) else 0)
      = (u.card : ℝ) := by
  rw [← Finset.sum_filter]
  simp

/-- Uniform fixed-cardinality law has expected squared norm `k`. -/
theorem bisFixedCardUniformSqNormMean_eq
    {T k : ℕ} (hk : k ≤ T) :
    bisWeightedSqNormMean
      (fun u : Finset (Fin T) =>
        bisFixedCardUniformMass (Finset.univ : Finset (Fin T)) k u)
      (fun u i => if i ∈ u then (1 : ℝ) else 0)
      = (k : ℝ) := by
  unfold bisWeightedSqNormMean
  calc
    (Finset.sum Finset.univ fun a : Finset (Fin T) =>
        bisFixedCardUniformMass Finset.univ k a *
          Finset.sum Finset.univ (fun i : Fin T => (if i ∈ a then (1 : ℝ) else 0) ^ 2))
      = Finset.sum ((Finset.univ : Finset (Fin T)).powersetCard k)
          (fun a : Finset (Fin T) =>
            bisFixedCardUniformMass Finset.univ k a *
              Finset.sum Finset.univ
                (fun i : Fin T => (if i ∈ a then (1 : ℝ) else 0) ^ 2)) := by
          symm
          refine Finset.sum_subset (by intro u hu; simp) ?_
          intro u _hu hnot
          unfold bisFixedCardUniformMass
          simp [hnot]
    _ = Finset.sum ((Finset.univ : Finset (Fin T)).powersetCard k)
          (fun a : Finset (Fin T) =>
            bisFixedCardUniformMass Finset.univ k a * (a.card : ℝ)) := by
          refine Finset.sum_congr rfl ?_
          intro u _
          rw [bisSubsetIndicator_sqNorm_eq_card]
    _ = (k : ℝ) := by
          rw [bisFixedCardUniformMass_mean_count_eq
            (Finset.univ : Finset (Fin T)) k (by simpa [Finset.card_univ] using hk)]

/--
Formal second-order log coefficient for uniform fixed-cardinality BIS in
zero-sum directions.

This is the algebraic coefficient predicted by the high-noise Taylor expansion;
the Taylor remainder itself is not proved here.
-/
theorem bisFixedCardUniformFormalHighNoiseLogSecondCoeff_zeroSum
    {T k : ℕ} (hT : 2 ≤ T) (hk : k ≤ T) (w : Fin T → ℝ)
    (hsum : Finset.sum Finset.univ w = 0) :
    bisFormalHighNoiseLogSecondCoeff
      (fun u : Finset (Fin T) =>
        bisFixedCardUniformMass (Finset.univ : Finset (Fin T)) k u)
      (fun u i => if i ∈ u then (1 : ℝ) else 0) w
      = ((((k : ℝ) * ((T - k : ℕ) : ℝ))
          / ((T : ℝ) * ((T - 1 : ℕ) : ℝ)))
          * Finset.sum Finset.univ (fun i : Fin T => w i ^ 2) - (k : ℝ)) / 2 := by
  unfold bisFormalHighNoiseLogSecondCoeff
  rw [bisFixedCardUniformInnerCenteredSecondMoment_zeroSum_fin hT hk w hsum]
  rw [bisFixedCardUniformSqNormMean_eq hk]

/--
Formal second-order log coefficient for uniform fixed-cardinality BIS in an
arbitrary direction, written through the projected squared norm.

This is the coefficient form that pairs with the full centered covariance
spectrum:

```text
((k(T-k)/(T(T-1))) * (||w||² - (sum_i w_i)²/T) - k) / 2.
```
-/
theorem bisFixedCardUniformFormalHighNoiseLogSecondCoeff_centeredNorm
    {T k : ℕ} (hT : 2 ≤ T) (hk : k ≤ T) (w : Fin T → ℝ) :
    bisFormalHighNoiseLogSecondCoeff
      (fun u : Finset (Fin T) =>
        bisFixedCardUniformMass (Finset.univ : Finset (Fin T)) k u)
      (fun u i => if i ∈ u then (1 : ℝ) else 0) w
      = (((((k : ℝ) * ((T - k : ℕ) : ℝ))
          / ((T : ℝ) * ((T - 1 : ℕ) : ℝ)))
          * (Finset.sum Finset.univ (fun i : Fin T => w i ^ 2)
            - (Finset.sum Finset.univ w) ^ 2 / (T : ℝ)) - (k : ℝ)) / 2) := by
  unfold bisFormalHighNoiseLogSecondCoeff
  rw [bisFixedCardUniformInnerCenteredSecondMoment_centeredNorm_fin hT hk w]
  rw [bisFixedCardUniformSqNormMean_eq hk]

/--
Projected-form version of the formal high-noise second-order coefficient for
uniform fixed-cardinality BIS.
-/
theorem bisFixedCardUniformFormalHighNoiseLogSecondCoeff_zeroSumComponent
    {T k : ℕ} (hT : 2 ≤ T) (hk : k ≤ T) (w : Fin T → ℝ) :
    bisFormalHighNoiseLogSecondCoeff
      (fun u : Finset (Fin T) =>
        bisFixedCardUniformMass (Finset.univ : Finset (Fin T)) k u)
      (fun u i => if i ∈ u then (1 : ℝ) else 0) w
      = (((((k : ℝ) * ((T - k : ℕ) : ℝ))
          / ((T : ℝ) * ((T - 1 : ℕ) : ℝ)))
          * Finset.sum Finset.univ (fun i : Fin T => (bisZeroSumComponent w i) ^ 2)
          - (k : ℝ)) / 2) := by
  rw [bisFixedCardUniformFormalHighNoiseLogSecondCoeff_centeredNorm hT hk w]
  rw [bisZeroSumComponent_sqNorm_eq_centeredNorm (lt_of_lt_of_le (by norm_num) hT)]

/--
Derivative of the quadratic argument used in the scalar log Taylor core.

This is the first analytic ingredient for the high-noise expansion:
`1 + a τ + b τ²` has derivative `a` at `τ=0`.
-/
theorem bisQuadraticArg_hasDerivAt_zero (a b : ℝ) :
    HasDerivAt (fun τ : ℝ => 1 + a * τ + b * τ ^ 2) a 0 := by
  have h := (((hasDerivAt_const (0 : ℝ) (1 : ℝ)).add
      ((hasDerivAt_id (0 : ℝ)).const_mul a)).add
      (((hasDerivAt_id (0 : ℝ)).pow 2).const_mul b))
  convert! h using 1 <;> first | exact Subsingleton.elim _ _ | rfl | norm_num <;> ring

/--
First derivative at zero of `log(1 + aτ + bτ²)`.

This names the scalar Taylor fact that the first log coefficient is `a`.
-/
theorem bisLogQuadratic_hasDerivAt_zero (a b : ℝ) :
    HasDerivAt (fun τ : ℝ => Real.log (1 + a * τ + b * τ ^ 2)) a 0 := by
  have harg := bisQuadraticArg_hasDerivAt_zero a b
  have hpos : (0 : ℝ) < 1 + a * 0 + b * 0 ^ 2 := by
    norm_num
  convert! Real.hasDerivAt_log hpos.ne' |>.comp 0 harg using 1 <;>
    first | exact Subsingleton.elim _ _ | rfl | norm_num <;> ring

/--
Derivative at zero of the logarithmic derivative of `1 + aτ + bτ²`.

Together with `bisLogQuadratic_hasDerivAt_zero`, this is the scalar second-order
Taylor-coefficient fact: the second derivative of
`log(1 + aτ + bτ²)` at zero is `2b - a²`.
-/
theorem bisLogQuadraticDerivQuotient_hasDerivAt_zero (a b : ℝ) :
    HasDerivAt
      (fun τ : ℝ => (a + 2 * b * τ) / (1 + a * τ + b * τ ^ 2))
      (2 * b - a ^ 2) 0 := by
  have hn : HasDerivAt (fun τ : ℝ => a + 2 * b * τ) (2 * b) 0 := by
    convert! (hasDerivAt_const (0 : ℝ) a).add
      ((hasDerivAt_id (0 : ℝ)).const_mul (2 * b)) using 1 <;>
      first | exact Subsingleton.elim _ _ | rfl | norm_num <;> ring
  have hd := bisQuadraticArg_hasDerivAt_zero a b
  have hden : 1 + a * 0 + b * 0 ^ 2 ≠ 0 := by
    norm_num
  convert! hn.div hd hden using 1 <;>
    first | exact Subsingleton.elim _ _ | rfl | norm_num <;> ring

/--
Second derivative at zero of `log(1 + aτ + bτ²)`, stated as differentiability
of the derivative function.

The proof first identifies the derivative of the log quadratic with the
logarithmic-derivative quotient in a neighborhood of zero, where the quadratic
argument is nonzero, and then reuses
`bisLogQuadraticDerivQuotient_hasDerivAt_zero`.
-/
theorem bisLogQuadratic_deriv_hasDerivAt_zero (a b : ℝ) :
    HasDerivAt
      (fun τ : ℝ => deriv (fun s : ℝ => Real.log (1 + a * s + b * s ^ 2)) τ)
      (2 * b - a ^ 2) 0 := by
  let q : ℝ → ℝ := fun s => 1 + a * s + b * s ^ 2
  have hq0 : HasDerivAt q a 0 := by
    simpa [q] using bisQuadraticArg_hasDerivAt_zero a b
  have hne : ∀ᶠ τ : ℝ in 𝓝 (0 : ℝ), q τ ≠ 0 := by
    have hcont : ContinuousAt q 0 := hq0.continuousAt
    have hq0ne : q 0 ≠ 0 := by
      simp [q]
    exact hcont.eventually_ne hq0ne
  have hderiv_eq :
      (fun τ : ℝ => deriv (fun s : ℝ => Real.log (q s)) τ)
        =ᶠ[𝓝 (0 : ℝ)]
      (fun τ : ℝ => (a + 2 * b * τ) / q τ) := by
    filter_upwards [hne] with τ hτ
    have hqτ : HasDerivAt q (a + 2 * b * τ) τ := by
      have h := (((hasDerivAt_const (τ : ℝ) (1 : ℝ)).add
          ((hasDerivAt_id (τ : ℝ)).const_mul a)).add
          (((hasDerivAt_id (τ : ℝ)).pow 2).const_mul b))
      convert! h using 1 <;> norm_num <;> ring
    have hlogτ :
        HasDerivAt (fun s : ℝ => Real.log (q s))
          ((a + 2 * b * τ) / q τ) τ := by
      simpa [Function.comp_def, div_eq_mul_inv, mul_comm, mul_left_comm, mul_assoc] using
        (Real.hasDerivAt_log hτ).comp τ hqτ
    exact hlogτ.deriv
  have hquot :
      HasDerivAt (fun τ : ℝ => (a + 2 * b * τ) / q τ)
        (2 * b - a ^ 2) 0 := by
    simpa [q] using bisLogQuadraticDerivQuotient_hasDerivAt_zero a b
  have hmain := hquot.congr_of_eventuallyEq hderiv_eq
  simpa [q] using hmain

/--
Local `C²` smoothness at zero of the scalar log-quadratic core.

The quadratic argument equals `1` at zero, so the logarithm is smooth in a
neighborhood of zero.  This is the Mathlib Taylor-hypothesis surface needed for
a future remainder theorem.
-/
theorem bisLogQuadratic_contDiffAt_two_zero (a b : ℝ) :
    ContDiffAt ℝ 2 (fun s : ℝ => Real.log (1 + a * s + b * s ^ 2)) 0 := by
  fun_prop (disch := norm_num)

/--
The degree-two Taylor polynomial of `log(1 + aτ + bτ²)` at zero.

This records the scalar polynomial part needed by the high-noise expansion:
the constant term is zero, the linear coefficient is `a`, and the quadratic
coefficient is `(2b - a²)/2`.
-/
theorem bisLogQuadratic_taylorWithinEval_two_univ_zero (a b τ : ℝ) :
    taylorWithinEval
        (fun s : ℝ => Real.log (1 + a * s + b * s ^ 2)) 2 Set.univ 0 τ
      = a * τ + ((2 * b - a ^ 2) / 2) * τ ^ 2 := by
  have hderiv0 :
      deriv (fun s : ℝ => Real.log (1 + a * s + b * s ^ 2)) 0 = a :=
    (bisLogQuadratic_hasDerivAt_zero a b).deriv
  have hderiv2 :
      deriv (fun τ : ℝ =>
          deriv (fun s : ℝ => Real.log (1 + a * s + b * s ^ 2)) τ) 0
        = 2 * b - a ^ 2 :=
    (bisLogQuadratic_deriv_hasDerivAt_zero a b).deriv
  rw [taylor_within_apply]
  rw [Finset.sum_range_succ]
  simp only [Finset.sum_range_succ, Finset.sum_range_zero]
  simp [iteratedDerivWithin_univ, iteratedDeriv_zero, iteratedDeriv_succ,
    hderiv0, hderiv2]
  ring

/--
The degree-two Taylor polynomial of `log(1 + aτ + bτ²)` at zero, restricted to
a nondegenerate closed interval containing zero.

This is the interval version needed to rewrite Mathlib's local Taylor theorem
into the explicit coefficient form used by the high-noise expansion.
-/
theorem bisLogQuadratic_taylorWithinEval_two_Icc_zero
    (a b l u τ : ℝ) (hlu : l < u) (h0 : 0 ∈ Set.Icc l u) :
    taylorWithinEval
        (fun s : ℝ => Real.log (1 + a * s + b * s ^ 2)) 2 (Set.Icc l u) 0 τ
      = a * τ + ((2 * b - a ^ 2) / 2) * τ ^ 2 := by
  let f : ℝ → ℝ := fun s => Real.log (1 + a * s + b * s ^ 2)
  have hcd2 : ContDiffAt ℝ 2 f 0 := by
    simpa [f] using bisLogQuadratic_contDiffAt_two_zero a b
  have hderiv0 : deriv f 0 = a := by
    simpa [f] using (bisLogQuadratic_hasDerivAt_zero a b).deriv
  have hderiv2 : deriv (deriv f) 0 = 2 * b - a ^ 2 := by
    simpa [f] using (bisLogQuadratic_deriv_hasDerivAt_zero a b).deriv
  have hiter0 :
      iteratedDerivWithin 0 f (Set.Icc l u) 0 = iteratedDeriv 0 f 0 := by
    exact iteratedDerivWithin_eq_iteratedDeriv
      (uniqueDiffOn_Icc hlu) (hcd2.of_le (by norm_num)) h0
  have hiter1 :
      iteratedDerivWithin 1 f (Set.Icc l u) 0 = iteratedDeriv 1 f 0 := by
    exact iteratedDerivWithin_eq_iteratedDeriv
      (uniqueDiffOn_Icc hlu) (hcd2.of_le (by norm_num)) h0
  have hiter2 :
      iteratedDerivWithin 2 f (Set.Icc l u) 0 = iteratedDeriv 2 f 0 := by
    exact iteratedDerivWithin_eq_iteratedDeriv (uniqueDiffOn_Icc hlu) hcd2 h0
  rw [taylor_within_apply]
  rw [Finset.sum_range_succ]
  simp only [Finset.sum_range_succ, Finset.sum_range_zero]
  simp [f, hiter0, hiter1, hiter2, iteratedDeriv_zero, iteratedDeriv_succ,
    hderiv0, hderiv2]
  ring

/--
Local Taylor little-o remainder for the scalar log-quadratic core.

Lean chooses a closed interval around zero on which the logarithmic quadratic is
`C²`, then applies Mathlib's Taylor theorem on that interval.  The polynomial is
stated with `taylorWithinEval` on the chosen interval; the separate theorem
`bisLogQuadratic_taylorWithinEval_two_univ_zero` records the explicit
degree-two polynomial coefficients.
-/
theorem bisLogQuadratic_exists_taylor_isLittleO_two (a b : ℝ) :
    ∃ l u : ℝ,
      0 ∈ Set.Icc l u ∧ Set.Icc l u ∈ 𝓝 (0 : ℝ) ∧
        (fun τ : ℝ =>
            Real.log (1 + a * τ + b * τ ^ 2)
              - taylorWithinEval
                  (fun s : ℝ => Real.log (1 + a * s + b * s ^ 2)) 2
                  (Set.Icc l u) 0 τ)
          =o[𝓝[Set.Icc l u] (0 : ℝ)] (fun τ : ℝ => (τ - 0) ^ 2) := by
  let f : ℝ → ℝ := fun s => Real.log (1 + a * s + b * s ^ 2)
  have hfAt : ContDiffAt ℝ 2 f 0 := by
    simpa [f] using bisLogQuadratic_contDiffAt_two_zero a b
  rcases hfAt.contDiffOn (m := (2 : WithTop ℕ∞)) le_rfl (by simp) with
    ⟨s, hs_mem, hs_cd⟩
  rcases exists_Icc_mem_subset_of_mem_nhds hs_mem with ⟨l, u, hmem, hnhds, hsub⟩
  refine ⟨l, u, hmem, hnhds, ?_⟩
  have hcd : ContDiffOn ℝ 2 f (Set.Icc l u) := hs_cd.mono hsub
  simpa [f] using taylor_isLittleO (convex_Icc l u) hmem hcd

/--
Local Taylor little-o remainder in explicit coefficient form.

There is a closed interval around zero on which
`log(1 + aτ + bτ²) - (aτ + ((2b-a²)/2)τ²)` is `o(τ²)` at zero within the
interval.
-/
theorem bisLogQuadratic_exists_explicit_taylor_isLittleO_two (a b : ℝ) :
    ∃ l u : ℝ,
      0 ∈ Set.Icc l u ∧ Set.Icc l u ∈ 𝓝 (0 : ℝ) ∧
        (fun τ : ℝ =>
            Real.log (1 + a * τ + b * τ ^ 2)
              - (a * τ + ((2 * b - a ^ 2) / 2) * τ ^ 2))
          =o[𝓝[Set.Icc l u] (0 : ℝ)] (fun τ : ℝ => (τ - 0) ^ 2) := by
  rcases bisLogQuadratic_exists_taylor_isLittleO_two a b with
    ⟨l, u, h0, hnhds, hrem⟩
  have hioo : (0 : ℝ) ∈ Set.Ioo l u := Icc_mem_nhds_iff.mp hnhds
  have hpoly : ∀ τ : ℝ,
      taylorWithinEval
          (fun s : ℝ => Real.log (1 + a * s + b * s ^ 2)) 2
          (Set.Icc l u) 0 τ
        = a * τ + ((2 * b - a ^ 2) / 2) * τ ^ 2 := by
    intro τ
    exact bisLogQuadratic_taylorWithinEval_two_Icc_zero
      a b l u τ (lt_trans hioo.1 hioo.2) h0
  refine ⟨l, u, h0, hnhds, ?_⟩
  exact hrem.congr_left (fun τ => by rw [hpoly τ])

/--
Finite normalized mixtures of quadratic log arguments inherit the scalar
Taylor remainder.

If the component masses sum to one, then the mixture

```text
∑ x, mass x * (1 + A x τ + B x τ²)
```

is exactly `1 + aτ + bτ²`, where `a` and `b` are the weighted sums of `A` and
`B`.  This theorem packages that algebra with the scalar explicit Taylor
remainder.
-/
theorem bisLogFiniteQuadraticMixture_exists_explicit_taylor_isLittleO_two
    {α : Type} [Fintype α]
    (mass A B : α → ℝ)
    (hmass : Finset.sum Finset.univ mass = 1) :
    ∃ l u : ℝ,
      0 ∈ Set.Icc l u ∧ Set.Icc l u ∈ 𝓝 (0 : ℝ) ∧
        (fun τ : ℝ =>
            Real.log (Finset.sum Finset.univ fun x : α =>
              mass x * (1 + A x * τ + B x * τ ^ 2))
              - ((Finset.sum Finset.univ fun x : α => mass x * A x) * τ
                + ((2 * (Finset.sum Finset.univ fun x : α => mass x * B x)
                    - (Finset.sum Finset.univ fun x : α => mass x * A x) ^ 2) / 2)
                  * τ ^ 2))
          =o[𝓝[Set.Icc l u] (0 : ℝ)] (fun τ : ℝ => (τ - 0) ^ 2) := by
  let a : ℝ := Finset.sum Finset.univ fun x : α => mass x * A x
  let b : ℝ := Finset.sum Finset.univ fun x : α => mass x * B x
  rcases bisLogQuadratic_exists_explicit_taylor_isLittleO_two a b with
    ⟨l, u, h0, hnhds, hrem⟩
  refine ⟨l, u, h0, hnhds, ?_⟩
  have hinside : ∀ τ : ℝ,
      Finset.sum Finset.univ (fun x : α =>
          mass x * (1 + A x * τ + B x * τ ^ 2))
        = 1 + a * τ + b * τ ^ 2 := by
    intro τ
    calc
      Finset.sum Finset.univ (fun x : α =>
          mass x * (1 + A x * τ + B x * τ ^ 2))
          = Finset.sum Finset.univ (fun x : α =>
              mass x + (mass x * A x) * τ + (mass x * B x) * τ ^ 2) := by
              refine Finset.sum_congr rfl ?_
              intro x _
              ring
      _ = Finset.sum Finset.univ mass + a * τ + b * τ ^ 2 := by
              rw [Finset.sum_add_distrib, Finset.sum_add_distrib,
                Finset.sum_mul, Finset.sum_mul]
      _ = 1 + a * τ + b * τ ^ 2 := by
              rw [hmass]
  exact hrem.congr_left (fun τ => by simp [a, b, hinside τ])

/--
Derivative of the no-constant quadratic exponent used by Gaussian
likelihood-ratio factors.
-/
theorem bisQuadraticNoConstArg_hasDerivAt (a c τ : ℝ) :
    HasDerivAt (fun s : ℝ => a * s + c * s ^ 2) (a + 2 * c * τ) τ := by
  have h := (((hasDerivAt_id (τ : ℝ)).const_mul a).add
    (((hasDerivAt_id (τ : ℝ)).pow 2).const_mul c))
  convert! h using 1 <;> norm_num <;> ring

/-- First derivative at zero of `exp(aτ + cτ²)`. -/
theorem bisExpQuadratic_hasDerivAt_zero (a c : ℝ) :
    HasDerivAt (fun τ : ℝ => Real.exp (a * τ + c * τ ^ 2)) a 0 := by
  have harg := bisQuadraticNoConstArg_hasDerivAt a c 0
  have hcomp := (Real.hasDerivAt_exp (a * 0 + c * 0 ^ 2)).comp 0 harg
  convert! hcomp using 1 <;> norm_num <;> ring

/--
Derivative at zero of the derivative-function model for `exp(aτ + cτ²)`.

The derivative of `exp(aτ + cτ²)` is
`(a + 2cτ) * exp(aτ + cτ²)`, whose derivative at zero is `a² + 2c`.
-/
theorem bisExpQuadraticDerivModel_hasDerivAt_zero (a c : ℝ) :
    HasDerivAt
      (fun τ : ℝ => (a + 2 * c * τ) * Real.exp (a * τ + c * τ ^ 2))
      (a ^ 2 + 2 * c) 0 := by
  have hn : HasDerivAt (fun τ : ℝ => a + 2 * c * τ) (2 * c) 0 := by
    convert! (hasDerivAt_const (0 : ℝ) a).add
      ((hasDerivAt_id (0 : ℝ)).const_mul (2 * c)) using 1 <;> norm_num <;> ring
  have he := bisExpQuadratic_hasDerivAt_zero a c
  have hmul := hn.mul he
  convert! hmul using 1 <;> norm_num <;> ring

/-- Second derivative at zero of `exp(aτ + cτ²)`, as a derivative-function fact. -/
theorem bisExpQuadratic_deriv_hasDerivAt_zero (a c : ℝ) :
    HasDerivAt
      (fun τ : ℝ => deriv (fun s : ℝ => Real.exp (a * s + c * s ^ 2)) τ)
      (a ^ 2 + 2 * c) 0 := by
  have hderiv_eq :
      (fun τ : ℝ => deriv (fun s : ℝ => Real.exp (a * s + c * s ^ 2)) τ)
        =ᶠ[𝓝 (0 : ℝ)]
      (fun τ : ℝ => (a + 2 * c * τ) * Real.exp (a * τ + c * τ ^ 2)) := by
    filter_upwards [Filter.Eventually.of_forall (fun τ : ℝ => True.intro)] with τ _
    have harg := bisQuadraticNoConstArg_hasDerivAt a c τ
    have hexp :
        HasDerivAt (fun s : ℝ => Real.exp (a * s + c * s ^ 2))
          ((a + 2 * c * τ) * Real.exp (a * τ + c * τ ^ 2)) τ := by
      convert! (Real.hasDerivAt_exp (a * τ + c * τ ^ 2)).comp τ harg using 1 <;>
        norm_num <;> ring
    exact hexp.deriv
  exact (bisExpQuadraticDerivModel_hasDerivAt_zero a c).congr_of_eventuallyEq hderiv_eq

/-- Local `C²` smoothness at zero of `exp(aτ + cτ²)`. -/
theorem bisExpQuadratic_contDiffAt_two_zero (a c : ℝ) :
    ContDiffAt ℝ 2 (fun s : ℝ => Real.exp (a * s + c * s ^ 2)) 0 := by
  fun_prop

/-- The degree-two Taylor polynomial of `exp(aτ + cτ²)` at zero. -/
theorem bisExpQuadratic_taylorWithinEval_two_univ_zero (a c τ : ℝ) :
    taylorWithinEval
        (fun s : ℝ => Real.exp (a * s + c * s ^ 2)) 2 Set.univ 0 τ
      = 1 + a * τ + ((a ^ 2 + 2 * c) / 2) * τ ^ 2 := by
  have hderiv0 :
      deriv (fun s : ℝ => Real.exp (a * s + c * s ^ 2)) 0 = a :=
    (bisExpQuadratic_hasDerivAt_zero a c).deriv
  have hderiv2 :
      deriv (fun τ : ℝ =>
          deriv (fun s : ℝ => Real.exp (a * s + c * s ^ 2)) τ) 0
        = a ^ 2 + 2 * c :=
    (bisExpQuadratic_deriv_hasDerivAt_zero a c).deriv
  rw [taylor_within_apply]
  rw [Finset.sum_range_succ]
  simp only [Finset.sum_range_succ, Finset.sum_range_zero]
  simp [iteratedDerivWithin_univ, iteratedDeriv_zero, iteratedDeriv_succ,
    hderiv0, hderiv2]
  ring

/-- Interval-restricted degree-two Taylor polynomial of `exp(aτ + cτ²)` at zero. -/
theorem bisExpQuadratic_taylorWithinEval_two_Icc_zero
    (a c l u τ : ℝ) (hlu : l < u) (h0 : 0 ∈ Set.Icc l u) :
    taylorWithinEval
        (fun s : ℝ => Real.exp (a * s + c * s ^ 2)) 2 (Set.Icc l u) 0 τ
      = 1 + a * τ + ((a ^ 2 + 2 * c) / 2) * τ ^ 2 := by
  let f : ℝ → ℝ := fun s => Real.exp (a * s + c * s ^ 2)
  have hcd2 : ContDiffAt ℝ 2 f 0 := by
    simpa [f] using bisExpQuadratic_contDiffAt_two_zero a c
  have hderiv0 : deriv f 0 = a := by
    simpa [f] using (bisExpQuadratic_hasDerivAt_zero a c).deriv
  have hderiv2 : deriv (deriv f) 0 = a ^ 2 + 2 * c := by
    simpa [f] using (bisExpQuadratic_deriv_hasDerivAt_zero a c).deriv
  have hiter0 :
      iteratedDerivWithin 0 f (Set.Icc l u) 0 = iteratedDeriv 0 f 0 := by
    exact iteratedDerivWithin_eq_iteratedDeriv
      (uniqueDiffOn_Icc hlu) (hcd2.of_le (by norm_num)) h0
  have hiter1 :
      iteratedDerivWithin 1 f (Set.Icc l u) 0 = iteratedDeriv 1 f 0 := by
    exact iteratedDerivWithin_eq_iteratedDeriv
      (uniqueDiffOn_Icc hlu) (hcd2.of_le (by norm_num)) h0
  have hiter2 :
      iteratedDerivWithin 2 f (Set.Icc l u) 0 = iteratedDeriv 2 f 0 := by
    exact iteratedDerivWithin_eq_iteratedDeriv (uniqueDiffOn_Icc hlu) hcd2 h0
  rw [taylor_within_apply]
  rw [Finset.sum_range_succ]
  simp only [Finset.sum_range_succ, Finset.sum_range_zero]
  simp [f, hiter0, hiter1, hiter2, iteratedDeriv_zero, iteratedDeriv_succ,
    hderiv0, hderiv2]
  ring

/-- Local explicit Taylor little-o remainder for `exp(aτ + cτ²)`. -/
theorem bisExpQuadratic_exists_explicit_taylor_isLittleO_two (a c : ℝ) :
    ∃ l u : ℝ,
      0 ∈ Set.Icc l u ∧ Set.Icc l u ∈ 𝓝 (0 : ℝ) ∧
        (fun τ : ℝ =>
            Real.exp (a * τ + c * τ ^ 2)
              - (1 + a * τ + ((a ^ 2 + 2 * c) / 2) * τ ^ 2))
          =o[𝓝[Set.Icc l u] (0 : ℝ)] (fun τ : ℝ => (τ - 0) ^ 2) := by
  let f : ℝ → ℝ := fun s => Real.exp (a * s + c * s ^ 2)
  have hfAt : ContDiffAt ℝ 2 f 0 := by
    simpa [f] using bisExpQuadratic_contDiffAt_two_zero a c
  rcases hfAt.contDiffOn (m := (2 : WithTop ℕ∞)) le_rfl (by simp) with
    ⟨s, hs_mem, hs_cd⟩
  rcases exists_Icc_mem_subset_of_mem_nhds hs_mem with ⟨l, u, h0, hnhds, hsub⟩
  have hioo : (0 : ℝ) ∈ Set.Ioo l u := Icc_mem_nhds_iff.mp hnhds
  have hcd : ContDiffOn ℝ 2 f (Set.Icc l u) := hs_cd.mono hsub
  have hrem := taylor_isLittleO (convex_Icc l u) h0 hcd
  have hpoly : ∀ τ : ℝ,
      taylorWithinEval f 2 (Set.Icc l u) 0 τ
        = 1 + a * τ + ((a ^ 2 + 2 * c) / 2) * τ ^ 2 := by
    intro τ
    simpa [f] using bisExpQuadratic_taylorWithinEval_two_Icc_zero
      a c l u τ (lt_trans hioo.1 hioo.2) h0
  refine ⟨l, u, h0, hnhds, ?_⟩
  exact hrem.congr_left (fun τ => by rw [hpoly τ])

/--
First derivative at zero of a normalized finite log-sum-exp quadratic mixture.
-/
theorem bisLogFiniteExpQuadraticMixture_hasDerivAt_zero
    {α : Type} [Fintype α]
    (mass A C : α → ℝ)
    (hmass : Finset.sum Finset.univ mass = 1) :
    HasDerivAt
      (fun τ : ℝ => Real.log (Finset.sum Finset.univ fun x : α =>
        mass x * Real.exp (A x * τ + C x * τ ^ 2)))
      (Finset.sum Finset.univ fun x : α => mass x * A x) 0 := by
  let g : ℝ → ℝ := fun τ =>
    Finset.sum Finset.univ fun x : α =>
      mass x * Real.exp (A x * τ + C x * τ ^ 2)
  let a : ℝ := Finset.sum Finset.univ fun x : α => mass x * A x
  have hg0 : HasDerivAt g a 0 := by
    simpa [g, a] using (HasDerivAt.fun_sum (u := (Finset.univ : Finset α))
      (A := fun x : α => fun τ : ℝ =>
        mass x * Real.exp (A x * τ + C x * τ ^ 2))
      (A' := fun x : α => mass x * A x)
      (fun x _hx => (bisExpQuadratic_hasDerivAt_zero (A x) (C x)).const_mul (mass x)))
  have hg0ne : g 0 ≠ 0 := by
    simp [g, hmass]
  have hlog : HasDerivAt (fun τ : ℝ => Real.log (g τ)) (a / g 0) 0 := by
    simpa [Function.comp_def, div_eq_mul_inv, mul_comm, mul_left_comm, mul_assoc] using
      (Real.hasDerivAt_log hg0ne).comp 0 hg0
  convert hlog using 1
  · simp [g, a, hmass]

/--
Second derivative at zero of a normalized finite log-sum-exp quadratic mixture.

For normalized masses, the second derivative of
`log(∑ mass x * exp(A x τ + C x τ²))` at zero is

```text
∑ mass x * (A x)^2 + 2∑ mass x * C x - (∑ mass x * A x)^2.
```

This is the analytic high-noise bridge from exponential-quadratic Gaussian
components to covariance-style finite algebra.
-/
theorem bisLogFiniteExpQuadraticMixture_deriv_hasDerivAt_zero
    {α : Type} [Fintype α]
    (mass A C : α → ℝ)
    (hmass : Finset.sum Finset.univ mass = 1) :
    HasDerivAt
      (fun τ : ℝ => deriv (fun s : ℝ => Real.log (Finset.sum Finset.univ fun x : α =>
        mass x * Real.exp (A x * s + C x * s ^ 2))) τ)
      ((Finset.sum Finset.univ fun x : α => mass x * (A x ^ 2 + 2 * C x))
        - (Finset.sum Finset.univ fun x : α => mass x * A x) ^ 2) 0 := by
  let g : ℝ → ℝ := fun τ =>
    Finset.sum Finset.univ fun x : α =>
      mass x * Real.exp (A x * τ + C x * τ ^ 2)
  let m : ℝ → ℝ := fun τ =>
    Finset.sum Finset.univ fun x : α =>
      mass x * ((A x + 2 * C x * τ) * Real.exp (A x * τ + C x * τ ^ 2))
  let a : ℝ := Finset.sum Finset.univ fun x : α => mass x * A x
  let e2 : ℝ := Finset.sum Finset.univ fun x : α => mass x * (A x ^ 2 + 2 * C x)
  have hg0 : HasDerivAt g a 0 := by
    simpa [g, a] using (HasDerivAt.fun_sum (u := (Finset.univ : Finset α))
      (A := fun x : α => fun τ : ℝ =>
        mass x * Real.exp (A x * τ + C x * τ ^ 2))
      (A' := fun x : α => mass x * A x)
      (fun x _hx => (bisExpQuadratic_hasDerivAt_zero (A x) (C x)).const_mul (mass x)))
  have hm0 : HasDerivAt m e2 0 := by
    simpa [m, e2] using (HasDerivAt.fun_sum (u := (Finset.univ : Finset α))
      (A := fun x : α => fun τ : ℝ =>
        mass x * ((A x + 2 * C x * τ) * Real.exp (A x * τ + C x * τ ^ 2)))
      (A' := fun x : α => mass x * (A x ^ 2 + 2 * C x))
      (fun x _hx =>
        (bisExpQuadraticDerivModel_hasDerivAt_zero (A x) (C x)).const_mul (mass x)))
  have hg0val : g 0 = 1 := by
    simp [g, hmass]
  have hne : ∀ᶠ τ : ℝ in 𝓝 (0 : ℝ), g τ ≠ 0 := by
    have hcont : ContinuousAt g 0 := hg0.continuousAt
    have hg0ne : g 0 ≠ 0 := by simp [hg0val]
    exact hcont.eventually_ne hg0ne
  have hlog_deriv_eq :
      (fun τ : ℝ => deriv (fun s : ℝ => Real.log (g s)) τ)
        =ᶠ[𝓝 (0 : ℝ)]
      (fun τ : ℝ => m τ / g τ) := by
    filter_upwards [hne] with τ hτ
    have hgτ : HasDerivAt g (m τ) τ := by
      simpa [g, m] using (HasDerivAt.fun_sum (u := (Finset.univ : Finset α))
        (A := fun x : α => fun s : ℝ =>
          mass x * Real.exp (A x * s + C x * s ^ 2))
        (A' := fun x : α =>
          mass x * ((A x + 2 * C x * τ) * Real.exp (A x * τ + C x * τ ^ 2)))
        (fun x _hx => by
          have harg := bisQuadraticNoConstArg_hasDerivAt (A x) (C x) τ
          have hexp :
              HasDerivAt (fun s : ℝ => Real.exp (A x * s + C x * s ^ 2))
                ((A x + 2 * C x * τ) * Real.exp (A x * τ + C x * τ ^ 2)) τ := by
            convert! (Real.hasDerivAt_exp (A x * τ + C x * τ ^ 2)).comp τ harg using 1 <;>
              norm_num <;> ring
          exact hexp.const_mul (mass x)))
    have hlogτ : HasDerivAt (fun s : ℝ => Real.log (g s)) (m τ / g τ) τ := by
      simpa [Function.comp_def, div_eq_mul_inv, mul_comm, mul_left_comm, mul_assoc] using
        (Real.hasDerivAt_log hτ).comp τ hgτ
    exact hlogτ.deriv
  have hquot : HasDerivAt (fun τ : ℝ => m τ / g τ) (e2 - a ^ 2) 0 := by
    have hden : g 0 ≠ 0 := by simp [hg0val]
    have h := hm0.div hg0 hden
    convert! h using 1 <;> norm_num [m, g, a, e2, hmass] <;> ring
  have hmain := hquot.congr_of_eventuallyEq hlog_deriv_eq
  simpa [g, a, e2] using hmain

/-- Local `C²` smoothness at zero of a normalized finite log-sum-exp quadratic mixture. -/
theorem bisLogFiniteExpQuadraticMixture_contDiffAt_two_zero
    {α : Type} [Fintype α]
    (mass A C : α → ℝ)
    (hmass : Finset.sum Finset.univ mass = 1) :
    ContDiffAt ℝ 2
      (fun τ : ℝ => Real.log (Finset.sum Finset.univ fun x : α =>
        mass x * Real.exp (A x * τ + C x * τ ^ 2))) 0 := by
  fun_prop (disch := simp [hmass])

/-- Degree-two Taylor polynomial of a normalized finite log-sum-exp quadratic mixture. -/
theorem bisLogFiniteExpQuadraticMixture_taylorWithinEval_two_univ_zero
    {α : Type} [Fintype α]
    (mass A C : α → ℝ)
    (hmass : Finset.sum Finset.univ mass = 1) (τ : ℝ) :
    taylorWithinEval
      (fun s : ℝ => Real.log (Finset.sum Finset.univ fun x : α =>
        mass x * Real.exp (A x * s + C x * s ^ 2))) 2 Set.univ 0 τ
      = (Finset.sum Finset.univ fun x : α => mass x * A x) * τ
        + (((Finset.sum Finset.univ fun x : α => mass x * (A x ^ 2 + 2 * C x))
          - (Finset.sum Finset.univ fun x : α => mass x * A x) ^ 2) / 2) * τ ^ 2 := by
  have hderiv0 :
      deriv (fun s : ℝ => Real.log (Finset.sum Finset.univ fun x : α =>
        mass x * Real.exp (A x * s + C x * s ^ 2))) 0
      = (Finset.sum Finset.univ fun x : α => mass x * A x) :=
    (bisLogFiniteExpQuadraticMixture_hasDerivAt_zero mass A C hmass).deriv
  have hderiv2 :
      deriv (fun τ : ℝ => deriv (fun s : ℝ =>
        Real.log (Finset.sum Finset.univ fun x : α =>
          mass x * Real.exp (A x * s + C x * s ^ 2))) τ) 0
      = ((Finset.sum Finset.univ fun x : α => mass x * (A x ^ 2 + 2 * C x))
        - (Finset.sum Finset.univ fun x : α => mass x * A x) ^ 2) :=
    (bisLogFiniteExpQuadraticMixture_deriv_hasDerivAt_zero mass A C hmass).deriv
  rw [taylor_within_apply]
  rw [Finset.sum_range_succ]
  simp only [Finset.sum_range_succ, Finset.sum_range_zero]
  simp [iteratedDerivWithin_univ, iteratedDeriv_zero, iteratedDeriv_succ,
    hderiv0, hderiv2]
  simp [hmass]
  ring_nf

/--
Interval-restricted degree-two Taylor polynomial of a normalized finite
log-sum-exp quadratic mixture.
-/
theorem bisLogFiniteExpQuadraticMixture_taylorWithinEval_two_Icc_zero
    {α : Type} [Fintype α]
    (mass A C : α → ℝ)
    (hmass : Finset.sum Finset.univ mass = 1)
    (l u τ : ℝ) (hlu : l < u) (h0 : 0 ∈ Set.Icc l u) :
    taylorWithinEval
      (fun s : ℝ => Real.log (Finset.sum Finset.univ fun x : α =>
        mass x * Real.exp (A x * s + C x * s ^ 2))) 2 (Set.Icc l u) 0 τ
      = (Finset.sum Finset.univ fun x : α => mass x * A x) * τ
        + (((Finset.sum Finset.univ fun x : α => mass x * (A x ^ 2 + 2 * C x))
          - (Finset.sum Finset.univ fun x : α => mass x * A x) ^ 2) / 2) * τ ^ 2 := by
  let f : ℝ → ℝ := fun s =>
    Real.log (Finset.sum Finset.univ fun x : α =>
      mass x * Real.exp (A x * s + C x * s ^ 2))
  have hcd2 : ContDiffAt ℝ 2 f 0 := by
    simpa [f] using bisLogFiniteExpQuadraticMixture_contDiffAt_two_zero mass A C hmass
  have hderiv0 :
      deriv f 0 = (Finset.sum Finset.univ fun x : α => mass x * A x) := by
    simpa [f] using (bisLogFiniteExpQuadraticMixture_hasDerivAt_zero mass A C hmass).deriv
  have hderiv2 :
      deriv (deriv f) 0
        = ((Finset.sum Finset.univ fun x : α => mass x * (A x ^ 2 + 2 * C x))
          - (Finset.sum Finset.univ fun x : α => mass x * A x) ^ 2) := by
    simpa [f] using
      (bisLogFiniteExpQuadraticMixture_deriv_hasDerivAt_zero mass A C hmass).deriv
  have hiter0 : iteratedDerivWithin 0 f (Set.Icc l u) 0 = iteratedDeriv 0 f 0 := by
    exact iteratedDerivWithin_eq_iteratedDeriv
      (uniqueDiffOn_Icc hlu) (hcd2.of_le (by norm_num)) h0
  have hiter1 : iteratedDerivWithin 1 f (Set.Icc l u) 0 = iteratedDeriv 1 f 0 := by
    exact iteratedDerivWithin_eq_iteratedDeriv
      (uniqueDiffOn_Icc hlu) (hcd2.of_le (by norm_num)) h0
  have hiter2 : iteratedDerivWithin 2 f (Set.Icc l u) 0 = iteratedDeriv 2 f 0 := by
    exact iteratedDerivWithin_eq_iteratedDeriv (uniqueDiffOn_Icc hlu) hcd2 h0
  rw [taylor_within_apply]
  rw [Finset.sum_range_succ]
  simp only [Finset.sum_range_succ, Finset.sum_range_zero]
  simp [f, hiter0, hiter1, hiter2, iteratedDeriv_zero, iteratedDeriv_succ,
    hderiv0, hderiv2]
  simp [hmass]
  ring_nf

/--
Local explicit Taylor little-o remainder for a normalized finite log-sum-exp
quadratic mixture.
-/
theorem bisLogFiniteExpQuadraticMixture_exists_explicit_taylor_isLittleO_two
    {α : Type} [Fintype α]
    (mass A C : α → ℝ)
    (hmass : Finset.sum Finset.univ mass = 1) :
    ∃ l u : ℝ,
      0 ∈ Set.Icc l u ∧ Set.Icc l u ∈ 𝓝 (0 : ℝ) ∧
        (fun τ : ℝ =>
            Real.log (Finset.sum Finset.univ fun x : α =>
              mass x * Real.exp (A x * τ + C x * τ ^ 2))
              - ((Finset.sum Finset.univ fun x : α => mass x * A x) * τ
                + (((Finset.sum Finset.univ fun x : α => mass x * (A x ^ 2 + 2 * C x))
                    - (Finset.sum Finset.univ fun x : α => mass x * A x) ^ 2) / 2)
                  * τ ^ 2))
          =o[𝓝[Set.Icc l u] (0 : ℝ)] (fun τ : ℝ => (τ - 0) ^ 2) := by
  let f : ℝ → ℝ := fun s =>
    Real.log (Finset.sum Finset.univ fun x : α =>
      mass x * Real.exp (A x * s + C x * s ^ 2))
  have hfAt : ContDiffAt ℝ 2 f 0 := by
    simpa [f] using bisLogFiniteExpQuadraticMixture_contDiffAt_two_zero mass A C hmass
  rcases hfAt.contDiffOn (m := (2 : WithTop ℕ∞)) le_rfl (by simp) with
    ⟨s, hs_mem, hs_cd⟩
  rcases exists_Icc_mem_subset_of_mem_nhds hs_mem with ⟨l, u, h0, hnhds, hsub⟩
  have hioo : (0 : ℝ) ∈ Set.Ioo l u := Icc_mem_nhds_iff.mp hnhds
  have hcd : ContDiffOn ℝ 2 f (Set.Icc l u) := hs_cd.mono hsub
  have hrem := taylor_isLittleO (convex_Icc l u) h0 hcd
  have hpoly : ∀ τ : ℝ,
      taylorWithinEval f 2 (Set.Icc l u) 0 τ
        = (Finset.sum Finset.univ fun x : α => mass x * A x) * τ
          + (((Finset.sum Finset.univ fun x : α => mass x * (A x ^ 2 + 2 * C x))
              - (Finset.sum Finset.univ fun x : α => mass x * A x) ^ 2) / 2)
            * τ ^ 2 := by
    intro τ
    simpa [f] using bisLogFiniteExpQuadraticMixture_taylorWithinEval_two_Icc_zero
      mass A C hmass l u τ (lt_trans hioo.1 hioo.2) h0
  refine ⟨l, u, h0, hnhds, ?_⟩
  exact hrem.congr_left (fun τ => by rw [hpoly τ])

/--
Abstract substitution bridge from the local high-noise parameter `τ` to the
paper noise parameter `σ`.

If a remainder is `o(τ²)` in a local interval around zero, then substituting
`τ = σ⁻¹` gives an `atTop` high-noise remainder against the composed scale
`(σ⁻¹)²`.  This theorem deliberately does not rewrite the target as a
Laurent-style expression; it only transports the existing local theorem to the
`σ → ∞` filter.
-/
theorem highNoise_isLittleO_tau_to_sigma_inv
    (g : ℝ → ℝ) (l u : ℝ)
    (h : g =o[𝓝[Set.Icc l u] (0 : ℝ)] (fun τ : ℝ => (τ - 0) ^ 2))
    (hmem : Set.Icc l u ∈ 𝓝 (0 : ℝ)) :
    (g ∘ fun σ : ℝ => σ⁻¹) =o[atTop]
      ((fun τ : ℝ => (τ - 0) ^ 2) ∘ fun σ : ℝ => σ⁻¹) := by
  have htendsto_nhds : Tendsto (fun σ : ℝ => σ⁻¹) atTop (𝓝 (0 : ℝ)) :=
    tendsto_inv_atTop_zero
  have heventually : ∀ᶠ σ in atTop, σ⁻¹ ∈ Set.Icc l u :=
    htendsto_nhds.eventually hmem
  have htendsto : Tendsto (fun σ : ℝ => σ⁻¹) atTop (𝓝[Set.Icc l u] (0 : ℝ)) := by
    exact tendsto_nhdsWithin_iff.mpr ⟨htendsto_nhds, heventually⟩
  exact h.comp_tendsto htendsto

/--
Deterministic coefficient-order bridge with explicit local remainder budgets.

If two expansions have the same linear coefficient, `bA < bB`, and both
remainders are eventually bounded by one quarter of the quadratic coefficient
gap, then expansion `A` is eventually smaller on positive local `τ`.

This is the theorem-facing comparison layer that should be used before any
privacy-profile or tail integration theorem: it converts coefficient hierarchy
into an eventual pointwise likelihood-ratio ordering under explicit remainder
control.
-/
theorem highNoise_quadraticCoeff_eventually_lt_of_remainder_bound
    (a bA bB : ℝ) (rA rB : ℝ → ℝ) (hcoeff : bA < bB)
    (hA : ∀ᶠ τ in 𝓝[>] (0 : ℝ), |rA τ| ≤ ((bB - bA) / 4) * τ ^ 2)
    (hB : ∀ᶠ τ in 𝓝[>] (0 : ℝ), |rB τ| ≤ ((bB - bA) / 4) * τ ^ 2) :
    ∀ᶠ τ in 𝓝[>] (0 : ℝ),
      a * τ + bA * τ ^ 2 + rA τ < a * τ + bB * τ ^ 2 + rB τ := by
  have hdelta_pos : 0 < (bB - bA) / 4 := by nlinarith
  filter_upwards [hA, hB, self_mem_nhdsWithin] with τ hAb hBb hτpos
  have hτsq_pos : 0 < τ ^ 2 := sq_pos_of_ne_zero (ne_of_gt hτpos)
  have hA_le : rA τ ≤ ((bB - bA) / 4) * τ ^ 2 :=
    le_trans (le_abs_self _) hAb
  have hB_ge : -((bB - bA) / 4 * τ ^ 2) ≤ rB τ := by
    have hneg := neg_le_abs (rB τ)
    nlinarith
  have hgap : 2 * (((bB - bA) / 4) * τ ^ 2) < (bB - bA) * τ ^ 2 := by
    nlinarith
  nlinarith

/--
Coefficient ordering with little-o remainders.

If two high-noise kernels share their linear coefficient and their quadratic
coefficients satisfy `bA < bB`, then little-o remainders against `τ²` are small
enough for expansion `A` to be eventually smaller on the positive neighborhood
of zero.
-/
theorem highNoise_quadraticCoeff_eventually_lt_of_isLittleO
    (a bA bB : ℝ) (rA rB : ℝ → ℝ) (hcoeff : bA < bB)
    (hA : rA =o[𝓝[>] (0 : ℝ)] fun τ : ℝ => τ ^ 2)
    (hB : rB =o[𝓝[>] (0 : ℝ)] fun τ : ℝ => τ ^ 2) :
    ∀ᶠ τ in 𝓝[>] (0 : ℝ),
      a * τ + bA * τ ^ 2 + rA τ < a * τ + bB * τ ^ 2 + rB τ := by
  have hdelta_pos : 0 < (bB - bA) / 4 := by nlinarith
  have hAb := hA.bound hdelta_pos
  have hBb := hB.bound hdelta_pos
  exact highNoise_quadraticCoeff_eventually_lt_of_remainder_bound a bA bB rA rB hcoeff
    (hAb.mono (fun τ hτ => by
      have hs : |τ ^ 2| = τ ^ 2 := abs_of_nonneg (sq_nonneg τ)
      simpa [Real.norm_eq_abs, hs] using hτ))
    (hBb.mono (fun τ hτ => by
      have hs : |τ ^ 2| = τ ^ 2 := abs_of_nonneg (sq_nonneg τ)
      simpa [Real.norm_eq_abs, hs] using hτ))

/--
Deterministic first-order coefficient dominance with explicit local tail
budgets.

If the linear coefficients satisfy `aA < aB`, then the linear gap dominates
quadratic and remainder terms that are eventually bounded by a fixed fraction
of `(aB - aA) * τ` on the positive neighborhood of zero.

This is the first layer of the high-noise hierarchy: before comparing
quadratic covariance coefficients, candidate sampling laws must first equalize
the linear/marginal term.
-/
theorem highNoise_linearCoeff_eventually_lt_of_remainder_bound
    (aA aB bA bB : ℝ) (rA rB : ℝ → ℝ) (hcoeff : aA < aB)
    (hA : ∀ᶠ τ in 𝓝[>] (0 : ℝ),
      |bA * τ ^ 2 + rA τ| ≤ ((aB - aA) / 4) * τ)
    (hB : ∀ᶠ τ in 𝓝[>] (0 : ℝ),
      |bB * τ ^ 2 + rB τ| ≤ ((aB - aA) / 4) * τ) :
    ∀ᶠ τ in 𝓝[>] (0 : ℝ),
      aA * τ + bA * τ ^ 2 + rA τ < aB * τ + bB * τ ^ 2 + rB τ := by
  have hdelta_pos : 0 < (aB - aA) / 4 := by nlinarith
  filter_upwards [hA, hB, self_mem_nhdsWithin] with τ hAb hBb hτpos
  have hτgt : 0 < τ := hτpos
  have hA_le : bA * τ ^ 2 + rA τ ≤ ((aB - aA) / 4) * τ :=
    le_trans (le_abs_self _) hAb
  have hB_ge : -(((aB - aA) / 4) * τ) ≤ bB * τ ^ 2 + rB τ := by
    have hneg := neg_le_abs (bB * τ ^ 2 + rB τ)
    nlinarith
  calc
    aA * τ + bA * τ ^ 2 + rA τ
        ≤ aA * τ + ((aB - aA) / 4) * τ := by nlinarith
    _ < aB * τ - ((aB - aA) / 4) * τ := by nlinarith
    _ ≤ aB * τ + bB * τ ^ 2 + rB τ := by nlinarith

/--
First-order coefficient dominance with little-o tails.

This theorem packages the common high-noise use case where the entire
nonlinear tail `b τ² + r(τ)` is `o(τ)`.  Under `aA < aB`, expansion `A` is
eventually smaller on positive local `τ`.
-/
theorem highNoise_linearCoeff_eventually_lt_of_isLittleO
    (aA aB bA bB : ℝ) (rA rB : ℝ → ℝ) (hcoeff : aA < aB)
    (hA : (fun τ : ℝ => bA * τ ^ 2 + rA τ) =o[𝓝[>] (0 : ℝ)] fun τ : ℝ => τ)
    (hB : (fun τ : ℝ => bB * τ ^ 2 + rB τ) =o[𝓝[>] (0 : ℝ)] fun τ : ℝ => τ) :
    ∀ᶠ τ in 𝓝[>] (0 : ℝ),
      aA * τ + bA * τ ^ 2 + rA τ < aB * τ + bB * τ ^ 2 + rB τ := by
  have hdelta_pos : 0 < (aB - aA) / 4 := by nlinarith
  have hAb := hA.bound hdelta_pos
  have hBb := hB.bound hdelta_pos
  have hAb' : ∀ᶠ τ in 𝓝[>] (0 : ℝ),
      |bA * τ ^ 2 + rA τ| ≤ ((aB - aA) / 4) * τ := by
    filter_upwards [hAb, self_mem_nhdsWithin] with τ hτ hτpos
    have habs : |τ| = τ := abs_of_pos hτpos
    simpa [Real.norm_eq_abs, habs] using hτ
  have hBb' : ∀ᶠ τ in 𝓝[>] (0 : ℝ),
      |bB * τ ^ 2 + rB τ| ≤ ((aB - aA) / 4) * τ := by
    filter_upwards [hBb, self_mem_nhdsWithin] with τ hτ hτpos
    have habs : |τ| = τ := abs_of_pos hτpos
    simpa [Real.norm_eq_abs, habs] using hτ
  exact highNoise_linearCoeff_eventually_lt_of_remainder_bound aA aB bA bB rA rB hcoeff
    hAb' hBb'

/--
Lexicographic coefficient dominance for local high-noise expansions.

The theorem combines the first-order and shared-linear quadratic comparison
layers.  If either the linear coefficient is strictly smaller, or the linear
coefficients agree and the quadratic coefficient is strictly smaller, then the
corresponding expansion is eventually smaller on positive local `τ`.

The linear branch consumes `o(τ)` tails for the nonlinear part.  The equal-linear
quadratic branch consumes the sharper `o(τ²)` Taylor remainders.
-/
theorem highNoise_lexicographicCoeff_eventually_lt
    (aA aB bA bB : ℝ) (rA rB : ℝ → ℝ)
    (hlex : aA < aB ∨ (aA = aB ∧ bA < bB))
    (hAlinear : (fun τ : ℝ => bA * τ ^ 2 + rA τ) =o[𝓝[>] (0 : ℝ)] fun τ : ℝ => τ)
    (hBlinear : (fun τ : ℝ => bB * τ ^ 2 + rB τ) =o[𝓝[>] (0 : ℝ)] fun τ : ℝ => τ)
    (hAquadratic : rA =o[𝓝[>] (0 : ℝ)] fun τ : ℝ => τ ^ 2)
    (hBquadratic : rB =o[𝓝[>] (0 : ℝ)] fun τ : ℝ => τ ^ 2) :
    ∀ᶠ τ in 𝓝[>] (0 : ℝ),
      aA * τ + bA * τ ^ 2 + rA τ < aB * τ + bB * τ ^ 2 + rB τ := by
  rcases hlex with hlinear | ⟨haeq, hquad⟩
  · exact highNoise_linearCoeff_eventually_lt_of_isLittleO
      aA aB bA bB rA rB hlinear hAlinear hBlinear
  · subst aB
    exact highNoise_quadraticCoeff_eventually_lt_of_isLittleO
      aA bA bB rA rB hquad hAquadratic hBquadratic

/--
Quadratic Taylor remainders imply the nonlinear first-order tail condition.

This is an ergonomics bridge for the lexicographic high-noise comparison:
from the usual local Taylor hypotheses `r(τ)=o(τ²)`, Lean can derive that the
whole nonlinear part `bτ²+r(τ)` is `o(τ)` on the positive neighborhood of zero.
-/
theorem highNoise_nonlinearTail_isLittleO_linear_of_quadraticRemainder
    (b : ℝ) (r : ℝ → ℝ)
    (h : r =o[𝓝[>] (0 : ℝ)] fun τ : ℝ => τ ^ 2) :
    (fun τ : ℝ => b * τ ^ 2 + r τ) =o[𝓝[>] (0 : ℝ)] fun τ : ℝ => τ := by
  have hpow_nhds : (fun τ : ℝ => τ ^ 2) =o[𝓝 (0 : ℝ)] fun τ : ℝ => τ := by
    simpa using (isLittleO_pow_id (𝕜 := ℝ) one_lt_two)
  have hpow : (fun τ : ℝ => τ ^ 2) =o[𝓝[>] (0 : ℝ)] fun τ : ℝ => τ :=
    hpow_nhds.mono nhdsWithin_le_nhds
  exact (hpow.const_mul_left b).add (h.isBigO.trans_isLittleO hpow)

/--
Lexicographic coefficient dominance from ordinary quadratic Taylor remainders.

This wrapper is the downstream-friendly version of
`highNoise_lexicographicCoeff_eventually_lt`: callers provide only the usual
`r_A=o(τ²)` and `r_B=o(τ²)` high-noise Taylor remainders.  The linear branch
then derives the needed `bτ²+r(τ)=o(τ)` tails automatically, while the
equal-linear branch reuses the sharper quadratic comparison directly.
-/
theorem highNoise_lexicographicCoeff_eventually_lt_of_quadraticRemainders
    (aA aB bA bB : ℝ) (rA rB : ℝ → ℝ)
    (hlex : aA < aB ∨ (aA = aB ∧ bA < bB))
    (hAquadratic : rA =o[𝓝[>] (0 : ℝ)] fun τ : ℝ => τ ^ 2)
    (hBquadratic : rB =o[𝓝[>] (0 : ℝ)] fun τ : ℝ => τ ^ 2) :
    ∀ᶠ τ in 𝓝[>] (0 : ℝ),
      aA * τ + bA * τ ^ 2 + rA τ < aB * τ + bB * τ ^ 2 + rB τ := by
  exact highNoise_lexicographicCoeff_eventually_lt aA aB bA bB rA rB hlex
    (highNoise_nonlinearTail_isLittleO_linear_of_quadraticRemainder bA rA hAquadratic)
    (highNoise_nonlinearTail_isLittleO_linear_of_quadraticRemainder bB rB hBquadratic)
    hAquadratic hBquadratic

/--
Finite probability mass wrapper for theorem-facing sampling laws.

The analytic mixture theorem only needs mass normalization.  Sampling-law
semantics also require nonnegative masses, so paper-facing high-noise theorem
wrappers should consume this structure rather than a bare function whenever
possible.
-/
structure FiniteProbabilityMass (α : Type) [Fintype α] where
  mass : α → ℝ
  mass_nonneg : ∀ x, 0 ≤ mass x
  mass_sum_eq_one : Finset.sum Finset.univ mass = 1

/-- Finite probability masses are determined by their mass functions. -/
@[ext] theorem FiniteProbabilityMass.ext
    {α : Type} [Fintype α]
    {a b : FiniteProbabilityMass α}
    (h : a.mass = b.mass) :
    a = b := by
  cases a
  cases b
  simp_all

/-- The centered covariance minimax factor for binary `k`-out-of-`T` laws. -/
noncomputable def bisCenteredCovarianceMinimaxFactor (T k : ℕ) : ℝ :=
  ((k : ℝ) * ((T - k : ℕ) : ℝ)) / ((T : ℝ) * ((T - 1 : ℕ) : ℝ))

/--
Pairwise half-contrast of a weighted covariance matrix.

For a covariance matrix `C`, this is
`((e_i - e_j)^T C (e_i - e_j)) / 2`, written entrywise.  It is the concrete
centered direction used by the finite-sum minimax lower-bound witness.
-/
noncomputable def bisWeightedCovariancePairwiseHalfContrast
    {α : Type} [Fintype α] {T : ℕ}
    (mass : α → ℝ) (x : α → Fin T → ℝ) (i j : Fin T) : ℝ :=
  (bisWeightedCovarianceEntry mass x i i
    + bisWeightedCovarianceEntry mass x j j
    - bisWeightedCovarianceEntry mass x i j
    - bisWeightedCovarianceEntry mass x j i) / 2

/--
Probability-law wrapper for the fixed-count uniform-marginal covariance lower
contrast.

This is the same lower-bound witness as
`exists_weightedCovariancePairwiseHalfContrast_ge_k_factor_of_fixedCount_uniformMean_binary`,
but exposed through `FiniteProbabilityMass` so paper-facing statements do not
look like signed-weight algebra.
-/
theorem exists_probabilityCovariancePairwiseHalfContrast_ge_minimaxFactor
    {α : Type} [Fintype α] {T k : ℕ}
    (law : FiniteProbabilityMass α) (x : α → Fin T → ℝ) (hT : 2 ≤ T) (hk : k ≤ T)
    (hsum : ∀ a : α, Finset.sum Finset.univ (fun i : Fin T => x a i) = (k : ℝ))
    (hbinary : ∀ (a : α) (i : Fin T), x a i * x a i = x a i)
    (hmean : ∀ i : Fin T, bisWeightedMeanCoord law.mass x i = (k : ℝ) / (T : ℝ)) :
    ∃ i j : Fin T, i ≠ j ∧
      bisCenteredCovarianceMinimaxFactor T k
        ≤ bisWeightedCovariancePairwiseHalfContrast law.mass x i j := by
  simpa [bisCenteredCovarianceMinimaxFactor, bisWeightedCovariancePairwiseHalfContrast]
    using
      exists_weightedCovariancePairwiseHalfContrast_ge_k_factor_of_fixedCount_uniformMean_binary
        law.mass x hT hk law.mass_sum_eq_one hsum hbinary hmean

/--
Named BIS attainment wrapper for the centered covariance minimax factor.

For every nonzero zero-sum direction, uniform fixed-cardinality BIS has exactly
the minimax Rayleigh quotient.  This is still a covariance-level theorem, not a
privacy-profile or sampling-law uniqueness statement.
-/
theorem bisFixedCardUniformCovarianceRayleigh_eq_minimaxFactor_zeroSum_fin
    {T k : ℕ} (hT : 2 ≤ T) (hk : k ≤ T) (w : Fin T → ℝ)
    (hsum : Finset.sum Finset.univ w = 0)
    (hnorm : Finset.sum Finset.univ (fun i : Fin T => w i ^ 2) ≠ 0) :
    ((Finset.sum Finset.univ fun i : Fin T =>
      Finset.sum Finset.univ fun j : Fin T =>
        w i * w j *
          bisFixedCardUniformCovarianceEntry (Finset.univ : Finset (Fin T)) k i j)
      / Finset.sum Finset.univ (fun i : Fin T => w i ^ 2))
      = bisCenteredCovarianceMinimaxFactor T k := by
  simpa [bisCenteredCovarianceMinimaxFactor] using
    bisFixedCardUniformCovarianceRayleigh_zeroSum_fin hT hk w hsum hnorm

/--
Compact covariance-minimax wrapper.

Every probability law with binary fixed-count support and uniform coordinate
mean has a centered pairwise contrast at least as large as the BIS factor, while
BIS attains exactly that factor in every nonzero zero-sum direction.

This is the theorem-facing covariance minimax API without introducing an
`inf`/`sup` object.  It deliberately stops before hockey-stick/profile
transport and before any distribution-level uniqueness claim.
-/
theorem bisCovarianceMinimaxLowerAndBISAttainment_probability
    {α : Type} [Fintype α] {T k : ℕ}
    (law : FiniteProbabilityMass α) (x : α → Fin T → ℝ) (hT : 2 ≤ T) (hk : k ≤ T)
    (hsum : ∀ a : α, Finset.sum Finset.univ (fun i : Fin T => x a i) = (k : ℝ))
    (hbinary : ∀ (a : α) (i : Fin T), x a i * x a i = x a i)
    (hmean : ∀ i : Fin T, bisWeightedMeanCoord law.mass x i = (k : ℝ) / (T : ℝ)) :
    (∃ i j : Fin T, i ≠ j ∧
      bisCenteredCovarianceMinimaxFactor T k
        ≤ bisWeightedCovariancePairwiseHalfContrast law.mass x i j)
    ∧
    (∀ w : Fin T → ℝ,
      Finset.sum Finset.univ w = 0 →
      Finset.sum Finset.univ (fun i : Fin T => w i ^ 2) ≠ 0 →
        ((Finset.sum Finset.univ fun i : Fin T =>
          Finset.sum Finset.univ fun j : Fin T =>
            w i * w j *
              bisFixedCardUniformCovarianceEntry (Finset.univ : Finset (Fin T)) k i j)
          / Finset.sum Finset.univ (fun i : Fin T => w i ^ 2))
          = bisCenteredCovarianceMinimaxFactor T k) := by
  constructor
  · exact exists_probabilityCovariancePairwiseHalfContrast_ge_minimaxFactor
      law x hT hk hsum hbinary hmean
  · intro w hw_sum hw_norm
    exact bisFixedCardUniformCovarianceRayleigh_eq_minimaxFactor_zeroSum_fin
      hT hk w hw_sum hw_norm

/--
Weighted mean of the inner product equals the inner product with the weighted
coordinate mean.

This is the algebraic bridge from the generic finite log-sum-exp Taylor
coefficient to the paper's high-noise first-order term `<E X,w>`.
-/
theorem bisWeightedMeanInner_eq_sum_meanCoord_mul
    {α : Type} [Fintype α] {T : ℕ}
    (mass : α → ℝ) (x : α → Fin T → ℝ) (w : Fin T → ℝ) :
    (Finset.sum Finset.univ fun a : α =>
      mass a * (Finset.sum Finset.univ fun i : Fin T => x a i * w i))
      = Finset.sum Finset.univ fun i : Fin T => bisWeightedMeanCoord mass x i * w i := by
  unfold bisWeightedMeanCoord
  calc
    (Finset.sum Finset.univ fun a : α =>
      mass a * (Finset.sum Finset.univ fun i : Fin T => x a i * w i))
        = Finset.sum Finset.univ fun a : α =>
            Finset.sum Finset.univ fun i : Fin T => mass a * (x a i * w i) := by
            simp_rw [Finset.mul_sum]
    _ = Finset.sum Finset.univ fun i : Fin T =>
          Finset.sum Finset.univ fun a : α => mass a * (x a i * w i) := by
          rw [Finset.sum_comm]
    _ = Finset.sum Finset.univ fun i : Fin T =>
          (Finset.sum Finset.univ fun a : α => mass a * x a i) * w i := by
          refine Finset.sum_congr rfl ?_
          intro i _
          rw [Finset.sum_mul]
          refine Finset.sum_congr rfl ?_
          intro a _
          ring

/--
All-ones centered inner moment equals participation-count variance.

If the theorem-facing count is represented by summing the coordinates of the
participation vector, then the centered second moment of `<X, 1>` is exactly
the weighted squared deviation of the participation count.
-/
theorem bisWeightedInnerCenteredSecondMoment_constOne_eq_countSqDeviation
    {α : Type} [Fintype α] [DecidableEq α] {T : ℕ}
    (mass : α → ℝ) (x : α → Fin T → ℝ) (count : α → ℕ) (target : ℝ)
    (hmass_total : Finset.sum Finset.univ mass = 1)
    (hcount : ∀ a : α, Finset.sum Finset.univ (fun i : Fin T => x a i) = (count a : ℝ))
    (hmean : Finset.sum Finset.univ (fun a : α => mass a * (count a : ℝ)) = target) :
    (Finset.sum Finset.univ fun a : α =>
        mass a * (Finset.sum Finset.univ fun i : Fin T => x a i * (1 : ℝ)) ^ 2)
      - (Finset.sum Finset.univ fun i : Fin T => bisWeightedMeanCoord mass x i * (1 : ℝ)) ^ 2
      = bisWeightedCountSqDeviation Finset.univ mass count target := by
  have hfirst :
      (Finset.sum Finset.univ fun a : α =>
        mass a * (Finset.sum Finset.univ fun i : Fin T => x a i * (1 : ℝ)) ^ 2)
        = Finset.sum Finset.univ (fun a : α => mass a * (count a : ℝ) ^ 2) := by
    refine Finset.sum_congr rfl ?_
    intro a _
    rw [show (Finset.sum Finset.univ fun i : Fin T => x a i * (1 : ℝ)) = (count a : ℝ) by
      simpa using hcount a]
  have hmeanInner :
      (Finset.sum Finset.univ fun i : Fin T => bisWeightedMeanCoord mass x i * (1 : ℝ))
        = target := by
    rw [← bisWeightedMeanInner_eq_sum_meanCoord_mul mass x (fun _ : Fin T => (1 : ℝ))]
    calc
      (Finset.sum Finset.univ fun a : α =>
          mass a * (Finset.sum Finset.univ fun i : Fin T => x a i * (1 : ℝ)))
        = Finset.sum Finset.univ (fun a : α => mass a * (count a : ℝ)) := by
            refine Finset.sum_congr rfl ?_
            intro a _
            rw [show (Finset.sum Finset.univ fun i : Fin T => x a i * (1 : ℝ))
                = (count a : ℝ) by
              simpa using hcount a]
      _ = target := hmean
  rw [bisWeightedCountSqDeviation_eq_secondMoment_sub_sq_of_mean
    (s := (Finset.univ : Finset α)) (mass := mass) (count := count)
    (target := target) hmass_total hmean]
  rw [hfirst, hmeanInner]

/--
High-noise Taylor theorem for the paper's finite Gaussian likelihood-ratio
kernel.

With `τ = 1 / σ`, each participation vector contributes the component

```text
exp(<x,w> τ - ||x||² τ² / 2).
```

This theorem instantiates the generic finite log-sum-exp quadratic-mixture
Taylor theorem and rewrites the coefficients into the already-formalized
high-noise algebra:

```text
log E[exp(<X,w>τ - ||X||²τ²/2)]
  = <E X,w> τ + formalSecondCoeff τ² + o(τ²).
```

It is a local Taylor theorem at `τ=0`; it does not by itself prove the
`σ → ∞` privacy-profile limit or compare sampling laws.
-/
theorem bisHighNoiseLogLR_exists_explicit_taylor_isLittleO_two
    {α : Type} [Fintype α] {T : ℕ}
    (mass : α → ℝ) (x : α → Fin T → ℝ) (w : Fin T → ℝ)
    (hmass : Finset.sum Finset.univ mass = 1) :
    ∃ l u : ℝ,
      0 ∈ Set.Icc l u ∧ Set.Icc l u ∈ 𝓝 (0 : ℝ) ∧
        (fun τ : ℝ =>
            Real.log (Finset.sum Finset.univ fun a : α =>
              mass a * Real.exp
                ((Finset.sum Finset.univ fun i : Fin T => x a i * w i) * τ
                  + (-(Finset.sum Finset.univ fun i : Fin T => (x a i) ^ 2) / 2) * τ ^ 2))
              - ((Finset.sum Finset.univ fun i : Fin T =>
                    bisWeightedMeanCoord mass x i * w i) * τ
                + bisFormalHighNoiseLogSecondCoeff mass x w * τ ^ 2))
          =o[𝓝[Set.Icc l u] (0 : ℝ)] (fun τ : ℝ => (τ - 0) ^ 2) := by
  let A : α → ℝ := fun a => Finset.sum Finset.univ fun i : Fin T => x a i * w i
  let C : α → ℝ := fun a => -(Finset.sum Finset.univ fun i : Fin T => (x a i) ^ 2) / 2
  rcases bisLogFiniteExpQuadraticMixture_exists_explicit_taylor_isLittleO_two mass A C hmass with
    ⟨l, u, h0, hnhds, hrem⟩
  have hmean : (Finset.sum Finset.univ fun a : α => mass a * A a)
      = Finset.sum Finset.univ fun i : Fin T => bisWeightedMeanCoord mass x i * w i := by
    simpa [A] using bisWeightedMeanInner_eq_sum_meanCoord_mul mass x w
  have hquad :
      (((Finset.sum Finset.univ fun a : α => mass a * (A a ^ 2 + 2 * C a))
          - (Finset.sum Finset.univ fun a : α => mass a * A a) ^ 2) / 2)
        = bisFormalHighNoiseLogSecondCoeff mass x w := by
    unfold bisFormalHighNoiseLogSecondCoeff bisWeightedSqNormMean
    simp only [A, C]
    rw [hmean]
    have hterm : ∀ a : α,
        mass a * ((Finset.sum Finset.univ fun i : Fin T => x a i * w i) ^ 2
            + 2 * ((-(Finset.sum Finset.univ fun i : Fin T => (x a i) ^ 2)) / 2))
          = mass a * (Finset.sum Finset.univ fun i : Fin T => x a i * w i) ^ 2
            - mass a * (Finset.sum Finset.univ fun i : Fin T => (x a i) ^ 2) := by
      intro a
      ring
    rw [show (Finset.sum Finset.univ fun a : α =>
        mass a * ((Finset.sum Finset.univ fun i : Fin T => x a i * w i) ^ 2
            + 2 * ((-(Finset.sum Finset.univ fun i : Fin T => (x a i) ^ 2)) / 2)))
        = Finset.sum Finset.univ fun a : α =>
            mass a * (Finset.sum Finset.univ fun i : Fin T => x a i * w i) ^ 2
              - mass a * (Finset.sum Finset.univ fun i : Fin T => (x a i) ^ 2) by
          exact Finset.sum_congr rfl (fun a _ => hterm a)]
    rw [Finset.sum_sub_distrib]
    ring
  refine ⟨l, u, h0, hnhds, ?_⟩
  exact hrem.congr_left (fun _τ => by rw [hquad, hmean])

/--
Probability-law wrapper for the finite Gaussian high-noise LR Taylor theorem.

This is semantically the same expansion as
`bisHighNoiseLogLR_exists_explicit_taylor_isLittleO_two`, but it carries the
nonnegative probability-mass assumptions in the input object.  The proof
delegates to the normalized analytic theorem; nonnegativity is retained for
later profile/tail theorem surfaces.
-/
theorem bisHighNoiseLogLR_probabilityMass_exists_explicit_taylor_isLittleO_two
    {α : Type} [Fintype α] {T : ℕ}
    (law : FiniteProbabilityMass α) (x : α → Fin T → ℝ) (w : Fin T → ℝ) :
    ∃ l u : ℝ,
      0 ∈ Set.Icc l u ∧ Set.Icc l u ∈ 𝓝 (0 : ℝ) ∧
        (fun τ : ℝ =>
            Real.log (Finset.sum Finset.univ fun a : α =>
              law.mass a * Real.exp
                ((Finset.sum Finset.univ fun i : Fin T => x a i * w i) * τ
                  + (-(Finset.sum Finset.univ fun i : Fin T => (x a i) ^ 2) / 2) * τ ^ 2))
              - ((Finset.sum Finset.univ fun i : Fin T =>
                    bisWeightedMeanCoord law.mass x i * w i) * τ
                + bisFormalHighNoiseLogSecondCoeff law.mass x w * τ ^ 2))
          =o[𝓝[Set.Icc l u] (0 : ℝ)] (fun τ : ℝ => (τ - 0) ^ 2) := by
  exact bisHighNoiseLogLR_exists_explicit_taylor_isLittleO_two
    law.mass x w law.mass_sum_eq_one

/--
Probability-law covariance form of the high-noise quadratic coefficient.

For a finite probability law over participation vectors, the second-order log
coefficient is exactly one half of

```text
wᵀ Cov(X) w - E||X||².
```

This wrapper is intentionally coefficient-only.  It does not assert a tail or
privacy-profile comparison.
-/
theorem bisHighNoiseLogSecondCoeff_probabilityMass_eq_covariance_sub_sqNormMean
    {α : Type} [Fintype α] {T : ℕ}
    (law : FiniteProbabilityMass α) (x : α → Fin T → ℝ) (w : Fin T → ℝ) :
    bisFormalHighNoiseLogSecondCoeff law.mass x w
      = ((Finset.sum Finset.univ fun i : Fin T =>
            Finset.sum Finset.univ fun j : Fin T =>
              w i * w j * bisWeightedCovarianceEntry law.mass x i j)
          - bisWeightedSqNormMean law.mass x) / 2 := by
  exact bisFormalHighNoiseLogSecondCoeff_eq_covariance_sub_sqNormMean law.mass x w

/--
For binary fixed-count participation vectors, the expected squared norm is the
fixed participation count.

This is the `E||X||² = k` bridge needed to turn covariance minimax into a
high-noise quadratic-coefficient statement.
-/
theorem bisWeightedSqNormMean_eq_fixedCoordSum_of_binary
    {α : Type} [Fintype α] {T : ℕ}
    (mass : α → ℝ) (x : α → Fin T → ℝ) (target : ℝ)
    (hmass_total : Finset.sum Finset.univ mass = 1)
    (hsum : ∀ a : α, Finset.sum Finset.univ (fun i : Fin T => x a i) = target)
    (hbinary : ∀ (a : α) (i : Fin T), x a i * x a i = x a i) :
    bisWeightedSqNormMean mass x = target := by
  unfold bisWeightedSqNormMean
  calc
    (Finset.sum Finset.univ fun a : α =>
        mass a * Finset.sum Finset.univ (fun i : Fin T => x a i ^ 2))
        = Finset.sum Finset.univ fun a : α =>
            mass a * Finset.sum Finset.univ (fun i : Fin T => x a i) := by
            refine Finset.sum_congr rfl ?_
            intro a _
            congr 1
            refine Finset.sum_congr rfl ?_
            intro i _
            simpa [pow_two] using hbinary a i
    _ = Finset.sum Finset.univ fun a : α => mass a * target := by
            refine Finset.sum_congr rfl ?_
            intro a _
            rw [hsum a]
    _ = target := by
            rw [← Finset.sum_mul, hmass_total, one_mul]

/--
Binary fixed-count high-noise coefficient formula.

For an admissible finite probability law with fixed binary count `k`, the
quadratic coefficient is

```text
(w^T Cov(X) w - k) / 2.
```

This is a coefficient-level bridge only; it does not transport the local
Taylor expansion to a hockey-stick/profile theorem.
-/
theorem bisHighNoiseLogSecondCoeff_probabilityMass_eq_covariance_sub_fixedCount
    {α : Type} [Fintype α] {T k : ℕ}
    (law : FiniteProbabilityMass α) (x : α → Fin T → ℝ) (w : Fin T → ℝ)
    (hsum : ∀ a : α, Finset.sum Finset.univ (fun i : Fin T => x a i) = (k : ℝ))
    (hbinary : ∀ (a : α) (i : Fin T), x a i * x a i = x a i) :
    bisFormalHighNoiseLogSecondCoeff law.mass x w
      = ((Finset.sum Finset.univ fun i : Fin T =>
            Finset.sum Finset.univ fun j : Fin T =>
              w i * w j * bisWeightedCovarianceEntry law.mass x i j)
          - (k : ℝ)) / 2 := by
  rw [bisHighNoiseLogSecondCoeff_probabilityMass_eq_covariance_sub_sqNormMean]
  rw [bisWeightedSqNormMean_eq_fixedCoordSum_of_binary
    law.mass x (k : ℝ) law.mass_sum_eq_one hsum hbinary]

/-- Unit-centered high-noise quadratic coefficient induced by a covariance value. -/
noncomputable def bisCenteredUnitHighNoiseSecondCoeff (T k : ℕ) : ℝ :=
  (bisCenteredCovarianceMinimaxFactor T k - (k : ℝ)) / 2

/--
High-noise quadratic coefficient for the normalized pairwise contrast direction
encoded by a pairwise half-contrast.

The half-contrast is the covariance Rayleigh value for the unit vector
`(e_i-e_j)/sqrt(2)`, avoiding explicit square-root normalization in the API.
-/
noncomputable def bisWeightedPairwiseUnitHighNoiseSecondCoeff
    {α : Type} [Fintype α] {T k : ℕ}
    (mass : α → ℝ) (x : α → Fin T → ℝ) (i j : Fin T) : ℝ :=
  (bisWeightedCovariancePairwiseHalfContrast mass x i j - (k : ℝ)) / 2

/--
Coefficient-level lower-bound witness for admissible probability laws.

Every binary fixed-count, uniform-marginal probability law has some normalized
pairwise centered direction whose high-noise quadratic coefficient is at least
the BIS unit-centered coefficient.
-/
theorem exists_probabilityPairwiseUnitHighNoiseSecondCoeff_ge_minimaxCoeff
    {α : Type} [Fintype α] {T k : ℕ}
    (law : FiniteProbabilityMass α) (x : α → Fin T → ℝ) (hT : 2 ≤ T) (hk : k ≤ T)
    (hsum : ∀ a : α, Finset.sum Finset.univ (fun i : Fin T => x a i) = (k : ℝ))
    (hbinary : ∀ (a : α) (i : Fin T), x a i * x a i = x a i)
    (hmean : ∀ i : Fin T, bisWeightedMeanCoord law.mass x i = (k : ℝ) / (T : ℝ)) :
    ∃ i j : Fin T, i ≠ j ∧
      bisCenteredUnitHighNoiseSecondCoeff T k
        ≤ bisWeightedPairwiseUnitHighNoiseSecondCoeff (T := T) (k := k) law.mass x i j := by
  rcases exists_probabilityCovariancePairwiseHalfContrast_ge_minimaxFactor
      law x hT hk hsum hbinary hmean with ⟨i, j, hij, hle⟩
  refine ⟨i, j, hij, ?_⟩
  unfold bisCenteredUnitHighNoiseSecondCoeff bisWeightedPairwiseUnitHighNoiseSecondCoeff
  linarith

/--
BIS attainment at the high-noise quadratic coefficient layer.

For every nonzero zero-sum direction, the normalized covariance Rayleigh value
of BIS gives the named unit-centered high-noise coefficient.
-/
theorem bisFixedCardUniformUnitHighNoiseSecondCoeff_eq_minimaxCoeff_zeroSum_fin
    {T k : ℕ} (hT : 2 ≤ T) (hk : k ≤ T) (w : Fin T → ℝ)
    (hsum : Finset.sum Finset.univ w = 0)
    (hnorm : Finset.sum Finset.univ (fun i : Fin T => w i ^ 2) ≠ 0) :
    (((Finset.sum Finset.univ fun i : Fin T =>
      Finset.sum Finset.univ fun j : Fin T =>
        w i * w j *
          bisFixedCardUniformCovarianceEntry (Finset.univ : Finset (Fin T)) k i j)
      / Finset.sum Finset.univ (fun i : Fin T => w i ^ 2))
      - (k : ℝ)) / 2
      = bisCenteredUnitHighNoiseSecondCoeff T k := by
  rw [bisFixedCardUniformCovarianceRayleigh_eq_minimaxFactor_zeroSum_fin
    hT hk w hsum hnorm]
  rfl

/--
Compact coefficient-level minimax wrapper.

This composes the covariance-minimax API with the binary fixed-count
`E||X||² = k` bridge.  It is still a local high-noise coefficient theorem, not
a hockey-stick/profile transport theorem.
-/
theorem bisHighNoiseCenteredQuadraticCoeffMinimax_probability
    {α : Type} [Fintype α] {T k : ℕ}
    (law : FiniteProbabilityMass α) (x : α → Fin T → ℝ) (hT : 2 ≤ T) (hk : k ≤ T)
    (hsum : ∀ a : α, Finset.sum Finset.univ (fun i : Fin T => x a i) = (k : ℝ))
    (hbinary : ∀ (a : α) (i : Fin T), x a i * x a i = x a i)
    (hmean : ∀ i : Fin T, bisWeightedMeanCoord law.mass x i = (k : ℝ) / (T : ℝ)) :
    (∃ i j : Fin T, i ≠ j ∧
      bisCenteredUnitHighNoiseSecondCoeff T k
        ≤ bisWeightedPairwiseUnitHighNoiseSecondCoeff (T := T) (k := k) law.mass x i j)
    ∧
    (∀ w : Fin T → ℝ,
      Finset.sum Finset.univ w = 0 →
      Finset.sum Finset.univ (fun i : Fin T => w i ^ 2) ≠ 0 →
        (((Finset.sum Finset.univ fun i : Fin T =>
          Finset.sum Finset.univ fun j : Fin T =>
            w i * w j *
              bisFixedCardUniformCovarianceEntry (Finset.univ : Finset (Fin T)) k i j)
          / Finset.sum Finset.univ (fun i : Fin T => w i ^ 2))
          - (k : ℝ)) / 2
          = bisCenteredUnitHighNoiseSecondCoeff T k) := by
  constructor
  · exact exists_probabilityPairwiseUnitHighNoiseSecondCoeff_ge_minimaxCoeff
      law x hT hk hsum hbinary hmean
  · intro w hw_sum hw_norm
    exact bisFixedCardUniformUnitHighNoiseSecondCoeff_eq_minimaxCoeff_zeroSum_fin
      hT hk w hw_sum hw_norm

/--
Uniform fixed-cardinality BIS high-noise Taylor theorem in zero-sum directions.

For the uniform `k`-out-of-`T` law and any direction `w` with zero coordinate
sum, the first-order term vanishes and the local high-noise LR expansion has
the spectrum coefficient already proved for the fixed-cardinality covariance:

```text
((k(T-k)/(T(T-1))) * ||w||² - k) / 2.
```

This is a local Taylor theorem in `τ`; it does not prove the full
`σ → ∞` profile asymptotic or optimality statement.
-/
theorem bisFixedCardUniformHighNoiseLogLR_zeroSum_exists_explicit_taylor_isLittleO_two
    {T k : ℕ} (hT : 2 ≤ T) (hk : k ≤ T) (w : Fin T → ℝ)
    (hsum : Finset.sum Finset.univ w = 0) :
    ∃ l u : ℝ,
      0 ∈ Set.Icc l u ∧ Set.Icc l u ∈ 𝓝 (0 : ℝ) ∧
        (fun τ : ℝ =>
            Real.log (Finset.sum Finset.univ fun s : Finset (Fin T) =>
              bisFixedCardUniformMass (Finset.univ : Finset (Fin T)) k s * Real.exp
                ((Finset.sum Finset.univ fun i : Fin T =>
                    (if i ∈ s then (1 : ℝ) else 0) * w i) * τ
                  + (-(Finset.sum Finset.univ fun i : Fin T =>
                      ((if i ∈ s then (1 : ℝ) else 0)) ^ 2) / 2) * τ ^ 2))
              - (((((k : ℝ) * ((T - k : ℕ) : ℝ))
                    / ((T : ℝ) * ((T - 1 : ℕ) : ℝ)))
                    * Finset.sum Finset.univ (fun i : Fin T => w i ^ 2) - (k : ℝ)) / 2
                  * τ ^ 2))
          =o[𝓝[Set.Icc l u] (0 : ℝ)] (fun τ : ℝ => (τ - 0) ^ 2) := by
  have hmass : Finset.sum Finset.univ (fun u : Finset (Fin T) =>
      bisFixedCardUniformMass (Finset.univ : Finset (Fin T)) k u) = 1 := by
    rw [bisFixedCardUniformMass_sum_univ_eq_one
      (Finset.univ : Finset (Fin T)) k (by simpa [Finset.card_univ] using hk)]
  rcases bisHighNoiseLogLR_exists_explicit_taylor_isLittleO_two
    (fun u : Finset (Fin T) => bisFixedCardUniformMass (Finset.univ : Finset (Fin T)) k u)
    (fun u i => if i ∈ u then (1 : ℝ) else 0) w hmass with
    ⟨l, u, h0, hnhds, hrem⟩
  have hlin : (Finset.sum Finset.univ fun i : Fin T =>
      bisWeightedMeanCoord
        (fun u : Finset (Fin T) => bisFixedCardUniformMass (Finset.univ : Finset (Fin T)) k u)
        (fun u i => if i ∈ u then (1 : ℝ) else 0) i * w i) = 0 := by
    exact bisFixedCardUniformMeanInner_zero_of_zeroSum hk w hsum
  have hquad := bisFixedCardUniformFormalHighNoiseLogSecondCoeff_zeroSum hT hk w hsum
  refine ⟨l, u, h0, hnhds, ?_⟩
  exact hrem.congr_left (fun τ => by
    rw [hlin, hquad]
    ring)

/--
Substitute `τ = 1 / σ` in a local `τ → 0` little-o statement.

This is the generic analysis bridge from the local Taylor variable used in the
high-noise proofs to the usual `σ → ∞` parameterization.
-/
theorem bisLittleO_comp_inv_atTop_of_nhdsWithin
    {s : Set ℝ} {f : ℝ → ℝ}
    (hs : s ∈ 𝓝 (0 : ℝ))
    (h : f =o[𝓝[s] (0 : ℝ)] fun τ : ℝ => τ ^ 2) :
    (fun σ : ℝ => f (σ⁻¹)) =o[atTop] fun σ : ℝ => (σ⁻¹) ^ 2 := by
  have ht : Tendsto (fun σ : ℝ => σ⁻¹) atTop (𝓝[s] (0 : ℝ)) := by
    rw [nhdsWithin]
    exact tendsto_inf.2 ⟨tendsto_inv_atTop_zero,
      tendsto_principal.2 (tendsto_inv_atTop_zero.eventually hs)⟩
  simpa [Function.comp_def] using h.comp_tendsto ht

/--
`σ → ∞` form of the generic high-noise Gaussian LR Taylor bridge.

This is obtained from `bisHighNoiseLogLR_exists_explicit_taylor_isLittleO_two`
by substituting `τ = 1 / σ`.  It remains an asymptotic expansion of the
log-likelihood kernel, not a privacy-profile or tail theorem.
-/
theorem bisHighNoiseLogLR_invSigma_isLittleO_two
    {α : Type} [Fintype α] {T : ℕ}
    (mass : α → ℝ) (x : α → Fin T → ℝ) (w : Fin T → ℝ)
    (hmass : Finset.sum Finset.univ mass = 1) :
    (fun σ : ℝ =>
        Real.log (Finset.sum Finset.univ fun a : α =>
          mass a * Real.exp
            ((Finset.sum Finset.univ fun i : Fin T => x a i * w i) * σ⁻¹
              + (-(Finset.sum Finset.univ fun i : Fin T => (x a i) ^ 2) / 2) * (σ⁻¹) ^ 2))
          - ((Finset.sum Finset.univ fun i : Fin T =>
                bisWeightedMeanCoord mass x i * w i) * σ⁻¹
            + bisFormalHighNoiseLogSecondCoeff mass x w * (σ⁻¹) ^ 2))
      =o[atTop] fun σ : ℝ => (σ⁻¹) ^ 2 := by
  rcases bisHighNoiseLogLR_exists_explicit_taylor_isLittleO_two mass x w hmass with
    ⟨l, u, _h0, hnhds, hrem⟩
  have hrem' :
      (fun τ : ℝ =>
          Real.log (Finset.sum Finset.univ fun a : α =>
            mass a * Real.exp
              ((Finset.sum Finset.univ fun i : Fin T => x a i * w i) * τ
                + (-(Finset.sum Finset.univ fun i : Fin T => (x a i) ^ 2) / 2) * τ ^ 2))
            - ((Finset.sum Finset.univ fun i : Fin T =>
                  bisWeightedMeanCoord mass x i * w i) * τ
              + bisFormalHighNoiseLogSecondCoeff mass x w * τ ^ 2))
        =o[𝓝[Set.Icc l u] (0 : ℝ)] fun τ : ℝ => τ ^ 2 := by
    simpa using hrem
  exact bisLittleO_comp_inv_atTop_of_nhdsWithin hnhds hrem'

/--
`σ → ∞` form of the uniform fixed-cardinality BIS zero-sum high-noise
expansion.

This theorem is still kernel-level: it proves the log-likelihood expansion
after substituting `τ = 1 / σ`; it does not yet prove a hockey-stick/profile
limit.
-/
theorem bisFixedCardUniformHighNoiseLogLR_zeroSum_invSigma_isLittleO_two
    {T k : ℕ} (hT : 2 ≤ T) (hk : k ≤ T) (w : Fin T → ℝ)
    (hsum : Finset.sum Finset.univ w = 0) :
    (fun σ : ℝ =>
        Real.log (Finset.sum Finset.univ fun s : Finset (Fin T) =>
          bisFixedCardUniformMass (Finset.univ : Finset (Fin T)) k s * Real.exp
            ((Finset.sum Finset.univ fun i : Fin T =>
                (if i ∈ s then (1 : ℝ) else 0) * w i) * σ⁻¹
              + (-(Finset.sum Finset.univ fun i : Fin T =>
                  ((if i ∈ s then (1 : ℝ) else 0)) ^ 2) / 2) * (σ⁻¹) ^ 2))
          - (((((k : ℝ) * ((T - k : ℕ) : ℝ))
                / ((T : ℝ) * ((T - 1 : ℕ) : ℝ)))
                * Finset.sum Finset.univ (fun i : Fin T => w i ^ 2) - (k : ℝ)) / 2
              * (σ⁻¹) ^ 2))
      =o[atTop] fun σ : ℝ => (σ⁻¹) ^ 2 := by
  rcases bisFixedCardUniformHighNoiseLogLR_zeroSum_exists_explicit_taylor_isLittleO_two
      hT hk w hsum with
    ⟨l, u, _h0, hnhds, hrem⟩
  have hrem' :
      (fun τ : ℝ =>
          Real.log (Finset.sum Finset.univ fun s : Finset (Fin T) =>
            bisFixedCardUniformMass (Finset.univ : Finset (Fin T)) k s * Real.exp
              ((Finset.sum Finset.univ fun i : Fin T =>
                  (if i ∈ s then (1 : ℝ) else 0) * w i) * τ
                + (-(Finset.sum Finset.univ fun i : Fin T =>
                    ((if i ∈ s then (1 : ℝ) else 0)) ^ 2) / 2) * τ ^ 2))
            - (((((k : ℝ) * ((T - k : ℕ) : ℝ))
                  / ((T : ℝ) * ((T - 1 : ℕ) : ℝ)))
                  * Finset.sum Finset.univ (fun i : Fin T => w i ^ 2) - (k : ℝ)) / 2
                * τ ^ 2))
        =o[𝓝[Set.Icc l u] (0 : ℝ)] fun τ : ℝ => τ ^ 2 := by
    simpa using hrem
  exact bisLittleO_comp_inv_atTop_of_nhdsWithin hnhds hrem'

/--
`σ → ∞` high-noise expansion for uniform fixed-cardinality BIS in an arbitrary
direction.

The linear coefficient is the uniform marginal term `(k/T) * Σ_i w_i`; the
quadratic coefficient is the projected finite-population coefficient.
This remains a kernel-level log-likelihood expansion, not a privacy-profile
or hockey-stick theorem.
-/
theorem bisFixedCardUniformHighNoiseLogLR_centeredNorm_invSigma_isLittleO_two
    {T k : ℕ} (hT : 2 ≤ T) (hk : k ≤ T) (w : Fin T → ℝ) :
    (fun σ : ℝ =>
        Real.log (Finset.sum Finset.univ fun s : Finset (Fin T) =>
          bisFixedCardUniformMass (Finset.univ : Finset (Fin T)) k s * Real.exp
            ((Finset.sum Finset.univ fun i : Fin T =>
                (if i ∈ s then (1 : ℝ) else 0) * w i) * σ⁻¹
              + (-(Finset.sum Finset.univ fun i : Fin T =>
                  ((if i ∈ s then (1 : ℝ) else 0)) ^ 2) / 2) * (σ⁻¹) ^ 2))
          - ((((k : ℝ) / (T : ℝ)) * Finset.sum Finset.univ w) * σ⁻¹
            + (((((k : ℝ) * ((T - k : ℕ) : ℝ))
                  / ((T : ℝ) * ((T - 1 : ℕ) : ℝ)))
                  * (Finset.sum Finset.univ (fun i : Fin T => w i ^ 2)
                    - (Finset.sum Finset.univ w) ^ 2 / (T : ℝ)) - (k : ℝ)) / 2)
              * (σ⁻¹) ^ 2))
      =o[atTop] fun σ : ℝ => (σ⁻¹) ^ 2 := by
  have hmass : Finset.sum Finset.univ (fun u : Finset (Fin T) =>
      bisFixedCardUniformMass (Finset.univ : Finset (Fin T)) k u) = 1 := by
    rw [bisFixedCardUniformMass_sum_univ_eq_one
      (Finset.univ : Finset (Fin T)) k (by simpa [Finset.card_univ] using hk)]
  have h := bisHighNoiseLogLR_invSigma_isLittleO_two
    (fun u : Finset (Fin T) =>
      bisFixedCardUniformMass (Finset.univ : Finset (Fin T)) k u)
    (fun u i => if i ∈ u then (1 : ℝ) else 0) w hmass
  have hlin : (Finset.sum Finset.univ fun i : Fin T =>
      bisWeightedMeanCoord
        (fun u : Finset (Fin T) =>
          bisFixedCardUniformMass (Finset.univ : Finset (Fin T)) k u)
        (fun u i => if i ∈ u then (1 : ℝ) else 0) i * w i)
      = ((k : ℝ) / (T : ℝ)) * Finset.sum Finset.univ w := by
    exact bisFixedCardUniformMeanInner_eq_uniform hk w
  have hquad := bisFixedCardUniformFormalHighNoiseLogSecondCoeff_centeredNorm hT hk w
  exact h.congr_left (fun σ => by
    rw [hlin, hquad])

/--
If the coordinate mean vector is constant, its inner product with `w` is that
constant times the coordinate sum of `w`.

This is the generic first-layer high-noise marginal-uniformity algebra.
-/
theorem bisWeightedMeanInner_eq_const_mul_sum_of_forall_meanCoord
    {α : Type} [Fintype α] {T : ℕ}
    (mass : α → ℝ) (x : α → Fin T → ℝ) (w : Fin T → ℝ) (c : ℝ)
    (hmean : ∀ i : Fin T, bisWeightedMeanCoord mass x i = c) :
    (Finset.sum Finset.univ fun i : Fin T => bisWeightedMeanCoord mass x i * w i)
      = c * Finset.sum Finset.univ w := by
  calc
    (Finset.sum Finset.univ fun i : Fin T => bisWeightedMeanCoord mass x i * w i)
      = Finset.sum Finset.univ fun i : Fin T => c * w i := by
          refine Finset.sum_congr rfl ?_
          intro i _
          rw [hmean i]
    _ = c * Finset.sum Finset.univ w := by
          rw [Finset.mul_sum]

/--
Uniform coordinate marginals remove the first-order high-noise term on
zero-sum directions.

This theorem keeps the sampling law arbitrary except for normalized masses and
constant coordinate mean.  It is the generic version of the first high-noise
optimization layer before specializing the second-order coefficient.
-/
theorem bisHighNoiseLogLR_uniformMean_zeroSum_invSigma_isLittleO_two
    {α : Type} [Fintype α] {T : ℕ}
    (mass : α → ℝ) (x : α → Fin T → ℝ) (w : Fin T → ℝ) (c : ℝ)
    (hmass : Finset.sum Finset.univ mass = 1)
    (hmean : ∀ i : Fin T, bisWeightedMeanCoord mass x i = c)
    (hsum : Finset.sum Finset.univ w = 0) :
    (fun σ : ℝ =>
        Real.log (Finset.sum Finset.univ fun a : α =>
          mass a * Real.exp
            ((Finset.sum Finset.univ fun i : Fin T => x a i * w i) * σ⁻¹
              + (-(Finset.sum Finset.univ fun i : Fin T => (x a i) ^ 2) / 2) * (σ⁻¹) ^ 2))
          - (bisFormalHighNoiseLogSecondCoeff mass x w * (σ⁻¹) ^ 2))
      =o[atTop] fun σ : ℝ => (σ⁻¹) ^ 2 := by
  have hlin : (Finset.sum Finset.univ fun i : Fin T =>
      bisWeightedMeanCoord mass x i * w i) = 0 := by
    rw [bisWeightedMeanInner_eq_const_mul_sum_of_forall_meanCoord mass x w c hmean,
      hsum, mul_zero]
  have h := bisHighNoiseLogLR_invSigma_isLittleO_two mass x w hmass
  exact h.congr_left (fun σ => by
    rw [hlin]
    ring)

/--
Uniform fixed-cardinality BIS has zero centered moment in the all-ones
direction.

This is the finite covariance version of the paper's second high-noise layer:
fixing the participation count removes variance in the all-ones direction.
-/
theorem bisFixedCardUniformInnerCenteredSecondMoment_constOne_fin
    {T k : ℕ} (hk : k ≤ T) :
    (Finset.sum Finset.univ fun u : Finset (Fin T) =>
        bisFixedCardUniformMass (Finset.univ : Finset (Fin T)) k u
          * (Finset.sum Finset.univ
              (fun i : Fin T => (if i ∈ u then (1 : ℝ) else 0) * (1 : ℝ))) ^ 2)
      - (Finset.sum Finset.univ fun i : Fin T =>
          bisWeightedMeanCoord
            (fun u : Finset (Fin T) =>
              bisFixedCardUniformMass (Finset.univ : Finset (Fin T)) k u)
            (fun u i => if i ∈ u then (1 : ℝ) else 0) i * (1 : ℝ)) ^ 2
      = 0 := by
  have hfirst : (Finset.sum Finset.univ fun u : Finset (Fin T) =>
        bisFixedCardUniformMass (Finset.univ : Finset (Fin T)) k u
          * (Finset.sum Finset.univ
              (fun i : Fin T => (if i ∈ u then (1 : ℝ) else 0) * (1 : ℝ))) ^ 2)
      = (k : ℝ) ^ 2 := by
    calc
      (Finset.sum Finset.univ fun u : Finset (Fin T) =>
        bisFixedCardUniformMass (Finset.univ : Finset (Fin T)) k u
          * (Finset.sum Finset.univ
              (fun i : Fin T => (if i ∈ u then (1 : ℝ) else 0) * (1 : ℝ))) ^ 2)
        = Finset.sum Finset.univ (fun u : Finset (Fin T) =>
            bisFixedCardUniformMass (Finset.univ : Finset (Fin T)) k u * (u.card : ℝ) ^ 2) := by
            refine Finset.sum_congr rfl ?_
            intro u _
            rw [show (Finset.sum Finset.univ
                (fun i : Fin T => (if i ∈ u then (1 : ℝ) else 0) * (1 : ℝ)))
                = (u.card : ℝ) by
              simp [bisSubsetIndicator_sum_eq_card u]]
      _ = Finset.sum ((Finset.univ : Finset (Fin T)).powersetCard k)
          (fun u : Finset (Fin T) =>
            bisFixedCardUniformMass (Finset.univ : Finset (Fin T)) k u * (u.card : ℝ) ^ 2) := by
          symm
          refine Finset.sum_subset (by intro u hu; simp) ?_
          intro u _hu hnot
          unfold bisFixedCardUniformMass
          simp [hnot]
      _ = (k : ℝ) ^ 2 := by
          rw [bisFixedCardUniformMass_secondMoment_count_eq_sq
            (Finset.univ : Finset (Fin T)) k (by simpa [Finset.card_univ] using hk)]
  have hsecond : (Finset.sum Finset.univ fun i : Fin T =>
          bisWeightedMeanCoord
            (fun u : Finset (Fin T) =>
              bisFixedCardUniformMass (Finset.univ : Finset (Fin T)) k u)
            (fun u i => if i ∈ u then (1 : ℝ) else 0) i * (1 : ℝ)) = (k : ℝ) := by
    rw [← bisWeightedMeanInner_eq_sum_meanCoord_mul
      (fun u : Finset (Fin T) =>
        bisFixedCardUniformMass (Finset.univ : Finset (Fin T)) k u)
      (fun u i => if i ∈ u then (1 : ℝ) else 0) (fun _ : Fin T => (1 : ℝ))]
    calc
      (Finset.sum Finset.univ fun u : Finset (Fin T) =>
          bisFixedCardUniformMass (Finset.univ : Finset (Fin T)) k u *
            Finset.sum Finset.univ
              (fun i : Fin T => (if i ∈ u then (1 : ℝ) else 0) * 1))
        = Finset.sum Finset.univ (fun u : Finset (Fin T) =>
            bisFixedCardUniformMass (Finset.univ : Finset (Fin T)) k u * (u.card : ℝ)) := by
            refine Finset.sum_congr rfl ?_
            intro u _
            rw [show (Finset.sum Finset.univ
                (fun i : Fin T => (if i ∈ u then (1 : ℝ) else 0) * (1 : ℝ)))
                = (u.card : ℝ) by
              simp [bisSubsetIndicator_sum_eq_card u]]
      _ = (k : ℝ) := by
          calc
            Finset.sum Finset.univ (fun u : Finset (Fin T) =>
                bisFixedCardUniformMass (Finset.univ : Finset (Fin T)) k u * (u.card : ℝ))
              = Finset.sum ((Finset.univ : Finset (Fin T)).powersetCard k)
                  (fun u : Finset (Fin T) =>
                    bisFixedCardUniformMass (Finset.univ : Finset (Fin T)) k u * (u.card : ℝ)) := by
                  symm
                  refine Finset.sum_subset (by intro u hu; simp) ?_
                  intro u _hu hnot
                  unfold bisFixedCardUniformMass
                  simp [hnot]
            _ = (k : ℝ) := by
                  rw [bisFixedCardUniformMass_mean_count_eq
                    (Finset.univ : Finset (Fin T)) k (by simpa [Finset.card_univ] using hk)]
  rw [hfirst, hsecond]
  ring

@[simp] theorem bisExactSubsetRatioAverage_zero {t : ℕ}
    (ratio : Fin (t + 1) → ℝ) :
    bisExactSubsetRatioAverage ratio 0 = 1 := by
  unfold bisExactSubsetRatioAverage
  simp

theorem bisScreeningBoundTarget_zero {t : ℕ}
    (ratio : Fin (t + 1) → ℝ) :
    bisScreeningBoundTarget ratio 0 := by
  intro _hnonneg
  simp [bisScreeningAverage]

@[simp] theorem bisExactSubsetRatioAverage_one {t : ℕ}
    (ratio : Fin (t + 1) → ℝ) :
    bisExactSubsetRatioAverage ratio 1
      = (Finset.sum Finset.univ ratio) / (t + 1 : ℝ) := by
  unfold bisExactSubsetRatioAverage
  rw [Finset.powersetCard_one]
  simp

theorem bisScreeningBoundTarget_one {t : ℕ}
    (ratio : Fin (t + 1) → ℝ) :
    bisScreeningBoundTarget ratio 1 := by
  intro _hnonneg
  simp [bisScreeningAverage]

end
end DP
end Mf
