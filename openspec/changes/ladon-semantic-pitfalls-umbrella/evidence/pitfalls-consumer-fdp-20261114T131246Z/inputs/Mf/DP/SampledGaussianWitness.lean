import Mf.DP.ClassicalEventDPProfileSubsampling
import Mf.DP.FDPSubsampling
import Mf.DP.PoissonGaussianMixturePLD
import Mf.DP.ProductGaussianMixturePLD
import Mf.DP.ProductGaussianMixtureProfileDomination

namespace Mf
namespace DP

noncomputable section

/-!
Sampled-Gaussian subsampling theorem surface.

This module is the first concrete consumer of the tradeoff/GDP/subsampling
infrastructure. It packages the classical subsampling reparameterization into a
named GDP witness and exposes theorem-facing wrappers that compare that witness
to the exact Poisson Gaussian-mixture tradeoff surface.

The current theorem layer is intentionally split in two:
- the classical event-DP `C_p` theorem is now reusable via
  `Mf.DP.ClassicalEventDPSubsampling`
- the stronger appendix-style classical sampled event-bound export is now
  reusable via `Mf.DP.ClassicalEventDPProfileSubsampling`
- the exact sampled-Poisson Gaussian endpoint still needs an additional
  bridge-envelope closure beyond those classical layers

A later change can discharge that remaining exact-consumer hypothesis for
specific sampled Gaussian families.

Literature anchors:
- `paper/theory/mu-dp/subsample.tex`
- `paper/theory/mu-dp/fDP/GDP.tex`
- `paper/theory/prv/arxiv_version.tex` `sec:poisson`
-/

/--
Inverse reparameterization from the sampled privacy parameter back to the base
GDP parameter appearing in the weighted branch of the `C_p` subsampling
operator.

For `p > 0` and `ε >= 0`, this is the unique `η` such that
`log (1 - p + p * exp η) = ε`.
-/
def sampledGaussianBaseEpsilon (p ε : ℝ) : ℝ :=
  Real.log ((Real.exp ε - 1 + p) / p)

/--
Named sampled-Gaussian GDP profile witness obtained by the classical weighted
branch `δ' = p δ`.
-/
def sampledGaussianGDPWitnessProfile (μ p ε : ℝ) : ℝ :=
  p * gdpProfile μ (sampledGaussianBaseEpsilon p ε)

/--
Named theorem-facing tradeoff witness induced by the sampled-Gaussian GDP
profile bound at privacy parameter `ε`.
-/
def sampledGaussianGDPWeightedWitness (μ p ε : ℝ) : TradeoffFunction :=
  TradeoffFunction.ofDPEventBound ε (sampledGaussianGDPWitnessProfile μ p ε)

/--
Named theorem-facing inverse-branch witness from the `C_p` subsampling
operator, still parameterized by the public sampled privacy level `ε`.

This is the `f_p^{-1}` branch corresponding to the same base GDP tradeoff used
by the weighted witness, and is the natural second consumer surface when the
weighted/profile route is too weak to close the sampled theorem.
-/
def sampledGaussianGDPInverseWitness (μ p ε : ℝ) : TradeoffFunction :=
  TradeoffFunction.leftContinuousInverse
    (TradeoffFunction.withIdentityWeight p
      ((⟨μ⟩ : GaussianDP).tradeoffAt (sampledGaussianBaseEpsilon p ε)))

/--
Named theorem-facing raw sampled-Gaussian witness corresponding to the
symmetrized `min {f_p, f_p^{-1}}` layer before convexification.

This is the right public witness surface when one wants to reason against the
actual raw `C_p` ingredients rather than only the weighted or inverse branches
separately.
-/
def sampledGaussianGDPRawWitness (μ p ε : ℝ) : TradeoffFunction :=
  TradeoffFunction.rawPSamplingOperator p
    ((⟨μ⟩ : GaussianDP).tradeoffAt (sampledGaussianBaseEpsilon p ε))

private theorem tradeoffFunction_eq_of_eval_eq
    {T U : TradeoffFunction}
    (h : ∀ α : ℝ, T.eval α = U.eval α) :
    T = U := by
  cases T with
  | mk evalT lowerT upperT =>
    cases U with
    | mk evalU lowerU upperU =>
      have hfun : evalT = evalU := by
        funext α
        exact h α
      cases hfun
      have hlower : lowerT = lowerU := Subsingleton.elim _ _
      have hupper : upperT = upperU := Subsingleton.elim _ _
      cases hlower
      cases hupper
      rfl

@[simp] theorem sampledGaussianGDPWeightedWitness_eval
    (μ p ε α : ℝ) :
    (sampledGaussianGDPWeightedWitness μ p ε).eval α =
      1 - sampledGaussianGDPWitnessProfile μ p ε - Real.exp ε * α := by
  rfl

/--
For `p > 0` and `ε >= 0`, the named weighted sampled-GDP witness evaluates
exactly as the paper's weighted branch `f_p` applied to the base GDP tradeoff
at the reparameterized privacy level.
-/
theorem sampledGaussianGDPWeightedWitness_eval_eq_withIdentityWeight_tradeoffAt
    (μ p ε α : ℝ)
    (hp : 0 < p)
    (hε : 0 ≤ ε) :
    (sampledGaussianGDPWeightedWitness μ p ε).eval α =
      (TradeoffFunction.withIdentityWeight p
        ((⟨μ⟩ : GaussianDP).tradeoffAt (sampledGaussianBaseEpsilon p ε))).eval α := by
  rw [sampledGaussianGDPWeightedWitness_eval]
  rw [TradeoffFunction.withIdentityWeight_eval, GaussianDP.tradeoffAt_eval]
  have hbase :
      Real.exp (sampledGaussianBaseEpsilon p ε) = (Real.exp ε - 1 + p) / p := by
    have hExp : 1 ≤ Real.exp ε := by
      exact Real.one_le_exp_iff.mpr hε
    have hNum : 0 < Real.exp ε - 1 + p := by
      nlinarith
    have hDiv : 0 < (Real.exp ε - 1 + p) / p := div_pos hNum hp
    simpa [sampledGaussianBaseEpsilon] using Real.exp_log hDiv
  rw [hbase]
  have hLinear :
      p *
          (1
            - gdpProfile μ (sampledGaussianBaseEpsilon p ε)
            - ((Real.exp ε - 1 + p) / p) * α) +
        (1 - p) * (1 - α) =
        1 - p * gdpProfile μ (sampledGaussianBaseEpsilon p ε) - Real.exp ε * α := by
    field_simp [hp.ne']
    ring
  have hTarget :
      1 - p * gdpProfile μ (sampledGaussianBaseEpsilon p ε) - Real.exp ε * α =
      1 - sampledGaussianGDPWitnessProfile μ p ε - Real.exp ε * α := by
    simp [sampledGaussianGDPWitnessProfile]
  rw [hLinear, hTarget]

@[simp] theorem sampledGaussianGDPInverseWitness_eval
    (μ p ε α : ℝ) :
    (sampledGaussianGDPInverseWitness μ p ε).eval α =
      (TradeoffFunction.leftContinuousInverse
        (TradeoffFunction.withIdentityWeight p
          ((⟨μ⟩ : GaussianDP).tradeoffAt (sampledGaussianBaseEpsilon p ε)))).eval α := by
  rfl

/--
For `p > 0` and `ε >= 0`, the named inverse sampled-GDP witness evaluates
exactly as the left-continuous inverse of the named weighted sampled-GDP
witness.
-/
theorem sampledGaussianGDPInverseWitness_eval_eq_leftContinuousInverse_weightedWitness
    (μ p ε α : ℝ)
    (hp : 0 < p)
    (hε : 0 ≤ ε) :
    (sampledGaussianGDPInverseWitness μ p ε).eval α =
      (TradeoffFunction.leftContinuousInverse
        (sampledGaussianGDPWeightedWitness μ p ε)).eval α := by
  have hWeighted :
      TradeoffFunction.withIdentityWeight p
          ((⟨μ⟩ : GaussianDP).tradeoffAt (sampledGaussianBaseEpsilon p ε)) =
        sampledGaussianGDPWeightedWitness μ p ε := by
    apply tradeoffFunction_eq_of_eval_eq
    intro β
    symm
    exact sampledGaussianGDPWeightedWitness_eval_eq_withIdentityWeight_tradeoffAt
      μ p ε β hp hε
  rw [sampledGaussianGDPInverseWitness_eval, hWeighted]

@[simp] theorem sampledGaussianGDPRawWitness_eval
    (μ p ε α : ℝ) :
    (sampledGaussianGDPRawWitness μ p ε).eval α =
      min
        ((TradeoffFunction.withIdentityWeight p
          ((⟨μ⟩ : GaussianDP).tradeoffAt (sampledGaussianBaseEpsilon p ε))).eval α)
        ((TradeoffFunction.leftContinuousInverse
          (TradeoffFunction.withIdentityWeight p
            ((⟨μ⟩ : GaussianDP).tradeoffAt (sampledGaussianBaseEpsilon p ε)))).eval α) := by
  rfl

/--
Under the usual sampled-Gaussian side conditions, the raw witness evaluates as
the pointwise minimum of the named weighted and inverse witnesses.
-/
theorem sampledGaussianGDPRawWitness_eval_eq_min_namedWitnesses
    (μ p ε α : ℝ)
    (hp : 0 < p)
    (hε : 0 ≤ ε) :
    (sampledGaussianGDPRawWitness μ p ε).eval α =
      min
        ((sampledGaussianGDPWeightedWitness μ p ε).eval α)
        ((sampledGaussianGDPInverseWitness μ p ε).eval α) := by
  have hWeighted :
      TradeoffFunction.withIdentityWeight p
          ((⟨μ⟩ : GaussianDP).tradeoffAt (sampledGaussianBaseEpsilon p ε)) =
        sampledGaussianGDPWeightedWitness μ p ε := by
    apply tradeoffFunction_eq_of_eval_eq
    intro β
    symm
    exact sampledGaussianGDPWeightedWitness_eval_eq_withIdentityWeight_tradeoffAt
      μ p ε β hp hε
  rw [sampledGaussianGDPRawWitness_eval]
  rw [hWeighted]
  rw [sampledGaussianGDPInverseWitness_eval_eq_leftContinuousInverse_weightedWitness μ p ε α hp hε]

/--
Closed form for the left-continuous inverse of the affine `(ε, δ)` event-bound
witness.

This is the clipped threshold solving
`1 - δ - exp ε * t <= α` over the unit interval.
-/
theorem leftContinuousInverse_ofDPEventBound_eval
    (ε δ α : ℝ) :
    (TradeoffFunction.leftContinuousInverse (TradeoffFunction.ofDPEventBound ε δ)).eval α =
      max 0 (min 1 ((1 - δ - α) / Real.exp ε)) := by
  rw [TradeoffFunction.leftContinuousInverse_eval]
  let s : ℝ := (1 - δ - α) / Real.exp ε
  have hExpPos : 0 < Real.exp ε := Real.exp_pos ε
  have hBdd : BddBelow
      (TradeoffFunction.leftInverseSet
        (TradeoffFunction.ofDPEventBound ε δ) α) := by
    refine ⟨0, ?_⟩
    intro t ht
    rcases ht with ht | rfl
    · exact ht.1
    · norm_num
  by_cases hs0 : s ≤ 0
  · have hzero_mem :
        (0 : ℝ) ∈ TradeoffFunction.leftInverseSet (TradeoffFunction.ofDPEventBound ε δ) α := by
      left
      refine ⟨by norm_num, by norm_num, ?_⟩
      rw [TradeoffFunction.ofDPEventBound_eval]
      have hs0' : 1 - δ - α ≤ 0 := by
        dsimp [s] at hs0
        by_contra hpos
        have hsPos : 0 < s := by
          dsimp [s]
          exact div_pos (lt_of_not_ge hpos) hExpPos
        linarith
      linarith
    have hzero_lb :
        0 ≤ sInf (TradeoffFunction.leftInverseSet (TradeoffFunction.ofDPEventBound ε δ) α) := by
      exact le_csInf ⟨1, Or.inr rfl⟩ (by
        intro t ht
        rcases ht with ht | rfl
        · exact ht.1
        · norm_num)
    have hInf_le_zero :
        sInf (TradeoffFunction.leftInverseSet (TradeoffFunction.ofDPEventBound ε δ) α) ≤ 0 := by
      exact csInf_le hBdd hzero_mem
    have hsMin : min 1 s = s := min_eq_right (by linarith)
    have hsMax : max 0 s = 0 := max_eq_left hs0
    have hclip : max 0 (min 1 ((1 - δ - α) / Real.exp ε)) = 0 := by
      change max 0 (min 1 s) = 0
      rw [hsMin, hsMax]
    rw [hclip]
    exact le_antisymm hInf_le_zero hzero_lb
  · have hs_pos : 0 < s := lt_of_not_ge hs0
    by_cases hs1 : s ≤ 1
    · have hs_mem :
          s ∈ TradeoffFunction.leftInverseSet (TradeoffFunction.ofDPEventBound ε δ) α := by
        left
        refine ⟨le_of_lt hs_pos, hs1, ?_⟩
        rw [TradeoffFunction.ofDPEventBound_eval]
        have hsEq : 1 - δ - Real.exp ε * s = α := by
          dsimp [s]
          field_simp [hExpPos.ne']
          ring
        linarith [hsEq]
      have hs_lb :
          s ≤ sInf (TradeoffFunction.leftInverseSet (TradeoffFunction.ofDPEventBound ε δ) α) := by
        refine le_csInf ⟨1, Or.inr rfl⟩ ?_
        intro t ht
        rcases ht with ht | rfl
        · have htIneq : 1 - δ - Real.exp ε * t ≤ α := ht.2.2
          have : s ≤ t := by
            by_contra hst
            have ht_lt : t < s := lt_of_not_ge hst
            have hnum_le : 1 - δ - α ≤ Real.exp ε * t := by
              linarith
            have hmul_lt : Real.exp ε * t < 1 - δ - α := by
              have hmul_lt' : Real.exp ε * t < Real.exp ε * s := by
                exact mul_lt_mul_of_pos_left ht_lt hExpPos
              dsimp [s] at hmul_lt' ⊢
              field_simp [hExpPos.ne'] at hmul_lt'
              linarith
            exact False.elim ((not_lt_of_ge hnum_le) hmul_lt)
          exact this
        · linarith
      have hInf_le_s :
          sInf (TradeoffFunction.leftInverseSet (TradeoffFunction.ofDPEventBound ε δ) α) ≤ s := by
        exact csInf_le hBdd hs_mem
      have hsMin : min 1 s = s := min_eq_right hs1
      have hsMax : max 0 s = s := max_eq_right (le_of_lt hs_pos)
      have hclip : max 0 (min 1 ((1 - δ - α) / Real.exp ε)) = s := by
        change max 0 (min 1 s) = s
        rw [hsMin, hsMax]
      rw [hclip]
      exact le_antisymm hInf_le_s hs_lb
    · have hs_gt_one : 1 < s := lt_of_not_ge hs1
      have hleft_empty :
          ∀ t : ℝ,
            ¬ (0 ≤ t ∧
              t ≤ 1 ∧
              (TradeoffFunction.ofDPEventBound ε δ).eval t ≤ α) := by
          intro t ht
          have ht_le : t ≤ 1 := ht.2.1
          have hs_le_t : s ≤ t := by
            have htIneq : 1 - δ - Real.exp ε * t ≤ α := ht.2.2
            by_contra hst
            have ht_lt : t < s := lt_of_not_ge hst
            have hnum_le : 1 - δ - α ≤ Real.exp ε * t := by
              linarith
            have hmul_lt : Real.exp ε * t < 1 - δ - α := by
              have hmul_lt' : Real.exp ε * t < Real.exp ε * s := by
                exact mul_lt_mul_of_pos_left ht_lt hExpPos
              dsimp [s] at hmul_lt' ⊢
              field_simp [hExpPos.ne'] at hmul_lt'
              linarith
            exact False.elim ((not_lt_of_ge hnum_le) hmul_lt)
          linarith
      have hInf_eq_one :
          sInf (TradeoffFunction.leftInverseSet (TradeoffFunction.ofDPEventBound ε δ) α) = 1 := by
        apply le_antisymm
        · exact csInf_le hBdd (by right; rfl)
        · refine le_csInf ⟨1, Or.inr rfl⟩ ?_
          intro t ht
          rcases ht with ht | rfl
          · exact False.elim (hleft_empty t ht)
          · linarith
      have hsMin : min 1 s = 1 := min_eq_left (le_of_lt hs_gt_one)
      have hclip : max 0 (min 1 ((1 - δ - α) / Real.exp ε)) = 1 := by
        change max 0 (min 1 s) = 1
        rw [hsMin, max_eq_right (by norm_num : 0 ≤ (1 : ℝ))]
      rw [hInf_eq_one, hclip]

/--
Closed form for the named inverse sampled-GDP witness.
-/
theorem sampledGaussianGDPInverseWitness_eval_eq_clippedAffine
    (μ p ε α : ℝ)
    (hp : 0 < p)
    (hε : 0 ≤ ε) :
    (sampledGaussianGDPInverseWitness μ p ε).eval α =
      max 0
        (min 1
          ((1 - sampledGaussianGDPWitnessProfile μ p ε - α) / Real.exp ε)) := by
  rw [sampledGaussianGDPInverseWitness_eval_eq_leftContinuousInverse_weightedWitness
    μ p ε α hp hε]
  simpa [sampledGaussianGDPWeightedWitness] using
    leftContinuousInverse_ofDPEventBound_eval ε (sampledGaussianGDPWitnessProfile μ p ε) α

/--
Closed form for the raw sampled-GDP witness as the minimum of the weighted
affine branch and the clipped affine inverse branch.
-/
theorem sampledGaussianGDPRawWitness_eval_eq_min_affine_clippedAffine
    (μ p ε α : ℝ)
    (hp : 0 < p)
    (hε : 0 ≤ ε) :
    (sampledGaussianGDPRawWitness μ p ε).eval α =
      min
        (1 - sampledGaussianGDPWitnessProfile μ p ε - Real.exp ε * α)
        (max 0 (min 1 ((1 - sampledGaussianGDPWitnessProfile μ p ε - α) / Real.exp ε))) := by
  rw [sampledGaussianGDPRawWitness_eval_eq_min_namedWitnesses μ p ε α hp hε]
  rw [sampledGaussianGDPWeightedWitness_eval]
  rw [sampledGaussianGDPInverseWitness_eval_eq_clippedAffine μ p ε α hp hε]

/--
On the natural window `0 <= α <= 1 - δ`, the inverse sampled-GDP witness
unclamps to the simple affine threshold formula.
-/
theorem sampledGaussianGDPInverseWitness_eval_eq_affine_of_window
    (μ p ε α : ℝ)
    (hp : 0 < p)
    (hε : 0 ≤ ε)
    (hδ0 : 0 ≤ sampledGaussianGDPWitnessProfile μ p ε)
    (hα0 : 0 ≤ α)
    (hα1 : α ≤ 1 - sampledGaussianGDPWitnessProfile μ p ε) :
    (sampledGaussianGDPInverseWitness μ p ε).eval α =
      (1 - sampledGaussianGDPWitnessProfile μ p ε - α) / Real.exp ε := by
  rw [sampledGaussianGDPInverseWitness_eval_eq_clippedAffine μ p ε α hp hε]
  have hExpPos : 0 < Real.exp ε := Real.exp_pos ε
  have hExpOne : 1 ≤ Real.exp ε := Real.one_le_exp_iff.mpr hε
  have hNumNonneg : 0 ≤ 1 - sampledGaussianGDPWitnessProfile μ p ε - α := by
    linarith
  have hNumLeOne : 1 - sampledGaussianGDPWitnessProfile μ p ε - α ≤ 1 := by
    linarith
  have hFracNonneg :
      0 ≤ (1 - sampledGaussianGDPWitnessProfile μ p ε - α) / Real.exp ε := by
    exact div_nonneg hNumNonneg (le_of_lt hExpPos)
  have hFracLeOne :
      (1 - sampledGaussianGDPWitnessProfile μ p ε - α) / Real.exp ε ≤ 1 := by
    have hNumLeExp : 1 - sampledGaussianGDPWitnessProfile μ p ε - α ≤ Real.exp ε := by
      exact le_trans hNumLeOne hExpOne
    have hNumLeExp' :
        1 - sampledGaussianGDPWitnessProfile μ p ε - α ≤ 1 * Real.exp ε := by
      simpa [one_mul] using hNumLeExp
    exact (div_le_iff₀ hExpPos).2 hNumLeExp'
  rw [min_eq_right hFracLeOne, max_eq_right hFracNonneg]

/--
The inverse sampled-GDP witness is always clipped into the unit interval.
-/
theorem sampledGaussianGDPInverseWitness_eval_nonneg
    (μ p ε α : ℝ)
    (hp : 0 < p)
    (hε : 0 ≤ ε) :
    0 ≤ (sampledGaussianGDPInverseWitness μ p ε).eval α := by
  rw [sampledGaussianGDPInverseWitness_eval_eq_clippedAffine μ p ε α hp hε]
  exact le_max_left _ _

/--
The inverse sampled-GDP witness is always at most `1`.
-/
theorem sampledGaussianGDPInverseWitness_eval_le_one
    (μ p ε α : ℝ)
    (hp : 0 < p)
    (hε : 0 ≤ ε) :
    (sampledGaussianGDPInverseWitness μ p ε).eval α ≤ 1 := by
  rw [sampledGaussianGDPInverseWitness_eval_eq_clippedAffine μ p ε α hp hε]
  calc
    max 0 (min 1 ((1 - sampledGaussianGDPWitnessProfile μ p ε - α) / Real.exp ε))
        ≤ 1 := by
          exact max_le (by norm_num) (min_le_left _ _)

/--
On the natural window and below the switch threshold, the inverse branch lies
below the weighted branch.
-/
theorem sampledGaussianGDPInverseWitness_eval_le_weighted_of_window_of_le_switch
    (μ p ε α : ℝ)
    (hp : 0 < p)
    (hε : 0 ≤ ε)
    (hδ0 : 0 ≤ sampledGaussianGDPWitnessProfile μ p ε)
    (hα0 : 0 ≤ α)
    (hα1 : α ≤ 1 - sampledGaussianGDPWitnessProfile μ p ε)
    (hswitch :
      α ≤ (1 - sampledGaussianGDPWitnessProfile μ p ε) / (Real.exp ε + 1)) :
    (sampledGaussianGDPInverseWitness μ p ε).eval α ≤
      (sampledGaussianGDPWeightedWitness μ p ε).eval α := by
  rw [sampledGaussianGDPInverseWitness_eval_eq_affine_of_window μ p ε α hp hε hδ0 hα0 hα1]
  rw [sampledGaussianGDPWeightedWitness_eval]
  have hDenPos : 0 < Real.exp ε + 1 := by positivity
  have hswitch' :
      α * (Real.exp ε + 1) ≤ 1 - sampledGaussianGDPWitnessProfile μ p ε := by
    exact (le_div_iff₀ hDenPos).mp hswitch
  have hExpPos : 0 < Real.exp ε := Real.exp_pos ε
  have hExpSubNonneg : 0 ≤ Real.exp ε - 1 := by
    nlinarith [Real.one_le_exp_iff.mpr hε]
  have hInnerNonneg :
      0 ≤ 1 - sampledGaussianGDPWitnessProfile μ p ε - α * (Real.exp ε + 1) := by
    nlinarith [hswitch']
  refine (div_le_iff₀ hExpPos).2 ?_
  nlinarith [hExpSubNonneg, hInnerNonneg]

/--
On the natural window and above the switch threshold, the weighted branch lies
below the inverse branch.
-/
theorem sampledGaussianGDPWeightedWitness_eval_le_inverse_of_window_of_switch_le
    (μ p ε α : ℝ)
    (hp : 0 < p)
    (hε : 0 ≤ ε)
    (hδ0 : 0 ≤ sampledGaussianGDPWitnessProfile μ p ε)
    (hα0 : 0 ≤ α)
    (hα1 : α ≤ 1 - sampledGaussianGDPWitnessProfile μ p ε)
    (hswitch :
      (1 - sampledGaussianGDPWitnessProfile μ p ε) / (Real.exp ε + 1) ≤ α) :
    (sampledGaussianGDPWeightedWitness μ p ε).eval α ≤
      (sampledGaussianGDPInverseWitness μ p ε).eval α := by
  rw [sampledGaussianGDPInverseWitness_eval_eq_affine_of_window μ p ε α hp hε hδ0 hα0 hα1]
  rw [sampledGaussianGDPWeightedWitness_eval]
  have hDenPos : 0 < Real.exp ε + 1 := by positivity
  have hswitch' :
      1 - sampledGaussianGDPWitnessProfile μ p ε ≤ α * (Real.exp ε + 1) := by
    exact (div_le_iff₀ hDenPos).mp hswitch
  have hExpPos : 0 < Real.exp ε := Real.exp_pos ε
  have hExpSubNonneg : 0 ≤ Real.exp ε - 1 := by
    nlinarith [Real.one_le_exp_iff.mpr hε]
  have hInnerNonpos :
      1 - sampledGaussianGDPWitnessProfile μ p ε - α * (Real.exp ε + 1) ≤ 0 := by
    nlinarith [hswitch']
  have hMul :
      (1 - sampledGaussianGDPWitnessProfile μ p ε - Real.exp ε * α) * Real.exp ε ≤
        1 - sampledGaussianGDPWitnessProfile μ p ε - α := by
    nlinarith [hExpSubNonneg, hInnerNonpos]
  exact (le_div_iff₀ hExpPos).2 hMul

/--
On the natural window and below the switch threshold, the raw sampled-GDP
witness is realized by the inverse branch.
-/
theorem sampledGaussianGDPRawWitness_eval_eq_inverse_of_window_of_le_switch
    (μ p ε α : ℝ)
    (hp : 0 < p)
    (hε : 0 ≤ ε)
    (hδ0 : 0 ≤ sampledGaussianGDPWitnessProfile μ p ε)
    (hα0 : 0 ≤ α)
    (hα1 : α ≤ 1 - sampledGaussianGDPWitnessProfile μ p ε)
    (hswitch :
      α ≤ (1 - sampledGaussianGDPWitnessProfile μ p ε) / (Real.exp ε + 1)) :
    (sampledGaussianGDPRawWitness μ p ε).eval α =
      (sampledGaussianGDPInverseWitness μ p ε).eval α := by
  rw [sampledGaussianGDPRawWitness_eval_eq_min_namedWitnesses μ p ε α hp hε]
  apply min_eq_right
  exact sampledGaussianGDPInverseWitness_eval_le_weighted_of_window_of_le_switch
    μ p ε α hp hε hδ0 hα0 hα1 hswitch

/--
On the natural window and above the switch threshold, the raw sampled-GDP
witness is realized by the weighted branch.
-/
theorem sampledGaussianGDPRawWitness_eval_eq_weighted_of_window_of_switch_le
    (μ p ε α : ℝ)
    (hp : 0 < p)
    (hε : 0 ≤ ε)
    (hδ0 : 0 ≤ sampledGaussianGDPWitnessProfile μ p ε)
    (hα0 : 0 ≤ α)
    (hα1 : α ≤ 1 - sampledGaussianGDPWitnessProfile μ p ε)
    (hswitch :
      (1 - sampledGaussianGDPWitnessProfile μ p ε) / (Real.exp ε + 1) ≤ α) :
    (sampledGaussianGDPRawWitness μ p ε).eval α =
      (sampledGaussianGDPWeightedWitness μ p ε).eval α := by
  rw [sampledGaussianGDPRawWitness_eval_eq_min_namedWitnesses μ p ε α hp hε]
  apply min_eq_left
  exact sampledGaussianGDPWeightedWitness_eval_le_inverse_of_window_of_switch_le
    μ p ε α hp hε hδ0 hα0 hα1 hswitch

/--
On the natural window and below the switch threshold, the raw sampled-GDP
witness has the explicit inverse-branch affine form.
-/
theorem sampledGaussianGDPRawWitness_eval_eq_affineInverse_of_window_of_le_switch
    (μ p ε α : ℝ)
    (hp : 0 < p)
    (hε : 0 ≤ ε)
    (hδ0 : 0 ≤ sampledGaussianGDPWitnessProfile μ p ε)
    (hα0 : 0 ≤ α)
    (hα1 : α ≤ 1 - sampledGaussianGDPWitnessProfile μ p ε)
    (hswitch :
      α ≤ (1 - sampledGaussianGDPWitnessProfile μ p ε) / (Real.exp ε + 1)) :
    (sampledGaussianGDPRawWitness μ p ε).eval α =
      (1 - sampledGaussianGDPWitnessProfile μ p ε - α) / Real.exp ε := by
  rw [sampledGaussianGDPRawWitness_eval_eq_inverse_of_window_of_le_switch
    μ p ε α hp hε hδ0 hα0 hα1 hswitch]
  exact sampledGaussianGDPInverseWitness_eval_eq_affine_of_window
    μ p ε α hp hε hδ0 hα0 hα1

/--
On the natural window and above the switch threshold, the raw sampled-GDP
witness has the explicit weighted-branch affine form.
-/
theorem sampledGaussianGDPRawWitness_eval_eq_affineWeighted_of_window_of_switch_le
    (μ p ε α : ℝ)
    (hp : 0 < p)
    (hε : 0 ≤ ε)
    (hδ0 : 0 ≤ sampledGaussianGDPWitnessProfile μ p ε)
    (hα0 : 0 ≤ α)
    (hα1 : α ≤ 1 - sampledGaussianGDPWitnessProfile μ p ε)
    (hswitch :
      (1 - sampledGaussianGDPWitnessProfile μ p ε) / (Real.exp ε + 1) ≤ α) :
    (sampledGaussianGDPRawWitness μ p ε).eval α =
      1 - sampledGaussianGDPWitnessProfile μ p ε - Real.exp ε * α := by
  rw [sampledGaussianGDPRawWitness_eval_eq_weighted_of_window_of_switch_le
    μ p ε α hp hε hδ0 hα0 hα1 hswitch]
  exact sampledGaussianGDPWeightedWitness_eval μ p ε α

/--
Piecewise-affine formula for the raw sampled-GDP witness on the natural window.

This is the local analogue of the piecewise-affine surfaces emphasized in
`paper/theory/composition-theorems`, Appendix
`subsec:computation_piecewise_affine`: below the switch threshold the raw
witness follows the inverse affine branch, and above it follows the weighted
affine branch.
-/
theorem sampledGaussianGDPRawWitness_eval_eq_piecewise_of_window
    (μ p ε α : ℝ)
    (hp : 0 < p)
    (hε : 0 ≤ ε)
    (hδ0 : 0 ≤ sampledGaussianGDPWitnessProfile μ p ε)
    (hα0 : 0 ≤ α)
    (hα1 : α ≤ 1 - sampledGaussianGDPWitnessProfile μ p ε) :
    (sampledGaussianGDPRawWitness μ p ε).eval α =
      if α ≤ (1 - sampledGaussianGDPWitnessProfile μ p ε) / (Real.exp ε + 1) then
        (1 - sampledGaussianGDPWitnessProfile μ p ε - α) / Real.exp ε
      else
        1 - sampledGaussianGDPWitnessProfile μ p ε - Real.exp ε * α := by
  by_cases hswitch :
      α ≤ (1 - sampledGaussianGDPWitnessProfile μ p ε) / (Real.exp ε + 1)
  · rw [if_pos hswitch]
    exact sampledGaussianGDPRawWitness_eval_eq_affineInverse_of_window_of_le_switch
      μ p ε α hp hε hδ0 hα0 hα1 hswitch
  · rw [if_neg hswitch]
    exact sampledGaussianGDPRawWitness_eval_eq_affineWeighted_of_window_of_switch_le
      μ p ε α hp hε hδ0 hα0 hα1 (le_of_not_ge hswitch)

/--
If the exact Poisson Gaussian-mixture tradeoff dominates the inverse affine
branch below the switch threshold and the weighted affine branch above the
switch threshold, then it dominates the raw sampled-GDP witness on the whole
natural window.
-/
theorem sgdpRaw_eval_le_pgmTradeoff_of_pwBounds
    {d m : ℕ}
    (μ : ℝ)
    (C : Fin m → Fin d → ℝ)
    (p ε α : ℝ)
    (hp : 0 < p)
    (hp1 : p ≤ 1)
    (σ : ℝ)
    (hε : 0 ≤ ε)
    (hδ0 : 0 ≤ sampledGaussianGDPWitnessProfile μ p ε)
    (hα0 : 0 ≤ α)
    (hα1 : α ≤ 1 - sampledGaussianGDPWitnessProfile μ p ε)
    (hinv :
      α ≤ (1 - sampledGaussianGDPWitnessProfile μ p ε) / (Real.exp ε + 1) →
        (1 - sampledGaussianGDPWitnessProfile μ p ε - α) / Real.exp ε ≤
          (poissonGaussianMixtureTradeoffAt C p ε hp.le hp1 σ).eval α)
    (hweighted :
      (1 - sampledGaussianGDPWitnessProfile μ p ε) / (Real.exp ε + 1) ≤ α →
        1 - sampledGaussianGDPWitnessProfile μ p ε - Real.exp ε * α ≤
          (poissonGaussianMixtureTradeoffAt C p ε hp.le hp1 σ).eval α) :
    (sampledGaussianGDPRawWitness μ p ε).eval α ≤
      (poissonGaussianMixtureTradeoffAt C p ε hp.le hp1 σ).eval α := by
  by_cases hswitch :
      α ≤ (1 - sampledGaussianGDPWitnessProfile μ p ε) / (Real.exp ε + 1)
  · rw [sampledGaussianGDPRawWitness_eval_eq_affineInverse_of_window_of_le_switch
      μ p ε α hp hε hδ0 hα0 hα1 hswitch]
    exact hinv hswitch
  · rw [sampledGaussianGDPRawWitness_eval_eq_affineWeighted_of_window_of_switch_le
      μ p ε α hp hε hδ0 hα0 hα1 (le_of_not_ge hswitch)]
    exact hweighted (le_of_not_ge hswitch)

/--
Windowwise raw sampled-GDP comparison theorem from branchwise affine upper
bounds against the exact Poisson Gaussian-mixture tradeoff surface.
-/
theorem sgdpRaw_window_le_pgmTradeoff_of_pwBounds
    {d m : ℕ}
    (μ : ℝ)
    (C : Fin m → Fin d → ℝ)
    (p ε : ℝ)
    (hp : 0 < p)
    (hp1 : p ≤ 1)
    (σ : ℝ)
    (hε : 0 ≤ ε)
    (hδ0 : 0 ≤ sampledGaussianGDPWitnessProfile μ p ε)
    (hinv :
      ∀ α : ℝ,
        0 ≤ α →
        α ≤ 1 - sampledGaussianGDPWitnessProfile μ p ε →
        α ≤ (1 - sampledGaussianGDPWitnessProfile μ p ε) / (Real.exp ε + 1) →
          (1 - sampledGaussianGDPWitnessProfile μ p ε - α) / Real.exp ε ≤
            (poissonGaussianMixtureTradeoffAt C p ε hp.le hp1 σ).eval α)
    (hweighted :
      ∀ α : ℝ,
        0 ≤ α →
        α ≤ 1 - sampledGaussianGDPWitnessProfile μ p ε →
        (1 - sampledGaussianGDPWitnessProfile μ p ε) / (Real.exp ε + 1) ≤ α →
          1 - sampledGaussianGDPWitnessProfile μ p ε - Real.exp ε * α ≤
            (poissonGaussianMixtureTradeoffAt C p ε hp.le hp1 σ).eval α) :
    ∀ α : ℝ,
      0 ≤ α →
      α ≤ 1 - sampledGaussianGDPWitnessProfile μ p ε →
      (sampledGaussianGDPRawWitness μ p ε).eval α ≤
        (poissonGaussianMixtureTradeoffAt C p ε hp.le hp1 σ).eval α := by
  intro α hα0 hα1
  exact sgdpRaw_eval_le_pgmTradeoff_of_pwBounds
    μ C p ε α hp hp1 σ hε hδ0 hα0 hα1
    (fun hswitch => hinv α hα0 hα1 hswitch)
    (fun hswitch => hweighted α hα0 hα1 hswitch)

/--
Below the switch threshold on the natural window, any exact-tradeoff bound for
the raw sampled-GDP witness yields the corresponding inverse-affine bound.
-/
theorem affineInverse_eval_le_poissonGaussianMixtureTradeoffAt_of_rawWitness_le
    {d m : ℕ}
    (μ : ℝ)
    (C : Fin m → Fin d → ℝ)
    (p ε α : ℝ)
    (hp : 0 < p)
    (hp1 : p ≤ 1)
    (σ : ℝ)
    (hε : 0 ≤ ε)
    (hδ0 : 0 ≤ sampledGaussianGDPWitnessProfile μ p ε)
    (hα0 : 0 ≤ α)
    (hα1 : α ≤ 1 - sampledGaussianGDPWitnessProfile μ p ε)
    (hswitch :
      α ≤ (1 - sampledGaussianGDPWitnessProfile μ p ε) / (Real.exp ε + 1))
    (hraw :
      (sampledGaussianGDPRawWitness μ p ε).PointwiseLE
        (poissonGaussianMixtureTradeoffAt C p ε hp.le hp1 σ)) :
    (1 - sampledGaussianGDPWitnessProfile μ p ε - α) / Real.exp ε ≤
      (poissonGaussianMixtureTradeoffAt C p ε hp.le hp1 σ).eval α := by
  rw [← sampledGaussianGDPRawWitness_eval_eq_affineInverse_of_window_of_le_switch
    μ p ε α hp hε hδ0 hα0 hα1 hswitch]
  exact hraw α

/--
Above the switch threshold on the natural window, any exact-tradeoff bound for
the raw sampled-GDP witness yields the corresponding weighted-affine bound.
-/
theorem affineWeighted_eval_le_poissonGaussianMixtureTradeoffAt_of_rawWitness_le
    {d m : ℕ}
    (μ : ℝ)
    (C : Fin m → Fin d → ℝ)
    (p ε α : ℝ)
    (hp : 0 < p)
    (hp1 : p ≤ 1)
    (σ : ℝ)
    (hε : 0 ≤ ε)
    (hδ0 : 0 ≤ sampledGaussianGDPWitnessProfile μ p ε)
    (hα0 : 0 ≤ α)
    (hα1 : α ≤ 1 - sampledGaussianGDPWitnessProfile μ p ε)
    (hswitch :
      (1 - sampledGaussianGDPWitnessProfile μ p ε) / (Real.exp ε + 1) ≤ α)
    (hraw :
      (sampledGaussianGDPRawWitness μ p ε).PointwiseLE
        (poissonGaussianMixtureTradeoffAt C p ε hp.le hp1 σ)) :
    1 - sampledGaussianGDPWitnessProfile μ p ε - Real.exp ε * α ≤
      (poissonGaussianMixtureTradeoffAt C p ε hp.le hp1 σ).eval α := by
  rw [← sampledGaussianGDPRawWitness_eval_eq_affineWeighted_of_window_of_switch_le
    μ p ε α hp hε hδ0 hα0 hα1 hswitch]
  exact hraw α

/--
The raw sampled-GDP witness lies below the weighted branch pointwise.
-/
theorem sampledGaussianGDPRawWitness_le_weighted
    (μ p ε : ℝ)
    (hp : 0 < p)
    (hε : 0 ≤ ε) :
    (sampledGaussianGDPRawWitness μ p ε).PointwiseLE
      (sampledGaussianGDPWeightedWitness μ p ε) := by
  intro α
  rw [sampledGaussianGDPRawWitness_eval, sampledGaussianGDPWeightedWitness_eval]
  rw [TradeoffFunction.withIdentityWeight_eval, GaussianDP.tradeoffAt_eval]
  have hbase :
      Real.exp (sampledGaussianBaseEpsilon p ε) = (Real.exp ε - 1 + p) / p := by
    have hExp : 1 ≤ Real.exp ε := by
      exact Real.one_le_exp_iff.mpr hε
    have hNum : 0 < Real.exp ε - 1 + p := by
      nlinarith
    have hDiv : 0 < (Real.exp ε - 1 + p) / p := div_pos hNum hp
    simpa [sampledGaussianBaseEpsilon] using Real.exp_log hDiv
  rw [hbase]
  have hLinear :
      p *
          (1
            - gdpProfile μ (sampledGaussianBaseEpsilon p ε)
            - ((Real.exp ε - 1 + p) / p) * α) +
        (1 - p) * (1 - α) =
        1 - p * gdpProfile μ (sampledGaussianBaseEpsilon p ε) - Real.exp ε * α := by
    field_simp [hp.ne']
    ring
  have hTarget :
      1 - p * gdpProfile μ (sampledGaussianBaseEpsilon p ε) - Real.exp ε * α =
      1 - sampledGaussianGDPWitnessProfile μ p ε - Real.exp ε * α := by
    simp [sampledGaussianGDPWitnessProfile]
  rw [hLinear, hTarget]
  exact min_le_left _ _

/--
The raw sampled-GDP witness lies below the inverse branch pointwise.
-/
theorem sampledGaussianGDPRawWitness_le_inverse
    (μ p ε : ℝ) :
    (sampledGaussianGDPRawWitness μ p ε).PointwiseLE
      (sampledGaussianGDPInverseWitness μ p ε) := by
  intro α
  rw [sampledGaussianGDPRawWitness_eval, sampledGaussianGDPInverseWitness_eval]
  exact min_le_right _ _

/--
Any weighted-branch bound immediately yields the corresponding raw-witness
bound, since the raw witness lies below the weighted branch.
-/
theorem sampledGaussianGDPRawWitness_le_poissonGaussianMixtureTradeoffAt_of_weightedWitness_le
    {d m : ℕ}
    (μ : ℝ)
    (C : Fin m → Fin d → ℝ)
    (p ε : ℝ)
    (hp : 0 < p)
    (hp1 : p ≤ 1)
    (hε : 0 ≤ ε)
    (σ : ℝ)
    (hweighted :
      (sampledGaussianGDPWeightedWitness μ p ε).PointwiseLE
        (poissonGaussianMixtureTradeoffAt C p ε hp.le hp1 σ)) :
    (sampledGaussianGDPRawWitness μ p ε).PointwiseLE
      (poissonGaussianMixtureTradeoffAt C p ε hp.le hp1 σ) := by
  exact TradeoffFunction.pointwiseLE_trans
    (sampledGaussianGDPRawWitness_le_weighted μ p ε hp hε)
    hweighted

/--
Any inverse-branch bound immediately yields the corresponding raw-witness
bound, since the raw witness lies below the inverse branch.
-/
theorem sampledGaussianGDPRawWitness_le_poissonGaussianMixtureTradeoffAt_of_inverseWitness_le
    {d m : ℕ}
    (μ : ℝ)
    (C : Fin m → Fin d → ℝ)
    (p ε : ℝ)
    (hp : 0 < p)
    (hp1 : p ≤ 1)
    (σ : ℝ)
    (hinv :
      (sampledGaussianGDPInverseWitness μ p ε).PointwiseLE
        (poissonGaussianMixtureTradeoffAt C p ε hp.le hp1 σ)) :
    (sampledGaussianGDPRawWitness μ p ε).PointwiseLE
      (poissonGaussianMixtureTradeoffAt C p ε hp.le hp1 σ) := by
  exact TradeoffFunction.pointwiseLE_trans
    (sampledGaussianGDPRawWitness_le_inverse μ p ε)
    hinv

theorem bridgeProfile_eq_gdpProfile_two_mul
    {a ε : ℝ}
    (ha : a ≠ 0) :
    bridgeProfile a ε = gdpProfile (2 * a) ε := by
  have h2a : (2 * a) ≠ 0 := mul_ne_zero (by norm_num) ha
  rw [gdpProfile_eq]
  unfold bridgeProfile FiniteGaussianPrivacy.bridgeProfile
    FiniteGaussianPrivacy.bridgeU FiniteGaussianPrivacy.bridgeV
  congr 1
  · simp [gdpProfileCDFPlusArg]
  · congr 1
    simp [gdpProfileCDFMinusArg]
    field_simp [h2a]

theorem sampledGaussianBaseEpsilon_exp
    {p ε : ℝ}
    (hp : 0 < p)
    (hε : 0 ≤ ε) :
    Real.exp (sampledGaussianBaseEpsilon p ε) = (Real.exp ε - 1 + p) / p := by
  have hExp : 1 ≤ Real.exp ε := by
    exact Real.one_le_exp_iff.mpr hε
  have hNum : 0 < Real.exp ε - 1 + p := by
    nlinarith
  have hDiv : 0 < (Real.exp ε - 1 + p) / p := div_pos hNum hp
  simpa [sampledGaussianBaseEpsilon] using Real.exp_log hDiv

theorem sampledGaussianBaseEpsilon_nonneg
    {p ε : ℝ}
    (hp : 0 < p)
    (hε : 0 ≤ ε) :
    0 ≤ sampledGaussianBaseEpsilon p ε := by
  have hExp : 1 ≤ Real.exp ε := Real.one_le_exp_iff.mpr hε
  have hDivOne : 1 ≤ (Real.exp ε - 1 + p) / p := by
    have hnum : 1 * p ≤ Real.exp ε - 1 + p := by
      linarith
    exact (le_div_iff₀ hp).2 hnum
  rw [sampledGaussianBaseEpsilon]
  exact Real.log_nonneg hDivOne

/--
Applying the classical sampled-epsilon reparameterization to the sampled-Gaussian
base privacy parameter recovers the public sampled privacy parameter.

This is the parameter identity needed to align the stronger classical sampled
event-bound theorem with the public sampled-Gaussian witness surface.
-/
theorem classicalProfileSubsamplingEpsilon_sampledGaussianBaseEpsilon
    {p ε : ℝ}
    (hp : 0 < p)
    (hε : 0 ≤ ε) :
    classicalProfileSubsamplingEpsilon p (sampledGaussianBaseEpsilon p ε) = ε := by
  have hbase := sampledGaussianBaseEpsilon_exp hp hε
  have hcalc : 1 - p + p * Real.exp (sampledGaussianBaseEpsilon p ε) = Real.exp ε := by
    rw [hbase]
    field_simp [hp.ne']
    ring_nf
  have harg : 0 < 1 - p + p * Real.exp (sampledGaussianBaseEpsilon p ε) := by
    rw [hcalc]
    exact Real.exp_pos ε
  apply Real.exp_injective
  rw [classicalSubsamplingEpsilon_exp (p := p) (ε := sampledGaussianBaseEpsilon p ε) harg]
  exact hcalc

/--
The sampled-Gaussian profile witness is exactly the classical sampled delta
scaling applied to the base GDP profile at the reparameterized privacy level.
-/
theorem classicalProfileSubsamplingDelta_gdp_eq_sampledGaussianGDPWitnessProfile
    (μ p ε : ℝ) :
    classicalProfileSubsamplingDelta p
        (gdpProfile μ (sampledGaussianBaseEpsilon p ε)) =
      sampledGaussianGDPWitnessProfile μ p ε := by
  rfl

/--
The stronger classical sampled event-bound witness instantiated at the base GDP
profile coincides exactly with the named sampled-Gaussian weighted witness.

This is the theorem-facing parameter bridge between the classical sampled
event-bound export and the local sampled-Gaussian witness surface.
-/
theorem classicalSubsamplingEventBoundWitness_eq_sampledGaussianGDPWeightedWitness
    (μ p ε : ℝ)
    (hp : 0 < p)
    (hε : 0 ≤ ε) :
    classicalSubsamplingEventBoundWitness p (sampledGaussianBaseEpsilon p ε)
        (gdpProfile μ (sampledGaussianBaseEpsilon p ε)) =
      sampledGaussianGDPWeightedWitness μ p ε := by
  apply tradeoffFunction_eq_of_eval_eq
  intro α
  have hεeq :
      classicalSubsamplingEpsilon p (sampledGaussianBaseEpsilon p ε) = ε := by
    simpa using classicalProfileSubsamplingEpsilon_sampledGaussianBaseEpsilon hp hε
  have hδeq :
      classicalSubsamplingDelta p (gdpProfile μ (sampledGaussianBaseEpsilon p ε)) =
        sampledGaussianGDPWitnessProfile μ p ε := by
    simpa using classicalProfileSubsamplingDelta_gdp_eq_sampledGaussianGDPWitnessProfile μ p ε
  rw [classicalSubsamplingEventBoundWitness_eval, sampledGaussianGDPWeightedWitness_eval]
  rw [hεeq, hδeq]

/--
Specialization of the stronger classical appendix event-bound theorem to the
sampled-Gaussian weighted witness.

This is still an appendix-state theorem: it exposes the exact witness imported
from `Mf.DP.ClassicalEventDPProfileSubsampling`, but it does not yet identify a
concrete scalar bridge-envelope state. The final exact sampled-Poisson consumer
remains downstream of that remaining bridge.
-/
theorem classicalSubsamplingAppendixSampledGaussianWeightedWitness_le_beta
    (S : ClassicalSubsamplingAppendixState)
    (μ ε : ℝ)
    (hp0 : 0 ≤ S.p)
    (hp1 : S.p ≤ 1)
    (hp : 0 < S.p)
    (hε : 0 ≤ ε)
    (hkEq : S.k = -Real.exp (sampledGaussianBaseEpsilon S.p ε))
    (hbEq : S.b = 1 - gdpProfile μ (sampledGaussianBaseEpsilon S.p ε))
    (hfeas : ClassicalSubsamplingAppendixFeasible S) :
    (sampledGaussianGDPWeightedWitness μ S.p ε).eval S.alpha ≤ S.beta := by
  have hclassical :
      (classicalSubsamplingEventBoundWitness S.p (sampledGaussianBaseEpsilon S.p ε)
          (gdpProfile μ (sampledGaussianBaseEpsilon S.p ε))).eval S.alpha ≤ S.beta := by
    exact classicalSubsamplingAppendixEventBoundWitness_le_beta
      (S := S)
      (ε := sampledGaussianBaseEpsilon S.p ε)
      (δ := gdpProfile μ (sampledGaussianBaseEpsilon S.p ε))
      hp0 hp1 (sampledGaussianBaseEpsilon_nonneg hp hε) hkEq hbEq hfeas
  have hεeq :
      classicalSubsamplingEpsilon S.p (sampledGaussianBaseEpsilon S.p ε) = ε := by
    simpa using classicalProfileSubsamplingEpsilon_sampledGaussianBaseEpsilon hp hε
  have hδeq :
      classicalSubsamplingDelta S.p
          (gdpProfile μ (sampledGaussianBaseEpsilon S.p ε)) =
        sampledGaussianGDPWitnessProfile μ S.p ε := by
    simpa using classicalProfileSubsamplingDelta_gdp_eq_sampledGaussianGDPWitnessProfile μ S.p ε
  rw [classicalSubsamplingEventBoundWitness_eval] at hclassical
  rw [sampledGaussianGDPWeightedWitness_eval]
  rw [hεeq, hδeq] at hclassical
  exact hclassical

theorem bsrGaussianMeasure_apply_eq_ofReal_integral_pdfReal_local
    {n : ℕ} {σ : ℝ} (hσ : σ ≠ 0) (μ : BSROutput n) (s : Set (BSROutput n))
    (hs : MeasurableSet s) :
    bsrGaussianMeasure σ μ s
      = ENNReal.ofReal (∫ y in s, bsrGaussianPdfReal σ μ y ∂MeasureTheory.volume) := by
  rw [bsrGaussianMeasure_eq_withDensity_pdf (σ := σ) (μ := μ) hσ]
  rw [MeasureTheory.withDensity_apply _ hs]
  simpa [bsrGaussianPdf, Mf.Probability.FiniteGaussian.pdf] using
    (MeasureTheory.ofReal_integral_eq_lintegral_ofReal
      ((integrable_bsrGaussianPdfReal (σ := σ) (μ := μ) hσ).restrict)
      (Filter.Eventually.of_forall fun y => bsrGaussianPdfReal_nonneg σ μ y)).symm

/--
Pointwise comparison from the weighted branch of the sampled-GDP witness to the
exact Poisson Gaussian-mixture tradeoff surface.
-/
theorem sampledGaussianGDPWeightedWitness_le_poissonGaussianMixtureTradeoffAt_of_profile_le
    {d m : ℕ}
    (μ : ℝ)
    (C : Fin m → Fin d → ℝ)
    (p ε : ℝ)
    (hp0 : 0 ≤ p)
    (hp1 : p ≤ 1)
    (σ : ℝ)
    (hprof :
      poissonGaussianMixtureProfile C p hp0 hp1 σ ε
        ≤ sampledGaussianGDPWitnessProfile μ p ε) :
    (sampledGaussianGDPWeightedWitness μ p ε).PointwiseLE
      (poissonGaussianMixtureTradeoffAt C p ε hp0 hp1 σ) := by
  intro α
  rw [sampledGaussianGDPWeightedWitness_eval, poissonGaussianMixtureTradeoffAt_eval]
  linarith

/--
The same sampled-Gaussian profile hypothesis also yields a theorem-facing raw
branch bound `min {f_p, f_p^{-1}} <= exact`.
-/
theorem sampledGaussianGDPRawWitness_le_poissonGaussianMixtureTradeoffAt_of_profile_le
    {d m : ℕ}
    (μ : ℝ)
    (C : Fin m → Fin d → ℝ)
    (p ε : ℝ)
    (hp : 0 < p)
    (hp1 : p ≤ 1)
    (hε : 0 ≤ ε)
    (σ : ℝ)
    (hprof :
      poissonGaussianMixtureProfile C p hp.le hp1 σ ε
        ≤ sampledGaussianGDPWitnessProfile μ p ε) :
    (sampledGaussianGDPRawWitness μ p ε).PointwiseLE
      (poissonGaussianMixtureTradeoffAt C p ε hp.le hp1 σ) := by
  exact sampledGaussianGDPRawWitness_le_poissonGaussianMixtureTradeoffAt_of_weightedWitness_le
    (μ := μ)
    (C := C)
    (p := p)
    (ε := ε)
    (hp := hp)
    (hp1 := hp1)
    (hε := hε)
    (σ := σ)
    (sampledGaussianGDPWeightedWitness_le_poissonGaussianMixtureTradeoffAt_of_profile_le
      μ C p ε hp.le hp1 σ hprof)

/--
Below the switch threshold on the natural window, the sampled-Gaussian profile
hypothesis yields the corresponding inverse-affine upper bound against the
exact Poisson tradeoff.
-/
theorem affineInverse_eval_le_poissonGaussianMixtureTradeoffAt_of_profile_le
    {d m : ℕ}
    (μ : ℝ)
    (C : Fin m → Fin d → ℝ)
    (p ε α : ℝ)
    (hp : 0 < p)
    (hp1 : p ≤ 1)
    (σ : ℝ)
    (hε : 0 ≤ ε)
    (hδ0 : 0 ≤ sampledGaussianGDPWitnessProfile μ p ε)
    (hα0 : 0 ≤ α)
    (hα1 : α ≤ 1 - sampledGaussianGDPWitnessProfile μ p ε)
    (hswitch :
      α ≤ (1 - sampledGaussianGDPWitnessProfile μ p ε) / (Real.exp ε + 1))
    (hprof :
      poissonGaussianMixtureProfile C p hp.le hp1 σ ε
        ≤ sampledGaussianGDPWitnessProfile μ p ε) :
    (1 - sampledGaussianGDPWitnessProfile μ p ε - α) / Real.exp ε ≤
      (poissonGaussianMixtureTradeoffAt C p ε hp.le hp1 σ).eval α := by
  apply affineInverse_eval_le_poissonGaussianMixtureTradeoffAt_of_rawWitness_le
    (μ := μ) (C := C) (p := p) (ε := ε) (α := α)
    (hp := hp) (hp1 := hp1) (σ := σ)
    (hε := hε) (hδ0 := hδ0) (hα0 := hα0) (hα1 := hα1) (hswitch := hswitch)
  exact sampledGaussianGDPRawWitness_le_poissonGaussianMixtureTradeoffAt_of_profile_le
    μ C p ε hp hp1 hε σ hprof

/--
Above the switch threshold on the natural window, the sampled-Gaussian profile
hypothesis yields the corresponding weighted-affine upper bound against the
exact Poisson tradeoff.
-/
theorem affineWeighted_eval_le_poissonGaussianMixtureTradeoffAt_of_profile_le
    {d m : ℕ}
    (μ : ℝ)
    (C : Fin m → Fin d → ℝ)
    (p ε α : ℝ)
    (hp : 0 < p)
    (hp1 : p ≤ 1)
    (σ : ℝ)
    (hε : 0 ≤ ε)
    (hδ0 : 0 ≤ sampledGaussianGDPWitnessProfile μ p ε)
    (hα0 : 0 ≤ α)
    (hα1 : α ≤ 1 - sampledGaussianGDPWitnessProfile μ p ε)
    (hswitch :
      (1 - sampledGaussianGDPWitnessProfile μ p ε) / (Real.exp ε + 1) ≤ α)
    (hprof :
      poissonGaussianMixtureProfile C p hp.le hp1 σ ε
        ≤ sampledGaussianGDPWitnessProfile μ p ε) :
    1 - sampledGaussianGDPWitnessProfile μ p ε - Real.exp ε * α ≤
      (poissonGaussianMixtureTradeoffAt C p ε hp.le hp1 σ).eval α := by
  apply affineWeighted_eval_le_poissonGaussianMixtureTradeoffAt_of_rawWitness_le
    (μ := μ) (C := C) (p := p) (ε := ε) (α := α)
    (hp := hp) (hp1 := hp1) (σ := σ)
    (hε := hε) (hδ0 := hδ0) (hα0 := hα0) (hα1 := hα1) (hswitch := hswitch)
  exact sampledGaussianGDPRawWitness_le_poissonGaussianMixtureTradeoffAt_of_profile_le
    μ C p ε hp hp1 hε σ hprof

/--
Under the sampled-Gaussian profile hypothesis, the exact Poisson tradeoff
dominates the corresponding piecewise-affine sampled-GDP envelope on the
natural window.
-/
theorem sampledGaussianPiecewiseEnvelope_eval_le_poissonGaussianMixtureTradeoffAt_of_profile_le
    {d m : ℕ}
    (μ : ℝ)
    (C : Fin m → Fin d → ℝ)
    (p ε α : ℝ)
    (hp : 0 < p)
    (hp1 : p ≤ 1)
    (σ : ℝ)
    (hε : 0 ≤ ε)
    (hδ0 : 0 ≤ sampledGaussianGDPWitnessProfile μ p ε)
    (hα0 : 0 ≤ α)
    (hα1 : α ≤ 1 - sampledGaussianGDPWitnessProfile μ p ε)
    (hprof :
      poissonGaussianMixtureProfile C p hp.le hp1 σ ε
        ≤ sampledGaussianGDPWitnessProfile μ p ε) :
    (if
        α ≤ (1 - sampledGaussianGDPWitnessProfile μ p ε) / (Real.exp ε + 1)
      then
        (1 - sampledGaussianGDPWitnessProfile μ p ε - α) / Real.exp ε
      else
        1 - sampledGaussianGDPWitnessProfile μ p ε - Real.exp ε * α) ≤
      (poissonGaussianMixtureTradeoffAt C p ε hp.le hp1 σ).eval α := by
  by_cases hswitch : α ≤ (1 - sampledGaussianGDPWitnessProfile μ p ε) / (Real.exp ε + 1)
  · simp only [if_pos hswitch]
    exact affineInverse_eval_le_poissonGaussianMixtureTradeoffAt_of_profile_le
      μ C p ε α hp hp1 σ hε hδ0 hα0 hα1 hswitch hprof
  · have hswitch' :
        (1 - sampledGaussianGDPWitnessProfile μ p ε) / (Real.exp ε + 1) ≤ α :=
      le_of_not_ge hswitch
    rw [if_neg hswitch]
    exact affineWeighted_eval_le_poissonGaussianMixtureTradeoffAt_of_profile_le
      μ C p ε α hp hp1 σ hε hδ0 hα0 hα1 hswitch' hprof

/--
Windowwise version of the piecewise-affine sampled-GDP envelope bound under
the sampled-Gaussian profile hypothesis.
-/
theorem sampledGaussianPiecewiseEnvelope_window_le_poissonGaussianMixtureTradeoffAt_of_profile_le
    {d m : ℕ}
    (μ : ℝ)
    (C : Fin m → Fin d → ℝ)
    (p ε : ℝ)
    (hp : 0 < p)
    (hp1 : p ≤ 1)
    (σ : ℝ)
    (hε : 0 ≤ ε)
    (hδ0 : 0 ≤ sampledGaussianGDPWitnessProfile μ p ε)
    (hprof :
      poissonGaussianMixtureProfile C p hp.le hp1 σ ε
        ≤ sampledGaussianGDPWitnessProfile μ p ε) :
    ∀ α : ℝ,
      0 ≤ α →
      α ≤ 1 - sampledGaussianGDPWitnessProfile μ p ε →
      (if
          α ≤ (1 - sampledGaussianGDPWitnessProfile μ p ε) / (Real.exp ε + 1)
        then
          (1 - sampledGaussianGDPWitnessProfile μ p ε - α) / Real.exp ε
        else
          1 - sampledGaussianGDPWitnessProfile μ p ε - Real.exp ε * α) ≤
        (poissonGaussianMixtureTradeoffAt C p ε hp.le hp1 σ).eval α := by
  intro α hα0 hα1
  exact sampledGaussianPiecewiseEnvelope_eval_le_poissonGaussianMixtureTradeoffAt_of_profile_le
    μ C p ε α hp hp1 σ hε hδ0 hα0 hα1 hprof

theorem dpEventBound_le_poissonGaussianMixtureTradeoffAt_of_profile_le
    {d m : ℕ}
    (δ : ℝ)
    (C : Fin m → Fin d → ℝ)
    (p ε : ℝ)
    (hp0 : 0 ≤ p)
    (hp1 : p ≤ 1)
    (σ : ℝ)
    (hprof :
      poissonGaussianMixtureProfile C p hp0 hp1 σ ε ≤ δ) :
    (TradeoffFunction.ofDPEventBound ε δ).PointwiseLE
      (poissonGaussianMixtureTradeoffAt C p ε hp0 hp1 σ) := by
  intro α
  rw [TradeoffFunction.ofDPEventBound_eval, poissonGaussianMixtureTradeoffAt_eval]
  linarith

/--
The reparameterized sampled GDP subsampling surface stays below the named
weighted sampled-GDP witness.
-/
theorem gaussianDP_subsampleTradeoffAt_le_sampledGaussianGDPWeightedWitness
    (G : GaussianDP)
    (p ε : ℝ)
    (hp : 0 < p)
    (hε : 0 ≤ ε) :
    (G.subsampleTradeoffAt p (sampledGaussianBaseEpsilon p ε)).PointwiseLE
      (sampledGaussianGDPWeightedWitness G.μ p ε) := by
  intro α
  have h :=
    GaussianDP.subsampleTradeoffAt_eval_le_weighted
      G p (sampledGaussianBaseEpsilon p ε) α
  rw [sampledGaussianGDPWeightedWitness_eval]
  rw [sampledGaussianBaseEpsilon_exp hp hε] at h
  have hLinear :
      p *
          (1
            - gdpProfile G.μ (sampledGaussianBaseEpsilon p ε)
            - ((Real.exp ε - 1 + p) / p) * α) +
        (1 - p) * (1 - α) =
        1 - p * gdpProfile G.μ (sampledGaussianBaseEpsilon p ε) - Real.exp ε * α := by
    field_simp [hp.ne']
    ring
  have hTarget :
      1 - p * gdpProfile G.μ (sampledGaussianBaseEpsilon p ε) - Real.exp ε * α =
      1 - sampledGaussianGDPWitnessProfile G.μ p ε - Real.exp ε * α := by
    simp [sampledGaussianGDPWitnessProfile]
  rw [hLinear, hTarget] at h
  exact h

/--
At the sampled privacy level, the reparameterized subsampled GDP tradeoff at
`α = 0` stays below the sampled-Gaussian weighted witness endpoint.

This is the GDP-side sampled-profile-point bootstrap available from the current
theorem base: it exposes the sampled point directly on the local subsampled
tradeoff surface without reopening the generic weighted-witness proof.
-/
theorem gaussianDP_subsampleTradeoffAt_eval_zero_le_one_sub_sampledGaussianGDPWitnessProfile
    (G : GaussianDP)
    (p ε : ℝ)
    (hp : 0 < p)
    (hε : 0 ≤ ε) :
    (G.subsampleTradeoffAt p (sampledGaussianBaseEpsilon p ε)).eval 0
      ≤ 1 - sampledGaussianGDPWitnessProfile G.μ p ε := by
  simpa [sampledGaussianGDPWeightedWitness_eval] using
    gaussianDP_subsampleTradeoffAt_le_sampledGaussianGDPWeightedWitness G p ε hp hε 0

/--
Equivalent gap form of the sampled tradeoff-at-zero bootstrap.

This is the theorem-facing inequality downstream packets can import when they
need the sampled-Gaussian witness profile expressed against the local
subsampled tradeoff point at `α = 0`.
-/
theorem sampledGaussianGDPWitnessProfile_le_one_sub_gaussianDP_subsampleTradeoffAt_eval_zero
    (G : GaussianDP)
    (p ε : ℝ)
    (hp : 0 < p)
    (hε : 0 ≤ ε) :
    sampledGaussianGDPWitnessProfile G.μ p ε
      ≤ 1 - (G.subsampleTradeoffAt p (sampledGaussianBaseEpsilon p ε)).eval 0 := by
  have h := gaussianDP_subsampleTradeoffAt_eval_zero_le_one_sub_sampledGaussianGDPWitnessProfile
    G p ε hp hε
  linarith

/--
The actual subsampled GDP endpoint at `α = 0`, expressed in the same
`δ`-style scalar form used by the sampled-Gaussian witness theorems.
-/
def sampledGaussianSubsampledEndpoint (G : GaussianDP) (p ε : ℝ) : ℝ :=
  1 - (G.subsampleTradeoffAt p (sampledGaussianBaseEpsilon p ε)).eval 0

/--
The sampled-Gaussian witness profile is bounded above by the actual subsampled
GDP endpoint at `α = 0`.

This is the theorem-facing transport from the surrogate witness cutoff to the
real subsampled tradeoff surface.
-/
theorem sampledGaussianGDPWitnessProfile_le_subsampledEndpoint
    (G : GaussianDP)
    (p ε : ℝ)
    (hp : 0 < p)
    (hε : 0 ≤ ε) :
    sampledGaussianGDPWitnessProfile G.μ p ε
      ≤ sampledGaussianSubsampledEndpoint G p ε := by
  simpa [sampledGaussianSubsampledEndpoint] using
    sampledGaussianGDPWitnessProfile_le_one_sub_gaussianDP_subsampleTradeoffAt_eval_zero
      G p ε hp hε

/--
The weighted affine branch built from the actual subsampled endpoint is bounded
above by the sampled-Gaussian weighted witness branch.
-/
theorem sampledGaussianSubsampledEndpointWeighted_eval_le_sampledGaussianGDPWeightedWitness
    (G : GaussianDP)
    (p ε α : ℝ)
    (hp : 0 < p)
    (hε : 0 ≤ ε) :
    1 - sampledGaussianSubsampledEndpoint G p ε - Real.exp ε * α ≤
      (sampledGaussianGDPWeightedWitness G.μ p ε).eval α := by
  have hδ :
      sampledGaussianGDPWitnessProfile G.μ p ε
        ≤ sampledGaussianSubsampledEndpoint G p ε := by
    exact sampledGaussianGDPWitnessProfile_le_subsampledEndpoint G p ε hp hε
  rw [sampledGaussianGDPWeightedWitness_eval]
  linarith

/--
The piecewise affine envelope built from the actual subsampled endpoint lies
below its weighted branch pointwise.

This is the key local transport lemma that avoids reintroducing the rejected
raw-profile inequality: once the endpoint is taken from the actual subsampled
tradeoff surface, the resulting piecewise envelope is a safe lower surrogate
for the weighted branch.
-/
theorem sampledGaussianSubsampledEndpointPiecewise_eval_le_weighted
    (G : GaussianDP)
    (p ε α : ℝ)
    (hε : 0 ≤ ε) :
    (if α ≤ (1 - sampledGaussianSubsampledEndpoint G p ε) / (Real.exp ε + 1) then
        (1 - sampledGaussianSubsampledEndpoint G p ε - α) / Real.exp ε
      else
        1 - sampledGaussianSubsampledEndpoint G p ε - Real.exp ε * α) ≤
      1 - sampledGaussianSubsampledEndpoint G p ε - Real.exp ε * α := by
  by_cases hswitch :
      α ≤ (1 - sampledGaussianSubsampledEndpoint G p ε) / (Real.exp ε + 1)
  · simp only [if_pos hswitch]
    have hexp_pos : 0 < Real.exp ε := Real.exp_pos ε
    have hexp_ge_one : 1 ≤ Real.exp ε := by
      have h := Real.exp_le_exp.mpr hε
      simpa using h
    have hden_pos : 0 < Real.exp ε + 1 := by positivity
    have hmul :
        α * (Real.exp ε + 1) ≤ 1 - sampledGaussianSubsampledEndpoint G p ε := by
      exact (le_div_iff₀ hden_pos).mp hswitch
    have hmul' :
        α * ((Real.exp ε)^2 - 1)
          ≤ (Real.exp ε - 1) * (1 - sampledGaussianSubsampledEndpoint G p ε) := by
      nlinarith
    have hscaled :
        1 - sampledGaussianSubsampledEndpoint G p ε - α
          ≤ Real.exp ε * (1 - sampledGaussianSubsampledEndpoint G p ε - Real.exp ε * α) := by
      nlinarith
    exact (div_le_iff₀ hexp_pos).2 (by simpa [mul_comm] using hscaled)
  · simp [if_neg hswitch]

/--
The reparameterized sampled GDP subsampling surface stays below the named
inverse sampled-GDP witness.
-/
theorem gaussianDP_subsampleTradeoffAt_le_sampledGaussianGDPInverseWitness
    (G : GaussianDP)
    (p ε : ℝ) :
    (G.subsampleTradeoffAt p (sampledGaussianBaseEpsilon p ε)).PointwiseLE
      (sampledGaussianGDPInverseWitness G.μ p ε) := by
  simpa [sampledGaussianGDPInverseWitness] using
    GaussianDP.subsampleTradeoffAt_le_inverseWeighted
      G p (sampledGaussianBaseEpsilon p ε)

/--
The reparameterized sampled GDP subsampling surface stays below the named raw
sampled-GDP witness `min {f_p, f_p^{-1}}`.
-/
theorem gaussianDP_subsampleTradeoffAt_le_sampledGaussianGDPRawWitness
    (G : GaussianDP)
    (p ε : ℝ) :
    (G.subsampleTradeoffAt p (sampledGaussianBaseEpsilon p ε)).PointwiseLE
      (sampledGaussianGDPRawWitness G.μ p ε) := by
  simpa [sampledGaussianGDPRawWitness, GaussianDP.subsampleTradeoffAt] using
    TradeoffFunction.pSamplingOperator_le_raw
      p ((⟨G.μ⟩ : GaussianDP).tradeoffAt (sampledGaussianBaseEpsilon p ε))

end

end DP
end Mf
