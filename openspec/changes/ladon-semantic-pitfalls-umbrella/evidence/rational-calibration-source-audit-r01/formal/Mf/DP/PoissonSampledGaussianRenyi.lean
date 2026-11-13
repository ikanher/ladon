import Mf.DP.CommonCovarianceGaussianRenyi

namespace Mf.DP

noncomputable section

open MeasureTheory
open scoped BigOperators

/-!
# Integer-order Poisson-sampled Gaussian Renyi algebra

This neutral owner defines the finite binomial moment that appears when a
single clipped record is included with public probability `q` and its
inclusion bit is hidden.  It does not yet identify that scalar expression with
a sampled mechanism; the release-law bridge belongs in the DP-Adam integration
layer.
-/

/-- Finite integer-order likelihood-ratio moment for a Poisson-sampled
equal-covariance Gaussian pair.  `z` is the squared mean separation divided by
the Gaussian variance. -/
def sampledGaussianRenyiMoment (order : ℕ) (q z : ℝ) : ℝ :=
  ∑ j ∈ Finset.range (order + 1),
    (order.choose j : ℝ) * (1 - q) ^ (order - j) * q ^ j *
      Real.exp ((((j : ℝ) ^ 2 - (j : ℝ)) * z) / 2)

/-- Density obtained by hiding one public-rate Bernoulli inclusion bit between
a shifted row and its base row. -/
def hiddenBernoulliDensity {A : Type*} (q : ℝ)
    (shifted base : A → ENNReal) : A → ENNReal :=
  fun x =>
    ENNReal.ofReal q * shifted x + ENNReal.ofReal (1 - q) * base x

/-- Integer-order pointwise binomial expansion after multiplying by the base
density to the complementary Renyi exponent. -/
theorem hiddenBernoulliDensity_rpow_nat_mul
    {A : Type*} (order : ℕ) (q : ℝ)
    (shifted base : A → ENNReal)
    (hbase0 : ∀ x, base x ≠ 0) (hbaseTop : ∀ x, base x ≠ ⊤) (x : A) :
    (hiddenBernoulliDensity q shifted base x) ^ (order : ℝ) *
        base x ^ (1 - (order : ℝ)) =
      ∑ j ∈ Finset.range (order + 1),
        (order.choose j : ENNReal) * ENNReal.ofReal q ^ j *
          ENNReal.ofReal (1 - q) ^ (order - j) *
          (shifted x ^ (j : ℝ) * base x ^ (1 - (j : ℝ))) := by
  rw [ENNReal.rpow_natCast, hiddenBernoulliDensity, add_pow,
    Finset.sum_mul]
  apply Finset.sum_congr rfl
  intro j hj
  have hjle : j ≤ order := Nat.le_of_lt_succ (Finset.mem_range.mp hj)
  rw [mul_pow, mul_pow, ← ENNReal.rpow_natCast (shifted x) j,
    ← ENNReal.rpow_natCast (base x) (order - j)]
  have hbase :
      base x ^ ((order - j : ℕ) : ℝ) *
          base x ^ (1 - (order : ℝ)) =
        base x ^ (1 - (j : ℝ)) := by
    rw [← ENNReal.rpow_add _ _ (hbase0 x) (hbaseTop x)]
    congr 1
    rw [Nat.cast_sub hjle]
    ring
  rw [show
      (ENNReal.ofReal q ^ j * shifted x ^ (j : ℝ)) *
            (ENNReal.ofReal (1 - q) ^ (order - j) *
              base x ^ ((order - j : ℕ) : ℝ)) *
          (order.choose j : ENNReal) * base x ^ (1 - (order : ℝ)) =
        (order.choose j : ENNReal) * ENNReal.ofReal q ^ j *
          ENNReal.ofReal (1 - q) ^ (order - j) *
          (shifted x ^ (j : ℝ) *
            (base x ^ ((order - j : ℕ) : ℝ) *
              base x ^ (1 - (order : ℝ)))) by ac_rfl]
  rw [hbase]

@[simp] theorem sampledGaussianRenyiMoment_zero_sampling
    (order : ℕ) (z : ℝ) :
    sampledGaussianRenyiMoment order 0 z = 1 := by
  rw [sampledGaussianRenyiMoment]
  rw [Finset.sum_eq_single 0]
  · simp
  · intro j hj hj0
    have hpow : (0 : ℝ) ^ j = 0 := zero_pow hj0
    rw [hpow]
    simp
  · simp

theorem sampledGaussianRenyiMoment_nonneg
    (order : ℕ) {q : ℝ} (z : ℝ) (hq0 : 0 ≤ q) (hq1 : q ≤ 1) :
    0 ≤ sampledGaussianRenyiMoment order q z := by
  rw [sampledGaussianRenyiMoment]
  apply Finset.sum_nonneg
  intro j hj
  have hchoose : 0 ≤ (order.choose j : ℝ) := by positivity
  have hone : 0 ≤ 1 - q := sub_nonneg.mpr hq1
  have hexp : 0 ≤ Real.exp ((((j : ℝ) ^ 2 - (j : ℝ)) * z) / 2) :=
    (Real.exp_pos _).le
  positivity

theorem sampledGaussianRenyiMoment_pos
    (order : ℕ) {q : ℝ} (z : ℝ)
    (hq0 : 0 ≤ q) (hq1 : q ≤ 1) :
    0 < sampledGaussianRenyiMoment order q z := by
  by_cases hq : q = 0
  · subst q
    simp
  · have hqpos : 0 < q := lt_of_le_of_ne hq0 (Ne.symm hq)
    let term : ℕ → ℝ := fun j =>
      (order.choose j : ℝ) * (1 - q) ^ (order - j) * q ^ j *
        Real.exp ((((j : ℝ) ^ 2 - (j : ℝ)) * z) / 2)
    have hterm : 0 < term order := by
      dsimp [term]
      simpa using mul_pos (pow_pos hqpos order)
        (Real.exp_pos ((((order : ℝ) ^ 2 - (order : ℝ)) * z) / 2))
    have hle : term order ≤ ∑ j ∈ Finset.range (order + 1), term j := by
      exact Finset.single_le_sum
        (f := term)
        (fun j _ => by
          dsimp [term]
          have hone : 0 ≤ 1 - q := sub_nonneg.mpr hq1
          positivity)
        (by simp)
    rw [sampledGaussianRenyiMoment]
    exact hterm.trans_le hle

/-- Gaussian likelihood-ratio moment at a natural order, specialized from the
arbitrary-real-order common-covariance identity. -/
theorem gaussianLikelihoodRatioMoment_nat {d : ℕ}
    (j : ℕ) (sigma : ℝ) (shifted base : BSROutput d)
    (hsigma : sigma ≠ 0) :
    renyiPower (j : ℝ) (volume : Measure (BSROutput d))
        (bsrGaussianCommonBaseDensity sigma shifted hsigma).density
        (bsrGaussianCommonBaseDensity sigma base hsigma).density =
      ENNReal.ofReal
        (Real.exp
          ((j : ℝ) * ((j : ℝ) - 1) * bsrSqDist shifted base /
            (2 * sigma ^ 2))) := by
  simpa [sub_eq_add_neg, mul_assoc] using
    (renyiPower_bsrGaussianCommonBaseDensity
      (j : ℝ) sigma shifted base hsigma)

/-- Common-base density of a hidden Bernoulli mixture between two Gaussian
means with the same covariance. -/
def sampledGaussianMixtureCommonBaseDensity {d : ℕ}
    (q sigma : ℝ) (shifted base : BSROutput d)
    (hq0 : 0 ≤ q) (hq1 : q ≤ 1) (hsigma : sigma ≠ 0) :
    CommonBaseProbabilityDensity (volume : Measure (BSROutput d)) where
  density := hiddenBernoulliDensity q
    (bsrGaussianCommonBaseDensity sigma shifted hsigma).density
    (bsrGaussianCommonBaseDensity sigma base hsigma).density
  measurable_density :=
    (measurable_const.mul
      (bsrGaussianCommonBaseDensity sigma shifted hsigma).measurable_density).add
      (measurable_const.mul
        (bsrGaussianCommonBaseDensity sigma base hsigma).measurable_density)
  density_ne_top := by
    intro x
    rw [hiddenBernoulliDensity]
    exact ENNReal.add_ne_top.mpr
      ⟨ENNReal.mul_ne_top (by simp)
          ((bsrGaussianCommonBaseDensity sigma shifted hsigma).density_ne_top x),
        ENNReal.mul_ne_top (by simp)
          ((bsrGaussianCommonBaseDensity sigma base hsigma).density_ne_top x)⟩
  mass_one := by
    unfold hiddenBernoulliDensity
    have hadd :
        (∫⁻ x : BSROutput d,
          ENNReal.ofReal q *
              (bsrGaussianCommonBaseDensity sigma shifted hsigma).density x +
            ENNReal.ofReal (1 - q) *
              (bsrGaussianCommonBaseDensity sigma base hsigma).density x
          ∂(volume : Measure (BSROutput d))) =
          (∫⁻ x : BSROutput d,
            ENNReal.ofReal q *
              (bsrGaussianCommonBaseDensity sigma shifted hsigma).density x
            ∂(volume : Measure (BSROutput d))) +
          (∫⁻ x : BSROutput d,
            ENNReal.ofReal (1 - q) *
              (bsrGaussianCommonBaseDensity sigma base hsigma).density x
            ∂(volume : Measure (BSROutput d))) := by
      apply MeasureTheory.lintegral_add_left
      exact measurable_const.mul
        (bsrGaussianCommonBaseDensity sigma shifted hsigma).measurable_density
    rw [hadd]
    rw [MeasureTheory.lintegral_const_mul _
          (bsrGaussianCommonBaseDensity sigma shifted hsigma).measurable_density,
      MeasureTheory.lintegral_const_mul _
          (bsrGaussianCommonBaseDensity sigma base hsigma).measurable_density,
      (bsrGaussianCommonBaseDensity sigma shifted hsigma).mass_one,
      (bsrGaussianCommonBaseDensity sigma base hsigma).mass_one,
      mul_one, mul_one, ← ENNReal.ofReal_add hq0 (sub_nonneg.mpr hq1)]
    norm_num

theorem sampledGaussianMixtureCommonBaseDensity_density_ne_zero {d : ℕ}
    (q sigma : ℝ) (shifted base : BSROutput d)
    (hq0 : 0 ≤ q) (hq1 : q ≤ 1) (hsigma : sigma ≠ 0)
    (x : BSROutput d) :
    (sampledGaussianMixtureCommonBaseDensity q sigma shifted base
      hq0 hq1 hsigma).density x ≠ 0 := by
  by_cases hq : q = 1
  · subst q
    simpa [sampledGaussianMixtureCommonBaseDensity,
      hiddenBernoulliDensity] using
      bsrGaussianCommonBaseDensity_density_ne_zero sigma shifted hsigma x
  · have h1q : 0 < 1 - q := sub_pos.mpr (lt_of_le_of_ne hq1 hq)
    have hbase :=
      bsrGaussianCommonBaseDensity_density_ne_zero sigma base hsigma x
    simp only [sampledGaussianMixtureCommonBaseDensity,
      hiddenBernoulliDensity]
    intro hzero
    have hbaseTerm := (add_eq_zero.mp hzero).2
    have hcoef : ENNReal.ofReal (1 - q) ≠ 0 := by positivity
    exact (mul_ne_zero hcoef hbase) hbaseTerm

/-- The hidden-bit common-base density is literally the two-component
Gaussian mixture measure.  This law identity is used by mechanism bridges;
it is stronger than moment matching. -/
theorem sampledGaussianMixtureCommonBaseDensity_measure_eq {d : ℕ}
    (q sigma : ℝ) (shifted base : BSROutput d)
    (hq0 : 0 ≤ q) (hq1 : q ≤ 1) (hsigma : sigma ≠ 0) :
    (sampledGaussianMixtureCommonBaseDensity q sigma shifted base
      hq0 hq1 hsigma).measure =
      ENNReal.ofReal q • bsrGaussianMeasure sigma shifted +
        ENNReal.ofReal (1 - q) • bsrGaussianMeasure sigma base := by
  let shiftedD := bsrGaussianCommonBaseDensity sigma shifted hsigma
  let baseD := bsrGaussianCommonBaseDensity sigma base hsigma
  rw [CommonBaseProbabilityDensity.measure]
  change (volume : Measure (BSROutput d)).withDensity
      (ENNReal.ofReal q • shiftedD.density +
        ENNReal.ofReal (1 - q) • baseD.density) = _
  rw [MeasureTheory.withDensity_add_left]
  · rw [MeasureTheory.withDensity_smul (μ := volume) (ENNReal.ofReal q)
        shiftedD.measurable_density,
      MeasureTheory.withDensity_smul (μ := volume) (ENNReal.ofReal (1 - q))
        baseD.measurable_density]
    rw [show (volume : Measure (BSROutput d)).withDensity shiftedD.density =
        bsrGaussianMeasure sigma shifted by
      exact bsrGaussianCommonBaseDensity_measure_eq sigma shifted hsigma]
    rw [show (volume : Measure (BSROutput d)).withDensity baseD.density =
        bsrGaussianMeasure sigma base by
      exact bsrGaussianCommonBaseDensity_measure_eq sigma base hsigma]
  · exact shiftedD.measurable_density.const_smul _

/-- Exact forward integer-order Renyi power of the hidden-bit sampled Gaussian
mixture against its unsampled Gaussian base. -/
theorem renyiPower_sampledGaussianMixture_forward {d : ℕ}
    (order : ℕ) (q sigma : ℝ) (shifted base : BSROutput d)
    (hq0 : 0 ≤ q) (hq1 : q ≤ 1) (hsigma : sigma ≠ 0) :
    renyiPower (order : ℝ) (volume : Measure (BSROutput d))
        (sampledGaussianMixtureCommonBaseDensity q sigma shifted base
          hq0 hq1 hsigma).density
        (bsrGaussianCommonBaseDensity sigma base hsigma).density =
      ENNReal.ofReal
        (sampledGaussianRenyiMoment order q
          (bsrSqDist shifted base / sigma ^ 2)) := by
  let shiftedD := bsrGaussianCommonBaseDensity sigma shifted hsigma
  let baseD := bsrGaussianCommonBaseDensity sigma base hsigma
  change ∫⁻ x,
      (hiddenBernoulliDensity q shiftedD.density baseD.density x) ^ (order : ℝ) *
        baseD.density x ^ (1 - (order : ℝ)) ∂volume = _
  simp_rw [hiddenBernoulliDensity_rpow_nat_mul order q shiftedD.density baseD.density
    (fun x => by
      dsimp [baseD, bsrGaussianCommonBaseDensity]
      simp [bsrGaussianPdfReal_pos sigma base x hsigma])
    baseD.density_ne_top]
  rw [MeasureTheory.lintegral_finsetSum]
  · rw [sampledGaussianRenyiMoment, ENNReal.ofReal_sum_of_nonneg]
    · apply Finset.sum_congr rfl
      intro j hj
      let c : ENNReal :=
        (order.choose j : ENNReal) * ENNReal.ofReal q ^ j *
          ENNReal.ofReal (1 - q) ^ (order - j)
      change (∫⁻ x, c *
          (shiftedD.density x ^ (j : ℝ) *
            baseD.density x ^ (1 - (j : ℝ))) ∂volume) = _
      rw [MeasureTheory.lintegral_const_mul]
      · change c * renyiPower (j : ℝ) volume shiftedD.density baseD.density = _
        rw [show renyiPower (j : ℝ) volume shiftedD.density baseD.density =
            ENNReal.ofReal
              (Real.exp
                ((j : ℝ) * ((j : ℝ) - 1) * bsrSqDist shifted base /
                  (2 * sigma ^ 2))) by
          exact gaussianLikelihoodRatioMoment_nat j sigma shifted base hsigma]
        dsimp [c]
        rw [show (order.choose j : ENNReal) =
            ENNReal.ofReal (order.choose j : ℝ) by simp,
          ← ENNReal.ofReal_pow hq0,
          ← ENNReal.ofReal_pow (sub_nonneg.mpr hq1)]
        rw [← ENNReal.ofReal_mul (by positivity : 0 ≤ (order.choose j : ℝ)),
          ← ENNReal.ofReal_mul (by positivity : 0 ≤ (order.choose j : ℝ) * q ^ j),
          ← ENNReal.ofReal_mul (by positivity :
            0 ≤ (order.choose j : ℝ) * q ^ j *
              (1 - q) ^ (order - j))]
        congr 1
        ring_nf
      · exact
          (ENNReal.continuous_rpow_const.measurable.comp
              shiftedD.measurable_density).mul
            (ENNReal.continuous_rpow_const.measurable.comp
              baseD.measurable_density)
    · intro j hj
      positivity
  · intro j hj
    exact (measurable_const.mul measurable_const |>.mul measurable_const).mul
      ((ENNReal.continuous_rpow_const.measurable.comp
          shiftedD.measurable_density).mul
        (ENNReal.continuous_rpow_const.measurable.comp
          baseD.measurable_density))

/-- Pointwise reverse-direction bound from the fact that the hidden mixture
contains `(1-q)` times its base density. -/
theorem base_rpow_mul_hiddenBernoulliDensity_rpow_le
    {A : Type*} (order : ℕ) (q : ℝ) (shifted base : A → ENNReal)
    (horder : 1 ≤ order)
    (hbase0 : ∀ x, base x ≠ 0) (hbaseTop : ∀ x, base x ≠ ⊤)
    (x : A) :
    base x ^ (order : ℝ) *
        hiddenBernoulliDensity q shifted base x ^ (1 - (order : ℝ)) ≤
      ENNReal.ofReal (1 - q) ^ (1 - (order : ℝ)) * base x := by
  let c := ENNReal.ofReal (1 - q)
  have hdom : c * base x ≤ hiddenBernoulliDensity q shifted base x := by
    dsimp [c, hiddenBernoulliDensity]
    exact le_add_self
  have horderReal : (1 : ℝ) ≤ order := by exact_mod_cast horder
  have hr : 0 ≤ (order : ℝ) - 1 := by linarith
  have hpow : (c * base x) ^ ((order : ℝ) - 1) ≤
      hiddenBernoulliDensity q shifted base x ^ ((order : ℝ) - 1) :=
    ENNReal.rpow_le_rpow hdom hr
  have hneg : 1 - (order : ℝ) = -((order : ℝ) - 1) := by ring
  have hinv :
      hiddenBernoulliDensity q shifted base x ^ (1 - (order : ℝ)) ≤
        (c * base x) ^ (1 - (order : ℝ)) := by
    rw [hneg, ENNReal.rpow_neg, ENNReal.rpow_neg, ENNReal.inv_le_inv]
    exact hpow
  calc
    _ ≤ base x ^ (order : ℝ) * (c * base x) ^ (1 - (order : ℝ)) :=
      by simpa [mul_comm] using
        mul_le_mul_left hinv (base x ^ (order : ℝ))
    _ = c ^ (1 - (order : ℝ)) * base x := by
      rw [hneg, ENNReal.rpow_neg, ENNReal.mul_rpow_of_nonneg _ _ hr]
      rw [ENNReal.mul_inv
        (Or.inr (ENNReal.rpow_ne_top_of_nonneg hr (hbaseTop x)))
        (Or.inl (ENNReal.rpow_ne_top_of_nonneg hr (by
          dsimp [c]
          simp)))]
      rw [show
          base x ^ (order : ℝ) *
                ((c ^ ((order : ℝ) - 1))⁻¹ *
                  (base x ^ ((order : ℝ) - 1))⁻¹) =
            (c ^ ((order : ℝ) - 1))⁻¹ *
              (base x ^ (order : ℝ) *
                (base x ^ ((order : ℝ) - 1))⁻¹) by ac_rfl]
      rw [← ENNReal.rpow_neg, ← ENNReal.rpow_neg]
      rw [← ENNReal.rpow_add _ _ (hbase0 x) (hbaseTop x)]
      simp

/-- Reverse integer-order Renyi power is bounded by the cost of the mixture's
unsampled mass. -/
theorem renyiPower_sampledGaussianMixture_reverse_le {d : ℕ}
    (order : ℕ) (q sigma : ℝ) (shifted base : BSROutput d)
    (horder : 1 ≤ order) (hq0 : 0 ≤ q) (hq1 : q < 1)
    (hsigma : sigma ≠ 0) :
    renyiPower (order : ℝ) (volume : Measure (BSROutput d))
        (bsrGaussianCommonBaseDensity sigma base hsigma).density
        (sampledGaussianMixtureCommonBaseDensity q sigma shifted base
          hq0 hq1.le hsigma).density ≤
      ENNReal.ofReal (1 - q) ^ (1 - (order : ℝ)) := by
  let shiftedD := bsrGaussianCommonBaseDensity sigma shifted hsigma
  let baseD := bsrGaussianCommonBaseDensity sigma base hsigma
  unfold renyiPower
  calc
    (∫⁻ x, baseD.density x ^ (order : ℝ) *
        hiddenBernoulliDensity q shiftedD.density baseD.density x ^
          (1 - (order : ℝ)) ∂volume) ≤
        ∫⁻ x, ENNReal.ofReal (1 - q) ^ (1 - (order : ℝ)) *
          baseD.density x ∂volume := by
      apply lintegral_mono
      intro x
      exact base_rpow_mul_hiddenBernoulliDensity_rpow_le
        order q shiftedD.density baseD.density horder
        (fun y => by
          dsimp [baseD, bsrGaussianCommonBaseDensity]
          simp [bsrGaussianPdfReal_pos sigma base y hsigma])
        baseD.density_ne_top x
    _ = ENNReal.ofReal (1 - q) ^ (1 - (order : ℝ)) := by
      rw [MeasureTheory.lintegral_const_mul _ baseD.measurable_density,
        baseD.mass_one, mul_one]

/-- Forward integer-order sampled-Gaussian RDP cost. -/
def sampledGaussianForwardRho (order : ℕ) (q z : ℝ) : ℝ :=
  Real.log (sampledGaussianRenyiMoment order q z) / ((order : ℝ) - 1)

/-- Conservative reverse cost obtained from the unsampled mixture mass. -/
def sampledGaussianReverseRho (q : ℝ) : ℝ :=
  -Real.log (1 - q)

theorem renyiDivergenceUpperAt_sampledGaussianMixture_forward {d : ℕ}
    (order : ℕ) (q sigma : ℝ) (shifted base : BSROutput d)
    (horder : 2 ≤ order) (hq0 : 0 ≤ q) (hq1 : q ≤ 1)
    (hsigma : sigma ≠ 0) :
    RenyiDivergenceUpperAt (order : ℝ)
      (sampledGaussianForwardRho order q
        (bsrSqDist shifted base / sigma ^ 2))
      (volume : Measure (BSROutput d))
      (sampledGaussianMixtureCommonBaseDensity q sigma shifted base
        hq0 hq1 hsigma)
      (bsrGaussianCommonBaseDensity sigma base hsigma) := by
  have horderReal : (1 : ℝ) < order := by exact_mod_cast horder
  refine ⟨horderReal, ?_⟩
  unfold RenyiPowerUpper sampledGaussianForwardRho
  rw [renyiPower_sampledGaussianMixture_forward]
  apply le_of_eq
  congr 1
  let moment := sampledGaussianRenyiMoment order q
    (bsrSqDist shifted base / sigma ^ 2)
  have hmom : 0 < moment := sampledGaussianRenyiMoment_pos order _ hq0 hq1
  have hden : (order : ℝ) - 1 ≠ 0 := by linarith
  rw [show ((order : ℝ) - 1) *
      (Real.log (sampledGaussianRenyiMoment order q
        (bsrSqDist shifted base / sigma ^ 2)) / ((order : ℝ) - 1)) =
      Real.log (sampledGaussianRenyiMoment order q
        (bsrSqDist shifted base / sigma ^ 2)) by field_simp [hden]]
  exact (Real.exp_log hmom).symm

theorem renyiDivergenceUpperAt_sampledGaussianMixture_reverse {d : ℕ}
    (order : ℕ) (q sigma : ℝ) (shifted base : BSROutput d)
    (horder : 2 ≤ order) (hq0 : 0 ≤ q) (hq1 : q < 1)
    (hsigma : sigma ≠ 0) :
    RenyiDivergenceUpperAt (order : ℝ) (sampledGaussianReverseRho q)
      (volume : Measure (BSROutput d))
      (bsrGaussianCommonBaseDensity sigma base hsigma)
      (sampledGaussianMixtureCommonBaseDensity q sigma shifted base
        hq0 hq1.le hsigma) := by
  have horderReal : (1 : ℝ) < order := by exact_mod_cast horder
  refine ⟨horderReal, ?_⟩
  unfold RenyiPowerUpper sampledGaussianReverseRho
  apply (renyiPower_sampledGaussianMixture_reverse_le
    order q sigma shifted base (by omega) hq0 hq1 hsigma).trans
  apply le_of_eq
  rw [ENNReal.ofReal_rpow_of_pos (sub_pos.mpr hq1)]
  apply congrArg ENNReal.ofReal
  rw [Real.rpow_def_of_pos (sub_pos.mpr hq1)]
  congr 1
  ring

@[simp] theorem sampledGaussianMixtureCommonBaseDensity_one {d : ℕ}
    (sigma : ℝ) (shifted base : BSROutput d) (hsigma : sigma ≠ 0) :
    sampledGaussianMixtureCommonBaseDensity 1 sigma shifted base
        zero_le_one le_rfl hsigma =
      bsrGaussianCommonBaseDensity sigma shifted hsigma := by
  apply CommonBaseProbabilityDensity.ext
  funext x
  simp [sampledGaussianMixtureCommonBaseDensity, hiddenBernoulliDensity]

theorem renyiDivergenceUpperAt_sampledGaussianMixture_one_forward {d : ℕ}
    (order : ℕ) (sigma : ℝ) (shifted base : BSROutput d)
    (horder : 2 ≤ order) (hsigma : sigma ≠ 0) :
    RenyiDivergenceUpperAt (order : ℝ)
      ((order : ℝ) * bsrSqDist shifted base / (2 * sigma ^ 2))
      (volume : Measure (BSROutput d))
      (sampledGaussianMixtureCommonBaseDensity 1 sigma shifted base
        zero_le_one le_rfl hsigma)
      (bsrGaussianCommonBaseDensity sigma base hsigma) := by
  rw [sampledGaussianMixtureCommonBaseDensity_one]
  exact renyiDivergenceUpperAt_bsrGaussian (order : ℝ) sigma shifted base
    (by exact_mod_cast horder) hsigma

theorem renyiDivergenceUpperAt_sampledGaussianMixture_one_reverse {d : ℕ}
    (order : ℕ) (sigma : ℝ) (shifted base : BSROutput d)
    (horder : 2 ≤ order) (hsigma : sigma ≠ 0) :
    RenyiDivergenceUpperAt (order : ℝ)
      ((order : ℝ) * bsrSqDist shifted base / (2 * sigma ^ 2))
      (volume : Measure (BSROutput d))
      (bsrGaussianCommonBaseDensity sigma base hsigma)
      (sampledGaussianMixtureCommonBaseDensity 1 sigma shifted base
        zero_le_one le_rfl hsigma) := by
  rw [sampledGaussianMixtureCommonBaseDensity_one]
  have hdist : bsrSqDist base shifted = bsrSqDist shifted base := by
    unfold bsrSqDist
    apply Finset.sum_congr rfl
    intro i hi
    ring
  simpa [hdist] using
    (renyiDivergenceUpperAt_bsrGaussian (order : ℝ) sigma base shifted
      (by exact_mod_cast horder) hsigma)

/-- Public two-sided scalar cost.  The `max 0` makes nonnegativity explicit;
at full sampling the ordinary Gaussian cost is used. -/
def sampledGaussianTwoSidedRho (order : ℕ) (q z : ℝ) : ℝ :=
  if q = 1 then max 0 ((order : ℝ) * z / 2)
  else max 0 (max (sampledGaussianForwardRho order q z)
    (sampledGaussianReverseRho q))

theorem sampledGaussianTwoSidedRho_nonneg
    (order : ℕ) (q z : ℝ) :
    0 ≤ sampledGaussianTwoSidedRho order q z := by
  by_cases hq : q = 1 <;> simp [sampledGaussianTwoSidedRho, hq]

theorem continuous_sampledGaussianRenyiMoment
    (order : ℕ) (z : ℝ) :
    Continuous fun q => sampledGaussianRenyiMoment order q z := by
  unfold sampledGaussianRenyiMoment
  fun_prop

/-- Two-sided cost on the strict subunit-sampling branch. -/
def sampledGaussianSubunitTwoSidedRho (order : ℕ) (q z : ℝ) : ℝ :=
  max 0 (max (sampledGaussianForwardRho order q z)
    (sampledGaussianReverseRho q))

/-- Both ordered sampled-Gaussian costs vanish as the sampling probability
goes to zero. -/
theorem tendsto_sampledGaussianSubunitTwoSidedRho_zero
    (order : ℕ) (z : ℝ) :
    Filter.Tendsto (fun q => sampledGaussianSubunitTwoSidedRho order q z)
      (nhds 0) (nhds 0) := by
  have hm : ContinuousAt (fun q => sampledGaussianRenyiMoment order q z) 0 :=
    (continuous_sampledGaussianRenyiMoment order z).continuousAt
  have hf : ContinuousAt (fun q => sampledGaussianForwardRho order q z) 0 := by
    unfold sampledGaussianForwardRho
    exact (hm.log (by simp)).div_const _
  have hr : ContinuousAt sampledGaussianReverseRho 0 := by
    unfold sampledGaussianReverseRho
    exact ((continuousAt_const.sub continuousAt_id).log (by norm_num)).neg
  have hall : ContinuousAt
      (fun q => sampledGaussianSubunitTwoSidedRho order q z) 0 := by
    unfold sampledGaussianSubunitTwoSidedRho
    exact continuousAt_const.max (hf.max hr)
  have hval : sampledGaussianSubunitTwoSidedRho order 0 z = 0 := by
    simp [sampledGaussianSubunitTwoSidedRho, sampledGaussianForwardRho,
      sampledGaussianReverseRho]
  change Filter.Tendsto (fun q => sampledGaussianSubunitTwoSidedRho order q z)
    (nhds 0) (nhds (sampledGaussianSubunitTwoSidedRho order 0 z)) at hall
  simpa only [hval] using hall

/-- For every positive normalized separation, sufficiently small positive
sampling rates have strictly smaller two-sided cost than full sampling. -/
theorem exists_samplingRate_sampledGaussianSubunitTwoSidedRho_lt_full
    (order : ℕ) (z : ℝ) (horder : 2 ≤ order) (hz : 0 < z) :
    ∃ q0 : ℝ, 0 < q0 ∧ q0 < 1 ∧
      ∀ q : ℝ, 0 ≤ q → q < q0 →
        sampledGaussianSubunitTwoSidedRho order q z <
          (order : ℝ) * z / 2 := by
  let conservative := (order : ℝ) * z / 2
  have hconservative : 0 < conservative := by
    dsimp [conservative]
    positivity
  have ht := tendsto_sampledGaussianSubunitTwoSidedRho_zero order z
  have hev : ∀ᶠ q : ℝ in nhds 0,
      sampledGaussianSubunitTwoSidedRho order q z < conservative :=
    (tendsto_order.1 ht).2 conservative hconservative
  rcases Metric.eventually_nhds_iff.mp hev with ⟨delta, hdelta, hball⟩
  let q0 := min (delta / 2) (1 / 2 : ℝ)
  have hq0 : 0 < q0 := by
    dsimp [q0]
    exact lt_min (by positivity) (by norm_num)
  have hq01 : q0 < 1 :=
    lt_of_le_of_lt (min_le_right _ _) (by norm_num)
  refine ⟨q0, hq0, hq01, ?_⟩
  intro q hqnonneg hq
  apply hball
  rw [Real.dist_eq]
  rw [sub_zero, abs_of_nonneg hqnonneg]
  exact hq.trans_le <| (min_le_left _ _).trans (by linarith)

theorem exists_samplingRate_sampledGaussianRho_lt_conservative
    (order : ℕ) (sigma : ℝ) (horder : 2 ≤ order) (hsigma : 0 < sigma) :
    ∃ q0 : ℝ, 0 < q0 ∧ q0 < 1 ∧
      ∀ q : ℝ, 0 ≤ q → q < q0 →
        sampledGaussianSubunitTwoSidedRho order q (1 / sigma ^ 2) <
          (order : ℝ) / (2 * sigma ^ 2) := by
  obtain ⟨q0, hq0, hq01, hq⟩ :=
    exists_samplingRate_sampledGaussianSubunitTwoSidedRho_lt_full
      order (1 / sigma ^ 2) horder (by positivity)
  refine ⟨q0, hq0, hq01, ?_⟩
  intro q hqnonneg hqq0
  have h := hq q hqnonneg hqq0
  convert h using 1 <;> field_simp

theorem sampledGaussianRenyiMoment_two (q z : ℝ) :
    sampledGaussianRenyiMoment 2 q z =
      1 + q ^ 2 * (Real.exp z - 1) := by
  norm_num [sampledGaussianRenyiMoment, Finset.sum_range_succ]
  all_goals ring

theorem sampledGaussianRenyiMoment_three (q z : ℝ) :
    sampledGaussianRenyiMoment 3 q z =
      (1 - q) ^ 3 + 3 * (1 - q) ^ 2 * q +
        3 * (1 - q) * q ^ 2 * Real.exp z +
        q ^ 3 * Real.exp (3 * z) := by
  norm_num [sampledGaussianRenyiMoment, Finset.sum_range_succ]
  all_goals (try ring) <;> simp

/-- Regression guardrail: at zero sampling the amplified cost is zero and
cannot equal the positive mask-revealing Gaussian cost. -/
theorem sampledGaussianRho_zero_lt_conservative
    (order : ℕ) (sigma : ℝ) (horder : 2 ≤ order) (hsigma : 0 < sigma) :
    sampledGaussianSubunitTwoSidedRho order 0 (1 / sigma ^ 2) <
      (order : ℝ) / (2 * sigma ^ 2) := by
  simp [sampledGaussianSubunitTwoSidedRho, sampledGaussianForwardRho,
    sampledGaussianReverseRho]
  positivity

private theorem natCast_sq_sub_self_nonneg (j : ℕ) :
    0 ≤ (j : ℝ) ^ 2 - (j : ℝ) := by
  cases j with
  | zero => norm_num
  | succ j =>
      have h : (1 : ℝ) ≤ (j.succ : ℕ) := by exact_mod_cast Nat.succ_le_succ (Nat.zero_le j)
      nlinarith

theorem sampledGaussianRenyiMoment_mono_separation
    (order : ℕ) {q z₁ z₂ : ℝ}
    (hq0 : 0 ≤ q) (hq1 : q ≤ 1) (hz : z₁ ≤ z₂) :
    sampledGaussianRenyiMoment order q z₁ ≤
      sampledGaussianRenyiMoment order q z₂ := by
  rw [sampledGaussianRenyiMoment, sampledGaussianRenyiMoment]
  apply Finset.sum_le_sum
  intro j hj
  have hcoeff :
      0 ≤ (order.choose j : ℝ) * (1 - q) ^ (order - j) * q ^ j := by
    have hchoose : 0 ≤ (order.choose j : ℝ) := by positivity
    have hone : 0 ≤ 1 - q := sub_nonneg.mpr hq1
    positivity
  apply mul_le_mul_of_nonneg_left _ hcoeff
  apply Real.exp_le_exp.mpr
  have hj : 0 ≤ (j : ℝ) ^ 2 - (j : ℝ) :=
    natCast_sq_sub_self_nonneg j
  have hmul := mul_le_mul_of_nonneg_left hz hj
  nlinarith

theorem sampledGaussianForwardRho_mono_separation
    (order : ℕ) {q z₁ z₂ : ℝ} (horder : 2 ≤ order)
    (hq0 : 0 ≤ q) (hq1 : q ≤ 1) (hz : z₁ ≤ z₂) :
    sampledGaussianForwardRho order q z₁ ≤
      sampledGaussianForwardRho order q z₂ := by
  unfold sampledGaussianForwardRho
  have horderReal : (1 : ℝ) < order := by exact_mod_cast horder
  have hden : 0 < (order : ℝ) - 1 := by linarith
  apply (div_le_div_iff_of_pos_right hden).2
  exact Real.log_le_log
    (sampledGaussianRenyiMoment_pos order z₁ hq0 hq1)
    (sampledGaussianRenyiMoment_mono_separation order hq0 hq1 hz)

end

end Mf.DP
