import Mf.Optimization.PoissonClippedSGD.Rates
import Mf.Optimization.PoissonClippedSGD.GaussianVectorLaw
import Mf.Optimization.GDPApproximationBatchComparativeStatics

/-!
# GDP-formula noise in the Poisson SGD stationarity bound

The subsampled privacy CLT of Bu et al., *Deep Learning with Gaussian
Differential Privacy* (`implement.tex`, the displayed formula for `mu_CLT`),
uses a logarithmic noise formula; its source is preserved under
`paper/convergence-rates-batch-size/study/paper/deep-learning-with-gaussian-differential-privacy/`.
Here that formula specifies an actual finite
Gaussian noise law and its optimization coefficient. Finite privacy requires
an additional mechanism theorem. The full-sampling formula is defined separately.
-/

namespace Mf.Optimization.PoissonClippedSGD
noncomputable section

/-- Raw subsampled-CLT multiplier; positivity lemmas require positive inputs. -/
def gdpFormulaMultiplier (q T mu : ℝ) : ℝ :=
  GDPApproximationBatchComparativeStatics.noise (1 / (T * q ^ 2)) (mu ^ 2)

/-- Total Euclidean noise scale after the public expected-batch normalization. -/
def gdpFormulaNoise (n d : ℕ) (q T c mu : ℝ) : ℝ :=
  c * Real.sqrt (d : ℝ) / (q * n) * gdpFormulaMultiplier q T mu

/-- Gaussian composition multiplier at full sampling, kept separate from the CLT formula. -/
def fullGaussianMultiplier (T mu : ℝ) : ℝ := Real.sqrt T / mu

/-- Post-normalization total noise scale for the full-sampling formula. -/
def fullGaussianNoise (n d : ℕ) (T c mu : ℝ) : ℝ :=
  c * Real.sqrt (d : ℝ) / n * fullGaussianMultiplier T mu

/-- Squared total noise scale, expressed without nested square roots. -/
def gdpFormulaVariance (n d q T c mu : ℝ) : ℝ :=
  c ^ 2 * d / (n ^ 2 * q ^ 2 * Real.log (1 + mu ^ 2 / (T * q ^ 2)))

/-- Poisson sampling plus the total Gaussian variance for the chosen formula. -/
def gdpTotalVariance (n d q T c sigma mu : ℝ) : ℝ :=
  (1 - q) / (q * n) * sigma ^ 2 + gdpFormulaVariance n d q T c mu

/-- The exact unsplit finite SGD coefficient after logarithmic substitution. -/
def gdpFormulaD (eta L n d q sigma F T c mu : ℝ) : ℝ :=
  4 * F / (eta * T) + 8 * sigma ^ 4 / c ^ 2 +
    2 * eta * L * gdpTotalVariance n d q T c sigma mu

/-- The expected-gradient upper bound as a function of the descent coefficient. -/
def stationarityUpper (c D : ℝ) : ℝ := Real.sqrt D + D / c

theorem gdpFormulaMultiplier_eq (q T mu : ℝ) :
    gdpFormulaMultiplier q T mu =
      1 / Real.sqrt (Real.log (1 + mu ^ 2 / (T * q ^ 2))) := by
  simp only [gdpFormulaMultiplier, GDPApproximationBatchComparativeStatics.noise]
  congr 3
  ring

theorem gdpFormula_log_pos {q T mu : ℝ} (hq : 0 < q) (hT : 0 < T)
    (hmu : 0 < mu) : 0 < Real.log (1 + mu ^ 2 / (T * q ^ 2)) := by
  apply Real.log_pos
  have : 0 < mu ^ 2 / (T * q ^ 2) := by positivity
  linarith

theorem gdpFormulaMultiplier_pos {q T mu : ℝ} (hq : 0 < q) (hT : 0 < T)
    (hmu : 0 < mu) : 0 < gdpFormulaMultiplier q T mu :=
  GDPApproximationBatchComparativeStatics.noise_pos (by positivity) (by positivity)

theorem gdpFormulaNoise_nonneg {n d : ℕ} {q T c mu : ℝ}
    (hq : 0 < q) (hT : 0 < T) (hc : 0 ≤ c) (hmu : 0 < mu) :
    0 ≤ gdpFormulaNoise n d q T c mu := by
  unfold gdpFormulaNoise
  exact mul_nonneg (by positivity) (gdpFormulaMultiplier_pos hq hT hmu).le

theorem gdpFormulaNoise_sq {n d : ℕ} {q T c mu : ℝ}
    (hq : 0 < q) (hT : 0 < T) (hmu : 0 < mu) :
    gdpFormulaNoise n d q T c mu ^ 2 =
      gdpFormulaVariance n d q T c mu := by
  rw [gdpFormulaNoise, gdpFormulaMultiplier_eq]
  unfold gdpFormulaVariance
  rw [mul_pow, div_pow, mul_pow, Real.sq_sqrt (Nat.cast_nonneg d),
    one_div_pow, Real.sq_sqrt (gdpFormula_log_pos hq hT hmu).le]
  ring

/-- The law used by SGD has the total energy appearing in the substituted bound. -/
theorem gdpFormulaNoise_energy {n d : ℕ} (hd : 0 < d) {q T c mu : ℝ}
    (hq : 0 < q) (hT : 0 < T) (hmu : 0 < mu) :
    (∫ z, ‖z‖ ^ 2 ∂gaussianVectorLaw d (gdpFormulaNoise n d q T c mu)) =
      gdpFormulaVariance n d q T c mu := by
  rw [gaussianVectorLaw_energy hd, gdpFormulaNoise_sq hq hT hmu]

theorem poissonRateD_eq_gdpFormulaD {n d : ℕ} (eta L sigma F c : ℝ)
    {q T mu : ℝ} (hq : 0 < q) (hT : 0 < T) (hmu : 0 < mu) :
    poissonRateD eta L ((1 - q) / (q * n)) sigma
        (gdpFormulaNoise n d q T c mu) F T c =
      gdpFormulaD eta L n d q sigma F T c mu := by
  simp only [poissonRateD, gdpFormulaD, gdpTotalVariance, gdpFormulaNoise_sq hq hT hmu]

theorem gdpFormulaD_expanded (eta L n d q sigma F T c mu : ℝ) :
    gdpFormulaD eta L n d q sigma F T c mu =
      4 * F / (eta * T) + 8 * sigma ^ 4 / c ^ 2 +
      2 * eta * L * ((1 - q) / (q * n) * sigma ^ 2) +
      2 * eta * L * c ^ 2 * d /
        (n ^ 2 * q ^ 2 * Real.log (1 + mu ^ 2 / (T * q ^ 2))) := by
  unfold gdpFormulaD gdpTotalVariance gdpFormulaVariance
  ring

theorem fullGaussianNoise_sq (n d : ℕ) {T : ℝ} (hT : 0 ≤ T) (c mu : ℝ) :
    fullGaussianNoise n d T c mu ^ 2 = c ^ 2 * d * T / ((n : ℝ) ^ 2 * mu ^ 2) := by
  unfold fullGaussianNoise fullGaussianMultiplier
  rw [mul_pow, div_pow, mul_pow, Real.sq_sqrt (Nat.cast_nonneg d),
    div_pow, Real.sq_sqrt hT]
  ring

theorem stationarityUpper_mono {c D D' : ℝ} (hc : 0 ≤ c) (h : D ≤ D') :
    stationarityUpper c D ≤ stationarityUpper c D' := by
  exact add_le_add (Real.sqrt_le_sqrt h) (div_le_div_of_nonneg_right h hc)

end
end Mf.Optimization.PoissonClippedSGD
