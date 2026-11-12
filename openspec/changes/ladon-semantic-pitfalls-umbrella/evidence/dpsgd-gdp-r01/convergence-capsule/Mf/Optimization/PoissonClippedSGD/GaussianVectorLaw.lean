import Mf.Optimization.PoissonClippedSGD.GaussianMoments
import Mathlib.MeasureTheory.Function.L2Space

/-!
# Gaussian noise as a Euclidean vector law

Push the independent coordinate law through the Euclidean identification.
The resulting law supplies the centered, finite-second-moment noise used by
the recursive optimization mechanism, also when the noise scale is zero.
-/

namespace Mf.Optimization.PoissonClippedSGD
open MeasureTheory
noncomputable section

def gaussianVectorLaw (d : ℕ) (s : ℝ) : Measure (EuclideanSpace ℝ (Fin d)) :=
  (gaussianCoordinateLaw d s).map Mf.DP.toEuclidean

instance gaussianVectorLaw_isProbabilityMeasure (d : ℕ) (s : ℝ) :
    IsProbabilityMeasure (gaussianVectorLaw d s) := by
  unfold gaussianVectorLaw
  exact Measure.isProbabilityMeasure_map Mf.DP.measurable_toEuclidean.aemeasurable

theorem gaussianVectorLaw_integrable (d : ℕ) (s : ℝ) :
    Integrable (fun z : EuclideanSpace ℝ (Fin d) => z) (gaussianVectorLaw d s) := by
  exact (integrable_map_measure
    (g := fun z : EuclideanSpace ℝ (Fin d) => z)
    measurable_id.aestronglyMeasurable
    Mf.DP.measurable_toEuclidean.aemeasurable).2 (gaussianVector_integrable d s)

theorem gaussianVectorLaw_mean (d : ℕ) (s : ℝ) :
    (∫ z, z ∂gaussianVectorLaw d s) = 0 := by
  calc
    _ = ∫ z, Mf.DP.toEuclidean z ∂gaussianCoordinateLaw d s :=
      integral_map Mf.DP.measurable_toEuclidean.aemeasurable
        (f := fun z : EuclideanSpace ℝ (Fin d) => z)
        measurable_id.aestronglyMeasurable
    _ = 0 := integral_gaussianVector d s

theorem gaussianVectorLaw_normSq_integrable (d : ℕ) (s : ℝ) :
    Integrable (fun z : EuclideanSpace ℝ (Fin d) => ‖z‖ ^ 2)
      (gaussianVectorLaw d s) := by
  exact (integrable_map_measure (by fun_prop)
    Mf.DP.measurable_toEuclidean.aemeasurable).2 (gaussianNormSq_integrable d s)

theorem gaussianVectorLaw_energy {d : ℕ} (hd : 0 < d) (s : ℝ) :
    (∫ z, ‖z‖ ^ 2 ∂gaussianVectorLaw d s) = s ^ 2 := by
  rw [gaussianVectorLaw, integral_map Mf.DP.measurable_toEuclidean.aemeasurable
    (by fun_prop)]
  exact integral_gaussianNormSq hd s

theorem gaussianVectorLaw_memLp (d : ℕ) (s : ℝ) :
    MemLp (fun z : EuclideanSpace ℝ (Fin d) => z) 2 (gaussianVectorLaw d s) :=
  (memLp_two_iff_integrable_sq_norm measurable_id.aestronglyMeasurable).2
    (gaussianVectorLaw_normSq_integrable d s)

/-- Coordinate scale after normalizing the noisy sum matches the total scale. -/
theorem normalized_noise_coordinate_scale (n d : ℕ) (q c sigmaMult : ℝ)
    (hd : 0 < d) :
    (c * Real.sqrt (d : ℝ) / (q * n) * sigmaMult) / Real.sqrt (d : ℝ) =
      c * sigmaMult / (q * n) := by
  have hd' : Real.sqrt (d : ℝ) ≠ 0 := by positivity
  field_simp

end
end Mf.Optimization.PoissonClippedSGD
